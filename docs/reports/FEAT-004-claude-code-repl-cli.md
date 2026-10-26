# Task Report: FEAT-004 — REPL, CLI, and display

**Date:** 2026-10-26
**Agent:** claude-code
**Task ID:** FEAT-004
**Status:** needs-review
**Commit:** `feat(FEAT-004): add REPL, CLI and display` (single amended task commit on `task/FEAT-004`)
**Worktree:** `/home/lukexodus/projects/minicalc-FEAT-004` (branch `task/FEAT-004`)
**Patch File:** `patch/FEAT-004-claude-code-repl-cli.patch`

---

## 1. Executive Summary

Implemented the third user-facing layer of MiniCalc: `display.py` (plain/ANSI
formatting, banner, help), `repl.py` (the interactive loop and meta-commands),
`minicalc/__main__.py` (REPL, script, and `-e` modes with argparse), and the
root `main.py` shim. All logic talks only to the stable `Interpreter` facade.
The implementation follows spec section 8, contract section 11, and [D-09], and
records the wording/spacing choices the spec left open in [D-14].

The non-integration suite is green (`129 passed, 3 deselected`). The three
`integration`-marked tests exercise the real stage pipeline and intentionally
fail until FEAT-001/002/003 are merged by INT-001 (`3 failed, 129 passed`).
Both acceptance commands pass: `--version` prints `MiniCalc 1.0.0` and
`-e 42` prints `= 42` with exit 0.

Foreign-exception policy (APC review requirement): the REPL catches any
`Exception` at the top level of its line loop and input read, prints one
`Internal error: <Type>: <message>` line to the injected output, and keeps the
session alive. Script mode wraps `Interpreter.run_source`; a foreign exception
prints the same line to stderr and returns exit 1 (the single `run_source`
call cannot resume the remaining lines without duplicating the facade), while
the per-outcome formatting loop catches and continues past its own errors.
`-e` mode reports foreign exceptions the same way and exits 1. No traceback
escapes and `minicalc/interpreter.py` was not modified.

---

## 2. Implementation Details

### 2.1 Changes Made

- `minicalc/display.py`: `use_color` (TTY plus absent `NO_COLOR`, tolerant of
  missing/raising `isatty`), `format_result`, `format_outcome`, `banner`, and
  `help_text`. Values are bold green; banner title and help headings are bold
  cyan; plain output contains no ANSI codes. Help has five aligned sections
  (Operators highest-to-lowest, Functions, Names, Commands, Examples).
- `minicalc/repl.py`: `Repl` with `PROMPT`, injectable `input_fn`/`output_fn`,
  banner once, blank-line suppression, `:help`, `:vars` (`ans` first, sorted
  and aligned variables, `(no variables)`), `:clear`, `:quit`/`:q`, unknown
  command text, MiniCalc error rendering plus a blank line, clean EOF/Ctrl-C,
  and the internal-error policy above.
- `minicalc/__main__.py`: `main(argv=None) -> int`, argparse `prog="minicalc"`
  with `file`, `-e/--expr`, `--no-color`, and `--version`; usage error when a
  file and `-e` are combined; script mode sends results to stdout and errors
  to stderr; unreadable/non-UTF-8 files exit 2; error/internal exits are 1.
- `main.py`: three-line shim calling `minicalc.__main__.main`.
- `tests/test_display.py`: exact banner/help forms, color and color-stripping,
  `NO_COLOR`, fake and hostile streams, result/outcome/error formatting.
- `tests/test_cli.py`: fake-interpreter REPL/CLI tests for every command, EOF,
  Ctrl-C, blank/comment lines, exit codes 0/1/2, color control, foreign
  exceptions, and no ANSI off a TTY; three `integration` tests use the real
  `Interpreter`.
- `pytest.ini`: registered the `integration` marker only.

### 2.2 Conformance to Specifications & Decisions

- Contract section 11 signatures and defaults match exactly; no stage module,
  `interpreter.py`, `errors.py`, or contract/spec file was changed.
- [D-02]: standard library only, plain ANSI escapes, no `rich`.
- [D-07]: REPL errors use `MiniCalcError.render` and never terminate the loop.
- [D-09]: prompt, result forms, meta-commands, modes, exit codes, and TTY/color
  rule are implemented as locked.
- [D-11]: every module and public function is documented; `Repl` and the test
  helper classes have `Attributes:` sections.
- [D-14]: added to the decision log with the wording, spacing, and
  foreign-exception choices the spec did not fix.

---

## 3. Verification & Test Evidence

### 3.1 Test Execution

Non-integration suite (all green):

```text
$ python -m pytest -q -m "not integration"
........................................................................ [ 55%]
.........................................................                [100%]
129 passed, 3 deselected in 4.42s
```

Full suite (only the intentionally pending integration tests fail):

```text
$ python -m pytest -q
...
FAILED tests/test_cli.py::test_repl_arithmetic_with_real_interpreter
FAILED tests/test_cli.py::test_cli_expression_arithmetic_with_real_interpreter
FAILED tests/test_cli.py::test_cli_script_arithmetic_with_real_interpreter
3 failed, 129 passed in 9.06s
```

The three failures are all `@pytest.mark.integration` and are caused by the
CORE-003 walking-skeleton stages (for example `+` is still a `LexError`).
INT-001 is expected to turn them green.

Acceptance commands:

```text
$ python -m minicalc --version
MiniCalc 1.0.0
exit=0
$ python -m minicalc -e 42
= 42
exit=0
```

### 3.2 Edge Cases & Negative Testing

- `use_color`: TTY on/off, `NO_COLOR` set and set-empty, an object without
  `isatty`, and an `isatty` that raises all tested.
- REPL: EOF and `KeyboardInterrupt` both print one blank line and return 0;
  foreign exceptions from both `run_line` and the input callable print
  `Internal error:` and the loop continues; `:quit`/`:q` do not consume more
  input or call the interpreter.
- `:vars`: `ans` first, sorted aligned rows, `ans` alone, and `(no variables)`.
- `:clear`: reports the variable count only and resets `ans`.
- CLI: exit 0/1/2 paths, missing file, undecodable file, file plus `-e`,
  `--no-color` overriding a TTY, non-TTY plain output, and foreign exceptions
  from `run_line`, `run_source`, and REPL construction (no `Traceback` text).
- `python -m minicalc` with piped input exercised banner, help, vars, value,
  clear, unknown command, and clean `:q` exit manually.

---

## 4. Decisions Recorded

- **[D-14]**: REPL/display wording and spacing not fixed by the spec — exact
  banner and help layout, bold-green values, bold-cyan headings, `:vars`
  alignment/count rules, unknown-command text, blank-line exits, the
  `Internal error:` format and continuation policy, exit codes for
  unreadable files, and suppression of an empty `-e` line.

---

## 5. Unified Git Diff

```diff
diff --git c/main.py w/main.py
new file mode 100644
index 0000000..74e1ebe
--- /dev/null
+++ w/main.py
@@ -0,0 +1,5 @@
+"""Shim so ``python main.py`` runs the MiniCalc command-line interface."""
+
+from minicalc.__main__ import main
+
+raise SystemExit(main())
diff --git c/minicalc/__main__.py w/minicalc/__main__.py
new file mode 100644
index 0000000..35f3e0d
--- /dev/null
+++ w/minicalc/__main__.py
@@ -0,0 +1,172 @@
+"""Command-line entry point: REPL, script file, and ``-e`` modes ([D-09]).
+
+Exit codes are 0 for success, 1 when a MiniCalc error occurred (or an
+unexpected internal error was reported), and 2 for usage or file-read errors.
+Foreign exceptions are reported as ``Internal error:`` lines so no traceback
+is shown to the user.
+"""
+
+from __future__ import annotations
+
+import argparse
+import sys
+
+from .display import format_outcome, format_result, use_color
+from .errors import MiniCalcError
+from .interpreter import Interpreter
+from .repl import Repl
+
+
+def _build_parser() -> argparse.ArgumentParser:
+    """Build the ``minicalc`` argument parser.
+
+    Returns:
+        A parser accepting an optional file, ``-e/--expr``, ``--no-color``,
+        and ``--version``.
+    """
+    parser = argparse.ArgumentParser(
+        prog="minicalc",
+        description="MiniCalc 1.0: a small integer-arithmetic language.",
+    )
+    parser.add_argument("file", nargs="?", help="run a MiniCalc script file")
+    parser.add_argument(
+        "-e",
+        "--expr",
+        metavar="EXPR",
+        help="evaluate one expression and exit",
+    )
+    parser.add_argument(
+        "--no-color",
+        action="store_true",
+        help="disable ANSI colors",
+    )
+    parser.add_argument(
+        "--version",
+        action="version",
+        version="MiniCalc 1.0.0",
+        help="show the version and exit",
+    )
+    return parser
+
+
+def _internal_error(exc: BaseException) -> str:
+    """Describe an unexpected exception on one line.
+
+    Args:
+        exc: The exception that escaped.
+
+    Returns:
+        A line beginning ``Internal error:`` with the exception type and
+        message, or just the type when the message is empty.
+    """
+    detail = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
+    return f"Internal error: {detail}"
+
+
+def _run_expression(interpreter: Interpreter, expr: str, color: bool) -> int:
+    """Evaluate one expression and print its result.
+
+    Args:
+        interpreter: The facade to use.
+        expr: The expression source.
+        color: Whether to style the output.
+
+    Returns:
+        0 on success, 1 for a MiniCalc error or an internal error.
+    """
+    try:
+        result = interpreter.run_line(expr)
+        formatted = format_result(result, color)
+        if formatted:
+            print(formatted)
+        return 0
+    except MiniCalcError as error:
+        print(error.render(color), file=sys.stderr)
+        return 1
+    except Exception as exc:
+        print(_internal_error(exc), file=sys.stderr)
+        return 1
+
+
+def _run_file(interpreter: Interpreter, path: str, color: bool) -> int:
+    """Run a UTF-8 script file and report each non-empty outcome.
+
+    Args:
+        interpreter: The facade to use.
+        path: The script path.
+        color: Whether to style values and errors.
+
+    Returns:
+        0 when every line succeeded, 1 when any line failed or an internal
+        error occurred, or 2 when the file cannot be read as UTF-8 text.
+    """
+    try:
+        with open(path, "r", encoding="utf-8") as handle:
+            text = handle.read()
+    except (OSError, UnicodeError) as exc:
+        print(f"minicalc: cannot read '{path}': {exc}", file=sys.stderr)
+        return 2
+
+    try:
+        outcomes = interpreter.run_source(text)
+    except Exception as exc:
+        print(_internal_error(exc), file=sys.stderr)
+        return 1
+
+    exit_code = 0
+    for outcome in outcomes:
+        try:
+            formatted = format_outcome(outcome, color)
+            if not formatted:
+                continue
+            if outcome.error is not None:
+                print(formatted, file=sys.stderr)
+                exit_code = 1
+            else:
+                print(formatted)
+        except Exception as exc:
+            print(_internal_error(exc), file=sys.stderr)
+            exit_code = 1
+    return exit_code
+
+
+def main(argv: list[str] | None = None) -> int:
+    """Run MiniCalc according to the command-line arguments.
+
+    Args:
+        argv: Argument list to parse; ``None`` means ``sys.argv[1:]``.
+
+    Returns:
+        0 for success, 1 when a MiniCalc or internal error occurred, and 2 for
+        usage errors and unreadable or undecodable script files.
+    """
+    parser = _build_parser()
+    try:
+        args = parser.parse_args(argv)
+    except SystemExit as exc:
+        return exc.code if isinstance(exc.code, int) else 0
+
+    if args.file is not None and args.expr is not None:
+        parser.print_usage(sys.stderr)
+        print(
+            "minicalc: error: a file and -e/--expr cannot be used together",
+            file=sys.stderr,
+        )
+        return 2
+
+    color = not args.no_color and use_color(sys.stdout)
+    interpreter = Interpreter()
+
+    if args.expr is not None:
+        return _run_expression(interpreter, args.expr, color)
+    if args.file is not None:
+        return _run_file(interpreter, args.file, color)
+    try:
+        return Repl(interpreter, color=color).run()
+    except Exception as exc:
+        print(_internal_error(exc), file=sys.stderr)
+        return 1
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git c/minicalc/display.py w/minicalc/display.py
new file mode 100644
index 0000000..39c2133
--- /dev/null
+++ w/minicalc/display.py
@@ -0,0 +1,188 @@
+"""User-facing formatting for MiniCalc results, banners, and help text.
+
+All rendering is ASCII-safe. Styling uses plain ANSI escape codes ([D-02])
+and is applied only when the caller asks for color; plain output never
+contains escape sequences.
+"""
+
+from __future__ import annotations
+
+import os
+from typing import TextIO
+
+from .interpreter import LineOutcome, Result
+
+#: Bold green, used for produced values.
+_BOLD_GREEN = "\x1b[1;32m"
+#: Bold cyan, used for banner titles and help section headings.
+_BOLD_CYAN = "\x1b[1;36m"
+#: Dim, used for the banner's hint line.
+_DIM = "\x1b[2m"
+#: Reset all ANSI attributes.
+_RESET = "\x1b[0m"
+#: Width of the banner rules.
+_RULE_WIDTH = 44
+#: Column width for the left side of aligned help rows.
+_HELP_COLUMN = 20
+
+
+def use_color(stream: TextIO) -> bool:
+    """Decide whether ANSI styling may be written to ``stream``.
+
+    Args:
+        stream: The output stream to inspect. Streams without an ``isatty``
+            attribute, or whose ``isatty`` raises, are treated as non-TTYs.
+
+    Returns:
+        True only when ``stream.isatty()`` is true and the ``NO_COLOR``
+        environment variable is absent ([D-09]).
+    """
+    try:
+        isatty = getattr(stream, "isatty", None)
+        if not callable(isatty) or not isatty():
+            return False
+    except Exception:
+        return False
+    return "NO_COLOR" not in os.environ
+
+
+def _paint(text: str, code: str, color: bool) -> str:
+    """Wrap ``text`` in an ANSI code when ``color`` is true.
+
+    Args:
+        text: The plain text to style.
+        code: The ANSI sequence that starts the style.
+        color: Whether styling is enabled.
+
+    Returns:
+        The styled text, or ``text`` unchanged.
+    """
+    if not color:
+        return text
+    return f"{code}{text}{_RESET}"
+
+
+def format_result(result: Result, color: bool = False) -> str:
+    """Format one successful result for interactive or one-shot output.
+
+    Args:
+        result: The result returned by ``Interpreter.run_line``.
+        color: Whether to render the value in bold green.
+
+    Returns:
+        ``"= 42"`` for a value, ``"x = 7"`` for an assignment, or ``""``
+        for an empty line.
+    """
+    if result.kind == "empty":
+        return ""
+    value = _paint(str(result.value), _BOLD_GREEN, color)
+    if result.kind == "assign":
+        return f"{result.name} = {value}"
+    return f"= {value}"
+
+
+def format_outcome(outcome: LineOutcome, color: bool = False) -> str:
+    """Format one script-mode line outcome, prefixed with its line number.
+
+    Args:
+        outcome: One item from ``Interpreter.run_source``.
+        color: Whether to style values and error carets.
+
+    Returns:
+        ``"line 3: = 42"`` or ``"line 4: x = 7"`` for results, ``""`` for an
+        empty line, and ``outcome.error.render(color)`` for an error.
+    """
+    if outcome.error is not None:
+        return outcome.error.render(color)
+    if outcome.result is None:
+        return ""
+    formatted = format_result(outcome.result, color)
+    if not formatted:
+        return ""
+    return f"line {outcome.line_no}: {formatted}"
+
+
+def banner(color: bool = False) -> str:
+    """Build the REPL welcome banner.
+
+    The plain form is four lines: a 44-character rule, the title, the hint,
+    and another rule. Only the title and hint are styled in color mode.
+
+    Args:
+        color: Whether to style the title and hint.
+
+    Returns:
+        The banner text without a trailing newline.
+    """
+    rule = "-" * _RULE_WIDTH
+    title = _paint("MiniCalc 1.0  integer arithmetic language", _BOLD_CYAN, color)
+    hint = _paint("Type :help for help, :quit to exit.", _DIM, color)
+    return "\n".join((rule, title, hint, rule))
+
+
+def _section(title: str, rows: list[tuple[str, str]], color: bool) -> str:
+    """Render one help section with aligned left and right columns.
+
+    Args:
+        title: The section heading (styled bold cyan in color mode).
+        rows: ``(left, right)`` pairs; the left column is padded.
+        color: Whether to style the heading.
+
+    Returns:
+        The heading and its indented rows, without a trailing newline.
+    """
+    heading = _paint(title, _BOLD_CYAN, color)
+    body = "\n".join(
+        f"  {left:<{_HELP_COLUMN}}  {right}" for left, right in rows
+    )
+    return f"{heading}\n{body}"
+
+
+def help_text(color: bool = False) -> str:
+    """Build the ``:help`` reference.
+
+    Args:
+        color: Whether to style section headings.
+
+    Returns:
+        Five sections separated by blank lines: operator precedence (highest
+        to lowest), functions, names, commands, and three examples.
+    """
+    operators = [
+        ("1  ( )", "grouping, function calls"),
+        ("2  **", "exponentiation (right-associative)"),
+        ("3  - +", "unary sign (prefix)"),
+        ("4  * / // %", "multiplication, division, modulo (left)"),
+        ("5  + -", "addition, subtraction (left)"),
+        ("6  == != < <= > >=", "comparison (cannot chain)"),
+    ]
+    functions = [
+        ("abs(x)", "absolute value"),
+        ("min(a, b, ...)", "smallest argument"),
+        ("max(a, b, ...)", "largest argument"),
+        ("gcd(a, b)", "greatest common divisor"),
+    ]
+    names = [
+        ("x = 7", "assign the value to a name"),
+        ("ans", "value of the last successful statement"),
+    ]
+    commands = [
+        (":help", "show this help"),
+        (":vars", "list ans and variables"),
+        (":clear", "remove all variables and ans"),
+        (":quit, :q", "exit the REPL"),
+    ]
+    examples = [
+        ("2 + 3 * 4", "= 14"),
+        ("x = 7", "x = 7"),
+        ("gcd(12, 18)", "= 6"),
+    ]
+    return "\n\n".join(
+        (
+            _section("Operators (highest to lowest)", operators, color),
+            _section("Functions", functions, color),
+            _section("Names", names, color),
+            _section("Commands", commands, color),
+            _section("Examples", examples, color),
+        )
+    )
diff --git c/minicalc/repl.py w/minicalc/repl.py
new file mode 100644
index 0000000..f488a12
--- /dev/null
+++ w/minicalc/repl.py
@@ -0,0 +1,158 @@
+"""The interactive MiniCalc REPL and its meta-commands ([D-09]).
+
+``Repl`` talks only to the ``Interpreter`` facade and to injected input and
+output callables, which keeps it testable without a terminal. Foreign
+exceptions from the facade or from a meta-command are reported as
+``Internal error:`` lines and never terminate the session.
+"""
+
+from __future__ import annotations
+
+from typing import Callable, ClassVar
+
+from .display import banner, format_result, help_text
+from .errors import MiniCalcError
+from .interpreter import Interpreter
+
+
+def _internal_error(exc: BaseException) -> str:
+    """Describe an unexpected exception on one line.
+
+    Args:
+        exc: The exception that escaped.
+
+    Returns:
+        A line beginning ``Internal error:`` with the exception type and
+        message, or just the type when the message is empty.
+    """
+    detail = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
+    return f"Internal error: {detail}"
+
+
+class Repl:
+    """Read, evaluate, print, and loop until ``:quit``, EOF, or Ctrl-C.
+
+    Attributes:
+        PROMPT (ClassVar[str]): The input prompt, ``"minicalc> "``.
+        interpreter: The facade used for every non-meta-command line.
+        input_fn: Callable taking the prompt and returning one line; its
+            defaults match the built-in ``input``.
+        output_fn: Callable receiving one string per output line; its defaults
+            match the built-in ``print``.
+        color: Whether error rendering and display styling use ANSI codes.
+    """
+
+    PROMPT: ClassVar[str] = "minicalc> "
+
+    def __init__(
+        self,
+        interpreter: Interpreter,
+        input_fn: Callable[[str], str] = input,
+        output_fn: Callable[[str], None] = print,
+        color: bool = False,
+    ) -> None:
+        """Store the interpreter and the injected I/O callables.
+
+        Args:
+            interpreter: The interpreter facade shared by every line.
+            input_fn: Reads one line, given the prompt.
+            output_fn: Writes one output line.
+            color: Whether to use ANSI styling in rendered output.
+        """
+        self.interpreter = interpreter
+        self.input_fn = input_fn
+        self.output_fn = output_fn
+        self.color = color
+
+    def run(self) -> int:
+        """Print the banner and process lines until the session ends.
+
+        Returns:
+            Always 0: EOF, Ctrl-C, and ``:quit`` are all clean exits.
+        """
+        self.output_fn(banner(self.color))
+        while True:
+            try:
+                line = self.input_fn(self.PROMPT)
+            except (EOFError, StopIteration):
+                self.output_fn("")
+                break
+            except KeyboardInterrupt:
+                self.output_fn("")
+                break
+            except Exception as exc:
+                self.output_fn(_internal_error(exc))
+                continue
+
+            try:
+                if not self._handle_line(line):
+                    break
+            except Exception as exc:
+                self.output_fn(_internal_error(exc))
+        return 0
+
+    def _handle_line(self, line: str) -> bool:
+        """Handle one input line.
+
+        Args:
+            line: The line returned by ``input_fn``, without a newline.
+
+        Returns:
+            False when the line was ``:quit`` or ``:q``; True otherwise.
+        """
+        stripped = line.strip()
+        if not stripped:
+            return True
+        if stripped.startswith(":"):
+            return self._meta_command(stripped)
+
+        try:
+            result = self.interpreter.run_line(line)
+        except MiniCalcError as error:
+            self.output_fn(error.render(self.color))
+            self.output_fn("")
+            return True
+
+        formatted = format_result(result, self.color)
+        if formatted:
+            self.output_fn(formatted)
+        return True
+
+    def _meta_command(self, command: str) -> bool:
+        """Execute a ``:`` meta-command.
+
+        Args:
+            command: The stripped input line, beginning with ``:``.
+
+        Returns:
+            False for ``:quit`` and ``:q``; True for every other command.
+        """
+        if command in (":quit", ":q"):
+            return False
+        if command == ":help":
+            self.output_fn(help_text(self.color))
+        elif command == ":vars":
+            self._print_vars()
+        elif command == ":clear":
+            count = len(self.interpreter.env.items())
+            self.interpreter.env.clear()
+            self.output_fn(f"Cleared {count} variable(s).")
+        else:
+            self.output_fn(
+                f"Unknown command '{command}'. Type :help for a list."
+            )
+        return True
+
+    def _print_vars(self) -> None:
+        """Print ``ans`` first (when set), then variables in sorted order."""
+        env = self.interpreter.env
+        rows: list[tuple[str, int]] = []
+        if env.ans is not None:
+            rows.append(("ans", env.ans))
+        rows.extend(env.items())
+        if not rows:
+            self.output_fn("(no variables)")
+            return
+        width = max(len(name) for name, _ in rows)
+        for name, value in rows:
+            self.output_fn(f"{name:<{width}} = {value}")
diff --git c/pytest.ini w/pytest.ini
index 4584de7..677a475 100644
--- c/pytest.ini
+++ w/pytest.ini
@@ -1,3 +1,5 @@
 [pytest]
 testpaths = tests
 pythonpath = .
+markers =
+    integration: requires the full lexer, parser, and evaluator (passes after INT-001)
diff --git c/tests/test_cli.py w/tests/test_cli.py
new file mode 100644
index 0000000..98951f9
--- /dev/null
+++ w/tests/test_cli.py
@@ -0,0 +1,594 @@
+"""Tests for the REPL and command-line entry point.
+
+The REPL and CLI logic tests use a fake interpreter so they are stable while
+the full lexer, parser, and evaluator are still landing. The
+``integration``-marked tests at the end use the real ``Interpreter`` and are
+expected to pass only after INT-001.
+"""
+
+from types import SimpleNamespace
+
+import pytest
+
+import minicalc.__main__ as cli
+from minicalc.display import banner, help_text
+from minicalc.errors import LexError, SourcePos
+from minicalc.interpreter import Interpreter, LineOutcome, Result
+from minicalc.repl import Repl
+
+
+class FakeEnvironment:
+    """Environment stand-in for REPL meta-command tests.
+
+    Attributes:
+        variables: User-defined name-to-value bindings.
+        ans: Value of the last successful statement, or ``None``.
+    """
+
+    def __init__(
+        self,
+        variables: dict[str, int] | None = None,
+        ans: int | None = None,
+    ) -> None:
+        """Create a fake environment.
+
+        Args:
+            variables: Initial user bindings.
+            ans: Initial ``ans`` value.
+        """
+        self.variables = dict(variables or {})
+        self.ans = ans
+
+    def items(self) -> list[tuple[str, int]]:
+        """Return bindings sorted by name."""
+        return sorted(self.variables.items())
+
+    def clear(self) -> None:
+        """Remove all bindings and ``ans``."""
+        self.variables.clear()
+        self.ans = None
+
+
+class FakeInterpreter:
+    """Interpreter stand-in returning scripted results or exceptions.
+
+    Attributes:
+        env: The fake environment exposed to the REPL.
+        results: Queue of ``Result`` objects or exceptions for ``run_line``.
+        calls: ``(source, line_no)`` pairs passed to ``run_line``.
+        outcomes: Outcomes returned by ``run_source``.
+        source_error: Exception raised by ``run_source`` when set.
+        source_text: The last text passed to ``run_source``.
+    """
+
+    def __init__(
+        self,
+        results: list[object] | None = None,
+        env: FakeEnvironment | None = None,
+        outcomes: list[LineOutcome] | None = None,
+        source_error: BaseException | None = None,
+    ) -> None:
+        """Create the fake with the given script.
+
+        Args:
+            results: ``Result`` objects or exceptions yielded by ``run_line``.
+            env: Environment to expose.
+            outcomes: Outcomes returned by ``run_source``.
+            source_error: Exception raised by ``run_source`` when set.
+        """
+        self.env = env if env is not None else FakeEnvironment()
+        self.results = list(results or [])
+        self.calls: list[tuple[str, int]] = []
+        self.outcomes = list(outcomes or [])
+        self.source_error = source_error
+        self.source_text = ""
+
+    def run_line(self, source: str, line_no: int = 1) -> Result:
+        """Return the next scripted result or raise the next exception."""
+        self.calls.append((source, line_no))
+        if not self.results:
+            return Result("empty")
+        item = self.results.pop(0)
+        if isinstance(item, BaseException):
+            raise item
+        return item  # type: ignore[return-value]
+
+    def run_source(self, text: str) -> list[LineOutcome]:
+        """Return the scripted outcomes or raise the scripted exception."""
+        self.source_text = text
+        if self.source_error is not None:
+            raise self.source_error
+        return list(self.outcomes)
+
+
+def _scripted(lines: list[str]):
+    """Build an ``input_fn`` that yields lines and then raises EOFError.
+
+    Args:
+        lines: The lines to return in order.
+
+    Returns:
+        A callable accepting the prompt and returning the next line.
+    """
+    iterator = iter(lines)
+
+    def input_fn(prompt: str) -> str:
+        assert prompt == Repl.PROMPT
+        try:
+            return next(iterator)
+        except StopIteration:
+            raise EOFError from None
+
+    return input_fn
+
+
+def _run_repl(
+    lines: list[str],
+    interpreter: FakeInterpreter,
+    color: bool = False,
+) -> tuple[int, list[str]]:
+    """Run a REPL with scripted input and collected output.
+
+    Args:
+        lines: Input lines; EOF follows after them.
+        interpreter: The fake interpreter to use.
+        color: Whether the REPL should style output.
+
+    Returns:
+        The ``run()`` return code and the output chunks in order.
+    """
+    output: list[str] = []
+    code = Repl(
+        interpreter,
+        input_fn=_scripted(lines),
+        output_fn=output.append,
+        color=color,
+    ).run()
+    return code, output
+
+
+# ---------------------------------------------------------------------------
+# REPL behavior
+# ---------------------------------------------------------------------------
+
+
+def test_banner_printed_once_then_quit() -> None:
+    """The banner is the first and only output for an immediate ``:quit``."""
+    code, output = _run_repl([":quit"], FakeInterpreter())
+    assert code == 0
+    assert output == [banner()]
+
+
+def test_blank_and_whitespace_lines_produce_no_output() -> None:
+    """Blank lines never reach the interpreter and print nothing."""
+    fake = FakeInterpreter()
+    code, output = _run_repl(["", "   ", "\t", ":quit"], fake)
+    assert code == 0
+    assert output == [banner()]
+    assert fake.calls == []
+
+
+def test_value_assignment_and_empty_lines() -> None:
+    """Results print in contract form and empty results print nothing."""
+    fake = FakeInterpreter(
+        [
+            Result("value", 42),
+            Result("assign", 7, "x"),
+            Result("empty"),
+        ]
+    )
+    code, output = _run_repl(["42", "x = 7", "# comment", ":quit"], fake)
+    assert code == 0
+    assert output[1:] == ["= 42", "x = 7"]
+    assert fake.calls == [("42", 1), ("x = 7", 1), ("# comment", 1)]
+
+
+def test_help_command_prints_help_text() -> None:
+    """``:help`` prints the shared help text without calling the interpreter."""
+    fake = FakeInterpreter()
+    _, output = _run_repl([":help", ":quit"], fake)
+    assert output[1] == help_text()
+    assert fake.calls == []
+
+
+def test_vars_with_no_values() -> None:
+    """``:vars`` reports when there is nothing to show."""
+    _, output = _run_repl([":vars", ":quit"], FakeInterpreter())
+    assert output[1] == "(no variables)"
+
+
+def test_vars_prints_ans_first_and_aligns_names() -> None:
+    """``ans`` comes first, then variables sorted and column-aligned."""
+    env = FakeEnvironment({"long": 9, "x": 7}, ans=42)
+    _, output = _run_repl([":vars", ":quit"], FakeInterpreter(env=env))
+    assert output[1:] == ["ans  = 42", "long = 9", "x    = 7"]
+
+
+def test_vars_prints_ans_alone() -> None:
+    """An ``ans`` value is shown even when no variables exist."""
+    env = FakeEnvironment(ans=42)
+    _, output = _run_repl([":vars", ":quit"], FakeInterpreter(env=env))
+    assert output[1] == "ans = 42"
+
+
+def test_clear_reports_variable_count_and_resets_env() -> None:
+    """``:clear`` counts variables (not ``ans``) and empties the environment."""
+    env = FakeEnvironment({"x": 1, "y": 2}, ans=3)
+    fake = FakeInterpreter(env=env)
+    _, output = _run_repl([":clear", ":quit"], fake)
+    assert output[1] == "Cleared 2 variable(s)."
+    assert env.variables == {}
+    assert env.ans is None
+
+
+def test_quit_and_q_both_exit_without_reading_more() -> None:
+    """``:quit`` and ``:q`` stop the loop and never call the interpreter."""
+    for command in (":quit", ":q"):
+        fake = FakeInterpreter()
+        code, output = _run_repl([command, "42"], fake)
+        assert code == 0
+        assert output == [banner()]
+        assert fake.calls == []
+
+
+def test_unknown_command_message() -> None:
+    """Unknown meta-commands are reported as plain text, not error objects."""
+    _, output = _run_repl([":foo", ":quit"], FakeInterpreter())
+    assert output[1] == "Unknown command ':foo'. Type :help for a list."
+
+
+def test_meta_commands_never_reach_the_interpreter() -> None:
+    """Every known meta-command is handled by the REPL itself."""
+    fake = FakeInterpreter()
+    _run_repl([":help", ":vars", ":clear", ":q"], fake)
+    assert fake.calls == []
+
+
+def test_minicalc_error_renders_then_blank_line() -> None:
+    """A MiniCalc error renders with a caret and is followed by a blank line."""
+    error = LexError("illegal character '@'", SourcePos(1, 3)).with_source("2 @ 3")
+    fake = FakeInterpreter([error, Result("value", 5)])
+    _, output = _run_repl(["2 @ 3", "5", ":quit"], fake)
+    assert output[1] == error.render(False)
+    assert output[2] == ""
+    assert output[3] == "= 5"
+
+
+def test_colored_error_rendering() -> None:
+    """In color mode, the rendered error carries ANSI styling."""
+    error = LexError("bad", SourcePos(1, 2)).with_source("2 @")
+    _, output = _run_repl(["2 @", ":quit"], FakeInterpreter([error]), color=True)
+    assert output[1] == error.render(True)
+    assert "\x1b[" in output[1]
+
+
+def test_foreign_exception_in_run_line_keeps_repl_alive() -> None:
+    """A non-MiniCalc exception becomes ``Internal error:`` and the REPL lives."""
+    fake = FakeInterpreter([RuntimeError("boom"), Result("value", 5)])
+    code, output = _run_repl(["1 + 1", "2 + 2", ":quit"], fake)
+    assert code == 0
+    assert output[1] == "Internal error: RuntimeError: boom"
+    assert output[2] == "= 5"
+    assert fake.calls == [("1 + 1", 1), ("2 + 2", 1)]
+
+
+def test_foreign_exception_from_input_keeps_repl_alive() -> None:
+    """A foreign input exception is reported and the loop continues."""
+    state = {"calls": 0}
+
+    def flaky_input(prompt: str) -> str:
+        state["calls"] += 1
+        if state["calls"] == 1:
+            raise RuntimeError("reader broke")
+        return ":quit"
+
+    output: list[str] = []
+    code = Repl(FakeInterpreter(), input_fn=flaky_input, output_fn=output.append).run()
+    assert code == 0
+    assert output[1] == "Internal error: RuntimeError: reader broke"
+
+
+def test_eof_exits_cleanly_with_newline() -> None:
+    """EOF (Ctrl-D) prints a newline and returns 0."""
+    code, output = _run_repl([], FakeInterpreter())
+    assert code == 0
+    assert output == [banner(), ""]
+
+
+def test_keyboard_interrupt_exits_cleanly_with_newline() -> None:
+    """Ctrl-C at the prompt prints a newline and returns 0."""
+
+    def interrupting_input(prompt: str) -> str:
+        raise KeyboardInterrupt
+
+    output: list[str] = []
+    code = Repl(
+        FakeInterpreter(), input_fn=interrupting_input, output_fn=output.append
+    ).run()
+    assert code == 0
+    assert output == [banner(), ""]
+
+
+def test_plain_mode_never_emits_ansi() -> None:
+    """With color disabled, no escape sequence appears in any output."""
+    fake = FakeInterpreter([Result("value", 42)])
+    _, output = _run_repl(["42", ":help", ":vars", ":quit"], fake)
+    assert all("\x1b" not in chunk for chunk in output)
+
+
+def test_color_mode_styles_results_and_banner() -> None:
+    """With color enabled, values and the banner use ANSI styling."""
+    fake = FakeInterpreter([Result("value", 42)])
+    _, output = _run_repl(["42", ":quit"], fake, color=True)
+    assert "\x1b[" in output[0]
+    assert output[1] == "= \x1b[1;32m42\x1b[0m"
+
+
+# ---------------------------------------------------------------------------
+# CLI behavior
+# ---------------------------------------------------------------------------
+
+
+def _install(monkeypatch: pytest.MonkeyPatch, fake: FakeInterpreter,
+             color: bool = False) -> None:
+    """Install a fake interpreter and a fixed color decision in the CLI.
+
+    Args:
+        monkeypatch: The pytest monkeypatch fixture.
+        fake: The fake interpreter to construct.
+        color: The value returned by ``use_color``.
+    """
+    monkeypatch.setattr(cli, "Interpreter", lambda: fake)
+    monkeypatch.setattr(cli, "use_color", lambda stream: color)
+
+
+def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
+    """``--version`` prints the exact version and exits 0."""
+    assert cli.main(["--version"]) == 0
+    assert capsys.readouterr().out == "MiniCalc 1.0.0\n"
+
+
+def test_help_flag(capsys: pytest.CaptureFixture[str]) -> None:
+    """``--help`` prints usage and exits 0."""
+    assert cli.main(["--help"]) == 0
+    assert "usage: minicalc" in capsys.readouterr().out
+
+
+def test_expr_42_with_real_interpreter(capsys: pytest.CaptureFixture[str]) -> None:
+    """The acceptance one-shot works even with the walking-skeleton stages."""
+    assert cli.main(["-e", "42"]) == 0
+    assert capsys.readouterr().out == "= 42\n"
+
+
+def test_expr_assignment_output(
+    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
+) -> None:
+    """``-e`` prints assignment results as ``name = value``."""
+    _install(monkeypatch, FakeInterpreter([Result("assign", 7, "x")]))
+    assert cli.main(["-e", "x = 7"]) == 0
+    assert capsys.readouterr().out == "x = 7\n"
+
+
+def test_expr_empty_result_prints_nothing(
+    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
+) -> None:
+    """An empty expression result exits 0 without a stray blank line."""
+    _install(monkeypatch, FakeInterpreter([Result("empty")]))
+    assert cli.main(["-e", ""]) == 0
+    assert capsys.readouterr().out == ""
+
+
+def test_expr_minicalc_error_goes_to_stderr(
+    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
+) -> None:
+    """A MiniCalc error renders to stderr and exits 1."""
+    error = LexError("bad character '@'", SourcePos(1, 3)).with_source("2 @")
+    _install(monkeypatch, FakeInterpreter([error]))
+    assert cli.main(["-e", "2 @"]) == 1
+    captured = capsys.readouterr()
+    assert captured.out == ""
+    assert captured.err.strip() == error.render(False)
+
+
+def test_expr_foreign_exception_is_reported(
+    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
+) -> None:
+    """A foreign exception is one ``Internal error:`` line, not a traceback."""
+    _install(monkeypatch, FakeInterpreter([RuntimeError("boom")]))
+    assert cli.main(["-e", "1"]) == 1
+    captured = capsys.readouterr()
+    assert captured.err == "Internal error: RuntimeError: boom\n"
+    assert "Traceback" not in captured.err
+
+
+def test_file_mode_reports_results_and_continues_after_errors(
+    monkeypatch: pytest.MonkeyPatch,
+    capsys: pytest.CaptureFixture[str],
+    tmp_path,
+) -> None:
+    """Script results go to stdout, errors to stderr, and later lines still run."""
+    error = LexError("bad character '@'", SourcePos(2, 3)).with_source("2 @ 3")
+    outcomes = [
+        LineOutcome(1, "42", Result("value", 42), None),
+        LineOutcome(2, "2 @ 3", None, error),
+        LineOutcome(3, "", Result("empty"), None),
+        LineOutcome(4, "x = 7", Result("assign", 7, "x"), None),
+    ]
+    fake = FakeInterpreter(outcomes=outcomes)
+    _install(monkeypatch, fake)
+    script = tmp_path / "script.mc"
+    script.write_text("42\n2 @ 3\n\nx = 7\n", encoding="utf-8")
+
+    assert cli.main([str(script)]) == 1
+    captured = capsys.readouterr()
+    assert captured.out.splitlines() == ["line 1: = 42", "line 4: x = 7"]
+    assert captured.err.strip() == error.render(False)
+    assert fake.source_text == "42\n2 @ 3\n\nx = 7\n"
+
+
+def test_file_mode_success_exits_zero(
+    monkeypatch: pytest.MonkeyPatch,
+    capsys: pytest.CaptureFixture[str],
+    tmp_path,
+) -> None:
+    """A script with no errors exits 0."""
+    outcomes = [LineOutcome(1, "42", Result("value", 42), None)]
+    _install(monkeypatch, FakeInterpreter(outcomes=outcomes))
+    script = tmp_path / "ok.mc"
+    script.write_text("42\n", encoding="utf-8")
+    assert cli.main([str(script)]) == 0
+    assert capsys.readouterr().out == "line 1: = 42\n"
+
+
+def test_file_mode_foreign_exception_is_reported(
+    monkeypatch: pytest.MonkeyPatch,
+    capsys: pytest.CaptureFixture[str],
+    tmp_path,
+) -> None:
+    """A foreign ``run_source`` exception is reported and exits nonzero."""
+    _install(monkeypatch, FakeInterpreter(source_error=RuntimeError("boom")))
+    script = tmp_path / "bad.mc"
+    script.write_text("42\n", encoding="utf-8")
+    assert cli.main([str(script)]) == 1
+    captured = capsys.readouterr()
+    assert captured.err == "Internal error: RuntimeError: boom\n"
+    assert "Traceback" not in captured.err
+
+
+def test_unreadable_file_is_a_usage_error(
+    capsys: pytest.CaptureFixture[str], tmp_path
+) -> None:
+    """A missing script reports a message on stderr and exits 2."""
+    missing = tmp_path / "missing.mc"
+    assert cli.main([str(missing)]) == 2
+    captured = capsys.readouterr()
+    assert captured.out == ""
+    assert "cannot read" in captured.err
+    assert str(missing) in captured.err
+    assert "Traceback" not in captured.err
+
+
+def test_undecodable_file_is_a_usage_error(
+    capsys: pytest.CaptureFixture[str], tmp_path
+) -> None:
+    """A non-UTF-8 script reports a message on stderr and exits 2."""
+    script = tmp_path / "binary.mc"
+    script.write_bytes(b"\xff\xfe\x00")
+    assert cli.main([str(script)]) == 2
+    captured = capsys.readouterr()
+    assert "cannot read" in captured.err
+    assert "Traceback" not in captured.err
+
+
+def test_file_and_expr_together_is_a_usage_error(
+    capsys: pytest.CaptureFixture[str], tmp_path
+) -> None:
+    """Supplying both a file and ``-e`` exits 2 with a usage line."""
+    script = tmp_path / "x.mc"
+    assert cli.main([str(script), "-e", "1"]) == 2
+    captured = capsys.readouterr()
+    assert captured.out == ""
+    assert "usage: minicalc" in captured.err
+    assert "cannot be used together" in captured.err
+
+
+def test_no_ansi_when_stdout_is_not_a_tty(
+    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
+) -> None:
+    """With no TTY, ``-e`` output is plain even without ``--no-color``."""
+    monkeypatch.setattr(cli, "Interpreter", lambda: FakeInterpreter([Result("value", 42)]))
+    assert cli.main(["-e", "42"]) == 0
+    assert "\x1b" not in capsys.readouterr().out
+
+
+def test_no_color_flag_disables_styling(
+    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
+) -> None:
+    """``--no-color`` overrides a TTY that would otherwise enable color."""
+    monkeypatch.setattr(cli, "use_color", lambda stream: True)
+    monkeypatch.setattr(cli, "Interpreter", lambda: FakeInterpreter([Result("value", 42)]))
+    assert cli.main(["-e", "42"]) == 0
+    assert "\x1b[" in capsys.readouterr().out
+
+    monkeypatch.setattr(
+        cli, "Interpreter", lambda: FakeInterpreter([Result("value", 42)])
+    )
+    assert cli.main(["--no-color", "-e", "42"]) == 0
+    assert "\x1b" not in capsys.readouterr().out
+
+
+def test_no_args_dispatches_to_repl(
+    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
+) -> None:
+    """No arguments constructs a REPL with the interpreter and color choice."""
+    created: dict[str, object] = {}
+
+    def fake_repl(interpreter, input_fn=input, output_fn=print, color=False):
+        created["interpreter"] = interpreter
+        created["color"] = color
+        return SimpleNamespace(run=lambda: 0)
+
+    fake = FakeInterpreter()
+    monkeypatch.setattr(cli, "Interpreter", lambda: fake)
+    monkeypatch.setattr(cli, "use_color", lambda stream: True)
+    monkeypatch.setattr(cli, "Repl", fake_repl)
+    assert cli.main([]) == 0
+    assert created == {"interpreter": fake, "color": True}
+
+
+def test_repl_construction_failure_is_an_internal_error(
+    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
+) -> None:
+    """A failure outside the REPL loop is reported without a traceback."""
+    def broken_repl(interpreter, input_fn=input, output_fn=print, color=False):
+        return SimpleNamespace(run=lambda: (_ for _ in ()).throw(RuntimeError("boom")))
+
+    monkeypatch.setattr(cli, "Interpreter", lambda: FakeInterpreter())
+    monkeypatch.setattr(cli, "use_color", lambda stream: False)
+    monkeypatch.setattr(cli, "Repl", broken_repl)
+    assert cli.main([]) == 1
+    captured = capsys.readouterr()
+    assert captured.err == "Internal error: RuntimeError: boom\n"
+    assert "Traceback" not in captured.err
+
+
+# ---------------------------------------------------------------------------
+# Integration tests (real stage pipeline; green after INT-001)
+# ---------------------------------------------------------------------------
+
+
+@pytest.mark.integration
+def test_repl_arithmetic_with_real_interpreter() -> None:
+    """The REPL evaluates arithmetic, assignments, and ``ans`` end to end."""
+    output: list[str] = []
+    code = Repl(
+        Interpreter(),
+        input_fn=_scripted(["2 + 3 * 4", "x = 7", "ans * x", ":quit"]),
+        output_fn=output.append,
+    ).run()
+    assert code == 0
+    assert output[1:] == ["= 14", "x = 7", "= 98"]
+
+
+@pytest.mark.integration
+def test_cli_expression_arithmetic_with_real_interpreter(
+    capsys: pytest.CaptureFixture[str],
+) -> None:
+    """``-e`` evaluates a full expression with the real pipeline."""
+    assert cli.main(["-e", "1 + 2"]) == 0
+    assert capsys.readouterr().out == "= 3\n"
+
+
+@pytest.mark.integration
+def test_cli_script_arithmetic_with_real_interpreter(
+    capsys: pytest.CaptureFixture[str], tmp_path
+) -> None:
+    """Script mode runs the real pipeline and preserves state across lines."""
+    script = tmp_path / "calc.mc"
+    script.write_text("2 + 3 * 4\nx = 7\nans * x\n", encoding="utf-8")
+    assert cli.main([str(script)]) == 0
+    assert capsys.readouterr().out.splitlines() == [
+        "line 1: = 14",
+        "line 2: x = 7",
+        "line 3: = 98",
+    ]
diff --git c/tests/test_display.py w/tests/test_display.py
new file mode 100644
index 0000000..4d3ec1a
--- /dev/null
+++ w/tests/test_display.py
@@ -0,0 +1,193 @@
+"""Tests for ``minicalc.display``: plain and ANSI-styled rendering."""
+
+import re
+
+import pytest
+
+from minicalc.display import (
+    banner,
+    format_outcome,
+    format_result,
+    help_text,
+    use_color,
+)
+from minicalc.errors import LexError, SourcePos
+from minicalc.interpreter import LineOutcome, Result
+
+ANSI = re.compile(r"\x1b\[[0-9;]*m")
+RULE = "-" * 44
+
+
+class _Stream:
+    """A minimal text stream stand-in.
+
+    Attributes:
+        tty: The value returned by ``isatty``.
+    """
+
+    def __init__(self, tty: bool) -> None:
+        """Store the fake terminal status.
+
+        Args:
+            tty: Whether the stream claims to be a terminal.
+        """
+        self.tty = tty
+
+    def isatty(self) -> bool:
+        """Report the configured terminal status."""
+        return self.tty
+
+
+class _BrokenStream:
+    """A stream whose ``isatty`` always raises.
+
+    Attributes:
+        None.
+    """
+
+    def isatty(self) -> bool:
+        """Raise, as an unusual stream might."""
+        raise OSError("no tty here")
+
+
+def _plain(text: str) -> str:
+    """Strip ANSI escape sequences from ``text``."""
+    return ANSI.sub("", text)
+
+
+def test_use_color_requires_a_tty(monkeypatch: pytest.MonkeyPatch) -> None:
+    """A TTY without NO_COLOR enables color."""
+    monkeypatch.delenv("NO_COLOR", raising=False)
+    assert use_color(_Stream(True)) is True
+
+
+def test_use_color_is_false_off_a_tty(monkeypatch: pytest.MonkeyPatch) -> None:
+    """A non-TTY never enables color."""
+    monkeypatch.delenv("NO_COLOR", raising=False)
+    assert use_color(_Stream(False)) is False
+
+
+def test_use_color_respects_no_color(monkeypatch: pytest.MonkeyPatch) -> None:
+    """NO_COLOR disables color even on a TTY, including when empty."""
+    monkeypatch.setenv("NO_COLOR", "1")
+    assert use_color(_Stream(True)) is False
+    monkeypatch.setenv("NO_COLOR", "")
+    assert use_color(_Stream(True)) is False
+
+
+def test_use_color_tolerates_streams_without_isatty() -> None:
+    """Objects without ``isatty`` are treated as plain streams."""
+    assert use_color(object()) is False  # type: ignore[arg-type]
+
+
+def test_use_color_tolerates_a_raising_isatty() -> None:
+    """A raising ``isatty`` is treated as a non-TTY."""
+    assert use_color(_BrokenStream()) is False  # type: ignore[arg-type]
+
+
+def test_format_result_value_assignment_and_empty() -> None:
+    """Plain results use the exact contract forms."""
+    assert format_result(Result("value", 42)) == "= 42"
+    assert format_result(Result("assign", 7, "x")) == "x = 7"
+    assert format_result(Result("empty")) == ""
+
+
+def test_format_result_colors_only_the_value() -> None:
+    """Color mode wraps the value in bold green and leaves the name plain."""
+    assert format_result(Result("value", 42), color=True) == (
+        "= \x1b[1;32m42\x1b[0m"
+    )
+    assert format_result(Result("assign", 7, "x"), color=True) == (
+        "x = \x1b[1;32m7\x1b[0m"
+    )
+
+
+def test_format_outcome_value_and_assignment() -> None:
+    """Script outcomes prefix results with their 1-based line number."""
+    assert format_outcome(LineOutcome(3, "42", Result("value", 42), None)) == (
+        "line 3: = 42"
+    )
+    assert format_outcome(
+        LineOutcome(4, "x = 7", Result("assign", 7, "x"), None)
+    ) == "line 4: x = 7"
+
+
+def test_format_outcome_empty_is_blank() -> None:
+    """Empty lines and blank comments produce no script output."""
+    assert format_outcome(LineOutcome(2, "", Result("empty"), None)) == ""
+    assert format_outcome(LineOutcome(2, "# note", Result("empty"), None)) == ""
+
+
+def test_format_outcome_error_uses_render() -> None:
+    """Errors delegate to ``render`` so the caret and position are kept."""
+    error = LexError("illegal character '@'", SourcePos(3, 5)).with_source("2 + @")
+    outcome = LineOutcome(3, "2 + @", None, error)
+    assert format_outcome(outcome) == error.render(False)
+    assert format_outcome(outcome, color=True) == error.render(True)
+
+
+def test_banner_exact_plain_text() -> None:
+    """The banner is exactly two 44-character rules and two text lines."""
+    expected = "\n".join(
+        (
+            RULE,
+            "MiniCalc 1.0  integer arithmetic language",
+            "Type :help for help, :quit to exit.",
+            RULE,
+        )
+    )
+    assert banner() == expected
+    lines = banner().splitlines()
+    assert lines[0] == RULE and lines[-1] == RULE
+    assert "\x1b" not in banner()
+
+
+def test_banner_color_strips_to_plain() -> None:
+    """Coloring the banner changes only escape codes, not the text."""
+    assert "\x1b[" in banner(color=True)
+    assert _plain(banner(color=True)) == banner()
+
+
+def test_help_text_has_all_sections_and_examples() -> None:
+    """Help covers operators, functions, names, commands, and three examples."""
+    text = help_text()
+    assert "\x1b" not in text
+    headings = re.findall(r"^(Operators.*|Functions|Names|Commands|Examples)$",
+                          text, re.MULTILINE)
+    assert headings == [
+        "Operators (highest to lowest)",
+        "Functions",
+        "Names",
+        "Commands",
+        "Examples",
+    ]
+    assert len(text.split("\n\n")) == 5
+    assert "abs(x)" in text and "gcd(a, b)" in text
+    assert ":help" in text and ":vars" in text
+    assert "2 + 3 * 4" in text and "gcd(12, 18)" in text
+
+
+def test_help_text_precedence_is_high_to_low() -> None:
+    """The operator rows appear from level 1 down to level 6."""
+    text = help_text()
+    positions = [text.index(f"  {level}  ") for level in range(1, 7)]
+    assert positions == sorted(positions)
+
+
+def test_help_text_columns_are_aligned() -> None:
+    """Every help row puts its description in the same column."""
+    rows = [
+        line
+        for line in help_text().splitlines()
+        if line.startswith("  ") and len(line) > 24
+    ]
+    assert rows
+    for line in rows:
+        assert line[23] == " "
+        assert line[24] != " "
+
+
+def test_help_text_color_strips_to_plain() -> None:
+    """Colored help has the same text as plain help."""
+    assert "\x1b[" in help_text(color=True)
+    assert _plain(help_text(color=True)) == help_text()

```

---

## 6. Flagged for APC / Operator Attention

- [ ] The task prompt calls `banner()` "three lines" but enumerates four (two
  44-character rules plus two text lines). I implemented all four enumerated
  lines; recorded in [D-14].
- [ ] Spec section 8 says script errors are "prefixed by the line number",
  while contract section 11 and the prompt define `format_outcome` errors as
  `error.render()` only. I followed the contract/prompt; `render()` already
  reports `at line N`.
- [ ] Script mode cannot continue after a foreign `run_source` exception
  because that is one facade call; it reports one `Internal error:` line and
  exits 1. Continuing would require reimplementing `run_source` line-by-line
  in the CLI, which the prompt did not ask for.
- [ ] Three `integration` tests fail by design until INT-001; they are marked
  and are not part of the non-integration green set.
- [ ] `docs/context/repo-tree.txt` was left untouched per instructions, so it
  does not yet list `main.py`, `minicalc/__main__.py`, `display.py`, or
  `repl.py`.
