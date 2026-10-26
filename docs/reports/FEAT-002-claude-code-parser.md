# Task Report: FEAT-002 — Full parser

**Date:** 2026-10-26
**Agent:** claude-code
**Task ID:** FEAT-002
**Status:** needs-review
**Commit:** `ae12ee4 feat(FEAT-002): implement full parser` (single task commit on `task/FEAT-002`)
**Worktree:** `../minicalc-FEAT-002` (branch `task/FEAT-002`)
**Patch File:** `patch/FEAT-002-claude-code-parser.patch`

---

## 1. Executive Summary

Replaced the CORE-003 parser stub with the complete hand-written
recursive-descent parser for the grammar in `docs/context/language-spec.md`
section 3. All six precedence levels, right-associative `**`, non-associative
comparisons, assignments, calls, and parenthesized expressions are implemented,
with every AST node position taken from the producing token as the contract
requires.

The new `tests/test_parser.py` builds tokens directly from `Token`/`TokenType`
(no lexer import) and covers every spec precedence row, every parse-error table
row with its exact column, all `pos` rules, the 200-entry nesting cap, a
5000-term flat chain, and 500 seeded random token sequences. The full suite is
green: **121 passed** (44 of them in the new parser test file).

---

## 2. Implementation Details

### 2.1 Changes Made

- `minicalc/parser.py`: rewrote the stub as a full recursive-descent parser.
  - One method per grammar rule: `_statement`, `_expression`, `_additive`,
    `_term`, `_unary`, `_power`, `_primary`, and `_call_args`; the grammar is
    documented in the `Parser` class docstring.
  - `additive` and `term` use loops, so left-associative chains consume
    constant stack space; only parentheses, calls, prefix unary, and `**`
    recurse.
  - `parse_statement()` returns `None` for an empty line, an `Assign` when the
    first two tokens are `IDENT ASSIGN`, and an expression node otherwise.
  - Node positions: operator token for `Binary`/`Unary`, function-name token for
    `Call`, identifier for `Name` and `Assign.target`, literal for `Number`.
  - Non-associative comparisons reject a second comparison operator with a
    message that tells the user to add parentheses.
  - Leftover tokens after a complete statement raise `ParseError`. A trailing
    `=` gets the dedicated message "left side of '=' must be a name" when the
    parsed left side was not a bare name, and "chained assignment is not
    supported" for `x = y = 3`; both point at the offending `=`.
  - `MAX_DEPTH = 200` is enforced on entries into `_expression`, and an escaping
    `RecursionError` inside `parse_statement` is converted to the same
    `ParseError("expression is nested too deeply")` at the current token.
  - The `# STUB (CORE-003)` marker is gone.
- `tests/test_parser.py`: 44 tests with a small self-contained token builder.
  Covers precedence/associativity, AST shape and every `pos` rule, assignment
  vs. expression, 0/1/many/nested call arguments, every error-table row,
  depth safety (100 succeeds, 300 fails cleanly, 201 is the hard cap when the
  Python recursion limit is raised), a 5000-term `1 + 1 + ...` chain, and 500
  seeded random token lists that must only ever return a node/`None` or raise
  `ParseError`.

### 2.2 Conformance to Specifications & Decisions

- Contract section 7: `Parser(tokens)` and `parse_statement() -> Node | None`
  are unchanged; the whole token list is consumed.
- [D-04]: hand-written recursive descent with a precedence-aware grammar.
- [D-06]: `**` right-associative and tighter than unary minus; comparisons
  non-associative; left-associative levels loop.
- [D-07]: every `ParseError` carries the exact `SourcePos` from the spec table;
  message text is not part of the golden comparison.
- [D-11]: module, class (`Attributes:`), and public-function docstrings added.
- [D-13]: error-message templates logged in `docs/decisions/decision-log.md`.

---

## 3. Verification & Test Evidence

### 3.1 Test Execution

Command executed:

```bash
python -m pytest -q
```

**Results:** 121 passed, 0 failed, 0 skipped.

```text
........................................................................ [ 59%]
.................................................                        [100%]
121 passed in 5.14s
```

New parser tests alone:

```text
$ python -m pytest -q tests/test_parser.py
............................................                             [100%]
44 passed in 6.73s
```

### 3.2 Edge Cases & Negative Testing

- Exact error columns verified for: `2 +`, `2 + * 3`, `(2 + 3`, `2 3`,
  `1 < 2 < 3`, `max(1,`, `max(1,)`, `)`, `= 5`, `x =`, `f(1 2)`, `()`,
  `2 **`, plus `5 = 3`, `a + 1 = 2`, and `x = y = 3`.
- `-2 ** 2` -> `Unary(-, Binary(**, 2, 2))`; `2 ** 3 ** 2` ->
  `Binary(**, 2, Binary(**, 3, 2))`; `10 - 3 - 2` -> left-nested `-`;
  `2 + 3 == 5` -> comparison at the root.
- `(1 < 2) < 3` parses; an unparenthesized chain is rejected at the second
  comparison operator.
- 100 nested parentheses succeed; 300 raise `ParseError` (no `RecursionError`
  escapes); with the recursion limit raised, 201 nested parentheses prove the
  `MAX_DEPTH` counter itself fires.
- A 5000-term additive chain parses iteratively.
- 500 random token sequences (seed `20261026`) produced only AST nodes,
  `None`, or `ParseError`.

---

## 4. Decisions Recorded

- **[D-13]**: parser error-message wording conventions. Settled templates are
  logged in `docs/decisions/decision-log.md` (lowercase "expected ... found
  <token>" shape, `end of line` for `EOF`, dedicated messages for the two
  assignment mistakes and for chained comparisons/nesting).

---

## 5. Unified Git Diff

```diff
diff --git c/minicalc/parser.py w/minicalc/parser.py
index 5baa4f6..e71a8e1 100644
--- c/minicalc/parser.py
+++ w/minicalc/parser.py
@@ -1,23 +1,73 @@
-"""Walking-skeleton parser: empty lines and bare number literals (CORE-003).
+"""Hand-written recursive-descent parser for MiniCalc (FEAT-002).
 
-# STUB (CORE-003): replaced wholesale by FEAT-002
-
-FEAT-002 replaces this module with the full precedence-aware grammar. Until
-then, ``NUMBER EOF`` is the only accepted statement.
+The parser consumes the flat token list produced by the lexer and builds the
+frozen AST nodes from :mod:`minicalc.ast_nodes`. It never re-reads source text:
+every node position comes from the token that produced it. The grammar itself
+is documented in the :class:`Parser` class docstring.
 """
 
 from __future__ import annotations
 
-from .ast_nodes import Node, Number
+from .ast_nodes import Assign, Binary, Call, Name, Node, Number, Op, Unary
 from .errors import ParseError
 from .tokens import Token, TokenType
 
+#: Maximum number of simultaneously active ``_expression`` calls. Deeper input
+#: raises ``ParseError`` instead of exhausting the Python stack.
+MAX_DEPTH: int = 200
+
+#: Binary-text spelling of every comparison operator token.
+_COMPARE_OPS: dict[TokenType, Op] = {
+    TokenType.EQ: "==",
+    TokenType.NE: "!=",
+    TokenType.LT: "<",
+    TokenType.LE: "<=",
+    TokenType.GT: ">",
+    TokenType.GE: ">=",
+}
+
+#: Binary-text spelling of every additive operator token.
+_ADDITIVE_OPS: dict[TokenType, Op] = {
+    TokenType.PLUS: "+",
+    TokenType.MINUS: "-",
+}
+
+#: Binary-text spelling of every multiplicative operator token.
+_TERM_OPS: dict[TokenType, Op] = {
+    TokenType.STAR: "*",
+    TokenType.SLASH: "/",
+    TokenType.DSLASH: "//",
+    TokenType.PERCENT: "%",
+}
+
 
 class Parser:
-    """Parse the walking-skeleton subset of the MiniCalc grammar.
+    """Turn one line's token list into a MiniCalc statement AST.
+
+    Grammar (lowest precedence first; authoritative copy in
+    ``docs/context/language-spec.md`` section 3)::
+
+        line        = [ statement ] EOF ;
+        statement   = assignment | expression ;
+        assignment  = IDENT ASSIGN expression ;
+        expression  = additive [ compare_op additive ] ;  (* non-associative *)
+        compare_op  = EQ | NE | LT | LE | GT | GE ;
+        additive    = term { ( PLUS | MINUS ) term } ;
+        term        = unary { ( STAR | SLASH | DSLASH | PERCENT ) unary } ;
+        unary       = ( MINUS | PLUS ) unary | power ;
+        power       = primary [ POW unary ] ;             (* right-associative *)
+        primary     = NUMBER | IDENT | call | LPAREN expression RPAREN ;
+        call        = IDENT LPAREN [ expression { COMMA expression } ] RPAREN ;
+
+    Left-associative levels (``additive`` and ``term``) are parsed with loops,
+    so long chains such as ``1 + 1 + ...`` use constant stack space. Recursion
+    is used only for genuinely nested constructs: parentheses, calls, prefix
+    unary operators, and the right-associative ``**``.
 
     Attributes:
         tokens: The token list to consume; the last token is ``EOF``.
+        index: Zero-based index of the next token to consume.
+        _depth: Number of ``_expression`` calls currently on the stack.
     """
 
     def __init__(self, tokens: list[Token]) -> None:
@@ -27,28 +77,247 @@ class Parser:
             tokens: Tokens in source order, ending with exactly one ``EOF``.
         """
         self.tokens = tokens
+        self.index = 0
+        self._depth = 0
 
+    # ------------------------------------------------------------------
+    # Token cursor helpers
+    # ------------------------------------------------------------------
+    def _peek(self, offset: int = 0) -> Token:
+        """Return a token without consuming it.
+
+        Args:
+            offset: How many tokens ahead of the cursor to inspect.
+
+        Returns:
+            The requested token, clamped to the final ``EOF`` token.
+        """
+        index = self.index + offset
+        if index >= len(self.tokens):
+            index = len(self.tokens) - 1
+        return self.tokens[index]
+
+    def _advance(self) -> Token:
+        """Consume and return the token at the cursor."""
+        token = self._peek()
+        if token.type is not TokenType.EOF:
+            self.index += 1
+        return token
+
+    @staticmethod
+    def _describe(token: Token) -> str:
+        """Return the user-facing description of a found token.
+
+        Args:
+            token: The token to describe.
+
+        Returns:
+            ``end of line`` for ``EOF``, otherwise the token's lexeme in
+            quotes so punctuation is visible in the message.
+        """
+        if token.type is TokenType.EOF:
+            return "end of line"
+        return repr(token.lexeme)
+
+    # ------------------------------------------------------------------
+    # Statement and grammar rules
+    # ------------------------------------------------------------------
     def parse_statement(self) -> Node | None:
         """Parse one statement from the token list.
 
         Returns:
-            ``None`` for an empty line (only ``EOF``), or a ``Number`` node
-            for a single number literal.
+            ``None`` when the line holds only ``EOF``, an ``Assign`` for an
+            assignment, or the root expression node otherwise.
 
         Raises:
-            ParseError: For any input outside the walking-skeleton subset.
+            ParseError: For malformed syntax, leftover tokens, chained
+                comparisons, chained assignments, a non-name assignment
+                target, or nesting beyond ``MAX_DEPTH``.
         """
-        first = self.tokens[0]
+        try:
+            return self._statement()
+        except RecursionError as exc:
+            raise ParseError(
+                "expression is nested too deeply", self._peek().pos
+            ) from exc
+
+    def _statement(self) -> Node | None:
+        """Parse ``line = [ statement ] EOF``.
+
+        Returns:
+            ``None`` for an empty line, otherwise the statement node.
+
+        Raises:
+            ParseError: For malformed syntax or tokens left after the
+                statement.
+        """
+        first = self._peek()
         if first.type is TokenType.EOF:
             return None
 
-        if (
-            len(self.tokens) == 2
-            and first.type is TokenType.NUMBER
-            and self.tokens[1].type is TokenType.EOF
-        ):
-            return Number(first.value, first.pos)  # type: ignore[arg-type]
+        if first.type is TokenType.IDENT and self._peek(1).type is TokenType.ASSIGN:
+            target_token = self._advance()
+            self._advance()  # ASSIGN
+            value = self._expression()
+            if self._peek().type is TokenType.ASSIGN:
+                raise ParseError(
+                    "chained assignment is not supported", self._peek().pos
+                )
+            node: Node = Assign(target_token.lexeme, value, target_token.pos)
+        else:
+            node = self._expression()
+            if self._peek().type is TokenType.ASSIGN:
+                raise ParseError(
+                    "left side of '=' must be a name", self._peek().pos
+                )
 
-        offending = self.tokens[1] if len(self.tokens) > 1 else first
-        found = offending.lexeme if offending.type is not TokenType.EOF else "end of line"
-        raise ParseError(f"expected a number, found {found!r}", offending.pos)
+        leftover = self._peek()
+        if leftover.type is not TokenType.EOF:
+            raise ParseError(
+                f"expected end of line, found {self._describe(leftover)}",
+                leftover.pos,
+            )
+        return node
+
+    def _expression(self) -> Node:
+        """Parse ``expression = additive [ compare_op additive ]``.
+
+        Comparison is non-associative: a second comparison operator in the
+        same expression is rejected.
+
+        Returns:
+            The expression node.
+
+        Raises:
+            ParseError: For a chained comparison or nesting beyond
+                ``MAX_DEPTH``.
+        """
+        self._depth += 1
+        try:
+            if self._depth > MAX_DEPTH:
+                raise ParseError(
+                    "expression is nested too deeply", self._peek().pos
+                )
+
+            left = self._additive()
+            operator = self._peek()
+            op_text = _COMPARE_OPS.get(operator.type)
+            if op_text is None:
+                return left
+
+            self._advance()
+            right = self._additive()
+            node = Binary(op_text, left, right, operator.pos)
+
+            chained = self._peek()
+            if chained.type in _COMPARE_OPS:
+                raise ParseError(
+                    "comparison operators cannot be chained; add parentheses",
+                    chained.pos,
+                )
+            return node
+        finally:
+            self._depth -= 1
+
+    def _additive(self) -> Node:
+        """Parse ``additive = term { ( PLUS | MINUS ) term }`` left-associatively."""
+        node = self._term()
+        while self._peek().type in _ADDITIVE_OPS:
+            operator = self._advance()
+            right = self._term()
+            node = Binary(_ADDITIVE_OPS[operator.type], node, right, operator.pos)
+        return node
+
+    def _term(self) -> Node:
+        """Parse ``term = unary { ( STAR | SLASH | DSLASH | PERCENT ) unary }``."""
+        node = self._unary()
+        while self._peek().type in _TERM_OPS:
+            operator = self._advance()
+            right = self._unary()
+            node = Binary(_TERM_OPS[operator.type], node, right, operator.pos)
+        return node
+
+    def _unary(self) -> Node:
+        """Parse ``unary = ( MINUS | PLUS ) unary | power``."""
+        token = self._peek()
+        if token.type in (TokenType.MINUS, TokenType.PLUS):
+            self._advance()
+            operand = self._unary()
+            return Unary("-" if token.type is TokenType.MINUS else "+", operand, token.pos)
+        return self._power()
+
+    def _power(self) -> Node:
+        """Parse ``power = primary [ POW unary ]``, right-associatively."""
+        base = self._primary()
+        token = self._peek()
+        if token.type is TokenType.POW:
+            self._advance()
+            exponent = self._unary()
+            return Binary("**", base, exponent, token.pos)
+        return base
+
+    def _primary(self) -> Node:
+        """Parse ``primary = NUMBER | IDENT | call | LPAREN expression RPAREN``.
+
+        Raises:
+            ParseError: When the current token cannot start an expression or a
+                closing parenthesis is missing.
+        """
+        token = self._peek()
+
+        if token.type is TokenType.NUMBER:
+            self._advance()
+            assert token.value is not None
+            return Number(token.value, token.pos)
+
+        if token.type is TokenType.IDENT:
+            self._advance()
+            if self._peek().type is TokenType.LPAREN:
+                args = self._call_args()
+                return Call(token.lexeme, args, token.pos)
+            return Name(token.lexeme, token.pos)
+
+        if token.type is TokenType.LPAREN:
+            self._advance()
+            node = self._expression()
+            closing = self._peek()
+            if closing.type is not TokenType.RPAREN:
+                raise ParseError(
+                    f"expected ')', found {self._describe(closing)}", closing.pos
+                )
+            self._advance()
+            return node
+
+        raise ParseError(
+            f"expected an expression, found {self._describe(token)}", token.pos
+        )
+
+    def _call_args(self) -> tuple[Node, ...]:
+        """Parse ``LPAREN [ expression { COMMA expression } ] RPAREN``.
+
+        Returns:
+            The argument tuple, in source order.
+
+        Raises:
+            ParseError: When an argument is missing or the closing parenthesis
+                or comma is missing.
+        """
+        self._advance()  # LPAREN
+
+        if self._peek().type is TokenType.RPAREN:
+            self._advance()
+            return ()
+
+        args: list[Node] = [self._expression()]
+        while self._peek().type is TokenType.COMMA:
+            self._advance()
+            args.append(self._expression())
+
+        closing = self._peek()
+        if closing.type is not TokenType.RPAREN:
+            raise ParseError(
+                f"expected ',' or ')', found {self._describe(closing)}",
+                closing.pos,
+            )
+        self._advance()
+        return tuple(args)
diff --git c/tests/test_parser.py w/tests/test_parser.py
new file mode 100644
index 0000000..fcff6b8
--- /dev/null
+++ w/tests/test_parser.py
@@ -0,0 +1,576 @@
+"""Parser tests for the full MiniCalc grammar (FEAT-002).
+
+Tokens are built directly from :class:`~minicalc.tokens.Token` and
+:class:`~minicalc.tokens.TokenType`; the lexer is intentionally not imported so
+parser behavior is tested in isolation from FEAT-001.
+"""
+
+from __future__ import annotations
+
+import random
+import re
+import sys
+
+import pytest
+
+from minicalc.ast_nodes import Assign, Binary, Call, Name, Node, Number, Unary
+from minicalc.errors import ParseError, SourcePos
+from minicalc.parser import MAX_DEPTH, Parser
+from minicalc.tokens import Token, TokenType
+
+#: Lexeme-to-type lookup for hand-written token lists.
+_TOKEN_TYPES: dict[str, TokenType] = {
+    "+": TokenType.PLUS,
+    "-": TokenType.MINUS,
+    "*": TokenType.STAR,
+    "/": TokenType.SLASH,
+    "//": TokenType.DSLASH,
+    "%": TokenType.PERCENT,
+    "**": TokenType.POW,
+    "==": TokenType.EQ,
+    "!=": TokenType.NE,
+    "<": TokenType.LT,
+    "<=": TokenType.LE,
+    ">": TokenType.GT,
+    ">=": TokenType.GE,
+    "=": TokenType.ASSIGN,
+    "(": TokenType.LPAREN,
+    ")": TokenType.RPAREN,
+    ",": TokenType.COMMA,
+}
+
+_NUMBER_RE = re.compile(r"[0-9]+")
+_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
+#: Longest operators first, so ``**`` wins over ``*`` and ``<=`` over ``<``.
+_TEST_TOKEN_RE = re.compile(
+    r"[0-9]+"
+    r"|[A-Za-z_][A-Za-z0-9_]*"
+    r"|//|\*\*|==|!=|<=|>="
+    r"|[+\-*/%<>=(),]"
+)
+
+
+def toks(source: str) -> list[Token]:
+    """Build a token list directly from test source text.
+
+    This tiny self-contained scanner (independent of ``minicalc.lexer``)
+    recognizes the vocabulary the parser needs and records each token's real
+    1-based column, so adjacent tokens such as ``()`` are handled exactly.
+
+    Args:
+        source: Test source text; whitespace separates tokens and is ignored.
+
+    Returns:
+        The tokens in source order, ending with one ``EOF`` token.
+
+    Raises:
+        ValueError: If a non-whitespace character is not part of the test
+            vocabulary.
+    """
+    tokens: list[Token] = []
+    cursor = 0
+    for match in _TEST_TOKEN_RE.finditer(source):
+        if source[cursor:match.start()].strip():
+            raise ValueError(f"unknown test token {source[cursor:match.start()]!r}")
+        lexeme = match.group()
+        pos = SourcePos(1, match.start() + 1)
+        if _NUMBER_RE.fullmatch(lexeme):
+            tokens.append(Token(TokenType.NUMBER, lexeme, pos, int(lexeme)))
+        elif _IDENT_RE.fullmatch(lexeme):
+            tokens.append(Token(TokenType.IDENT, lexeme, pos))
+        elif lexeme in _TOKEN_TYPES:
+            tokens.append(Token(_TOKEN_TYPES[lexeme], lexeme, pos))
+        else:
+            raise ValueError(f"unknown test token {lexeme!r}")
+        cursor = match.end()
+    if source[cursor:].strip():
+        raise ValueError(f"unknown test token {source[cursor:]!r}")
+    tokens.append(Token(TokenType.EOF, "", SourcePos(1, len(source) + 1)))
+    return tokens
+
+
+def parse(source: str) -> Node | None:
+    """Parse a test source string with a fresh parser."""
+    return Parser(toks(source)).parse_statement()
+
+
+def parse_error(source: str) -> ParseError:
+    """Parse ``source`` and return the ``ParseError`` it raises."""
+    with pytest.raises(ParseError) as info:
+        parse(source)
+    return info.value
+
+
+# ---------------------------------------------------------------------------
+# Statement selection
+# ---------------------------------------------------------------------------
+def test_empty_line_returns_none() -> None:
+    """Only ``EOF`` means an empty line."""
+    assert parse("") is None
+
+
+def test_expression_statement() -> None:
+    """A bare expression returns its root node."""
+    assert parse("x") == Name("x", SourcePos(1, 1))
+
+
+def test_assignment_statement() -> None:
+    """``IDENT ASSIGN expression`` becomes an ``Assign`` at the name."""
+    assert parse("x = 5") == Assign("x", Number(5, SourcePos(1, 5)), SourcePos(1, 1))
+
+
+def test_equality_is_not_assignment() -> None:
+    """``x == 5`` is a comparison, not an assignment."""
+    assert parse("x == 5") == Binary(
+        "==",
+        Name("x", SourcePos(1, 1)),
+        Number(5, SourcePos(1, 6)),
+        SourcePos(1, 3),
+    )
+
+
+def test_call_of_a_variable_parses() -> None:
+    """``x(1)`` parses as a call; rejecting non-functions is the evaluator's job."""
+    assert parse("x(1)") == Call("x", (Number(1, SourcePos(1, 3)),), SourcePos(1, 1))
+
+
+# ---------------------------------------------------------------------------
+# Precedence and associativity
+# ---------------------------------------------------------------------------
+def test_multiplication_binds_tighter_than_addition() -> None:
+    """``2 + 3 * 4`` groups the multiplication first."""
+    assert parse("2 + 3 * 4") == Binary(
+        "+",
+        Number(2, SourcePos(1, 1)),
+        Binary(
+            "*",
+            Number(3, SourcePos(1, 5)),
+            Number(4, SourcePos(1, 9)),
+            SourcePos(1, 7),
+        ),
+        SourcePos(1, 3),
+    )
+
+
+def test_parentheses_override_precedence() -> None:
+    """``(2 + 3) * 4`` makes the addition the left operand."""
+    assert parse("(2 + 3) * 4") == Binary(
+        "*",
+        Binary(
+            "+",
+            Number(2, SourcePos(1, 2)),
+            Number(3, SourcePos(1, 6)),
+            SourcePos(1, 4),
+        ),
+        Number(4, SourcePos(1, 11)),
+        SourcePos(1, 9),
+    )
+
+
+def test_additive_is_left_associative() -> None:
+    """``10 - 3 - 2`` is ``(10 - 3) - 2``."""
+    assert parse("10 - 3 - 2") == Binary(
+        "-",
+        Binary(
+            "-",
+            Number(10, SourcePos(1, 1)),
+            Number(3, SourcePos(1, 6)),
+            SourcePos(1, 4),
+        ),
+        Number(2, SourcePos(1, 10)),
+        SourcePos(1, 8),
+    )
+
+
+def test_term_level_is_left_associative() -> None:
+    """Every multiplicative operator shares one left-associative level."""
+    assert parse("8 / 4 // 2 % 3 * 2") == Binary(
+        "*",
+        Binary(
+            "%",
+            Binary(
+                "//",
+                Binary(
+                    "/",
+                    Number(8, SourcePos(1, 1)),
+                    Number(4, SourcePos(1, 5)),
+                    SourcePos(1, 3),
+                ),
+                Number(2, SourcePos(1, 10)),
+                SourcePos(1, 7),
+            ),
+            Number(3, SourcePos(1, 14)),
+            SourcePos(1, 12),
+        ),
+        Number(2, SourcePos(1, 18)),
+        SourcePos(1, 16),
+    )
+
+
+def test_additive_and_term_levels_combine() -> None:
+    """``*`` binds tighter than ``+`` on both sides."""
+    assert parse("2 * 3 + 4 * 5") == Binary(
+        "+",
+        Binary(
+            "*",
+            Number(2, SourcePos(1, 1)),
+            Number(3, SourcePos(1, 5)),
+            SourcePos(1, 3),
+        ),
+        Binary(
+            "*",
+            Number(4, SourcePos(1, 9)),
+            Number(5, SourcePos(1, 13)),
+            SourcePos(1, 11),
+        ),
+        SourcePos(1, 7),
+    )
+
+
+def test_power_is_right_associative() -> None:
+    """``2 ** 3 ** 2`` is ``2 ** (3 ** 2)``."""
+    assert parse("2 ** 3 ** 2") == Binary(
+        "**",
+        Number(2, SourcePos(1, 1)),
+        Binary(
+            "**",
+            Number(3, SourcePos(1, 6)),
+            Number(2, SourcePos(1, 11)),
+            SourcePos(1, 8),
+        ),
+        SourcePos(1, 3),
+    )
+
+
+def test_power_binds_tighter_than_unary_minus() -> None:
+    """``-2 ** 2`` is ``-(2 ** 2)``, per the spec."""
+    assert parse("-2 ** 2") == Unary(
+        "-",
+        Binary(
+            "**",
+            Number(2, SourcePos(1, 2)),
+            Number(2, SourcePos(1, 7)),
+            SourcePos(1, 4),
+        ),
+        SourcePos(1, 1),
+    )
+
+
+def test_exponent_may_be_a_unary_expression() -> None:
+    """``2 ** -1`` parses; the negative exponent fails only at evaluation."""
+    assert parse("2 ** -1") == Binary(
+        "**",
+        Number(2, SourcePos(1, 1)),
+        Unary("-", Number(1, SourcePos(1, 7)), SourcePos(1, 6)),
+        SourcePos(1, 3),
+    )
+
+
+def test_prefix_operators_are_right_associative() -> None:
+    """``--2`` and ``-+2`` stack as nested unary nodes."""
+    assert parse("--2") == Unary(
+        "-", Unary("-", Number(2, SourcePos(1, 3)), SourcePos(1, 2)), SourcePos(1, 1)
+    )
+    assert parse("-+2") == Unary(
+        "-", Unary("+", Number(2, SourcePos(1, 3)), SourcePos(1, 2)), SourcePos(1, 1)
+    )
+
+
+def test_comparison_binds_loosest() -> None:
+    """``2 + 3 == 5`` compares the arithmetic results."""
+    assert parse("2 + 3 == 5") == Binary(
+        "==",
+        Binary(
+            "+",
+            Number(2, SourcePos(1, 1)),
+            Number(3, SourcePos(1, 5)),
+            SourcePos(1, 3),
+        ),
+        Number(5, SourcePos(1, 10)),
+        SourcePos(1, 7),
+    )
+
+
+def test_parenthesized_comparison_inside_comparison() -> None:
+    """``(1 < 2) < 3`` is legal because the inner comparison is parenthesized."""
+    assert parse("(1 < 2) < 3") == Binary(
+        "<",
+        Binary(
+            "<",
+            Number(1, SourcePos(1, 2)),
+            Number(2, SourcePos(1, 6)),
+            SourcePos(1, 4),
+        ),
+        Number(3, SourcePos(1, 11)),
+        SourcePos(1, 9),
+    )
+
+
+# ---------------------------------------------------------------------------
+# Node positions
+# ---------------------------------------------------------------------------
+def test_positions_for_names_numbers_binary_unary_and_assign() -> None:
+    """Every node position follows the contract's rule."""
+    assert parse("  x = -1 + 2 * y") == Assign(
+        "x",
+        Binary(
+            "+",
+            Unary("-", Number(1, SourcePos(1, 8)), SourcePos(1, 7)),
+            Binary(
+                "*",
+                Number(2, SourcePos(1, 12)),
+                Name("y", SourcePos(1, 16)),
+                SourcePos(1, 14),
+            ),
+            SourcePos(1, 10),
+        ),
+        SourcePos(1, 3),
+    )
+
+
+def test_positions_for_calls_and_arguments() -> None:
+    """A call's position is its name; arguments keep their own positions."""
+    assert parse("  max(abs(1), 2, gcd(4, 6))") == Call(
+        "max",
+        (
+            Call("abs", (Number(1, SourcePos(1, 11)),), SourcePos(1, 7)),
+            Number(2, SourcePos(1, 15)),
+            Call(
+                "gcd",
+                (
+                    Number(4, SourcePos(1, 22)),
+                    Number(6, SourcePos(1, 25)),
+                ),
+                SourcePos(1, 18),
+            ),
+        ),
+        SourcePos(1, 3),
+    )
+
+
+# ---------------------------------------------------------------------------
+# Calls
+# ---------------------------------------------------------------------------
+def test_call_with_zero_arguments() -> None:
+    """``abs()`` parses with an empty tuple; arity is checked later."""
+    assert parse("abs()") == Call("abs", (), SourcePos(1, 1))
+
+
+def test_call_with_one_argument() -> None:
+    """A unary expression may be an argument."""
+    assert parse("abs(-3)") == Call(
+        "abs",
+        (Unary("-", Number(3, SourcePos(1, 6)), SourcePos(1, 5)),),
+        SourcePos(1, 1),
+    )
+
+
+def test_call_with_many_arguments() -> None:
+    """Commas separate an arbitrary number of arguments."""
+    assert parse("max(1, 2, 3, 4)") == Call(
+        "max",
+        (
+            Number(1, SourcePos(1, 5)),
+            Number(2, SourcePos(1, 8)),
+            Number(3, SourcePos(1, 11)),
+            Number(4, SourcePos(1, 14)),
+        ),
+        SourcePos(1, 1),
+    )
+
+
+def test_nested_calls_in_arguments() -> None:
+    """Calls nest inside arguments and keep their own node positions."""
+    assert parse("max(min(1, 2), abs(-3))") == Call(
+        "max",
+        (
+            Call(
+                "min",
+                (
+                    Number(1, SourcePos(1, 9)),
+                    Number(2, SourcePos(1, 12)),
+                ),
+                SourcePos(1, 5),
+            ),
+            Call(
+                "abs",
+                (Unary("-", Number(3, SourcePos(1, 21)), SourcePos(1, 20)),),
+                SourcePos(1, 16),
+            ),
+        ),
+        SourcePos(1, 1),
+    )
+
+
+# ---------------------------------------------------------------------------
+# Error table (spec section 3 plus the prompt's extension rows)
+# ---------------------------------------------------------------------------
+@pytest.mark.parametrize(
+    "source, column, fragment",
+    [
+        ("2 +", 4, "expected an expression, found end of line"),
+        ("2 + * 3", 5, "expected an expression, found '*'"),
+        ("(2 + 3", 7, "expected ')', found end of line"),
+        ("2 3", 3, "expected end of line, found '3'"),
+        ("1 < 2 < 3", 7, "comparison operators cannot be chained"),
+        ("max(1,", 7, "expected an expression, found end of line"),
+        ("max(1,)", 7, "expected an expression, found ')'"),
+        (")", 1, "expected an expression, found ')'"),
+        ("= 5", 1, "expected an expression, found '='"),
+        ("x =", 4, "expected an expression, found end of line"),
+        ("f(1 2)", 5, "expected ',' or ')', found '2'"),
+        ("()", 2, "expected an expression, found ')'"),
+        ("2 **", 5, "expected an expression, found end of line"),
+    ],
+)
+def test_error_table_row(source: str, column: int, fragment: str) -> None:
+    """Each documented syntax error is reported at its exact column."""
+    error = parse_error(source)
+    assert error.pos == SourcePos(1, column)
+    assert fragment in error.message
+
+
+def test_left_side_of_assignment_must_be_a_name() -> None:
+    """A complete expression followed by ``=`` is not an assignment."""
+    for source, column in (("5 = 3", 3), ("a + 1 = 2", 7)):
+        error = parse_error(source)
+        assert error.message == "left side of '=' must be a name"
+        assert error.pos == SourcePos(1, column)
+
+
+def test_chained_assignment_is_rejected() -> None:
+    """``x = y = 3`` names the second ``=`` as the offending token."""
+    error = parse_error("x = y = 3")
+    assert error.message == "chained assignment is not supported"
+    assert error.pos == SourcePos(1, 7)
+
+
+def test_comparison_chain_tells_the_user_to_add_parentheses() -> None:
+    """The chained-comparison message carries the required guidance."""
+    error = parse_error("1 < 2 < 3")
+    assert "add parentheses" in error.message
+
+
+def test_leftover_token_after_assignment() -> None:
+    """An assignment must also consume the whole line."""
+    error = parse_error("x = 1 2")
+    assert error.message == "expected end of line, found '2'"
+    assert error.pos == SourcePos(1, 7)
+
+
+# ---------------------------------------------------------------------------
+# Nesting depth and long flat chains
+# ---------------------------------------------------------------------------
+def _nested_parens(depth: int) -> str:
+    """Return ``depth`` nested parentheses around ``1``, space-separated."""
+    return " ".join(["("] * depth + ["1"] + [")"] * depth)
+
+
+def test_hundred_nested_parentheses_succeed() -> None:
+    """100 levels are well inside ``MAX_DEPTH`` and parse normally."""
+    node = parse(_nested_parens(100))
+    assert isinstance(node, Number)
+    assert node.value == 1
+
+
+def test_three_hundred_nested_parentheses_fail_cleanly() -> None:
+    """Pathological nesting raises ``ParseError``, never ``RecursionError``."""
+    error = parse_error(_nested_parens(300))
+    assert error.message == "expression is nested too deeply"
+
+
+def test_depth_limit_counts_expression_entries() -> None:
+    """``MAX_DEPTH`` itself (not just Python's stack) is enforced at 200."""
+    assert MAX_DEPTH == 200
+    previous_limit = sys.getrecursionlimit()
+    sys.setrecursionlimit(20000)
+    try:
+        error = parse_error(_nested_parens(MAX_DEPTH + 1))
+    finally:
+        sys.setrecursionlimit(previous_limit)
+    assert error.message == "expression is nested too deeply"
+
+
+def test_five_thousand_term_sum_does_not_recurse() -> None:
+    """Left-associative chains are parsed with a loop, not recursion."""
+    node = parse("1 + " * 4999 + "1")
+    assert isinstance(node, Binary)
+    assert node.op == "+"
+
+
+# ---------------------------------------------------------------------------
+# Robustness
+# ---------------------------------------------------------------------------
+_RANDOM_TOKEN_TYPES: tuple[TokenType, ...] = (
+    TokenType.NUMBER,
+    TokenType.IDENT,
+    TokenType.PLUS,
+    TokenType.MINUS,
+    TokenType.STAR,
+    TokenType.SLASH,
+    TokenType.DSLASH,
+    TokenType.PERCENT,
+    TokenType.POW,
+    TokenType.EQ,
+    TokenType.NE,
+    TokenType.LT,
+    TokenType.LE,
+    TokenType.GT,
+    TokenType.GE,
+    TokenType.ASSIGN,
+    TokenType.LPAREN,
+    TokenType.RPAREN,
+    TokenType.COMMA,
+)
+
+_RANDOM_LEXEMES: dict[TokenType, str] = {
+    TokenType.PLUS: "+",
+    TokenType.MINUS: "-",
+    TokenType.STAR: "*",
+    TokenType.SLASH: "/",
+    TokenType.DSLASH: "//",
+    TokenType.PERCENT: "%",
+    TokenType.POW: "**",
+    TokenType.EQ: "==",
+    TokenType.NE: "!=",
+    TokenType.LT: "<",
+    TokenType.LE: "<=",
+    TokenType.GT: ">",
+    TokenType.GE: ">=",
+    TokenType.ASSIGN: "=",
+    TokenType.LPAREN: "(",
+    TokenType.RPAREN: ")",
+    TokenType.COMMA: ",",
+}
+
+
+def _random_tokens(rng: random.Random) -> list[Token]:
+    """Build one random, syntactically arbitrary token list ending in ``EOF``."""
+    tokens: list[Token] = []
+    for index in range(rng.randint(0, 12)):
+        token_type = rng.choice(_RANDOM_TOKEN_TYPES)
+        pos = SourcePos(1, index + 1)
+        if token_type is TokenType.NUMBER:
+            value = rng.randint(0, 999)
+            tokens.append(Token(token_type, str(value), pos, value))
+        elif token_type is TokenType.IDENT:
+            tokens.append(Token(token_type, rng.choice(("x", "y", "max", "ans")), pos))
+        else:
+            tokens.append(Token(token_type, _RANDOM_LEXEMES[token_type], pos))
+    tokens.append(Token(TokenType.EOF, "", SourcePos(1, len(tokens) + 1)))
+    return tokens
+
+
+def test_random_token_sequences_only_raise_parse_error() -> None:
+    """500 seeded random token lists return a node/``None`` or ``ParseError``."""
+    rng = random.Random(20261026)
+    node_types = (Number, Name, Unary, Binary, Call, Assign)
+    for _ in range(500):
+        tokens = _random_tokens(rng)
+        try:
+            node = Parser(tokens).parse_statement()
+        except ParseError:
+            continue
+        except Exception as exc:  # noqa: BLE001 - this is the property under test
+            pytest.fail(f"unexpected {type(exc).__name__} for {tokens!r}: {exc}")
+        assert node is None or isinstance(node, node_types)
```

---

## 6. Flagged for APC / Operator Attention

- [ ] **Test token helper:** `toks()` is a tiny self-contained scanner rather
  than a literal whitespace split. A pure split cannot express the spec's
  adjacent-token rows (`()`) or `(1 < 2) < 3` with exact columns. It still
  builds `Token` objects directly and does not import the lexer.
- [ ] **Depth-limit interaction:** with Python's default recursion limit
  (~1000), 300 nested parentheses hit the `RecursionError` fallback before the
  `MAX_DEPTH = 200` counter; both paths raise the same `ParseError` message.
  Under the facade's raised limit (4000) the counter fires at 201, which is
  covered by a dedicated test.
- [ ] **End-to-end limitation:** the CORE-003 lexer stub does not tokenize
  operators or identifiers yet, so this parser is exercised through direct
  token lists until FEAT-001 lands. No parser behavior depends on the lexer.
- [ ] **Prompt row `2 ** `:** tested as `2 **` (trailing whitespace is not a
  token); EOF column follows the spec rule `len(line) + 1`.
