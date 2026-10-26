"""Tests for the REPL and command-line entry point.

The REPL and CLI logic tests use a fake interpreter so they are stable while
the full lexer, parser, and evaluator are still landing. The
``integration``-marked tests at the end use the real ``Interpreter`` and are
expected to pass only after INT-001.
"""

from types import SimpleNamespace

import pytest

import minicalc.__main__ as cli
from minicalc.display import banner, help_text
from minicalc.errors import LexError, SourcePos
from minicalc.interpreter import Interpreter, LineOutcome, Result
from minicalc.repl import Repl


class FakeEnvironment:
    """Environment stand-in for REPL meta-command tests.

    Attributes:
        variables: User-defined name-to-value bindings.
        ans: Value of the last successful statement, or ``None``.
    """

    def __init__(
        self,
        variables: dict[str, int] | None = None,
        ans: int | None = None,
    ) -> None:
        """Create a fake environment.

        Args:
            variables: Initial user bindings.
            ans: Initial ``ans`` value.
        """
        self.variables = dict(variables or {})
        self.ans = ans

    def items(self) -> list[tuple[str, int]]:
        """Return bindings sorted by name."""
        return sorted(self.variables.items())

    def clear(self) -> None:
        """Remove all bindings and ``ans``."""
        self.variables.clear()
        self.ans = None


class FakeInterpreter:
    """Interpreter stand-in returning scripted results or exceptions.

    Attributes:
        env: The fake environment exposed to the REPL.
        results: Queue of ``Result`` objects or exceptions for ``run_line``.
        calls: ``(source, line_no)`` pairs passed to ``run_line``.
        outcomes: Outcomes returned by ``run_source``.
        source_error: Exception raised by ``run_source`` when set.
        source_text: The last text passed to ``run_source``.
    """

    def __init__(
        self,
        results: list[object] | None = None,
        env: FakeEnvironment | None = None,
        outcomes: list[LineOutcome] | None = None,
        source_error: BaseException | None = None,
    ) -> None:
        """Create the fake with the given script.

        Args:
            results: ``Result`` objects or exceptions yielded by ``run_line``.
            env: Environment to expose.
            outcomes: Outcomes returned by ``run_source``.
            source_error: Exception raised by ``run_source`` when set.
        """
        self.env = env if env is not None else FakeEnvironment()
        self.results = list(results or [])
        self.calls: list[tuple[str, int]] = []
        self.outcomes = list(outcomes or [])
        self.source_error = source_error
        self.source_text = ""

    def run_line(self, source: str, line_no: int = 1) -> Result:
        """Return the next scripted result or raise the next exception."""
        self.calls.append((source, line_no))
        if not self.results:
            return Result("empty")
        item = self.results.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item  # type: ignore[return-value]

    def run_source(self, text: str) -> list[LineOutcome]:
        """Return the scripted outcomes or raise the scripted exception."""
        self.source_text = text
        if self.source_error is not None:
            raise self.source_error
        return list(self.outcomes)


def _scripted(lines: list[str]):
    """Build an ``input_fn`` that yields lines and then raises EOFError.

    Args:
        lines: The lines to return in order.

    Returns:
        A callable accepting the prompt and returning the next line.
    """
    iterator = iter(lines)

    def input_fn(prompt: str) -> str:
        assert prompt == Repl.PROMPT
        try:
            return next(iterator)
        except StopIteration:
            raise EOFError from None

    return input_fn


def _run_repl(
    lines: list[str],
    interpreter: FakeInterpreter,
    color: bool = False,
) -> tuple[int, list[str]]:
    """Run a REPL with scripted input and collected output.

    Args:
        lines: Input lines; EOF follows after them.
        interpreter: The fake interpreter to use.
        color: Whether the REPL should style output.

    Returns:
        The ``run()`` return code and the output chunks in order.
    """
    output: list[str] = []
    code = Repl(
        interpreter,
        input_fn=_scripted(lines),
        output_fn=output.append,
        color=color,
    ).run()
    return code, output


# ---------------------------------------------------------------------------
# REPL behavior
# ---------------------------------------------------------------------------


def test_banner_printed_once_then_quit() -> None:
    """The banner is the first and only output for an immediate ``:quit``."""
    code, output = _run_repl([":quit"], FakeInterpreter())
    assert code == 0
    assert output == [banner()]


def test_blank_and_whitespace_lines_produce_no_output() -> None:
    """Blank lines never reach the interpreter and print nothing."""
    fake = FakeInterpreter()
    code, output = _run_repl(["", "   ", "\t", ":quit"], fake)
    assert code == 0
    assert output == [banner()]
    assert fake.calls == []


def test_value_assignment_and_empty_lines() -> None:
    """Results print in contract form and empty results print nothing."""
    fake = FakeInterpreter(
        [
            Result("value", 42),
            Result("assign", 7, "x"),
            Result("empty"),
        ]
    )
    code, output = _run_repl(["42", "x = 7", "# comment", ":quit"], fake)
    assert code == 0
    assert output[1:] == ["= 42", "x = 7"]
    assert fake.calls == [("42", 1), ("x = 7", 1), ("# comment", 1)]


def test_help_command_prints_help_text() -> None:
    """``:help`` prints the shared help text without calling the interpreter."""
    fake = FakeInterpreter()
    _, output = _run_repl([":help", ":quit"], fake)
    assert output[1] == help_text()
    assert fake.calls == []


def test_vars_with_no_values() -> None:
    """``:vars`` reports when there is nothing to show."""
    _, output = _run_repl([":vars", ":quit"], FakeInterpreter())
    assert output[1] == "(no variables)"


def test_vars_prints_ans_first_and_aligns_names() -> None:
    """``ans`` comes first, then variables sorted and column-aligned."""
    env = FakeEnvironment({"long": 9, "x": 7}, ans=42)
    _, output = _run_repl([":vars", ":quit"], FakeInterpreter(env=env))
    assert output[1:] == ["ans  = 42", "long = 9", "x    = 7"]


def test_vars_prints_ans_alone() -> None:
    """An ``ans`` value is shown even when no variables exist."""
    env = FakeEnvironment(ans=42)
    _, output = _run_repl([":vars", ":quit"], FakeInterpreter(env=env))
    assert output[1] == "ans = 42"


def test_clear_reports_variable_count_and_resets_env() -> None:
    """``:clear`` counts variables (not ``ans``) and empties the environment."""
    env = FakeEnvironment({"x": 1, "y": 2}, ans=3)
    fake = FakeInterpreter(env=env)
    _, output = _run_repl([":clear", ":quit"], fake)
    assert output[1] == "Cleared 2 variable(s)."
    assert env.variables == {}
    assert env.ans is None


def test_quit_and_q_both_exit_without_reading_more() -> None:
    """``:quit`` and ``:q`` stop the loop and never call the interpreter."""
    for command in (":quit", ":q"):
        fake = FakeInterpreter()
        code, output = _run_repl([command, "42"], fake)
        assert code == 0
        assert output == [banner()]
        assert fake.calls == []


def test_unknown_command_message() -> None:
    """Unknown meta-commands are reported as plain text, not error objects."""
    _, output = _run_repl([":foo", ":quit"], FakeInterpreter())
    assert output[1] == "Unknown command ':foo'. Type :help for a list."


def test_meta_commands_never_reach_the_interpreter() -> None:
    """Every known meta-command is handled by the REPL itself."""
    fake = FakeInterpreter()
    _run_repl([":help", ":vars", ":clear", ":q"], fake)
    assert fake.calls == []


def test_minicalc_error_renders_then_blank_line() -> None:
    """A MiniCalc error renders with a caret and is followed by a blank line."""
    error = LexError("illegal character '@'", SourcePos(1, 3)).with_source("2 @ 3")
    fake = FakeInterpreter([error, Result("value", 5)])
    _, output = _run_repl(["2 @ 3", "5", ":quit"], fake)
    assert output[1] == error.render(False)
    assert output[2] == ""
    assert output[3] == "= 5"


def test_colored_error_rendering() -> None:
    """In color mode, the rendered error carries ANSI styling."""
    error = LexError("bad", SourcePos(1, 2)).with_source("2 @")
    _, output = _run_repl(["2 @", ":quit"], FakeInterpreter([error]), color=True)
    assert output[1] == error.render(True)
    assert "\x1b[" in output[1]


def test_foreign_exception_in_run_line_keeps_repl_alive() -> None:
    """A non-MiniCalc exception becomes ``Internal error:`` and the REPL lives."""
    fake = FakeInterpreter([RuntimeError("boom"), Result("value", 5)])
    code, output = _run_repl(["1 + 1", "2 + 2", ":quit"], fake)
    assert code == 0
    assert output[1] == "Internal error: RuntimeError: boom"
    assert output[2] == "= 5"
    assert fake.calls == [("1 + 1", 1), ("2 + 2", 1)]


def test_foreign_exception_from_input_keeps_repl_alive() -> None:
    """A foreign input exception is reported and the loop continues."""
    state = {"calls": 0}

    def flaky_input(prompt: str) -> str:
        state["calls"] += 1
        if state["calls"] == 1:
            raise RuntimeError("reader broke")
        return ":quit"

    output: list[str] = []
    code = Repl(FakeInterpreter(), input_fn=flaky_input, output_fn=output.append).run()
    assert code == 0
    assert output[1] == "Internal error: RuntimeError: reader broke"


def test_eof_exits_cleanly_with_newline() -> None:
    """EOF (Ctrl-D) prints a newline and returns 0."""
    code, output = _run_repl([], FakeInterpreter())
    assert code == 0
    assert output == [banner(), ""]


def test_keyboard_interrupt_exits_cleanly_with_newline() -> None:
    """Ctrl-C at the prompt prints a newline and returns 0."""

    def interrupting_input(prompt: str) -> str:
        raise KeyboardInterrupt

    output: list[str] = []
    code = Repl(
        FakeInterpreter(), input_fn=interrupting_input, output_fn=output.append
    ).run()
    assert code == 0
    assert output == [banner(), ""]


def test_plain_mode_never_emits_ansi() -> None:
    """With color disabled, no escape sequence appears in any output."""
    fake = FakeInterpreter([Result("value", 42)])
    _, output = _run_repl(["42", ":help", ":vars", ":quit"], fake)
    assert all("\x1b" not in chunk for chunk in output)


def test_color_mode_styles_results_and_banner() -> None:
    """With color enabled, values and the banner use ANSI styling."""
    fake = FakeInterpreter([Result("value", 42)])
    _, output = _run_repl(["42", ":quit"], fake, color=True)
    assert "\x1b[" in output[0]
    assert output[1] == "= \x1b[1;32m42\x1b[0m"


# ---------------------------------------------------------------------------
# CLI behavior
# ---------------------------------------------------------------------------


def _install(monkeypatch: pytest.MonkeyPatch, fake: FakeInterpreter,
             color: bool = False) -> None:
    """Install a fake interpreter and a fixed color decision in the CLI.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        fake: The fake interpreter to construct.
        color: The value returned by ``use_color``.
    """
    monkeypatch.setattr(cli, "Interpreter", lambda: fake)
    monkeypatch.setattr(cli, "use_color", lambda stream: color)


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """``--version`` prints the exact version and exits 0."""
    assert cli.main(["--version"]) == 0
    assert capsys.readouterr().out == "MiniCalc 1.0.0\n"


def test_help_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """``--help`` prints usage and exits 0."""
    assert cli.main(["--help"]) == 0
    assert "usage: minicalc" in capsys.readouterr().out


def test_expr_42_with_real_interpreter(capsys: pytest.CaptureFixture[str]) -> None:
    """The acceptance one-shot works even with the walking-skeleton stages."""
    assert cli.main(["-e", "42"]) == 0
    assert capsys.readouterr().out == "= 42\n"


def test_expr_assignment_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``-e`` prints assignment results as ``name = value``."""
    _install(monkeypatch, FakeInterpreter([Result("assign", 7, "x")]))
    assert cli.main(["-e", "x = 7"]) == 0
    assert capsys.readouterr().out == "x = 7\n"


def test_expr_empty_result_prints_nothing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An empty expression result exits 0 without a stray blank line."""
    _install(monkeypatch, FakeInterpreter([Result("empty")]))
    assert cli.main(["-e", ""]) == 0
    assert capsys.readouterr().out == ""


def test_expr_minicalc_error_goes_to_stderr(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A MiniCalc error renders to stderr and exits 1."""
    error = LexError("bad character '@'", SourcePos(1, 3)).with_source("2 @")
    _install(monkeypatch, FakeInterpreter([error]))
    assert cli.main(["-e", "2 @"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == error.render(False)


def test_expr_foreign_exception_is_reported(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A foreign exception is one ``Internal error:`` line, not a traceback."""
    _install(monkeypatch, FakeInterpreter([RuntimeError("boom")]))
    assert cli.main(["-e", "1"]) == 1
    captured = capsys.readouterr()
    assert captured.err == "Internal error: RuntimeError: boom\n"
    assert "Traceback" not in captured.err


def test_file_mode_reports_results_and_continues_after_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    """Script results go to stdout, errors to stderr, and later lines still run."""
    error = LexError("bad character '@'", SourcePos(2, 3)).with_source("2 @ 3")
    outcomes = [
        LineOutcome(1, "42", Result("value", 42), None),
        LineOutcome(2, "2 @ 3", None, error),
        LineOutcome(3, "", Result("empty"), None),
        LineOutcome(4, "x = 7", Result("assign", 7, "x"), None),
    ]
    fake = FakeInterpreter(outcomes=outcomes)
    _install(monkeypatch, fake)
    script = tmp_path / "script.mc"
    script.write_text("42\n2 @ 3\n\nx = 7\n", encoding="utf-8")

    assert cli.main([str(script)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["line 1: = 42", "line 4: x = 7"]
    assert captured.err.strip() == error.render(False)
    assert fake.source_text == "42\n2 @ 3\n\nx = 7\n"


def test_file_mode_success_exits_zero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    """A script with no errors exits 0."""
    outcomes = [LineOutcome(1, "42", Result("value", 42), None)]
    _install(monkeypatch, FakeInterpreter(outcomes=outcomes))
    script = tmp_path / "ok.mc"
    script.write_text("42\n", encoding="utf-8")
    assert cli.main([str(script)]) == 0
    assert capsys.readouterr().out == "line 1: = 42\n"


def test_file_mode_foreign_exception_is_reported(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    """A foreign ``run_source`` exception is reported and exits nonzero."""
    _install(monkeypatch, FakeInterpreter(source_error=RuntimeError("boom")))
    script = tmp_path / "bad.mc"
    script.write_text("42\n", encoding="utf-8")
    assert cli.main([str(script)]) == 1
    captured = capsys.readouterr()
    assert captured.err == "Internal error: RuntimeError: boom\n"
    assert "Traceback" not in captured.err


def test_unreadable_file_is_a_usage_error(
    capsys: pytest.CaptureFixture[str], tmp_path
) -> None:
    """A missing script reports a message on stderr and exits 2."""
    missing = tmp_path / "missing.mc"
    assert cli.main([str(missing)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "cannot read" in captured.err
    assert str(missing) in captured.err
    assert "Traceback" not in captured.err


def test_undecodable_file_is_a_usage_error(
    capsys: pytest.CaptureFixture[str], tmp_path
) -> None:
    """A non-UTF-8 script reports a message on stderr and exits 2."""
    script = tmp_path / "binary.mc"
    script.write_bytes(b"\xff\xfe\x00")
    assert cli.main([str(script)]) == 2
    captured = capsys.readouterr()
    assert "cannot read" in captured.err
    assert "Traceback" not in captured.err


def test_file_and_expr_together_is_a_usage_error(
    capsys: pytest.CaptureFixture[str], tmp_path
) -> None:
    """Supplying both a file and ``-e`` exits 2 with a usage line."""
    script = tmp_path / "x.mc"
    assert cli.main([str(script), "-e", "1"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "usage: minicalc" in captured.err
    assert "cannot be used together" in captured.err


def test_no_ansi_when_stdout_is_not_a_tty(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """With no TTY, ``-e`` output is plain even without ``--no-color``."""
    monkeypatch.setattr(cli, "Interpreter", lambda: FakeInterpreter([Result("value", 42)]))
    assert cli.main(["-e", "42"]) == 0
    assert "\x1b" not in capsys.readouterr().out


def test_no_color_flag_disables_styling(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--no-color`` overrides a TTY that would otherwise enable color."""
    monkeypatch.setattr(cli, "use_color", lambda stream: True)
    monkeypatch.setattr(cli, "Interpreter", lambda: FakeInterpreter([Result("value", 42)]))
    assert cli.main(["-e", "42"]) == 0
    assert "\x1b[" in capsys.readouterr().out

    monkeypatch.setattr(
        cli, "Interpreter", lambda: FakeInterpreter([Result("value", 42)])
    )
    assert cli.main(["--no-color", "-e", "42"]) == 0
    assert "\x1b" not in capsys.readouterr().out


def test_no_args_dispatches_to_repl(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """No arguments constructs a REPL with the interpreter and color choice."""
    created: dict[str, object] = {}

    def fake_repl(interpreter, input_fn=input, output_fn=print, color=False):
        created["interpreter"] = interpreter
        created["color"] = color
        return SimpleNamespace(run=lambda: 0)

    fake = FakeInterpreter()
    monkeypatch.setattr(cli, "Interpreter", lambda: fake)
    monkeypatch.setattr(cli, "use_color", lambda stream: True)
    monkeypatch.setattr(cli, "Repl", fake_repl)
    assert cli.main([]) == 0
    assert created == {"interpreter": fake, "color": True}


def test_repl_construction_failure_is_an_internal_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A failure outside the REPL loop is reported without a traceback."""
    def broken_repl(interpreter, input_fn=input, output_fn=print, color=False):
        return SimpleNamespace(run=lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    monkeypatch.setattr(cli, "Interpreter", lambda: FakeInterpreter())
    monkeypatch.setattr(cli, "use_color", lambda stream: False)
    monkeypatch.setattr(cli, "Repl", broken_repl)
    assert cli.main([]) == 1
    captured = capsys.readouterr()
    assert captured.err == "Internal error: RuntimeError: boom\n"
    assert "Traceback" not in captured.err


# ---------------------------------------------------------------------------
# Integration tests (real stage pipeline; green after INT-001)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_repl_arithmetic_with_real_interpreter() -> None:
    """The REPL evaluates arithmetic, assignments, and ``ans`` end to end."""
    output: list[str] = []
    code = Repl(
        Interpreter(),
        input_fn=_scripted(["2 + 3 * 4", "x = 7", "ans * x", ":quit"]),
        output_fn=output.append,
    ).run()
    assert code == 0
    assert output[1:] == ["= 14", "x = 7", "= 98"]


@pytest.mark.integration
def test_cli_expression_arithmetic_with_real_interpreter(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``-e`` evaluates a full expression with the real pipeline."""
    assert cli.main(["-e", "1 + 2"]) == 0
    assert capsys.readouterr().out == "= 3\n"


@pytest.mark.integration
def test_cli_script_arithmetic_with_real_interpreter(
    capsys: pytest.CaptureFixture[str], tmp_path
) -> None:
    """Script mode runs the real pipeline and preserves state across lines."""
    script = tmp_path / "calc.mc"
    script.write_text("2 + 3 * 4\nx = 7\nans * x\n", encoding="utf-8")
    assert cli.main([str(script)]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "line 1: = 14",
        "line 2: x = 7",
        "line 3: = 98",
    ]
