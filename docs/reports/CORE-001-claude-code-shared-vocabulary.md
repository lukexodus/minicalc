# Task Report: CORE-001 — Shared vocabulary: limits, errors, tokens, AST

**Date:** 2026-10-26
**Agent:** claude-code
**Task ID:** CORE-001
**Status:** needs-review
**Commit:** `feat(CORE-001): add limits, errors, tokens and AST nodes` (single task commit on `task/CORE-001`)
**Worktree:** `../minicalc-CORE-001` (branch `task/CORE-001`)
**Patch File:** `patch/CORE-001-claude-code-shared-vocabulary.patch`

---

## 1. Executive Summary

Added the four shared-vocabulary modules that every later task imports:
`limits.py` (32-bit bounds and `in_range`), `errors.py` (`SourcePos`,
`MiniCalcError`, and the eight concrete subclasses in the contract),
`tokens.py` (`TokenType`, `Token`), and `ast_nodes.py` (six frozen nodes plus
`Op` and `Node`). Tests cover the contract's `render()` example byte for byte,
color and tab rendering, the canonical golden format, the class hierarchy,
frozen/hashable dataclasses, and pickle round-trips.

`pytest -q` reports `42 passed` (41 new tests plus the existing package
smoke test). Public names and dataclass field order were verified with
`inspect`; evidence is in section 3.2.

---

## 2. Implementation Details

### 2.1 Changes Made

- `minicalc/limits.py`: exported `INT_MIN`, `INT_MAX`, `MAX_LINE_LENGTH`,
  and `in_range(value) -> bool` exactly as contract section 2.
- `minicalc/errors.py`: frozen `SourcePos(line, col)`; `MiniCalcError` with
  `kind`, `message`, `pos`, `source_line`, `with_source()`, `render()`, and
  `canonical()`. Concrete classes: `LexError`, `ParseError`, `EvalError`,
  `DivisionByZeroError`, `IntegerRangeError`, `DomainError`,
  `UndefinedNameError`, `CallError`, `AssignmentError`.
- `minicalc/tokens.py`: all 20 `TokenType` members and frozen
  `Token(type, lexeme, pos, value=None)`.
- `minicalc/ast_nodes.py`: frozen `Number`, `Name`, `Unary`, `Binary`,
  `Call`, `Assign` with `pos` last; `Op` literal alias; `Node` union.
- `tests/test_errors.py`: limits boundaries, exact render layouts (plain,
  color, tab, missing source line, missing position), canonical strings,
  hierarchy and `kind` values, frozen `SourcePos`, pickle round-trip.
- `tests/test_vocabulary.py`: token set, `Token` default/frozen/hashable,
  every node frozen and hashable, structural equality, `pos` last field,
  `Call.args` tuple.

Docstrings follow [D-11]: every module and public function has one, and every
class docstring has an `Attributes:` section. The exception classes document
the inherited `kind` class variable.

### 2.2 Conformance to Specifications & Decisions

- [D-05]: `INT_MIN`/`INT_MAX` are the design-locked signed 32-bit bounds.
- [D-07]: `canonical()` emits `ERR <ClassName> <line>:<col>` (or `?:?`),
  message text is never part of the golden form, and `render()` draws the
  caret under 1-based columns with tabs replaced by one space.
- [D-11]: docstrings as described above.
- No third-party imports; dependency direction is `limits` standalone,
  `errors` standalone, `tokens -> errors`, `ast_nodes -> errors`, so there are
  no circular imports.

---

## 3. Verification & Test Evidence

### 3.1 Test Execution

```text
$ python -m pytest -q
..........................................                               [100%]
42 passed in 10.94s
```

### 3.2 Public API and field-order evidence

```text
limits: ['INT_MAX', 'INT_MIN', 'MAX_LINE_LENGTH', 'in_range']
errors: ['AssignmentError', 'CallError', 'DivisionByZeroError', 'DomainError',
         'EvalError', 'IntegerRangeError', 'LexError', 'MiniCalcError',
         'ParseError', 'SourcePos', 'UndefinedNameError']
tokens: ['SourcePos', 'Token', 'TokenType']
ast_nodes: ['Assign', 'Binary', 'Call', 'Literal', 'Name', 'Node', 'Number',
            'Op', 'SourcePos', 'Unary', 'Union']
MiniCalcError.__init__ (self, message: str, pos: minicalc.errors.SourcePos | None = None,
                        source_line: str | None = None) -> None
in_range (value: int) -> bool
Token ['type', 'lexeme', 'pos', 'value']
Number ['value', 'pos']
Name ['ident', 'pos']
Unary ['op', 'operand', 'pos']
Binary ['op', 'left', 'right', 'pos']
Call ['func', 'args', 'pos']
Assign ['target', 'value', 'pos']
```

### 3.3 Edge Cases & Negative Testing

- `render()` reproduces the contract section 3 example exactly, including the
  six-space caret indentation for column 5.
- A tab in the source line is replaced by one space, keeping the caret aligned.
- `render()` with `pos=None` or `source_line=None` prints only the heading.
- Every dataclass raises `dataclasses.FrozenInstanceError` on assignment.
- AST nodes compare structurally, hash equal, and `Call.args` is a tuple.
- `pickle.loads(pickle.dumps(err))` preserves class, message, position, and
  source line through `__reduce__`.

---

## 4. Decisions Recorded

None. No decision ID was reserved for CORE-001 and no new design choice was
needed beyond the contract.

---

## 5. Unified Git Diff

```diff
diff --git c/minicalc/ast_nodes.py w/minicalc/ast_nodes.py
new file mode 100644
index 0000000..3eba5be
--- /dev/null
+++ w/minicalc/ast_nodes.py
@@ -0,0 +1,106 @@
+"""Immutable abstract-syntax-tree nodes for MiniCalc ([D-04]).
+
+Every node is a frozen dataclass carrying ``pos`` as its last field, so nodes
+are structurally comparable and hashable. ``Assign`` is produced only at the
+top of a statement; expressions never contain one.
+"""
+
+from dataclasses import dataclass as _dataclass
+from typing import Literal, Union
+
+from .errors import SourcePos
+
+#: Every binary operator that can appear in a ``Binary`` node.
+Op = Literal["+", "-", "*", "/", "//", "%", "**", "==", "!=", "<", "<=", ">", ">="]
+
+
+@_dataclass(frozen=True)
+class Number:
+    """An integer literal.
+
+    Attributes:
+        value: The literal value, already range-checked by the lexer.
+        pos: 1-based position of the first digit.
+    """
+
+    value: int
+    pos: SourcePos
+
+
+@_dataclass(frozen=True)
+class Name:
+    """A variable reference.
+
+    Attributes:
+        ident: The identifier text, case-sensitive.
+        pos: 1-based position of the first character of the name.
+    """
+
+    ident: str
+    pos: SourcePos
+
+
+@_dataclass(frozen=True)
+class Unary:
+    """A prefix unary operation.
+
+    Attributes:
+        op: Either ``"-"`` (negation) or ``"+"`` (identity).
+        operand: The expression the operator applies to.
+        pos: 1-based position of the operator character.
+    """
+
+    op: Literal["-", "+"]
+    operand: "Node"
+    pos: SourcePos
+
+
+@_dataclass(frozen=True)
+class Binary:
+    """A binary operation.
+
+    Attributes:
+        op: One of the operators in :data:`Op`.
+        left: The left operand.
+        right: The right operand.
+        pos: 1-based position of the operator character.
+    """
+
+    op: Op
+    left: "Node"
+    right: "Node"
+    pos: SourcePos
+
+
+@_dataclass(frozen=True)
+class Call:
+    """A call to a built-in function.
+
+    Attributes:
+        func: The built-in's name (``abs``, ``min``, ``max``, or ``gcd``).
+        args: Immutable tuple of argument expressions, in source order.
+        pos: 1-based position of the function name.
+    """
+
+    func: str
+    args: tuple["Node", ...]
+    pos: SourcePos
+
+
+@_dataclass(frozen=True)
+class Assign:
+    """An assignment statement (``name = expression``).
+
+    Attributes:
+        target: The identifier being bound.
+        value: The expression supplying the new value.
+        pos: 1-based position of the target identifier.
+    """
+
+    target: str
+    value: "Node"
+    pos: SourcePos
+
+
+#: Union of every concrete AST node type.
+Node = Union[Number, Name, Unary, Binary, Call, Assign]
diff --git c/minicalc/errors.py w/minicalc/errors.py
new file mode 100644
index 0000000..c2eacca
--- /dev/null
+++ w/minicalc/errors.py
@@ -0,0 +1,209 @@
+"""The MiniCalc error hierarchy ([D-07]).
+
+Every error carries an optional :class:`SourcePos`, and may carry the offending
+source line so :meth:`MiniCalcError.render` can draw a caret under the column.
+Golden tests compare :meth:`MiniCalcError.canonical` output only, never message
+text, so message wording stays free to improve.
+"""
+
+from dataclasses import dataclass as _dataclass
+from typing import ClassVar as _ClassVar
+
+#: Prefix used by ``render(color=True)`` for the ``Error:`` label.
+_BOLD_RED = "\x1b[1;31m"
+#: Prefix used by ``render(color=True)`` for the caret.
+_RED = "\x1b[31m"
+#: ANSI reset sequence.
+_RESET = "\x1b[0m"
+
+
+@_dataclass(frozen=True)
+class SourcePos:
+    """A 1-based position in the original source text.
+
+    Attributes:
+        line: 1-based line number.
+        col: 1-based column number; tabs count as one column.
+    """
+
+    line: int
+    col: int
+
+
+class MiniCalcError(Exception):
+    """Base class for every error MiniCalc reports to the user.
+
+    Attributes:
+        kind (ClassVar[str]): Human-readable category shown by ``render()``.
+        message: The specific message for this error instance.
+        pos: Position of the offending token, or ``None`` when unknown.
+        source_line: The offending line without its newline, used to draw a
+            caret; ``None`` when unavailable.
+    """
+
+    kind: _ClassVar[str] = "Error"
+
+    message: str
+    pos: SourcePos | None
+    source_line: str | None
+
+    def __init__(
+        self,
+        message: str,
+        pos: SourcePos | None = None,
+        source_line: str | None = None,
+    ) -> None:
+        """Initialize the error.
+
+        Args:
+            message: The specific message for this error instance.
+            pos: Position of the offending token, or ``None``.
+            source_line: The offending source line, or ``None``.
+        """
+        super().__init__(message)
+        self.message = message
+        self.pos = pos
+        self.source_line = source_line
+
+    def __str__(self) -> str:
+        """Return the bare message, matching ``err.message``."""
+        return self.message
+
+    def __reduce__(self) -> tuple[object, tuple[object, ...]]:
+        """Preserve the full error state across ``pickle`` round-trips."""
+        return (type(self), (self.message, self.pos, self.source_line))
+
+    def with_source(self, source_line: str) -> "MiniCalcError":
+        """Attach the offending source line and return this same error.
+
+        Args:
+            source_line: The offending line without its newline.
+
+        Returns:
+            This error instance, to allow chaining.
+        """
+        self.source_line = source_line
+        return self
+
+    def render(self, color: bool = False) -> str:
+        """Render a user-facing, optionally colored, multi-line message.
+
+        Args:
+            color: When True, style ``Error:`` in bold red and the caret in
+                red with ANSI escape codes.
+
+        Returns:
+            The error heading, plus the source line and caret when both
+            ``pos`` and ``source_line`` are available.
+        """
+        if self.pos is None:
+            heading = f"Error: {self.kind}: {self.message}"
+        else:
+            heading = (
+                f"Error: {self.kind} at line {self.pos.line}, "
+                f"column {self.pos.col}: {self.message}"
+            )
+
+        if color:
+            heading = heading.replace("Error:", f"{_BOLD_RED}Error:{_RESET}", 1)
+
+        lines = [heading]
+        if self.pos is not None and self.source_line is not None:
+            source = self.source_line.replace("\t", " ")
+            padding = "  " + " " * (self.pos.col - 1)
+            caret = "^"
+            if color:
+                caret = f"{_RED}^{_RESET}"
+            lines.append("  " + source)
+            lines.append(padding + caret)
+        return "\n".join(lines)
+
+    def canonical(self) -> str:
+        """Return the stable golden-test form of this error.
+
+        Returns:
+            ``ERR <ClassName> <line>:<col>``, or ``ERR <ClassName> ?:?`` when
+            the error has no position.
+        """
+        name = type(self).__name__
+        if self.pos is None:
+            return f"ERR {name} ?:?"
+        return f"ERR {name} {self.pos.line}:{self.pos.col}"
+
+
+class LexError(MiniCalcError):
+    """Raised by the lexer for malformed characters or literals.
+
+    Attributes:
+        kind (ClassVar[str]): ``"Lexical error"``.
+    """
+
+    kind: _ClassVar[str] = "Lexical error"
+
+
+class ParseError(MiniCalcError):
+    """Raised by the parser for malformed syntax.
+
+    Attributes:
+        kind (ClassVar[str]): ``"Syntax error"``.
+    """
+
+    kind: _ClassVar[str] = "Syntax error"
+
+
+class EvalError(MiniCalcError):
+    """Base class for every runtime (evaluation) error.
+
+    Attributes:
+        kind (ClassVar[str]): ``"Runtime error"``.
+    """
+
+    kind: _ClassVar[str] = "Runtime error"
+
+
+class DivisionByZeroError(EvalError):
+    """Raised when ``/``, ``//``, or ``%`` receives a zero divisor.
+
+    Attributes:
+        kind (ClassVar[str]): Inherited ``"Runtime error"``.
+    """
+
+
+class IntegerRangeError(EvalError):
+    """Raised when a produced value leaves the signed 32-bit range.
+
+    Attributes:
+        kind (ClassVar[str]): Inherited ``"Runtime error"``.
+    """
+
+
+class DomainError(EvalError):
+    """Raised for a mathematically invalid operation, such as a negative exponent.
+
+    Attributes:
+        kind (ClassVar[str]): Inherited ``"Runtime error"``.
+    """
+
+
+class UndefinedNameError(EvalError):
+    """Raised when a variable is not set, including an unset ``ans``.
+
+    Attributes:
+        kind (ClassVar[str]): Inherited ``"Runtime error"``.
+    """
+
+
+class CallError(EvalError):
+    """Raised for an unknown function, non-function call, or wrong arity.
+
+    Attributes:
+        kind (ClassVar[str]): Inherited ``"Runtime error"``.
+    """
+
+
+class AssignmentError(EvalError):
+    """Raised when assigning to ``ans`` or to a built-in name.
+
+    Attributes:
+        kind (ClassVar[str]): Inherited ``"Runtime error"``.
+    """
diff --git c/minicalc/limits.py w/minicalc/limits.py
new file mode 100644
index 0000000..d71685b
--- /dev/null
+++ w/minicalc/limits.py
@@ -0,0 +1,23 @@
+"""Numeric limits for the MiniCalc integer model ([D-05]).
+
+Values are signed 32-bit integers with checked arithmetic: a result outside
+this range raises ``IntegerRangeError`` instead of wrapping. The line-length
+cap keeps one source line small enough that the recursive-descent parser stays
+well below Python's recursion limit.
+"""
+
+INT_MIN: int = -2_147_483_648
+INT_MAX: int = 2_147_483_647
+MAX_LINE_LENGTH: int = 1000
+
+
+def in_range(value: int) -> bool:
+    """Return whether ``value`` fits the signed 32-bit range.
+
+    Args:
+        value: An integer produced by the lexer or evaluator.
+
+    Returns:
+        True when ``INT_MIN <= value <= INT_MAX``, otherwise False.
+    """
+    return INT_MIN <= value <= INT_MAX
diff --git c/minicalc/tokens.py w/minicalc/tokens.py
new file mode 100644
index 0000000..3fcf88a
--- /dev/null
+++ w/minicalc/tokens.py
@@ -0,0 +1,77 @@
+"""Token vocabulary shared by the lexer and parser.
+
+The lexer emits a flat list of :class:`Token` objects that always ends with one
+``TokenType.EOF`` token. The parser consumes that list without re-reading the
+source text, so every token keeps its exact ``lexeme`` and its 1-based
+:class:`~minicalc.errors.SourcePos`.
+"""
+
+from dataclasses import dataclass as _dataclass
+from enum import Enum as _Enum
+
+from .errors import SourcePos
+
+
+class TokenType(_Enum):
+    """Every token kind the MiniCalc lexer can produce.
+
+    Attributes:
+        NUMBER: Decimal integer literal; ``Token.value`` holds the integer.
+        IDENT: Identifier (``[A-Za-z_][A-Za-z0-9_]*``), case-sensitive.
+        PLUS: ``+`` operator.
+        MINUS: ``-`` operator.
+        STAR: ``*`` operator.
+        SLASH: ``/`` operator (truncating division).
+        DSLASH: ``//`` operator (floor division).
+        PERCENT: ``%`` operator (floored modulo).
+        POW: ``**`` operator (right-associative exponentiation).
+        EQ: ``==`` comparison operator.
+        NE: ``!=`` comparison operator.
+        LT: ``<`` comparison operator.
+        LE: ``<=`` comparison operator.
+        GT: ``>`` comparison operator.
+        GE: ``>=`` comparison operator.
+        ASSIGN: Single ``=`` assignment operator.
+        LPAREN: ``(``.
+        RPAREN: ``)``.
+        COMMA: ``,``.
+        EOF: End of the source line; always the last token.
+    """
+
+    NUMBER = "NUMBER"
+    IDENT = "IDENT"
+    PLUS = "PLUS"
+    MINUS = "MINUS"
+    STAR = "STAR"
+    SLASH = "SLASH"
+    DSLASH = "DSLASH"
+    PERCENT = "PERCENT"
+    POW = "POW"
+    EQ = "EQ"
+    NE = "NE"
+    LT = "LT"
+    LE = "LE"
+    GT = "GT"
+    GE = "GE"
+    ASSIGN = "ASSIGN"
+    LPAREN = "LPAREN"
+    RPAREN = "RPAREN"
+    COMMA = "COMMA"
+    EOF = "EOF"
+
+
+@_dataclass(frozen=True)
+class Token:
+    """One lexical token and its position in the source line.
+
+    Attributes:
+        type: The token kind.
+        lexeme: Exact source text of the token (``""`` for ``EOF``).
+        pos: 1-based line and column where the token starts.
+        value: Parsed integer for ``NUMBER`` tokens; ``None`` for all others.
+    """
+
+    type: TokenType
+    lexeme: str
+    pos: SourcePos
+    value: int | None = None
diff --git c/tests/test_errors.py w/tests/test_errors.py
new file mode 100644
index 0000000..a723e2e
--- /dev/null
+++ w/tests/test_errors.py
@@ -0,0 +1,147 @@
+"""Tests for limits and the MiniCalc error hierarchy (CORE-001)."""
+
+import pickle
+from dataclasses import FrozenInstanceError
+
+import pytest
+
+from minicalc.errors import (
+    AssignmentError,
+    CallError,
+    DivisionByZeroError,
+    DomainError,
+    EvalError,
+    IntegerRangeError,
+    LexError,
+    MiniCalcError,
+    ParseError,
+    SourcePos,
+    UndefinedNameError,
+)
+from minicalc.limits import INT_MAX, INT_MIN, MAX_LINE_LENGTH, in_range
+
+EVAL_ERRORS = [
+    DivisionByZeroError,
+    IntegerRangeError,
+    DomainError,
+    UndefinedNameError,
+    CallError,
+    AssignmentError,
+]
+
+
+def test_limits_values() -> None:
+    """The design-locked constants are exact."""
+    assert INT_MIN == -2_147_483_648
+    assert INT_MAX == 2_147_483_647
+    assert MAX_LINE_LENGTH == 1000
+
+
+@pytest.mark.parametrize(
+    ("value", "expected"),
+    [
+        (INT_MIN - 1, False),
+        (INT_MIN, True),
+        (INT_MAX, True),
+        (INT_MAX + 1, False),
+    ],
+)
+def test_in_range(value: int, expected: bool) -> None:
+    """Boundaries are inclusive."""
+    assert in_range(value) is expected
+
+
+def test_render_matches_contract_example() -> None:
+    """The contract section 3 layout is reproduced byte for byte."""
+    err = ParseError("expected an expression, found '*'", SourcePos(1, 5), "2 + * 3")
+    assert err.render() == (
+        "Error: Syntax error at line 1, column 5: expected an expression, found '*'\n"
+        "  2 + * 3\n"
+        "      ^"
+    )
+
+
+def test_render_without_source_line() -> None:
+    """No source line means no caret block."""
+    err = LexError("illegal character '@'", SourcePos(3, 2))
+    assert err.render() == "Error: Lexical error at line 3, column 2: illegal character '@'"
+
+
+def test_render_without_position() -> None:
+    """No position means the kind-only heading."""
+    err = MiniCalcError("something went wrong")
+    assert err.render() == "Error: Error: something went wrong"
+
+
+def test_render_tab_alignment() -> None:
+    """Each tab becomes one space so the caret stays aligned."""
+    err = ParseError("bad token", SourcePos(1, 2), "\t7 + 1")
+    assert err.render() == "Error: Syntax error at line 1, column 2: bad token\n   7 + 1\n   ^"
+
+
+def test_render_color_styles_only_label_and_caret() -> None:
+    """Color mode wraps exactly two spans."""
+    err = ParseError("expected an expression, found '*'", SourcePos(1, 5), "2 + * 3")
+    assert err.render(color=True) == (
+        "\x1b[1;31mError:\x1b[0m Syntax error at line 1, column 5: "
+        "expected an expression, found '*'\n"
+        "  2 + * 3\n"
+        "      \x1b[31m^\x1b[0m"
+    )
+
+
+def test_with_source_is_chainable() -> None:
+    """``with_source`` sets the line and returns the same object."""
+    err = ParseError("bad")
+    assert err.with_source("1 +") is err
+    assert err.source_line == "1 +"
+
+
+def test_str_is_message() -> None:
+    """``str(err)`` never includes the kind or position."""
+    err = DomainError("negative exponent", SourcePos(2, 4))
+    assert str(err) == "negative exponent"
+    assert err.message == "negative exponent"
+
+
+def test_canonical_formats() -> None:
+    """Canonical output names the concrete subclass and position."""
+    assert ParseError("x", SourcePos(1, 5)).canonical() == "ERR ParseError 1:5"
+    assert LexError("x", SourcePos(2, 1)).canonical() == "ERR LexError 2:1"
+    assert DivisionByZeroError("x", SourcePos(3, 9)).canonical() == (
+        "ERR DivisionByZeroError 3:9"
+    )
+    assert MiniCalcError("x").canonical() == "ERR MiniCalcError ?:?"
+
+
+@pytest.mark.parametrize(
+    "cls",
+    [LexError, ParseError, EvalError, *EVAL_ERRORS],
+)
+def test_hierarchy_and_kinds(cls: type[MiniCalcError]) -> None:
+    """Every class subclasses MiniCalcError with the right ``kind``."""
+    assert issubclass(cls, MiniCalcError)
+    expected_kind = {
+        LexError: "Lexical error",
+        ParseError: "Syntax error",
+    }.get(cls, "Runtime error")
+    assert cls.kind == expected_kind
+    if cls is not EvalError and cls not in (LexError, ParseError):
+        assert issubclass(cls, EvalError)
+
+
+def test_source_pos_is_frozen() -> None:
+    """``SourcePos`` cannot be mutated."""
+    pos = SourcePos(1, 2)
+    with pytest.raises(FrozenInstanceError):
+        pos.line = 3  # type: ignore[misc]
+
+
+def test_errors_are_picklable() -> None:
+    """Errors survive a pickle round-trip with position and source line."""
+    err = UndefinedNameError("x is not set", SourcePos(4, 7), "x + 1")
+    clone = pickle.loads(pickle.dumps(err))
+    assert type(clone) is UndefinedNameError
+    assert clone.message == err.message
+    assert clone.pos == err.pos
+    assert clone.source_line == err.source_line
diff --git c/tests/test_vocabulary.py w/tests/test_vocabulary.py
new file mode 100644
index 0000000..79afdae
--- /dev/null
+++ w/tests/test_vocabulary.py
@@ -0,0 +1,98 @@
+"""Tests for tokens and AST nodes (CORE-001)."""
+
+from dataclasses import FrozenInstanceError, fields
+
+import pytest
+
+from minicalc.ast_nodes import Assign, Binary, Call, Name, Number, Unary
+from minicalc.errors import SourcePos
+from minicalc.tokens import Token, TokenType
+
+POS = SourcePos(1, 1)
+
+
+def test_token_types_are_complete() -> None:
+    """The contract's token set is present and nothing extra is required."""
+    assert {member.name for member in TokenType} == {
+        "NUMBER",
+        "IDENT",
+        "PLUS",
+        "MINUS",
+        "STAR",
+        "SLASH",
+        "DSLASH",
+        "PERCENT",
+        "POW",
+        "EQ",
+        "NE",
+        "LT",
+        "LE",
+        "GT",
+        "GE",
+        "ASSIGN",
+        "LPAREN",
+        "RPAREN",
+        "COMMA",
+        "EOF",
+    }
+
+
+def test_token_fields_and_default() -> None:
+    """``value`` defaults to None and is only meaningful for NUMBER."""
+    token = Token(TokenType.IDENT, "x", POS)
+    assert token.value is None
+    assert token.type is TokenType.IDENT
+    assert token.lexeme == "x"
+    assert token.pos == POS
+
+
+def test_token_is_frozen_and_hashable() -> None:
+    """Tokens are immutable value objects."""
+    token = Token(TokenType.NUMBER, "42", POS, 42)
+    with pytest.raises(FrozenInstanceError):
+        token.value = 7  # type: ignore[misc]
+    assert token == Token(TokenType.NUMBER, "42", POS, 42)
+    assert hash(token) == hash(Token(TokenType.NUMBER, "42", POS, 42))
+
+
+def _node_samples() -> list[object]:
+    """Build one instance of every AST node type."""
+    number = Number(2, POS)
+    name = Name("x", POS)
+    unary = Unary("-", number, SourcePos(1, 2))
+    binary = Binary("+", number, name, SourcePos(1, 4))
+    call = Call("max", (number, name), POS)
+    assign = Assign("x", binary, POS)
+    return [number, name, unary, binary, call, assign]
+
+
+@pytest.mark.parametrize("node", _node_samples())
+def test_nodes_have_pos_last(node: object) -> None:
+    """Every node declares ``pos`` as its final dataclass field."""
+    assert fields(node)[-1].name == "pos"  # type: ignore[arg-type]
+    assert node.pos == getattr(node, "pos")  # type: ignore[attr-defined]
+
+
+@pytest.mark.parametrize("node", _node_samples())
+def test_nodes_are_frozen_hashable_and_value_equal(node: object) -> None:
+    """Nodes cannot be mutated and compare structurally."""
+    with pytest.raises(FrozenInstanceError):
+        node.pos = SourcePos(9, 9)  # type: ignore[misc,attr-defined]
+    clone = _node_samples()[_node_samples().index(node)]
+    assert node == clone
+    assert hash(node) == hash(clone)
+
+
+def test_call_args_are_a_tuple() -> None:
+    """``Call.args`` is immutable and keeps source order."""
+    call = Call("min", (Number(3, POS), Number(1, POS)), POS)
+    assert isinstance(call.args, tuple)
+    assert [arg.value for arg in call.args] == [3, 1]  # type: ignore[attr-defined]
+
+
+def test_structural_equality_distinguishes_fields() -> None:
+    """Different values or operators are not equal."""
+    assert Number(1, POS) != Number(2, POS)
+    assert Binary("+", Number(1, POS), Number(2, POS), POS) != Binary(
+        "-", Number(1, POS), Number(2, POS), POS
+    )

```

---

## 6. Flagged for APC / Operator Attention

- [ ] **F1 — "eight subclasses" count:** the CORE-001 prompt says "the eight
  subclasses listed in the contract", but section 3 lists nine concrete
  classes under `MiniCalcError` (`EvalError` plus six runtime leaf classes and
  the two lexer/parser classes). All nine were implemented; only `EvalError`
  is abstract. No code impact.
- [ ] **F2 — Python floor:** this machine only has Python 3.14.8. The code
  avoids post-3.10 syntax (`X | None`, `tuple[...]`, frozen dataclasses), but
  it has not been executed on 3.10. Same caveat as ARCH-002 F5.
- [ ] **F3 — Extra module-level names:** `ast_nodes` exposes `Literal` and
  `Union` from `typing` because they define the public aliases; `tokens`
  re-exports `SourcePos`. These are not behavior changes.
