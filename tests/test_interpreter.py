"""Facade-level tests for the walking skeleton (CORE-003)."""

import pytest

from minicalc.errors import EvalError, LexError, MiniCalcError, ParseError
from minicalc.evaluator import Evaluator
from minicalc.interpreter import Interpreter, LineOutcome, Result


def test_value_line_repr() -> None:
    """The acceptance snippet prints the exact ``Result`` repr."""
    assert repr(Interpreter().run_line("42")) == "Result(kind='value', value=42, name=None)"


def test_blank_and_comment_lines_are_empty() -> None:
    """Empty, whitespace-only, and comment-only lines produce no value."""
    interp = Interpreter()
    for source in ("", "   ", "\t", "# comment", "   # note"):
        assert interp.run_line(source) == Result("empty")


def test_error_carries_source_line_and_position() -> None:
    """A failing line re-raises with ``source_line`` attached."""
    with pytest.raises(ParseError) as info:
        Interpreter().run_line("2 3", 3)
    assert info.value.source_line == "2 3"
    assert info.value.pos is not None
    assert info.value.pos.line == 3


def test_failed_line_leaves_environment_unchanged() -> None:
    """A lex error does not touch variables or ``ans``."""
    interp = Interpreter()
    interp.env.set("x", 5)
    interp.env.record_result(7)
    with pytest.raises(LexError):
        interp.run_line("2 @ 3")
    assert interp.env.variables == {"x": 5}
    assert interp.env.ans == 7


def test_run_source_numbers_lines_and_continues() -> None:
    """Errors are captured per line and later lines still run."""
    outcomes = Interpreter().run_source("2 3\n\n# note\n42")
    assert [outcome.line_no for outcome in outcomes] == [1, 2, 3, 4]
    assert isinstance(outcomes[0].error, ParseError)
    assert outcomes[0].result is None
    assert outcomes[1].result == Result("empty")
    assert outcomes[2].result == Result("empty")
    assert outcomes[3].result == Result("value", 42)


def test_run_source_never_raises_minicalc_error() -> None:
    """The batch facade captures every error in ``LineOutcome``."""
    outcomes = Interpreter().run_source("2 @ 3\n99999999999\n42")
    assert all(isinstance(outcome, LineOutcome) for outcome in outcomes)
    assert all(isinstance(outcome.error, MiniCalcError) for outcome in outcomes[:2])
    assert outcomes[2].result == Result("value", 42)


def test_run_source_handles_crlf() -> None:
    """Only ``\\n`` splits lines; a trailing ``\\r`` is stripped."""
    outcomes = Interpreter().run_source("42\r\n43\r\n")
    assert [outcome.result for outcome in outcomes] == [
        Result("value", 42),
        Result("value", 43),
    ]
    assert [outcome.source for outcome in outcomes] == ["42", "43"]


def test_run_source_does_not_split_on_non_newline_breaks() -> None:
    """Form feed and U+2028 are illegal characters, not line separators."""
    outcomes = Interpreter().run_source("1\x0c2\n1\u20282\n")
    assert len(outcomes) == 2
    assert outcomes[0].error is not None
    assert outcomes[0].error.canonical() == "ERR LexError 1:2"
    assert outcomes[1].error is not None
    assert outcomes[1].error.canonical() == "ERR LexError 2:2"


def test_recursion_error_becomes_eval_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """An escaping RecursionError is converted, never leaked."""
    def recurse(self: Evaluator, node: object) -> int:
        return recurse(self, node)

    monkeypatch.setattr(Evaluator, "evaluate", recurse)
    with pytest.raises(EvalError) as info:
        Interpreter().run_line("42")
    assert str(info.value) == "expression is too deeply nested"
    assert info.value.pos is not None
    assert info.value.pos.col == 1


def test_long_line_is_a_lex_error_at_column_1001() -> None:
    """The 1000-character cap is enforced before tokenizing."""
    with pytest.raises(LexError) as info:
        Interpreter().run_line(" " * 1001)
    assert info.value.pos is not None
    assert info.value.pos.col == 1001


def test_golden_smoke_case_runs_through_facade() -> None:
    """The CORE-002 smoke file now exercises the real pipeline."""
    from pathlib import Path

    smoke = Path(__file__).resolve().parent / "golden" / "smoke.mc"
    outcomes = Interpreter().run_source(smoke.read_text(encoding="utf-8"))
    assert [outcome.result for outcome in outcomes] == [Result("value", 42)]
