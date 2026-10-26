# Task Report: CORE-003 — Walking skeleton and the Interpreter facade

**Date:** 2026-10-26
**Agent:** claude-code
**Task ID:** CORE-003
**Status:** needs-review
**Commit:** `feat(CORE-003): add walking skeleton and Interpreter facade` (single task commit on `task/CORE-003`)
**Worktree:** `../minicalc-CORE-003` (branch `task/CORE-003`)
**Patch File:** `patch/CORE-003-claude-code-walking-skeleton.patch`

---

## 1. Executive Summary

Phase 1 exit gate reached: the full pipeline now runs end to end behind the
final `Interpreter` facade. The lexer, parser, and evaluator are marked stubs
(FEAT-001/002/003 replace them wholesale), the `Environment` is complete, and
`run_line` / `run_source` implement contract section 10 including error
source attachment, continue-after-error, and the `RecursionError` safety net.

`pytest -q -rs` reports `77 passed` with **zero skips**; `tests/test_golden.py`
now collects the `smoke` case and passes it through the real pipeline. The
acceptance snippet prints exactly
`Result(kind='value', value=42, name=None)`.

---

## 2. Implementation Details

### 2.1 Changes Made

- `minicalc/lexer.py` (`# STUB (CORE-003): replaced wholesale by FEAT-001`):
  whitespace/`\r`, `#` comments, ASCII decimal literals with `INT_MAX` and
  `MAX_LINE_LENGTH` checks, illegal characters, and `EOF` at
  `len(source) + 1`. Letters directly after digits are reported at the start
  of the number, matching spec section 2.
- `minicalc/parser.py` (`# STUB (CORE-003): replaced wholesale by FEAT-002`):
  `None` for only-`EOF`, `Number` for `NUMBER EOF`, `ParseError` at the
  offending token otherwise.
- `minicalc/evaluator.py` (`# STUB (CORE-003): replaced wholesale by
  FEAT-003`): `Number` returns its value after `in_range`; every other node
  raises `EvalError("not implemented yet")` at the node position.
- `minicalc/environment.py`: full section 8 implementation, including the two
  exact `UndefinedNameError` messages, sorted `items()` excluding `ans`, and
  `clear()`.
- `minicalc/interpreter.py`: `Result`, `LineOutcome`, and `Interpreter` per
  section 10. `run_line` attaches `source` to every error, distinguishes
  parse-time and eval-time `RecursionError`, records `ans` only after success,
  and raises the recursion limit to 4000 only when lower. `run_source`
  numbers from 1, continues after errors, and never raises `MiniCalcError`.
  Lines are split only on `\n`; a trailing `\r` is stripped, so form feed and
  U+2028 remain illegal characters instead of becoming line separators.
- `tests/test_interpreter.py`, `tests/test_environment.py`: facade-level and
  environment tests, including blank/comment lines, CRLF input, the
  recursion net, the 1001-column line cap, and unchanged state after failure.

### 2.2 Conformance to Specifications & Decisions

- Contract sections 8 and 10: names, signatures, field order, and defaults
  match exactly (inspect evidence in 3.2).
- [D-07]: errors carry positions and `source_line`; the environment is
  unchanged on failure.
- [D-11]: every class has an `Attributes:` docstring; every module and public
  function is documented.
- Assignment results are implemented in the facade (`kind="assign"`,
  `name=target`) but cannot be exercised until the FEAT-003 evaluator handles
  `Assign`.

---

## 3. Verification & Test Evidence

### 3.1 Test Execution

```text
$ python -m pytest -q -rs
........................................................................ [ 93%]
.....                                                                    [100%]
77 passed in 4.92s
```

Zero skips. `tests/test_golden.py::test_golden_file[smoke]` is collected and
passes:

```text
$ python -m pytest -q --collect-only tests/test_golden.py
tests/test_golden.py::test_golden_file[smoke]

1 test collected in 9.67s
```

Acceptance snippet:

```text
$ python -c "from minicalc.interpreter import Interpreter; print(Interpreter().run_line('42'))"
Result(kind='value', value=42, name=None)
```

### 3.2 Signature and stub-marker evidence

```text
Result ['kind', 'value', 'name']
LineOutcome ['line_no', 'source', 'result', 'error']
Interpreter.run_line (self, source: str, line_no: int = 1) -> Result
Interpreter.run_source (self, text: str) -> list[LineOutcome]
Interpreter.__init__ (self, env: Environment | None = None) -> None
Environment.get (self, name: str, pos: SourcePos) -> int
Environment.set (self, name: str, value: int) -> None
Environment.record_result (self, value: int) -> None
Environment.clear (self) -> None
Environment.items (self) -> list[tuple[str, int]]

minicalc/lexer.py:3:# STUB (CORE-003): replaced wholesale by FEAT-001
minicalc/parser.py:3:# STUB (CORE-003): replaced wholesale by FEAT-002
minicalc/evaluator.py:3:# STUB (CORE-003): replaced wholesale by FEAT-003
```

### 3.3 Edge Cases & Negative Testing

- `run_source` on `2 3` (parser-reachable error) then `42`: error captured,
  lines numbered 1-4, later line still evaluated.
- A lex error leaves existing variables and `ans` untouched.
- CRLF input yields source lines without `\r`; only `\n` splits lines.
- Form feed and U+2028 inside a line are `LexError` at the offending column
  (`1\x0c2` and `1\u20282` each fail at column 2).
- Infinite evaluator recursion becomes `EvalError("expression is too deeply
  nested")` at column 1, not a crash.
- A 1001-character line raises `LexError` at column 1001.

---

## 4. Decisions Recorded

None. No decision ID was reserved for CORE-003.

---

## 5. Unified Git Diff

```diff
diff --git c/minicalc/environment.py w/minicalc/environment.py
new file mode 100644
index 0000000..f817fe9
--- /dev/null
+++ w/minicalc/environment.py
@@ -0,0 +1,78 @@
+"""Variable storage and the special ``ans`` binding (CORE-003).
+
+The environment is the only mutable state in the interpreter. ``ans`` is a
+separate read-only binding updated after each successful statement; it is not
+part of ``variables``.
+"""
+
+from __future__ import annotations
+
+from .errors import SourcePos, UndefinedNameError
+
+
+class Environment:
+    """Hold user variables and the current ``ans`` value.
+
+    Attributes:
+        variables: User-defined name-to-value bindings.
+        ans: Value of the last successful statement, or ``None`` before the
+            first success.
+    """
+
+    def __init__(self) -> None:
+        """Create an empty environment with no ``ans`` value."""
+        self.variables: dict[str, int] = {}
+        self.ans: int | None = None
+
+    def get(self, name: str, pos: SourcePos) -> int:
+        """Read a variable or ``ans``.
+
+        Args:
+            name: The identifier to look up.
+            pos: Position used for the error if the name has no value.
+
+        Returns:
+            The stored integer.
+
+        Raises:
+            UndefinedNameError: For an unset variable or an unset ``ans``.
+        """
+        if name == "ans":
+            if self.ans is None:
+                raise UndefinedNameError(
+                    "ans has no value yet; evaluate a statement first", pos
+                )
+            return self.ans
+        if name in self.variables:
+            return self.variables[name]
+        raise UndefinedNameError(f"name '{name}' is not defined", pos)
+
+    def set(self, name: str, value: int) -> None:
+        """Bind a variable.
+
+        Args:
+            name: The identifier to bind.
+            value: The integer value.
+        """
+        self.variables[name] = value
+
+    def record_result(self, value: int) -> None:
+        """Record the value of a successful statement as ``ans``.
+
+        Args:
+            value: The statement's value.
+        """
+        self.ans = value
+
+    def clear(self) -> None:
+        """Remove every variable and the ``ans`` value."""
+        self.variables.clear()
+        self.ans = None
+
+    def items(self) -> list[tuple[str, int]]:
+        """List user variables in sorted name order.
+
+        Returns:
+            Sorted ``(name, value)`` pairs; ``ans`` is never included.
+        """
+        return sorted(self.variables.items())
diff --git c/minicalc/evaluator.py w/minicalc/evaluator.py
new file mode 100644
index 0000000..e190ea8
--- /dev/null
+++ w/minicalc/evaluator.py
@@ -0,0 +1,51 @@
+"""Walking-skeleton evaluator: number literals only (CORE-003).
+
+# STUB (CORE-003): replaced wholesale by FEAT-003
+
+FEAT-003 replaces this module with full operator, variable, and built-in
+evaluation. Until then, a ``Number`` node evaluates to its literal value.
+"""
+
+from __future__ import annotations
+
+from .ast_nodes import Node, Number
+from .environment import Environment
+from .errors import EvalError, IntegerRangeError
+from .limits import in_range
+
+
+class Evaluator:
+    """Evaluate the walking-skeleton subset of the AST.
+
+    Attributes:
+        env: The environment used for variables and ``ans`` (not yet read by
+            the stub, but part of the locked constructor).
+    """
+
+    def __init__(self, env: Environment) -> None:
+        """Store the environment.
+
+        Args:
+            env: The interpreter's environment.
+        """
+        self.env = env
+
+    def evaluate(self, node: Node) -> int:
+        """Evaluate one node.
+
+        Args:
+            node: The AST node to evaluate.
+
+        Returns:
+            The integer value of a ``Number`` node.
+
+        Raises:
+            IntegerRangeError: If the literal is outside the 32-bit range.
+            EvalError: For every node type the walking skeleton does not yet
+                implement.
+        """
+        if isinstance(node, Number):
+            if not in_range(node.value):
+                raise IntegerRangeError("integer out of range", node.pos)
+            return node.value
+        raise EvalError("not implemented yet", node.pos)
diff --git c/minicalc/interpreter.py w/minicalc/interpreter.py
new file mode 100644
index 0000000..d8a9014
--- /dev/null
+++ w/minicalc/interpreter.py
@@ -0,0 +1,142 @@
+"""The stable MiniCalc facade: one line or a whole source through the pipeline.
+
+This module is final from CORE-003 onward. FEAT-001, FEAT-002, and FEAT-003
+replace the lexer, parser, and evaluator behind it without changing ``Result``,
+``LineOutcome``, or ``Interpreter``.
+"""
+
+from __future__ import annotations
+
+import sys
+from dataclasses import dataclass
+from typing import Literal
+
+from .ast_nodes import Assign
+from .environment import Environment
+from .errors import EvalError, MiniCalcError, ParseError, SourcePos
+from .evaluator import Evaluator
+from .lexer import Lexer
+from .parser import Parser
+
+_MIN_RECURSION_LIMIT = 4000
+
+
+@dataclass(frozen=True)
+class Result:
+    """The outcome of one successfully processed line.
+
+    Attributes:
+        kind: ``"value"`` for an expression, ``"assign"`` for an assignment,
+            or ``"empty"`` for a blank/comment-only line.
+        value: The produced integer for value and assign results.
+        name: The bound identifier when ``kind == "assign"``.
+    """
+
+    kind: Literal["value", "assign", "empty"]
+    value: int | None = None
+    name: str | None = None
+
+
+@dataclass(frozen=True)
+class LineOutcome:
+    """One line's result or error, in source order.
+
+    Attributes:
+        line_no: 1-based line number in the original text.
+        source: The original line, without its newline.
+        result: The successful result, or ``None`` when ``error`` is set.
+        error: The error, or ``None`` when ``result`` is set.
+    """
+
+    line_no: int
+    source: str
+    result: Result | None
+    error: MiniCalcError | None
+
+
+class Interpreter:
+    """Coordinate the lexer, parser, evaluator, and environment.
+
+    Attributes:
+        env: The persistent environment shared by every processed line.
+    """
+
+    def __init__(self, env: Environment | None = None) -> None:
+        """Create the facade, raising the recursion limit if needed.
+
+        Args:
+            env: Optional environment to reuse; a fresh one otherwise.
+        """
+        self.env = env if env is not None else Environment()
+        if sys.getrecursionlimit() < _MIN_RECURSION_LIMIT:
+            sys.setrecursionlimit(_MIN_RECURSION_LIMIT)
+
+    def run_line(self, source: str, line_no: int = 1) -> Result:
+        """Run one source line and return its result.
+
+        Args:
+            source: One line with no trailing newline.
+            line_no: 1-based line number used for positions.
+
+        Returns:
+            The line's ``Result``.
+
+        Raises:
+            MiniCalcError: Any lexical, syntax, or runtime error, with the
+                offending ``source`` attached for caret rendering.
+        """
+        try:
+            tokens = Lexer(source, line_no).tokenize()
+            try:
+                node = Parser(tokens).parse_statement()
+            except RecursionError as exc:
+                raise ParseError(
+                    "expression is too deeply nested",
+                    SourcePos(line_no, 1),
+                ) from exc
+
+            if node is None:
+                return Result("empty")
+
+            try:
+                value = Evaluator(self.env).evaluate(node)
+            except RecursionError as exc:
+                raise EvalError(
+                    "expression is too deeply nested",
+                    SourcePos(line_no, 1),
+                ) from exc
+
+            if isinstance(node, Assign):
+                result = Result("assign", value, node.target)
+            else:
+                result = Result("value", value)
+            self.env.record_result(value)
+            return result
+        except MiniCalcError as error:
+            raise error.with_source(source) from None
+
+    def run_source(self, text: str) -> list[LineOutcome]:
+        """Run every line of ``text``, continuing after errors.
+
+        Args:
+            text: A whole source file or script.
+
+        Returns:
+            One ``LineOutcome`` per line, numbered from 1. Never raises
+            ``MiniCalcError``.
+        """
+        lines = text.split("\n")
+        if lines and lines[-1] == "":
+            lines.pop()  # a trailing newline starts no new line
+
+        outcomes: list[LineOutcome] = []
+        for line_no, raw in enumerate(lines, start=1):
+            line = raw[:-1] if raw.endswith("\r") else raw
+            try:
+                result = self.run_line(line, line_no)
+                error = None
+            except MiniCalcError as exc:
+                result = None
+                error = exc.with_source(line)
+            outcomes.append(LineOutcome(line_no, line, result, error))
+        return outcomes
diff --git c/minicalc/lexer.py w/minicalc/lexer.py
new file mode 100644
index 0000000..a334828
--- /dev/null
+++ w/minicalc/lexer.py
@@ -0,0 +1,106 @@
+"""Walking-skeleton lexer: whitespace, comments, numbers, EOF (CORE-003).
+
+# STUB (CORE-003): replaced wholesale by FEAT-001
+
+FEAT-001 replaces this module with the full token set. Until then, only what
+the walking skeleton needs is recognized; every other character is an illegal
+character at its own column.
+"""
+
+from __future__ import annotations
+
+from .errors import LexError, SourcePos
+from .limits import INT_MAX, MAX_LINE_LENGTH
+from .tokens import Token, TokenType
+
+_ASCII_LETTER_OR_UNDERSCORE = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
+
+
+def _is_ascii_digit(char: str) -> bool:
+    """Return whether ``char`` is an ASCII decimal digit."""
+    return "0" <= char <= "9"
+
+
+def _is_ascii_letter_or_underscore(char: str) -> bool:
+    """Return whether ``char`` can start an identifier."""
+    return char in _ASCII_LETTER_OR_UNDERSCORE
+
+
+class Lexer:
+    """Turn one source line into tokens.
+
+    Attributes:
+        source: The single source line, without its newline.
+        line_no: 1-based line number stamped on every ``SourcePos``.
+    """
+
+    def __init__(self, source: str, line_no: int = 1) -> None:
+        """Store the line to tokenize.
+
+        Args:
+            source: One source line with no trailing newline.
+            line_no: 1-based line number for every token position.
+        """
+        self.source = source
+        self.line_no = line_no
+
+    def tokenize(self) -> list[Token]:
+        """Tokenize the stored line, always ending with one ``EOF`` token.
+
+        Returns:
+            Tokens in source order.
+
+        Raises:
+            LexError: For a line over ``MAX_LINE_LENGTH``, an out-of-range
+                literal, letters directly after digits, or an illegal
+                character.
+        """
+        source = self.source
+        if len(source) > MAX_LINE_LENGTH:
+            raise LexError(
+                "line too long",
+                SourcePos(self.line_no, MAX_LINE_LENGTH + 1),
+            )
+
+        tokens: list[Token] = []
+        index = 0
+        length = len(source)
+
+        while index < length:
+            char = source[index]
+
+            if char in " \t\r":
+                index += 1
+                continue
+
+            if char == "#":
+                break
+
+            if _is_ascii_digit(char):
+                start = index
+                while index < length and _is_ascii_digit(source[index]):
+                    index += 1
+                if index < length and _is_ascii_letter_or_underscore(source[index]):
+                    raise LexError(
+                        "letters cannot follow a number",
+                        SourcePos(self.line_no, start + 1),
+                    )
+                lexeme = source[start:index]
+                value = int(lexeme)
+                if value > INT_MAX:
+                    raise LexError(
+                        "integer literal out of range",
+                        SourcePos(self.line_no, start + 1),
+                    )
+                tokens.append(
+                    Token(TokenType.NUMBER, lexeme, SourcePos(self.line_no, start + 1), value)
+                )
+                continue
+
+            raise LexError(
+                f"illegal character {char!r}",
+                SourcePos(self.line_no, index + 1),
+            )
+
+        tokens.append(Token(TokenType.EOF, "", SourcePos(self.line_no, length + 1)))
+        return tokens
diff --git c/minicalc/parser.py w/minicalc/parser.py
new file mode 100644
index 0000000..5baa4f6
--- /dev/null
+++ w/minicalc/parser.py
@@ -0,0 +1,54 @@
+"""Walking-skeleton parser: empty lines and bare number literals (CORE-003).
+
+# STUB (CORE-003): replaced wholesale by FEAT-002
+
+FEAT-002 replaces this module with the full precedence-aware grammar. Until
+then, ``NUMBER EOF`` is the only accepted statement.
+"""
+
+from __future__ import annotations
+
+from .ast_nodes import Node, Number
+from .errors import ParseError
+from .tokens import Token, TokenType
+
+
+class Parser:
+    """Parse the walking-skeleton subset of the MiniCalc grammar.
+
+    Attributes:
+        tokens: The token list to consume; the last token is ``EOF``.
+    """
+
+    def __init__(self, tokens: list[Token]) -> None:
+        """Store the token list produced by the lexer.
+
+        Args:
+            tokens: Tokens in source order, ending with exactly one ``EOF``.
+        """
+        self.tokens = tokens
+
+    def parse_statement(self) -> Node | None:
+        """Parse one statement from the token list.
+
+        Returns:
+            ``None`` for an empty line (only ``EOF``), or a ``Number`` node
+            for a single number literal.
+
+        Raises:
+            ParseError: For any input outside the walking-skeleton subset.
+        """
+        first = self.tokens[0]
+        if first.type is TokenType.EOF:
+            return None
+
+        if (
+            len(self.tokens) == 2
+            and first.type is TokenType.NUMBER
+            and self.tokens[1].type is TokenType.EOF
+        ):
+            return Number(first.value, first.pos)  # type: ignore[arg-type]
+
+        offending = self.tokens[1] if len(self.tokens) > 1 else first
+        found = offending.lexeme if offending.type is not TokenType.EOF else "end of line"
+        raise ParseError(f"expected a number, found {found!r}", offending.pos)
diff --git c/tests/test_environment.py w/tests/test_environment.py
new file mode 100644
index 0000000..1ddbd32
--- /dev/null
+++ w/tests/test_environment.py
@@ -0,0 +1,64 @@
+"""Tests for the MiniCalc Environment (CORE-003)."""
+
+import pytest
+
+from minicalc.environment import Environment
+from minicalc.errors import SourcePos, UndefinedNameError
+
+POS = SourcePos(1, 1)
+
+
+def test_initial_state_is_empty() -> None:
+    """A new environment has no variables and no ``ans``."""
+    env = Environment()
+    assert env.variables == {}
+    assert env.ans is None
+    assert env.items() == []
+
+
+def test_unset_ans_message() -> None:
+    """Reading ``ans`` before the first success is a positioned error."""
+    env = Environment()
+    with pytest.raises(UndefinedNameError) as info:
+        env.get("ans", POS)
+    assert str(info.value) == "ans has no value yet; evaluate a statement first"
+    assert info.value.pos == POS
+
+
+def test_unknown_name_message() -> None:
+    """An unknown variable names itself in the error."""
+    env = Environment()
+    with pytest.raises(UndefinedNameError) as info:
+        env.get("x", POS)
+    assert str(info.value) == "name 'x' is not defined"
+    assert info.value.pos == POS
+
+
+def test_set_get_and_record_result() -> None:
+    """``set`` binds and ``record_result`` updates only ``ans``."""
+    env = Environment()
+    env.set("x", 7)
+    env.record_result(42)
+    assert env.get("x", POS) == 7
+    assert env.get("ans", POS) == 42
+    assert env.ans == 42
+    assert env.variables == {"x": 7}
+
+
+def test_items_sorted_and_excludes_ans() -> None:
+    """``items`` is sorted by name and never contains ``ans``."""
+    env = Environment()
+    env.set("b", 2)
+    env.set("a", 1)
+    env.record_result(9)
+    assert env.items() == [("a", 1), ("b", 2)]
+
+
+def test_clear_resets_everything() -> None:
+    """``clear`` removes variables and the ``ans`` value."""
+    env = Environment()
+    env.set("x", 1)
+    env.record_result(2)
+    env.clear()
+    assert env.variables == {}
+    assert env.ans is None
diff --git c/tests/test_interpreter.py w/tests/test_interpreter.py
new file mode 100644
index 0000000..1614034
--- /dev/null
+++ w/tests/test_interpreter.py
@@ -0,0 +1,108 @@
+"""Facade-level tests for the walking skeleton (CORE-003)."""
+
+import pytest
+
+from minicalc.errors import EvalError, LexError, MiniCalcError, ParseError
+from minicalc.evaluator import Evaluator
+from minicalc.interpreter import Interpreter, LineOutcome, Result
+
+
+def test_value_line_repr() -> None:
+    """The acceptance snippet prints the exact ``Result`` repr."""
+    assert repr(Interpreter().run_line("42")) == "Result(kind='value', value=42, name=None)"
+
+
+def test_blank_and_comment_lines_are_empty() -> None:
+    """Empty, whitespace-only, and comment-only lines produce no value."""
+    interp = Interpreter()
+    for source in ("", "   ", "\t", "# comment", "   # note"):
+        assert interp.run_line(source) == Result("empty")
+
+
+def test_error_carries_source_line_and_position() -> None:
+    """A failing line re-raises with ``source_line`` attached."""
+    with pytest.raises(ParseError) as info:
+        Interpreter().run_line("2 3", 3)
+    assert info.value.source_line == "2 3"
+    assert info.value.pos is not None
+    assert info.value.pos.line == 3
+
+
+def test_failed_line_leaves_environment_unchanged() -> None:
+    """A lex error does not touch variables or ``ans``."""
+    interp = Interpreter()
+    interp.env.set("x", 5)
+    interp.env.record_result(7)
+    with pytest.raises(LexError):
+        interp.run_line("2 @ 3")
+    assert interp.env.variables == {"x": 5}
+    assert interp.env.ans == 7
+
+
+def test_run_source_numbers_lines_and_continues() -> None:
+    """Errors are captured per line and later lines still run."""
+    outcomes = Interpreter().run_source("2 3\n\n# note\n42")
+    assert [outcome.line_no for outcome in outcomes] == [1, 2, 3, 4]
+    assert isinstance(outcomes[0].error, ParseError)
+    assert outcomes[0].result is None
+    assert outcomes[1].result == Result("empty")
+    assert outcomes[2].result == Result("empty")
+    assert outcomes[3].result == Result("value", 42)
+
+
+def test_run_source_never_raises_minicalc_error() -> None:
+    """The batch facade captures every error in ``LineOutcome``."""
+    outcomes = Interpreter().run_source("2 @ 3\n99999999999\n42")
+    assert all(isinstance(outcome, LineOutcome) for outcome in outcomes)
+    assert all(isinstance(outcome.error, MiniCalcError) for outcome in outcomes[:2])
+    assert outcomes[2].result == Result("value", 42)
+
+
+def test_run_source_handles_crlf() -> None:
+    """Only ``\\n`` splits lines; a trailing ``\\r`` is stripped."""
+    outcomes = Interpreter().run_source("42\r\n43\r\n")
+    assert [outcome.result for outcome in outcomes] == [
+        Result("value", 42),
+        Result("value", 43),
+    ]
+    assert [outcome.source for outcome in outcomes] == ["42", "43"]
+
+
+def test_run_source_does_not_split_on_non_newline_breaks() -> None:
+    """Form feed and U+2028 are illegal characters, not line separators."""
+    outcomes = Interpreter().run_source("1\x0c2\n1\u20282\n")
+    assert len(outcomes) == 2
+    assert outcomes[0].error is not None
+    assert outcomes[0].error.canonical() == "ERR LexError 1:2"
+    assert outcomes[1].error is not None
+    assert outcomes[1].error.canonical() == "ERR LexError 2:2"
+
+
+def test_recursion_error_becomes_eval_error(monkeypatch: pytest.MonkeyPatch) -> None:
+    """An escaping RecursionError is converted, never leaked."""
+    def recurse(self: Evaluator, node: object) -> int:
+        return recurse(self, node)
+
+    monkeypatch.setattr(Evaluator, "evaluate", recurse)
+    with pytest.raises(EvalError) as info:
+        Interpreter().run_line("42")
+    assert str(info.value) == "expression is too deeply nested"
+    assert info.value.pos is not None
+    assert info.value.pos.col == 1
+
+
+def test_long_line_is_a_lex_error_at_column_1001() -> None:
+    """The 1000-character cap is enforced before tokenizing."""
+    with pytest.raises(LexError) as info:
+        Interpreter().run_line(" " * 1001)
+    assert info.value.pos is not None
+    assert info.value.pos.col == 1001
+
+
+def test_golden_smoke_case_runs_through_facade() -> None:
+    """The CORE-002 smoke file now exercises the real pipeline."""
+    from pathlib import Path
+
+    smoke = Path(__file__).resolve().parent / "golden" / "smoke.mc"
+    outcomes = Interpreter().run_source(smoke.read_text(encoding="utf-8"))
+    assert [outcome.result for outcome in outcomes] == [Result("value", 42)]

```

---

## 6. Flagged for APC / Operator Attention

- [ ] **F1 — Zero-skips check:** the prompt does not require it; APC asked for
  it explicitly. Verified: `pytest -q -rs` shows no skip lines and the golden
  smoke case is collected. INT-001 should repeat this check.
- [ ] **F2 — Stub input surface:** the stub lexer tokenizes only numbers,
  comments, and whitespace, so `2 +` is a `LexError`, not a `ParseError`.
  Parser errors were tested with `2 3` instead. This is expected until
  FEAT-001 and FEAT-002 land and is not a facade issue.
- [ ] **F3 — `Result("assign")` untested end to end:** the facade code path
  exists, but the stub evaluator cannot evaluate `Assign`. FEAT-003 must add
  an end-to-end assignment golden case.
- [ ] **F4 — Reserved names:** `Environment.set` performs no reserved-name
  check; `AssignmentError` enforcement belongs to FEAT-003.
- [ ] **F5 — Exception scope:** `run_source` guarantees only that
  `MiniCalcError` never escapes. A foreign exception (for example a bug in a
  future module) would still propagate; the contract does not require
  swallowing it.
