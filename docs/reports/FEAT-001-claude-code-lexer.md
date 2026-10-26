# Task Report: FEAT-001 — Full lexer

**Date:** 2026-10-26
**Agent:** claude-code
**Task ID:** FEAT-001
**Status:** needs-review
**Commit:** `feat(FEAT-001): implement full lexer` (single task commit on `task/FEAT-001`)
**Worktree:** `../minicalc-FEAT-001` (branch `task/FEAT-001`)
**Patch File:** `patch/FEAT-001-claude-code-lexer.patch`

---

## 1. Executive Summary

Replaced the CORE-003 lexer stub with the complete FEAT-001 lexer for MiniCalc
v1.0. `minicalc/lexer.py` now performs one left-to-right O(n) scan over a
single source line, emitting every `TokenType` in the contract with longest-match
operators, ASCII-only identifier/number classes, positioned `LexError`s, and an
`EOF` token at `len(source) + 1`. Added `tests/test_lexer.py`, a table-driven
suite covering all spec section 2 error rows, operator neighbors, whitespace,
comments, columns, non-ASCII rejection, the 1000-character cap, and a seeded
500-sample fuzz check.

The full suite is green: **141 passed** (77 pre-existing + 64 new).

---

## 2. Implementation Details

### 2.1 Changes Made

- `minicalc/lexer.py`: rewrote the stub (STUB marker removed). Single index scan
  with explicit ASCII predicates (`"0" <= char <= "9"` and frozenset membership
  for letters/underscore; no `str.isdigit`/`isalpha`/`isalnum`). Two-character
  operators are tested before one-character operators; a lone `!` and stray `.`
  raise `LexError`; number scan rejects a following ASCII letter/underscore at
  the number's start and rejects values above `INT_MAX`; comments (`#`) stop the
  scan; `EOF` is always appended at `len(source) + 1`. The line-length guard runs
  before scanning and reports column `MAX_LINE_LENGTH + 1` (1001).
- `tests/test_lexer.py`: new `pytest.mark.parametrize` tables for tokenization
  and lexical errors, plus explicit tests for token values, all positions,
  EOF columns, tabs/CR, boundary literals, and the fuzz property. Tests import
  only the lexer/tokens/errors/limits modules, never the parser or evaluator.

### 2.2 Conformance to Specifications & Decisions

- `docs/context/language-spec.md` section 2: token set, longest match,
  ASCII-only names and digits, whitespace set `space/tab/CR`, `#` comments,
  1-based columns with tabs counting as one, and every listed error position.
- `docs/context/interface-contract.md` section 6: `Lexer(source, line_no=1)` and
  `tokenize() -> list[Token]` are unchanged; every `SourcePos` carries `line_no`;
  a line over `MAX_LINE_LENGTH` raises at `MAX_LINE_LENGTH + 1`.
- [D-05]: literals above `INT_MAX` are rejected by the lexer; `2147483647`
  is accepted. [D-11]: module, class (`Attributes:`), and public-function
  docstrings are present. [D-02]: standard library only.

---

## 3. Verification & Test Evidence

### 3.1 Test Execution

Command executed:
```bash
python -m pytest -q
```

**Results:**
- Tests passed: 141
- Tests failed: 0
- Tests skipped: 0

```
........................................................................ [ 51%]
.....................................................................    [100%]
141 passed in 7.22s
```

Forbidden-method evidence (`grep` run in the worktree):
```bash
$ grep -nE "\.(isdigit|isalpha|isalnum)\(" minicalc/lexer.py
(no output)
```

### 3.2 Edge Cases & Negative Testing

- Every lexical-error row in the spec table asserts `LexError` and the exact
  column: `3.14`/`3.` (col 2), `.5` (col 1), `12abc`/`9_` (col 1), over-range
  literals (col 1), `2 @ 3` (col 3), `$x`/`:` (col 1), `3 ! 4` (col 3), and a
  1001-character line (col 1001).
- Non-ASCII rejection: Arabic-Indic digit `\u0663`, non-breaking space
  `\u00a0`, line separator `\u2028`, form feed `\x0c`, and `é` all raise
  `LexError` at their own column.
- Boundaries: `2147483647` accepted; `2147483648` and longer literals rejected;
  leading zeros preserved in `lexeme` while `value` is parsed (`007` -> 7);
  1000-character line accepted.
- Positions: multi-token column mapping, tab as one column, `EOF` with and
  without a trailing comment, and `line_no` propagation.
- Fuzz property: 500 seeded (`random.Random(0)`) printable-ASCII lines up to
  1000 characters either return a list ending in `EOF` at `len(source) + 1` or
  raise `LexError`; no other exception escaped.

---

## 4. Decisions Recorded

None. No decision ID was reserved for FEAT-001, and no non-trivial design choice
required a new entry.

---

## 5. Unified Git Diff

Verbatim output of `git diff HEAD~1 -- minicalc tests` in the worktree:

```diff
diff --git c/minicalc/lexer.py w/minicalc/lexer.py
index a334828..cf787ab 100644
--- c/minicalc/lexer.py
+++ w/minicalc/lexer.py
@@ -1,10 +1,13 @@
-"""Walking-skeleton lexer: whitespace, comments, numbers, EOF (CORE-003).
+"""Full lexer for MiniCalc (FEAT-001).
 
-# STUB (CORE-003): replaced wholesale by FEAT-001
+Turn one source line into a flat list of :class:`~minicalc.tokens.Token`
+objects in a single left-to-right pass. Longest-match operator handling,
+explicit ASCII-only character classes, and positioned :class:`LexError`
+messages follow ``docs/context/language-spec.md`` section 2.
 
-FEAT-001 replaces this module with the full token set. Until then, only what
-the walking skeleton needs is recognized; every other character is an illegal
-character at its own column.
+Whitespace is exactly space, tab, and carriage return. A ``#`` ends
+tokenization; the rest of the line is a comment. Every line is capped at
+``MAX_LINE_LENGTH`` characters before scanning begins.
 """
 
 from __future__ import annotations
@@ -13,17 +16,77 @@ from .errors import LexError, SourcePos
 from .limits import INT_MAX, MAX_LINE_LENGTH
 from .tokens import Token, TokenType
 
-_ASCII_LETTER_OR_UNDERSCORE = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
+#: Characters that may start an identifier: ASCII letters and underscore.
+_IDENT_START = frozenset(
+    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
+)
+
+#: Characters that may continue an identifier: ASCII letters, digits, underscore.
+_IDENT_CONTINUE = _IDENT_START | frozenset("0123456789")
+
+#: Characters ignored between tokens.
+_WHITESPACE = frozenset(" \t\r")
+
+#: Two-character operators, checked before their one-character prefixes.
+_TWO_CHAR_TOKENS = {
+    "**": TokenType.POW,
+    "//": TokenType.DSLASH,
+    "==": TokenType.EQ,
+    "!=": TokenType.NE,
+    "<=": TokenType.LE,
+    ">=": TokenType.GE,
+}
+
+#: One-character tokens with no longer form to consider.
+_SINGLE_CHAR_TOKENS = {
+    "+": TokenType.PLUS,
+    "-": TokenType.MINUS,
+    "*": TokenType.STAR,
+    "/": TokenType.SLASH,
+    "%": TokenType.PERCENT,
+    "=": TokenType.ASSIGN,
+    "<": TokenType.LT,
+    ">": TokenType.GT,
+    "(": TokenType.LPAREN,
+    ")": TokenType.RPAREN,
+    ",": TokenType.COMMA,
+}
 
 
 def _is_ascii_digit(char: str) -> bool:
-    """Return whether ``char`` is an ASCII decimal digit."""
+    """Return whether ``char`` is an ASCII decimal digit ``0``-``9``.
+
+    Args:
+        char: A single character.
+
+    Returns:
+        True only for the ten ASCII digit characters.
+    """
     return "0" <= char <= "9"
 
 
-def _is_ascii_letter_or_underscore(char: str) -> bool:
-    """Return whether ``char`` can start an identifier."""
-    return char in _ASCII_LETTER_OR_UNDERSCORE
+def _is_ident_start(char: str) -> bool:
+    """Return whether ``char`` can start an identifier.
+
+    Args:
+        char: A single character.
+
+    Returns:
+        True for ASCII letters and underscore only.
+    """
+    return char in _IDENT_START
+
+
+def _is_ident_continue(char: str) -> bool:
+    """Return whether ``char`` can continue an identifier.
+
+    Args:
+        char: A single character.
+
+    Returns:
+        True for ASCII letters, digits, and underscore only.
+    """
+    return char in _IDENT_CONTINUE
 
 
 class Lexer:
@@ -44,21 +107,34 @@ class Lexer:
         self.source = source
         self.line_no = line_no
 
+    def _pos(self, index: int) -> SourcePos:
+        """Build the 1-based position for a 0-based scan index.
+
+        Args:
+            index: 0-based index into ``self.source``.
+
+        Returns:
+            The corresponding 1-based ``SourcePos``.
+        """
+        return SourcePos(self.line_no, index + 1)
+
     def tokenize(self) -> list[Token]:
         """Tokenize the stored line, always ending with one ``EOF`` token.
 
         Returns:
-            Tokens in source order.
+            Tokens in source order; the last is always ``EOF`` with an empty
+            lexeme at column ``len(source) + 1``.
 
         Raises:
-            LexError: For a line over ``MAX_LINE_LENGTH``, an out-of-range
-                literal, letters directly after digits, or an illegal
-                character.
+            LexError: For a line over ``MAX_LINE_LENGTH``, a decimal point, a
+                letter directly after digits, an out-of-range literal, a lone
+                ``!``, or any other illegal character.
         """
         source = self.source
         if len(source) > MAX_LINE_LENGTH:
             raise LexError(
-                "line too long",
+                f"line is too long ({len(source)} characters); "
+                f"the limit is {MAX_LINE_LENGTH}",
                 SourcePos(self.line_no, MAX_LINE_LENGTH + 1),
             )
 
@@ -69,7 +145,7 @@ class Lexer:
         while index < length:
             char = source[index]
 
-            if char in " \t\r":
+            if char in _WHITESPACE:
                 index += 1
                 continue
 
@@ -77,30 +153,104 @@ class Lexer:
                 break
 
             if _is_ascii_digit(char):
+                index = self._scan_number(source, index, tokens)
+                continue
+
+            if _is_ident_start(char):
                 start = index
-                while index < length and _is_ascii_digit(source[index]):
+                while index < length and _is_ident_continue(source[index]):
                     index += 1
-                if index < length and _is_ascii_letter_or_underscore(source[index]):
-                    raise LexError(
-                        "letters cannot follow a number",
-                        SourcePos(self.line_no, start + 1),
-                    )
-                lexeme = source[start:index]
-                value = int(lexeme)
-                if value > INT_MAX:
-                    raise LexError(
-                        "integer literal out of range",
-                        SourcePos(self.line_no, start + 1),
-                    )
                 tokens.append(
-                    Token(TokenType.NUMBER, lexeme, SourcePos(self.line_no, start + 1), value)
+                    Token(TokenType.IDENT, source[start:index], self._pos(start))
                 )
                 continue
 
-            raise LexError(
-                f"illegal character {char!r}",
-                SourcePos(self.line_no, index + 1),
-            )
+            pair = source[index : index + 2]
+            if pair in _TWO_CHAR_TOKENS:
+                tokens.append(Token(_TWO_CHAR_TOKENS[pair], pair, self._pos(index)))
+                index += 2
+                continue
+
+            if char in _SINGLE_CHAR_TOKENS:
+                tokens.append(
+                    Token(_SINGLE_CHAR_TOKENS[char], char, self._pos(index))
+                )
+                index += 1
+                continue
+
+            if char == ".":
+                if self._follows_number(tokens, index):
+                    raise LexError(
+                        "decimals are not supported; "
+                        "MiniCalc works with integers only",
+                        self._pos(index),
+                    )
+                raise LexError("illegal character '.'", self._pos(index))
+
+            if char == "!":
+                raise LexError(
+                    "illegal character '!'; use '!=' for not-equal",
+                    self._pos(index),
+                )
+
+            raise LexError(f"illegal character {char!r}", self._pos(index))
 
         tokens.append(Token(TokenType.EOF, "", SourcePos(self.line_no, length + 1)))
         return tokens
+
+    def _scan_number(self, source: str, index: int, tokens: list[Token]) -> int:
+        """Scan a digit run, append its token, and return the next index.
+
+        Args:
+            source: The source line being scanned.
+            index: 0-based index of the first digit.
+            tokens: Token list to append the ``NUMBER`` token to.
+
+        Returns:
+            The index of the first character after the number.
+
+        Raises:
+            LexError: If a letter or underscore directly follows the digits
+                (reported at the start of the number), or the literal exceeds
+                ``INT_MAX`` (also at the start of the number).
+        """
+        start = index
+        length = len(source)
+        while index < length and _is_ascii_digit(source[index]):
+            index += 1
+
+        if index < length and _is_ident_start(source[index]):
+            raise LexError(
+                f"unexpected {source[index]!r} after a number; "
+                "identifiers cannot start with a digit",
+                self._pos(start),
+            )
+
+        lexeme = source[start:index]
+        value = int(lexeme)
+        if value > INT_MAX:
+            raise LexError(
+                f"integer literal {lexeme} is larger than the maximum "
+                f"supported value {INT_MAX}",
+                self._pos(start),
+            )
+        tokens.append(Token(TokenType.NUMBER, lexeme, self._pos(start), value))
+        return index
+
+    @staticmethod
+    def _follows_number(tokens: list[Token], index: int) -> bool:
+        """Return whether the character at ``index`` directly follows a number.
+
+        Args:
+            tokens: Tokens produced so far.
+            index: 0-based index of the current character.
+
+        Returns:
+            True when the last token is a ``NUMBER`` ending immediately before
+            ``index`` (so a ``.`` there is a decimal point, not a stray dot).
+        """
+        if not tokens or tokens[-1].type is not TokenType.NUMBER:
+            return False
+        token = tokens[-1]
+        end = token.pos.col - 1 + len(token.lexeme)  # 0-based index after token
+        return end == index
diff --git c/tests/test_lexer.py w/tests/test_lexer.py
new file mode 100644
index 0000000..c009589
--- /dev/null
+++ w/tests/test_lexer.py
@@ -0,0 +1,302 @@
+"""Unit tests for the full MiniCalc lexer (FEAT-001).
+
+The tests import only the lexer, tokens, errors, and limits modules; they never
+touch the parser or evaluator (FEAT-002 / FEAT-003 are being built in parallel
+against the same contract).
+"""
+
+import random
+
+import pytest
+
+from minicalc.errors import LexError, SourcePos
+from minicalc.lexer import Lexer
+from minicalc.limits import INT_MAX, MAX_LINE_LENGTH
+from minicalc.tokens import Token, TokenType
+
+T = TokenType
+EOF = (T.EOF, "")
+IDENT_X = (T.IDENT, "x")
+IDENT_A = (T.IDENT, "a")
+IDENT_B = (T.IDENT, "b")
+NUMBER_2 = (T.NUMBER, "2")
+NUMBER_3 = (T.NUMBER, "3")
+NUMBER_7 = (T.NUMBER, "7")
+
+
+def token_pairs(source: str, line_no: int = 1) -> list[tuple[TokenType, str]]:
+    """Tokenize ``source`` and return ``(type, lexeme)`` pairs.
+
+    Args:
+        source: One source line, without a trailing newline.
+        line_no: 1-based line number to stamp on positions.
+
+    Returns:
+        The token list reduced to ``(TokenType, lexeme)`` tuples.
+    """
+    return [(token.type, token.lexeme) for token in Lexer(source, line_no).tokenize()]
+
+
+TOKEN_CASES = [
+    # Empty and comment-only lines produce only EOF.
+    ("", [EOF]),
+    (" \t\r ", [EOF]),
+    ("# a comment", [EOF]),
+    ("   # indented comment", [EOF]),
+    # Longest-match operator neighbors.
+    ("2**3", [NUMBER_2, (T.POW, "**"), NUMBER_3, EOF]),
+    ("2*3", [NUMBER_2, (T.STAR, "*"), NUMBER_3, EOF]),
+    ("7//2", [NUMBER_7, (T.DSLASH, "//"), NUMBER_2, EOF]),
+    ("7/2", [NUMBER_7, (T.SLASH, "/"), NUMBER_2, EOF]),
+    ("a==b", [IDENT_A, (T.EQ, "=="), IDENT_B, EOF]),
+    ("a=b", [IDENT_A, (T.ASSIGN, "="), IDENT_B, EOF]),
+    ("a!=b", [IDENT_A, (T.NE, "!="), IDENT_B, EOF]),
+    ("a<=b", [IDENT_A, (T.LE, "<="), IDENT_B, EOF]),
+    ("a<b", [IDENT_A, (T.LT, "<"), IDENT_B, EOF]),
+    ("a>=b", [IDENT_A, (T.GE, ">="), IDENT_B, EOF]),
+    ("a>b", [IDENT_A, (T.GT, ">"), IDENT_B, EOF]),
+    # Every remaining single-character operator.
+    (
+        "+ - * / % = ( ) ,",
+        [
+            (T.PLUS, "+"),
+            (T.MINUS, "-"),
+            (T.STAR, "*"),
+            (T.SLASH, "/"),
+            (T.PERCENT, "%"),
+            (T.ASSIGN, "="),
+            (T.LPAREN, "("),
+            (T.RPAREN, ")"),
+            (T.COMMA, ","),
+            EOF,
+        ],
+    ),
+    # Symbols laid out together, exercising longest match at each position.
+    (
+        "+ - * / // % ** == != < <= > >= = ( ) ,",
+        [
+            (T.PLUS, "+"),
+            (T.MINUS, "-"),
+            (T.STAR, "*"),
+            (T.SLASH, "/"),
+            (T.DSLASH, "//"),
+            (T.PERCENT, "%"),
+            (T.POW, "**"),
+            (T.EQ, "=="),
+            (T.NE, "!="),
+            (T.LT, "<"),
+            (T.LE, "<="),
+            (T.GT, ">"),
+            (T.GE, ">="),
+            (T.ASSIGN, "="),
+            (T.LPAREN, "("),
+            (T.RPAREN, ")"),
+            (T.COMMA, ","),
+            EOF,
+        ],
+    ),
+    # Identifiers accept ASCII letters, digits, and underscore after the first.
+    ("_x", [(T.IDENT, "_x"), EOF]),
+    ("x1", [(T.IDENT, "x1"), EOF]),
+    ("abs", [(T.IDENT, "abs"), EOF]),
+    ("A_b9", [(T.IDENT, "A_b9"), EOF]),
+    # Calls and comma-separated arguments.
+    (
+        "min(1, 2)",
+        [
+            (T.IDENT, "min"),
+            (T.LPAREN, "("),
+            (T.NUMBER, "1"),
+            (T.COMMA, ","),
+            (T.NUMBER, "2"),
+            (T.RPAREN, ")"),
+            EOF,
+        ],
+    ),
+    # Whitespace: space, tab, and carriage return all separate tokens.
+    ("1 \t+\r 2", [(T.NUMBER, "1"), (T.PLUS, "+"), (T.NUMBER, "2"), EOF]),
+    # Comments end tokenization wherever they appear.
+    ("1 + 2 # trailing", [(T.NUMBER, "1"), (T.PLUS, "+"), (T.NUMBER, "2"), EOF]),
+    ("1 # 2 + 3", [(T.NUMBER, "1"), EOF]),
+    # Leading zeros are allowed; the lexeme preserves the source text.
+    ("007", [(T.NUMBER, "007"), EOF]),
+    # A multi-token assignment statement.
+    (
+        "x = 1 + 2",
+        [
+            IDENT_X,
+            (T.ASSIGN, "="),
+            (T.NUMBER, "1"),
+            (T.PLUS, "+"),
+            NUMBER_2,
+            EOF,
+        ],
+    ),
+]
+
+
+@pytest.mark.parametrize("source,expected", TOKEN_CASES)
+def test_tokenization(
+    source: str, expected: list[tuple[TokenType, str]]
+) -> None:
+    """Each source line produces exactly the expected ``(type, lexeme)`` list."""
+    assert token_pairs(source) == expected
+
+
+def test_number_token_value_is_an_int() -> None:
+    """``NUMBER`` tokens carry the parsed integer value, including leading zeros."""
+    tokens = Lexer("007 2147483647 0").tokenize()
+    assert [(token.lexeme, token.value) for token in tokens[:-1]] == [
+        ("007", 7),
+        ("2147483647", INT_MAX),
+        ("0", 0),
+    ]
+
+
+def test_non_number_tokens_have_no_value() -> None:
+    """Only ``NUMBER`` tokens set ``value``."""
+    tokens = Lexer("x = 1 + 2").tokenize()
+    assert all(
+        token.value is None for token in tokens if token.type is not T.NUMBER
+    )
+
+
+def test_columns_for_multi_token_line() -> None:
+    """Token positions are 1-based columns of each token's first character."""
+    tokens = Lexer("x = 1 + 2").tokenize()
+    assert [token.pos for token in tokens] == [
+        SourcePos(1, 1),
+        SourcePos(1, 3),
+        SourcePos(1, 5),
+        SourcePos(1, 7),
+        SourcePos(1, 9),
+        SourcePos(1, 10),
+    ]
+
+
+def test_eof_column_without_comment() -> None:
+    """EOF sits one column past the end of the line."""
+    tokens = Lexer("1 + 2").tokenize()
+    assert tokens[-1] == Token(TokenType.EOF, "", SourcePos(1, 6))
+
+
+def test_eof_column_with_trailing_comment() -> None:
+    """A comment does not move EOF; it stays at ``len(source) + 1``."""
+    source = "1 + 2 # note"
+    tokens = Lexer(source).tokenize()
+    assert tokens[-1].type is TokenType.EOF
+    assert tokens[-1].pos == SourcePos(1, len(source) + 1)
+
+
+def test_eof_column_on_empty_and_comment_only_lines() -> None:
+    """Empty and comment-only lines still end with EOF at ``len + 1``."""
+    assert Lexer("").tokenize()[-1].pos == SourcePos(1, 1)
+    assert Lexer("# note").tokenize()[-1].pos == SourcePos(1, 7)
+
+
+def test_tab_counts_as_one_column() -> None:
+    """A tab advances the column by exactly one."""
+    tokens = Lexer("\tx").tokenize()
+    assert tokens[0].pos == SourcePos(1, 2)
+    assert tokens[-1].pos == SourcePos(1, 3)
+
+
+def test_carriage_return_is_whitespace() -> None:
+    """A Windows-style trailing carriage return is harmless."""
+    tokens = Lexer("1\r").tokenize()
+    assert [(token.type, token.lexeme) for token in tokens] == [
+        (T.NUMBER, "1"),
+        EOF,
+    ]
+    assert Lexer("1\r+2").tokenize()[-1].pos == SourcePos(1, 5)
+
+
+def test_line_number_is_stamped_on_every_position() -> None:
+    """The ``line_no`` argument appears in every ``SourcePos``, including EOF."""
+    tokens = Lexer("x = 1", line_no=7).tokenize()
+    assert [token.pos.line for token in tokens] == [7, 7, 7, 7]
+    assert tokens[-1].pos == SourcePos(7, 6)
+
+
+ERROR_CASES = [
+    # Decimals: the error points at the dot.
+    ("3.14", 2, "decimals"),
+    ("3.", 2, "decimals"),
+    ("0.5", 2, "decimals"),
+    # A dot that is not part of a decimal is an illegal character.
+    (".5", 1, "illegal character"),
+    ("x.", 2, "illegal character"),
+    # Letters or underscore directly after digits: reported at number start.
+    ("12abc", 1, "after a number"),
+    ("9_", 1, "after a number"),
+    ("7x", 1, "after a number"),
+    # Out-of-range literals: reported at number start.
+    ("99999999999", 1, "larger than"),
+    ("2147483648", 1, "larger than"),
+    ("0000002147483648", 1, "larger than"),
+    # Illegal characters: reported at the offending column.
+    ("2 @ 3", 3, "illegal character"),
+    ("$x", 1, "illegal character"),
+    (":", 1, "illegal character"),
+    ("3 ! 4", 3, "illegal character"),
+    ("!", 1, "illegal character"),
+    ("3!", 2, "illegal character"),
+    ("'\"[]{}~&|^`\\", 1, "illegal character"),
+    # Non-ASCII input is always an illegal character at its own column.
+    ("\u0663", 1, "illegal character"),  # Arabic-Indic digit three
+    ("1\u00a02", 2, "illegal character"),  # non-breaking space
+    ("1\u20282", 2, "illegal character"),  # line separator, not a newline
+    ("1\x0c2", 2, "illegal character"),  # form feed is not whitespace
+    ("12é", 3, "illegal character"),  # non-ASCII letter after digits
+    # The line-length cap is checked before scanning, at column 1001.
+    (" " * (MAX_LINE_LENGTH + 1), MAX_LINE_LENGTH + 1, "too long"),
+]
+
+
+@pytest.mark.parametrize("source,column,message_fragment", ERROR_CASES)
+def test_lexical_errors(
+    source: str, column: int, message_fragment: str
+) -> None:
+    """Every spec error row raises ``LexError`` at the required column."""
+    with pytest.raises(LexError) as excinfo:
+        Lexer(source).tokenize()
+    assert excinfo.value.pos == SourcePos(1, column)
+    assert message_fragment in excinfo.value.message.lower()
+
+
+def test_error_position_uses_given_line_number() -> None:
+    """Lexical errors are stamped with the ``line_no`` passed to the lexer."""
+    with pytest.raises(LexError) as excinfo:
+        Lexer("3.14", line_no=5).tokenize()
+    assert excinfo.value.pos == SourcePos(5, 2)
+
+
+def test_int_max_is_accepted() -> None:
+    """``INT_MAX`` is a legal literal."""
+    tokens = Lexer(str(INT_MAX)).tokenize()
+    assert tokens[0].value == INT_MAX
+    assert tokens[0].lexeme == str(INT_MAX)
+
+
+def test_line_at_max_length_is_accepted() -> None:
+    """A line of exactly ``MAX_LINE_LENGTH`` characters is still scanned."""
+    tokens = Lexer(" " * MAX_LINE_LENGTH).tokenize()
+    assert [(token.type, token.lexeme) for token in tokens] == [EOF]
+
+
+def test_random_printable_ascii_only_raises_lex_error() -> None:
+    """Fuzz: 500 seeded printable-ASCII lines end in EOF or raise ``LexError``."""
+    rng = random.Random(0)
+    alphabet = "".join(chr(code) for code in range(32, 127))
+    for _ in range(500):
+        source = "".join(
+            rng.choice(alphabet) for _ in range(rng.randrange(MAX_LINE_LENGTH + 1))
+        )
+        try:
+            tokens = Lexer(source).tokenize()
+        except LexError:
+            continue
+        assert tokens, "tokenize() must never return an empty list"
+        assert tokens[-1].type is TokenType.EOF
+        assert tokens[-1].lexeme == ""
+        assert tokens[-1].pos == SourcePos(1, len(source) + 1)
```

---

## 6. Flagged for APC / Operator Attention

- [ ] **`12é` ambiguity (non-blocking).** The spec table says letters directly
  after digits are reported at the start of the number, while the same section
  says every non-ASCII character is an illegal character at its own column.
  This implementation treats only ASCII letters/underscore as the
  "after a number" error; a non-ASCII letter such as `é` is reported as an
  illegal character at its own column (col 3 in `12é`). A test locks this
  behavior. Confirm or reword the spec if the number-start position is intended.
- [ ] **Patch path slug.** The FEAT-001 prompt suggests the `full-lexer` slug,
  but the handoff instructions specified `patch/FEAT-001-claude-code-lexer.patch`
  and `docs/reports/FEAT-001-claude-code-lexer.md`; the handoff names were used.
