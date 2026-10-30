# Task Report: DOC-001 — Class `Attributes:` docstrings and the docs checker

**Date:** 2026-10-30
**Agent:** opencode
**Task ID:** DOC-001
**Status:** needs-review
**Commit:** `9f51737` — `docs(DOC-001): document every class variable and add check_docs.py`
**Patch File:** `patch/DOC-001-opencode-class-docs.patch`
**Branch / Worktree:** `task/DOC-001` at `../minicalc-DOC-001`

---

## 1. Executive Summary

DOC-001 adds `scripts/check_docs.py`, a standard-library-only (`ast`) checker that
mechanically enforces [D-11], and brings the package docstrings up to that standard:
every module documented, every class documented, every class-level attribute /
dataclass field / enum member / `self.x` binding named in an `Attributes:` section,
and `Args:` / `Returns:` / `Raises:` present where the code requires them.

The checker was run against the merged tree **before** any docstring edit. It found
**0 violations across 28 classes and 29 functions** — the previously merged CORE/FEAT
work had already satisfied the letter of [D-11]. So this task's docstring delta is
*quality*, not compliance: the attributes that only said *what* a field is now say
*why* it exists (for example `Token.pos` feeds error carets, `Environment.ans` records
only successful expressions and is cleared by `:clear`), and the three non-obvious
algorithms called out in the prompt now carry short inline comments (precedence
climbing, truncating division, the `**` short-circuit).

Nothing executable changed: after removing docstring statements, the AST of all 15
in-scope files is identical to `HEAD~1`; the 439 tests that existed before still pass,
and 18 new checker tests bring the suite to 457 passing.

---

## 2. Implementation Details

### 2.1 Changes Made

- `scripts/check_docs.py` (new, 411 lines): parses each target file with `ast` and
  reports `path:line: message` for every violated rule, then prints
  `N classes, M functions checked`. Exit 0 clean, 1 with violations, 2 for a bad
  path. Attribute discovery covers class-level annotations (dataclass fields,
  `ClassVar` constants), class-level assignments (enum members), and
  `self.<name> = ...` / `self.<name>: T = ...` inside `__init__`. Section detection
  is Google-style (`Attributes:`, `Args:`, `Returns:`, `Raises:`) and accepts both
  `name:` and `name (type):` entries. `return`/`raise` detection walks only the
  function's own scope, so a nested closure's `return` does not demand a `Returns:`
  section on its parent.
- `tests/test_check_docs.py` (new, 18 tests): `tmp_path` fixtures for a fully
  documented module plus one fixture per violation type (missing module docstring,
  missing class docstring, missing `Attributes:` section, undocumented attribute,
  undocumented enum member, missing function docstring, missing `Args:`, missing
  `Returns:`, missing `Raises:`), the two exemption cases (private helper, dunder),
  `__init__` being required, nested-scope isolation, syntax-error handling, CLI exit
  codes and the summary line, and a guard that the real package stays clean.
- `minicalc/tokens.py`: `Token.lexeme` now explains that the verbatim text is what
  parser errors echo; `Token.pos` explains that it is the source of both error
  positions and the caret column; `Token.value` explains that the lexer parses once
  so the evaluator never touches text.
- `minicalc/errors.py`: `SourcePos.line`/`col` now state that `col` is what
  `render()` uses to indent the caret, and `__str__`/`__reduce__` gained `Returns:`
  sections even though the checker exempts dunders.
- `minicalc/lexer.py`: `Lexer.source` explains the single forward scan with no
  backtracking; `Lexer.line_no` explains why a fresh lexer per script line still
  reports the right file line.
- `minicalc/parser.py`: `Parser.index` explains why one cursor suffices (LL(1), no
  token copying); `Parser._depth` ties the counter to `MAX_DEPTH` and the
  `RecursionError` conversion. Inline comments added in `_additive`, `_term`, and
  `_power` for precedence climbing and `**` associativity/precedence.
- `minicalc/evaluator.py`: inline comments on truncating `/` (why not Python's
  `//`), on floored `%` (why no sign fix-up), and on the `**` short-circuit before
  the power is computed.
- `minicalc/environment.py`: `variables` explains why `ans` is kept out of the
  mapping; `ans` now says exactly when it is set (recorded by
  `Interpreter.run_line` only for a successful expression, never an assignment,
  [D-15] item 1), when it is cleared (`clear()`, the `:clear` command), and that a
  failed statement never touches it (atomicity, [D-07]).
- `minicalc/repl.py`: all five attributes now carry the rationale — `PROMPT` as a
  class constant readable without construction, `input_fn`/`output_fn` injection as
  the reason the REPL is testable without a terminal ([D-14]), and `color` as a
  decision already made once by `__main__` through `display.use_color`.

Untouched: `minicalc/ast_nodes.py`, `builtins.py`, `display.py`, `interpreter.py`,
`limits.py`, `__init__.py`, `__main__.py`, and `main.py`. Their docstrings already
met the standard and already explained their attributes; changing them would have
been churn without a reader benefit.

### 2.2 Conformance to Specifications & Decisions

- [D-11] is the target standard and is now executable: module docstrings, class
  docstrings with `Attributes:`, and `Args:`/`Returns:`/`Raises:` as applicable.
- `Attributes:` wording follows the spec, not new invention: `ans` text matches
  [D-15] item 1 and spec section 6 ("most recent successful expression"); `%` and
  `/` comments match [D-06]; the `**` guard matches spec section 5.
- [D-02] is respected by the checker itself: `argparse`, `ast`, `re`, `sys`,
  `dataclasses`, `pathlib` only — no third-party import.
- No code, no test assertion, no CLI string, and no spec file was changed. The
  `git diff` below is comments and docstrings only, plus the two new files.

## 3. Verification & Test Evidence

### 3.1 Checker

```text
$ python scripts/check_docs.py
28 classes, 29 functions checked
$ echo $?
0
```

Also verified on Python 3.12 (`py -3.12 scripts/check_docs.py`) → same output, exit 0,
so the checker works on both interpreters available on this machine ([D-02] needs 3.10+).

### 3.2 Test Suite

Pre-existing suite only (new file ignored) — must be unchanged at 439, which is the
count recorded in [D-18]:

```text
$ python -m pytest -q --ignore=tests/test_check_docs.py
439 passed in 3.93s
```

Full suite including the 18 new checker tests:

```text
$ python -m pytest -q
........................................................................ [ 15%]
........................................................................ [ 31%]
........................................................................ [ 47%]
........................................................................ [ 63%]
........................................................................ [ 78%]
........................................................................ [ 94%]
.........................                                                [100%]
457 passed in 3.66s
```

### 3.3 No-behavior-change proof (AST equality)

One-off script (not committed), comparing `ast.dump(..., include_attributes=False)`
with module/class/function docstring statements removed, between `HEAD~1` and the
working tree:

```text
$ python ../../AppData/Local/Temp/opencode/ast_equal_check.py HEAD~1
main.py: identical
minicalc/__init__.py: identical
minicalc/__main__.py: identical
minicalc/ast_nodes.py: identical
minicalc/builtins.py: identical
minicalc/display.py: identical
minicalc/environment.py: identical
minicalc/errors.py: identical
minicalc/evaluator.py: identical
minicalc/interpreter.py: identical
minicalc/lexer.py: identical
minicalc/limits.py: identical
minicalc/parser.py: identical
minicalc/repl.py: identical
minicalc/tokens.py: identical

0 file(s) differ in executable AST after docstrings removed
```

Comments are not part of the AST, so this proves the diff is docstring/comment-only.

### 3.4 Sampled docstrings (quality review)

**`minicalc/environment.py` — `Environment`**

```text
Hold user variables and the current ``ans`` value.

This is the only mutable state in the interpreter, so every statement sees
exactly the bindings the previous statements left behind.

Attributes:
    variables: User-defined name-to-value bindings. ``ans`` is deliberately
        kept out of this mapping so ``:vars`` and :meth:`items` list only
        names the user created, and so ``ans`` can never be overwritten by
        an assignment.
    ans: Value of the last successful expression, or ``None`` while none has
        succeeded yet. :meth:`record_result` sets it, and only
        ``Interpreter.run_line`` calls that method, after the statement is
        known to have succeeded and to be an expression rather than an
        assignment ([D-15] item 1). :meth:`clear` (the ``:clear`` command)
        resets it to ``None``, and no failed statement ever changes it,
        which is what keeps statements atomic ([D-07]).
```

**`minicalc/lexer.py` — `Lexer`**

```text
Turn one source line into tokens.

Attributes:
    source: The single source line, without its newline. Held rather than
        passed around so ``tokenize`` scans it once, left to right, with no
        backtracking and no copy of the text.
    line_no: 1-based line number stamped on every ``SourcePos``. A script
        runs each line through a fresh lexer, so this is what makes an
        error report the line inside the file rather than always 1.
```

**`minicalc/repl.py` — `Repl`**

```text
Read, evaluate, print, and loop until ``:quit``, EOF, or Ctrl-C.

Attributes:
    PROMPT (ClassVar[str]): The input prompt, ``"minicalc> "``. A class
        constant rather than an instance field so tests and callers can read
        the exact prompt without constructing a REPL.
    interpreter: The facade used for every non-meta-command line; the REPL
        never reaches into the lexer, parser, or evaluator directly.
    input_fn: Callable taking the prompt and returning one line; it defaults
        to the built-in ``input``. Injection is what lets the CLI tests drive
        a whole session from a list of strings ([D-14]).
    output_fn: Callable receiving one string per output line; it defaults to
        the built-in ``print``, so tests capture output without a terminal.
    color: Whether error rendering and display styling use ANSI codes. The
        decision is made once, by ``__main__`` through
        ``display.use_color``, so piped output is plain text here.
```

### 3.5 Checker self-tests cover every rule

Each rule has its own fixture; the negative fixtures fail with exactly one message
naming the missing section, so a checker that silently stopped enforcing a rule would
fail these tests:

```text
tests/test_check_docs.py::test_passing_module_has_no_violations PASSED
tests/test_check_docs.py::test_missing_module_docstring PASSED
tests/test_check_docs.py::test_missing_class_docstring PASSED
tests/test_check_docs.py::test_class_attributes_without_attributes_section PASSED
tests/test_check_docs.py::test_undocumented_attribute_is_reported PASSED
tests/test_check_docs.py::test_enum_members_count_as_attributes PASSED
tests/test_check_docs.py::test_typed_attribute_form_is_accepted PASSED
tests/test_check_docs.py::test_public_function_without_docstring PASSED
tests/test_check_docs.py::test_missing_args_section PASSED
tests/test_check_docs.py::test_missing_returns_section PASSED
tests/test_check_docs.py::test_missing_raises_section PASSED
tests/test_check_docs.py::test_private_helpers_and_dunders_are_exempt PASSED
tests/test_check_docs.py::test_init_requires_docstring_and_args PASSED
tests/test_check_docs.py::test_nested_function_return_does_not_leak PASSED
tests/test_check_docs.py::test_syntax_error_is_reported_not_raised PASSED
tests/test_check_docs.py::test_cli_reports_summary_and_exit_codes PASSED
tests/test_check_docs.py::test_cli_missing_path_is_a_usage_error PASSED
tests/test_check_docs.py::test_repository_package_is_clean PASSED
```

## 4. Decisions Recorded

None. No decision ID was reserved for DOC-001, and no settled decision was
re-litigated. The three judgement calls the prompt did not cover are listed in
section 6 instead of being written into the decision log.

## 5. Unified Git Diff

Produced with `git diff HEAD~1` in the worktree, byte-identical to
`patch/DOC-001-opencode-class-docs.patch`. It is the payload diff (the 9 code and
test files); the report, the `docs/tasks/status.md` row, and the patch file itself
are governance artifacts added to the same commit, exactly as in the FIX-001 and
FIX-002 handoffs.

```diff
diff --git a/minicalc/environment.py b/minicalc/environment.py
index 6180a53..3863473 100644
--- a/minicalc/environment.py
+++ b/minicalc/environment.py
@@ -13,10 +13,21 @@ from .errors import SourcePos, UndefinedNameError
 class Environment:
     """Hold user variables and the current ``ans`` value.
 
+    This is the only mutable state in the interpreter, so every statement sees
+    exactly the bindings the previous statements left behind.
+
     Attributes:
-        variables: User-defined name-to-value bindings.
-        ans: Value of the last successful expression, or ``None`` before the
-            first success.
+        variables: User-defined name-to-value bindings. ``ans`` is deliberately
+            kept out of this mapping so ``:vars`` and :meth:`items` list only
+            names the user created, and so ``ans`` can never be overwritten by
+            an assignment.
+        ans: Value of the last successful expression, or ``None`` while none has
+            succeeded yet. :meth:`record_result` sets it, and only
+            ``Interpreter.run_line`` calls that method, after the statement is
+            known to have succeeded and to be an expression rather than an
+            assignment ([D-15] item 1). :meth:`clear` (the ``:clear`` command)
+            resets it to ``None``, and no failed statement ever changes it,
+            which is what keeps statements atomic ([D-07]).
     """
 
     def __init__(self) -> None:
diff --git a/minicalc/errors.py b/minicalc/errors.py
index c2eacca..9b75bc8 100644
--- a/minicalc/errors.py
+++ b/minicalc/errors.py
@@ -22,8 +22,10 @@ class SourcePos:
     """A 1-based position in the original source text.
 
     Attributes:
-        line: 1-based line number.
-        col: 1-based column number; tabs count as one column.
+        line: 1-based line number, so script-mode errors can name the file line.
+        col: 1-based column number; tabs count as one column. ``render()``
+            indents the caret by ``col - 1``, so this field decides where the
+            caret lands under the offending character.
     """
 
     line: int
@@ -66,11 +68,21 @@ class MiniCalcError(Exception):
         self.source_line = source_line
 
     def __str__(self) -> str:
-        """Return the bare message, matching ``err.message``."""
+        """Return the bare message, matching ``err.message``.
+
+        Returns:
+            The message without the ``Error:`` heading or caret block that
+            :meth:`render` adds, so ``str(err)`` stays usable in logs.
+        """
         return self.message
 
     def __reduce__(self) -> tuple[object, tuple[object, ...]]:
-        """Preserve the full error state across ``pickle`` round-trips."""
+        """Preserve the full error state across ``pickle`` round-trips.
+
+        Returns:
+            The reconstructor pair Python's ``pickle`` protocol expects, so a
+            restored error still knows its position and source line.
+        """
         return (type(self), (self.message, self.pos, self.source_line))
 
     def with_source(self, source_line: str) -> "MiniCalcError":
diff --git a/minicalc/evaluator.py b/minicalc/evaluator.py
index a8ee9bf..d780171 100644
--- a/minicalc/evaluator.py
+++ b/minicalc/evaluator.py
@@ -119,6 +119,9 @@ class Evaluator:
         if op == "/":
             if right == 0:
                 raise DivisionByZeroError("division by zero", node.pos)
+            # Truncate toward zero, as the spec requires: Python's // floors, so
+            # divide the magnitudes and restore the sign explicitly. This keeps
+            # -7 / 2 at -3 while // below gives the floor, -4 ([D-06]).
             quotient = abs(left) // abs(right)
             if (left < 0) != (right < 0):
                 quotient = -quotient
@@ -130,6 +133,9 @@ class Evaluator:
         if op == "%":
             if right == 0:
                 raise DivisionByZeroError("division by zero", node.pos)
+            # Python's % is already floored and takes the divisor's sign, which
+            # is exactly the pairing the spec promises with // ([D-06]), so no
+            # sign fix-up is needed here.
             return self._checked(left % right, node.pos)
         if op == "**":
             return self._power(left, right, node.pos)
@@ -175,6 +181,9 @@ class Evaluator:
         if base == -1:
             return self._checked(1 if exponent % 2 == 0 else -1, pos)
         if exponent > 31:
+            # Short-circuit before computing: |base| >= 2 and exponent > 31 is
+            # always out of 32-bit range, and `2 ** 1000000000` must fail
+            # instantly rather than allocate a billion-digit integer (spec s.5).
             raise IntegerRangeError("integer result out of 32-bit range", pos)
         return self._checked(base**exponent, pos)
 
diff --git a/minicalc/lexer.py b/minicalc/lexer.py
index cf787ab..4ee49cd 100644
--- a/minicalc/lexer.py
+++ b/minicalc/lexer.py
@@ -93,8 +93,12 @@ class Lexer:
     """Turn one source line into tokens.
 
     Attributes:
-        source: The single source line, without its newline.
-        line_no: 1-based line number stamped on every ``SourcePos``.
+        source: The single source line, without its newline. Held rather than
+            passed around so ``tokenize`` scans it once, left to right, with no
+            backtracking and no copy of the text.
+        line_no: 1-based line number stamped on every ``SourcePos``. A script
+            runs each line through a fresh lexer, so this is what makes an
+            error report the line inside the file rather than always 1.
     """
 
     def __init__(self, source: str, line_no: int = 1) -> None:
diff --git a/minicalc/parser.py b/minicalc/parser.py
index e71a8e1..2ca3d91 100644
--- a/minicalc/parser.py
+++ b/minicalc/parser.py
@@ -65,9 +65,15 @@ class Parser:
     unary operators, and the right-associative ``**``.
 
     Attributes:
-        tokens: The token list to consume; the last token is ``EOF``.
-        index: Zero-based index of the next token to consume.
-        _depth: Number of ``_expression`` calls currently on the stack.
+        tokens: The token list to consume; the last token is ``EOF``. Holding
+            the list (rather than re-lexing) is what lets every node carry the
+            exact position of the token that produced it.
+        index: Zero-based index of the next token to consume. One cursor is
+            enough because the grammar is LL(1): every decision needs at most
+            the next token, so no token list is ever copied.
+        _depth: Number of ``_expression`` calls currently on the stack, compared
+            against ``MAX_DEPTH`` so pathological nesting becomes a
+            ``ParseError`` instead of an escaping ``RecursionError``.
     """
 
     def __init__(self, tokens: list[Token]) -> None:
@@ -221,6 +227,9 @@ class Parser:
 
     def _additive(self) -> Node:
         """Parse ``additive = term { ( PLUS | MINUS ) term }`` left-associatively."""
+        # Precedence climbing: each level loops over its own operators and calls
+        # the next-tighter level for operands. Looping (rather than recursing per
+        # operator) keeps `1 + 1 + ...` chains at constant stack depth.
         node = self._term()
         while self._peek().type in _ADDITIVE_OPS:
             operator = self._advance()
@@ -230,6 +239,8 @@ class Parser:
 
     def _term(self) -> Node:
         """Parse ``term = unary { ( STAR | SLASH | DSLASH | PERCENT ) unary }``."""
+        # Same shape as _additive, one precedence level tighter, which is what
+        # makes `2 + 3 * 4` mean `2 + (3 * 4)`.
         node = self._unary()
         while self._peek().type in _TERM_OPS:
             operator = self._advance()
@@ -252,6 +263,10 @@ class Parser:
         token = self._peek()
         if token.type is TokenType.POW:
             self._advance()
+            # The right side is _unary(), not _power(): that is what makes `**`
+            # right-associative (`2 ** 3 ** 2` == `2 ** (3 ** 2)`), and because
+            # `**` is reached from _unary only after a primary, it binds tighter
+            # than unary minus (`-2 ** 2` == `-(2 ** 2)`, spec section 3).
             exponent = self._unary()
             return Binary("**", base, exponent, token.pos)
         return base
diff --git a/minicalc/repl.py b/minicalc/repl.py
index f488a12..85449cd 100644
--- a/minicalc/repl.py
+++ b/minicalc/repl.py
@@ -33,13 +33,19 @@ class Repl:
     """Read, evaluate, print, and loop until ``:quit``, EOF, or Ctrl-C.
 
     Attributes:
-        PROMPT (ClassVar[str]): The input prompt, ``"minicalc> "``.
-        interpreter: The facade used for every non-meta-command line.
-        input_fn: Callable taking the prompt and returning one line; its
-            defaults match the built-in ``input``.
-        output_fn: Callable receiving one string per output line; its defaults
-            match the built-in ``print``.
-        color: Whether error rendering and display styling use ANSI codes.
+        PROMPT (ClassVar[str]): The input prompt, ``"minicalc> "``. A class
+            constant rather than an instance field so tests and callers can read
+            the exact prompt without constructing a REPL.
+        interpreter: The facade used for every non-meta-command line; the REPL
+            never reaches into the lexer, parser, or evaluator directly.
+        input_fn: Callable taking the prompt and returning one line; it defaults
+            to the built-in ``input``. Injection is what lets the CLI tests drive
+            a whole session from a list of strings ([D-14]).
+        output_fn: Callable receiving one string per output line; it defaults to
+            the built-in ``print``, so tests capture output without a terminal.
+        color: Whether error rendering and display styling use ANSI codes. The
+            decision is made once, by ``__main__`` through
+            ``display.use_color``, so piped output is plain text here.
     """
 
     PROMPT: ClassVar[str] = "minicalc> "
diff --git a/minicalc/tokens.py b/minicalc/tokens.py
index 3fcf88a..5de35ad 100644
--- a/minicalc/tokens.py
+++ b/minicalc/tokens.py
@@ -65,10 +65,15 @@ class Token:
     """One lexical token and its position in the source line.
 
     Attributes:
-        type: The token kind.
-        lexeme: Exact source text of the token (``""`` for ``EOF``).
-        pos: 1-based line and column where the token starts.
+        type: The token kind; the parser switches on this, never on text.
+        lexeme: Exact source text of the token (``""`` for ``EOF``). It is kept
+            verbatim so parser errors can echo the offending punctuation (for
+            example ``expected ')', found '*'``) instead of re-slicing source.
+        pos: 1-based line and column where the token starts. Error positions
+            and the caret line under a bad token both come from this field, so
+            a wrong ``pos`` shows up as a caret pointing at the wrong column.
         value: Parsed integer for ``NUMBER`` tokens; ``None`` for all others.
+            The lexer parses once, so the evaluator never touches text.
     """
 
     type: TokenType
diff --git a/scripts/check_docs.py b/scripts/check_docs.py
new file mode 100644
index 0000000..a716de1
--- /dev/null
+++ b/scripts/check_docs.py
@@ -0,0 +1,509 @@
+#!/usr/bin/env python3
+"""check_docs.py — enforce the [D-11] documentation standard.
+
+Scans every ``*.py`` under ``minicalc/`` plus ``main.py`` and reports the
+docstring rules the rubric's top Documentation band depends on:
+
+* every module has a docstring;
+* every class has a docstring, and a class that declares any attribute (a
+  class-level annotation or assignment, which covers dataclass fields and enum
+  members, or ``self.<name> = ...`` inside ``__init__``) also has an
+  ``Attributes:`` section that names every one of those attributes;
+* every public function and method (``__init__`` included) has a docstring,
+  with ``Args:`` when it takes parameters other than ``self``/``cls``,
+  ``Returns:`` when it returns a value, and ``Raises:`` when it raises.
+
+The checker is static: it parses with :mod:`ast` and never imports the target
+modules, so it runs on untrusted or half-written code and needs no third-party
+package ([D-02]).
+
+Usage::
+
+    python scripts/check_docs.py                 # whole package + main.py
+    python scripts/check_docs.py minicalc/lexer.py
+
+Exit codes: 0 when every rule holds, 1 when at least one violation is found,
+2 for a usage error.
+
+Design notes:
+    Names beginning with an underscore are private by convention and are not
+    required to document their steps; the prompt's rule is "public functions
+    and methods (no leading underscore, plus ``__init__``)".  Dunder methods
+    such as ``__str__`` therefore stay exempt, which keeps the checker aligned
+    with the written standard rather than with a stricter invented one.
+"""
+
+from __future__ import annotations
+
+import argparse
+import ast
+import re
+import sys
+from dataclasses import dataclass
+from pathlib import Path
+
+#: Attribute and section headers the checker understands in a Google-style
+#: docstring. Only the four required ones are validated; the rest merely stop
+#: an ``Attributes:`` body early, so a following ``Example:`` is not mistaken
+#: for a documented attribute.
+_SECTION_HEADERS = (
+    "Args:",
+    "Returns:",
+    "Raises:",
+    "Attributes:",
+    "Yields:",
+    "Example:",
+    "Examples:",
+    "Note:",
+    "Notes:",
+    "Todo:",
+)
+
+#: One documented entry, for example ``pos: ...`` or ``kind (ClassVar[str]):``.
+_ENTRY_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*:")
+
+#: Node types whose bodies belong to a different scope, so a ``return`` or
+#: ``raise`` inside them is not attributed to the enclosing function.
+_NESTED_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
+
+
+@dataclass(frozen=True)
+class Violation:
+    """One documentation rule violation.
+
+    Attributes:
+        path: File the violation was found in, relative to the repo root.
+        line: 1-based line of the offending definition.
+        message: Human-readable description of what is missing.
+    """
+
+    path: str
+    line: int
+    message: str
+
+    def format(self) -> str:
+        """Return the ``path:line: message`` form used by the CLI.
+
+        Returns:
+            The violation rendered on one line.
+        """
+        return f"{self.path}:{self.line}: {self.message}"
+
+
+@dataclass
+class Counts:
+    """How many definitions the checker inspected.
+
+    Attributes:
+        classes: Number of classes visited.
+        functions: Number of public functions and methods visited.
+    """
+
+    classes: int = 0
+    functions: int = 0
+
+
+def _own_nodes(body: list[ast.stmt]) -> list[ast.AST]:
+    """Collect the nodes evaluated in one function's own scope.
+
+    Nested ``def``/``class``/``lambda`` bodies are excluded because their
+    ``return`` and ``raise`` statements do not make the enclosing function a
+    returning or raising one.
+
+    Args:
+        body: Statement list to walk.
+
+    Returns:
+        Every node of the function body, excluding nested scopes.
+    """
+    collected: list[ast.AST] = []
+    stack: list[ast.AST] = list(body)
+    while stack:
+        node = stack.pop()
+        collected.append(node)
+        if isinstance(node, _NESTED_SCOPES):
+            continue
+        stack.extend(ast.iter_child_nodes(node))
+    return collected
+
+
+def _section(docstring: str, header: str) -> str | None:
+    """Return the body of one Google-style section.
+
+    Args:
+        docstring: The cleaned docstring to search.
+        header: Section header including the colon, for example ``"Args:"``.
+
+    Returns:
+        The text after the header up to the next section header, or ``None``
+        when the section is absent.
+    """
+    lines = docstring.splitlines()
+    for index, line in enumerate(lines):
+        if line.strip() == header:
+            body: list[str] = []
+            for follow in lines[index + 1 :]:
+                if follow.strip() in _SECTION_HEADERS:
+                    break
+                body.append(follow)
+            return "\n".join(body)
+    return None
+
+
+def _documented_names(section_text: str | None) -> set[str]:
+    """Extract the entry names documented in one section.
+
+    Args:
+        section_text: Section body, or ``None`` when the section is absent.
+
+    Returns:
+        Every name that starts a line in ``name:`` or ``name (type):`` form.
+    """
+    if not section_text:
+        return set()
+    names = set()
+    for line in section_text.splitlines():
+        match = _ENTRY_RE.match(line)
+        if match:
+            names.add(match.group(1))
+    return names
+
+
+def _class_attributes(node: ast.ClassDef) -> list[str]:
+    """List the attributes a class declares.
+
+    Covers class-level annotations (dataclass fields and ``ClassVar``
+    constants), class-level assignments (enum members), annotated or plain
+    ``self.<name> = ...`` bindings in ``__init__``, and documented instance
+    attributes introduced only by annotation.
+
+    Args:
+        node: The class definition to inspect.
+
+    Returns:
+        Attribute names in declaration order, without duplicates.
+    """
+    names: list[str] = []
+
+    def add(name: str) -> None:
+        if name not in names:
+            names.append(name)
+
+    for statement in node.body:
+        if isinstance(statement, ast.AnnAssign) and isinstance(
+            statement.target, ast.Name
+        ):
+            add(statement.target.id)
+        elif isinstance(statement, ast.Assign):
+            for target in statement.targets:
+                if isinstance(target, ast.Name):
+                    add(target.id)
+        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
+            if statement.name != "__init__":
+                continue
+            for inner in _own_nodes(statement.body):
+                if isinstance(inner, (ast.Assign, ast.AnnAssign)):
+                    targets = (
+                        inner.targets
+                        if isinstance(inner, ast.Assign)
+                        else [inner.target]
+                    )
+                    for target in targets:
+                        if (
+                            isinstance(target, ast.Attribute)
+                            and isinstance(target.value, ast.Name)
+                            and target.value.id == "self"
+                        ):
+                            add(target.attr)
+    return names
+
+
+def _parameter_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
+    """List a function's parameters, excluding ``self`` and ``cls``.
+
+    Args:
+        node: The function definition to inspect.
+
+    Returns:
+        Parameter names, including ``*args``/``**kwargs`` and keyword-only
+        parameters, in declaration order.
+    """
+    arguments = node.args
+    names = [
+        argument.arg
+        for argument in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
+        if argument.arg not in ("self", "cls")
+    ]
+    if arguments.vararg is not None:
+        names.append(arguments.vararg.arg)
+    if arguments.kwarg is not None:
+        names.append(arguments.kwarg.arg)
+    return names
+
+
+def _returns_value(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
+    """Report whether a function returns a value of its own.
+
+    Args:
+        node: The function definition to inspect.
+
+    Returns:
+        True when its own body (nested scopes excluded) has a ``return`` with
+        a value.
+    """
+    return any(
+        isinstance(inner, ast.Return) and inner.value is not None
+        for inner in _own_nodes(node.body)
+    )
+
+
+def _raises(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
+    """Report whether a function raises of its own.
+
+    Args:
+        node: The function definition to inspect.
+
+    Returns:
+        True when its own body (nested scopes excluded) has a ``raise``.
+    """
+    return any(isinstance(inner, ast.Raise) for inner in _own_nodes(node.body))
+
+
+def _check_class(node: ast.ClassDef, path: str, counts: Counts) -> list[Violation]:
+    """Check one class definition and its methods.
+
+    Args:
+        node: The class definition.
+        path: Path used in violation messages.
+        counts: Running totals, updated in place.
+
+    Returns:
+        Every violation found in the class, its docstring, and its methods.
+    """
+    counts.classes += 1
+    violations: list[Violation] = []
+    docstring = ast.get_docstring(node)
+    line = node.lineno
+
+    if docstring is None:
+        violations.append(Violation(path, line, f"class '{node.name}' has no docstring"))
+    else:
+        attributes = _class_attributes(node)
+        section = _section(docstring, "Attributes:")
+        if attributes and section is None:
+            violations.append(
+                Violation(
+                    path,
+                    line,
+                    f"class '{node.name}' has no 'Attributes:' section "
+                    f"documenting {_names(attributes)}",
+                )
+            )
+        elif attributes:
+            documented = _documented_names(section)
+            missing = [name for name in attributes if name not in documented]
+            if missing:
+                violations.append(
+                    Violation(
+                        path,
+                        line,
+                        f"class '{node.name}' does not document attribute(s) "
+                        f"{_names(missing)} in its 'Attributes:' section",
+                    )
+                )
+
+    for statement in node.body:
+        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
+            violations.extend(_check_function(statement, path, counts))
+    return violations
+
+
+def _check_function(
+    node: ast.FunctionDef | ast.AsyncFunctionDef, path: str, counts: Counts
+) -> list[Violation]:
+    """Check one module-level function or method.
+
+    Args:
+        node: The function definition.
+        path: Path used in violation messages.
+        counts: Running totals, updated in place.
+
+    Returns:
+        Every violation found for the function.
+    """
+    if node.name != "__init__" and node.name.startswith("_"):
+        return []  # private helper: not required to document its steps
+
+    counts.functions += 1
+    violations: list[Violation] = []
+    docstring = ast.get_docstring(node)
+    line = node.lineno
+    label = f"function '{node.name}'"
+
+    if docstring is None:
+        violations.append(Violation(path, line, f"{label} has no docstring"))
+        return violations
+
+    if _parameter_names(node) and _section(docstring, "Args:") is None:
+        violations.append(
+            Violation(path, line, f"{label} takes parameters but has no 'Args:' section")
+        )
+    if _returns_value(node) and _section(docstring, "Returns:") is None:
+        violations.append(
+            Violation(path, line, f"{label} returns a value but has no 'Returns:' section")
+        )
+    if _raises(node) and _section(docstring, "Raises:") is None:
+        violations.append(
+            Violation(path, line, f"{label} raises but has no 'Raises:' section")
+        )
+    return violations
+
+
+def _names(names: list[str]) -> str:
+    """Render attribute names for a violation message.
+
+    Args:
+        names: Attribute names to render.
+
+    Returns:
+        The names wrapped in backticks, separated by commas.
+    """
+    return ", ".join(f"`{name}`" for name in names)
+
+
+def check_file(path: Path, display_path: str, counts: Counts) -> list[Violation]:
+    """Check one Python file against the documentation standard.
+
+    Args:
+        path: File to read and parse.
+        display_path: Path used in violation messages.
+        counts: Running totals, updated in place.
+
+    Returns:
+        Every violation found in the file, in source order.
+    """
+    try:
+        source = path.read_text(encoding="utf-8")
+    except (OSError, UnicodeError) as exc:
+        return [Violation(display_path, 1, f"cannot read file: {exc}")]
+    try:
+        module = ast.parse(source, filename=display_path)
+    except SyntaxError as exc:
+        return [
+            Violation(display_path, exc.lineno or 1, f"cannot parse file: {exc.msg}")
+        ]
+
+    violations: list[Violation] = []
+    if ast.get_docstring(module) is None:
+        violations.append(Violation(display_path, 1, "module has no docstring"))
+
+    for statement in module.body:
+        if isinstance(statement, ast.ClassDef):
+            violations.extend(_check_class(statement, display_path, counts))
+        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
+            violations.extend(_check_function(statement, display_path, counts))
+    return violations
+
+
+def default_targets(repo_root: Path) -> list[Path]:
+    """List the files the checker inspects by default.
+
+    Args:
+        repo_root: Repository root holding ``minicalc/`` and ``main.py``.
+
+    Returns:
+        Every ``*.py`` under ``minicalc/`` plus ``main.py``, sorted, restricted
+        to files that exist.
+    """
+    targets = sorted((repo_root / "minicalc").rglob("*.py"))
+    main = repo_root / "main.py"
+    if main.exists():
+        targets.append(main)
+    return targets
+
+
+def _display_path(path: Path, repo_root: Path) -> str:
+    """Render a path relative to the repository root with forward slashes.
+
+    Args:
+        path: File to render.
+        repo_root: Repository root used as the base.
+
+    Returns:
+        The relative path, or the absolute path when it is outside the root.
+    """
+    try:
+        return path.resolve().relative_to(repo_root.resolve()).as_posix()
+    except ValueError:
+        return path.as_posix()
+
+
+def run(targets: list[Path], repo_root: Path) -> tuple[list[Violation], Counts]:
+    """Check every target file.
+
+    Args:
+        targets: Files to check.
+        repo_root: Base used to shorten paths in messages.
+
+    Returns:
+        The violations in path/line order and the definition counts.
+    """
+    counts = Counts()
+    violations: list[Violation] = []
+    for target in targets:
+        violations.extend(check_file(target, _display_path(target, repo_root), counts))
+    violations.sort(key=lambda violation: (violation.path, violation.line))
+    return violations, counts
+
+
+def main(argv: list[str] | None = None) -> int:
+    """Run the checker as a command-line tool.
+
+    Args:
+        argv: Arguments to parse; ``None`` means ``sys.argv[1:]``.
+
+    Returns:
+        0 when the standard holds, 1 when violations were found, 2 for a
+        usage error.
+    """
+    repo_root_default = Path(__file__).resolve().parent.parent
+    parser = argparse.ArgumentParser(
+        prog="check_docs",
+        description="Check MiniCalc docstrings against the [D-11] standard.",
+    )
+    parser.add_argument(
+        "paths",
+        nargs="*",
+        help="files or directories to check (default: minicalc/ and main.py)",
+    )
+    parser.add_argument(
+        "--repo-root",
+        default=str(repo_root_default),
+        help="repository root used to shorten reported paths",
+    )
+    args = parser.parse_args(argv)
+
+    repo_root = Path(args.repo_root).resolve()
+    if args.paths:
+        targets: list[Path] = []
+        for raw in args.paths:
+            candidate = Path(raw)
+            if candidate.is_dir():
+                targets.extend(sorted(candidate.rglob("*.py")))
+            elif candidate.exists():
+                targets.append(candidate)
+            else:
+                print(f"check_docs: no such file or directory: {raw}", file=sys.stderr)
+                return 2
+    else:
+        targets = default_targets(repo_root)
+
+    violations, counts = run(targets, repo_root)
+    for violation in violations:
+        print(violation.format())
+    print(f"{counts.classes} classes, {counts.functions} functions checked")
+    return 1 if violations else 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/tests/test_check_docs.py b/tests/test_check_docs.py
new file mode 100644
index 0000000..3dbd5f5
--- /dev/null
+++ b/tests/test_check_docs.py
@@ -0,0 +1,345 @@
+"""Tests for ``scripts/check_docs.py`` (DOC-001).
+
+Each test writes a small module into ``tmp_path`` and checks one rule from the
+[D-11] documentation standard, so a regression in the checker fails here
+instead of silently passing a submission that the rubric would mark down.
+"""
+
+from __future__ import annotations
+
+import importlib.util
+import sys
+from pathlib import Path
+from types import ModuleType
+
+import pytest
+
+REPO_ROOT = Path(__file__).resolve().parent.parent
+CHECKER_PATH = REPO_ROOT / "scripts" / "check_docs.py"
+
+#: A module that satisfies every rule: module docstring, a class with an
+#: ``Attributes:`` section covering dataclass fields and a ``self`` binding, and
+#: a public function with ``Args:``/``Returns:``/``Raises:``.
+PASSING_MODULE = '''"""A module that documents everything."""
+
+
+class Widget:
+    """A widget with one field and one stored attribute.
+
+    Attributes:
+        size: The widget's size in millimetres.
+        label (str): Human-readable name assigned in ``__init__``.
+    """
+
+    size: int
+
+    def __init__(self, label: str) -> None:
+        """Create the widget.
+
+        Args:
+            label: Human-readable name.
+        """
+        self.label = label
+
+
+def measure(value: int) -> int:
+    """Return the value unchanged.
+
+    Args:
+        value: Any integer.
+
+    Returns:
+        The same integer.
+
+    Raises:
+        ValueError: When ``value`` is negative.
+    """
+    if value < 0:
+        raise ValueError("negative")
+    return value
+'''
+
+
+def _load_checker() -> ModuleType:
+    """Import ``scripts/check_docs.py`` as a module.
+
+    Returns:
+        The imported checker module.
+    """
+    spec = importlib.util.spec_from_file_location("check_docs_under_test", CHECKER_PATH)
+    assert spec is not None and spec.loader is not None
+    module = importlib.util.module_from_spec(spec)
+    # Register before execution so dataclasses can resolve the module by name.
+    sys.modules[spec.name] = module
+    spec.loader.exec_module(module)
+    return module
+
+
+check_docs = _load_checker()
+
+
+def _check(tmp_path: Path, source: str) -> tuple[list[str], object]:
+    """Run the checker over one temporary module.
+
+    Args:
+        tmp_path: Pytest temporary directory.
+        source: Module source to write.
+
+    Returns:
+        The formatted violation messages and the definition counts.
+    """
+    path = tmp_path / "sample.py"
+    path.write_text(source, encoding="utf-8")
+    violations, counts = check_docs.run([path], tmp_path)
+    return [violation.format() for violation in violations], counts
+
+
+def test_passing_module_has_no_violations(tmp_path: Path) -> None:
+    """A fully documented module reports nothing and still counts definitions."""
+    messages, counts = _check(tmp_path, PASSING_MODULE)
+    assert messages == []
+    assert counts.classes == 1
+    assert counts.functions == 2
+
+
+def test_missing_module_docstring(tmp_path: Path) -> None:
+    """The first rule: every module has a docstring."""
+    messages, _ = _check(tmp_path, "x = 1\n")
+    assert messages == ["sample.py:1: module has no docstring"]
+
+
+def test_missing_class_docstring(tmp_path: Path) -> None:
+    """A class without a docstring is a violation at the class line."""
+    messages, _ = _check(tmp_path, '"""Mod."""\n\n\nclass A:\n    pass\n')
+    assert messages == ["sample.py:4: class 'A' has no docstring"]
+
+
+def test_class_attributes_without_attributes_section(tmp_path: Path) -> None:
+    """A dataclass field requires an ``Attributes:`` section."""
+    source = '"""Mod."""\n\n\nclass A:\n    """Just a class."""\n\n    size: int\n'
+    messages, _ = _check(tmp_path, source)
+    assert messages == [
+        "sample.py:4: class 'A' has no 'Attributes:' section documenting `size`"
+    ]
+
+
+def test_undocumented_attribute_is_reported(tmp_path: Path) -> None:
+    """Every attribute must be named, not just some of them."""
+    source = (
+        '"""Mod."""\n'
+        "\n"
+        "\n"
+        "class A:\n"
+        '    """A class.\n'
+        "\n"
+        "    Attributes:\n"
+        "        size: Documented.\n"
+        '    """\n'
+        "\n"
+        "    size: int\n"
+        "\n"
+        "    def __init__(self) -> None:\n"
+        '        """Create it."""\n'
+        "        self.secret = 1\n"
+    )
+    messages, _ = _check(tmp_path, source)
+    assert messages == [
+        "sample.py:4: class 'A' does not document attribute(s) `secret` "
+        "in its 'Attributes:' section"
+    ]
+
+
+def test_enum_members_count_as_attributes(tmp_path: Path) -> None:
+    """Enum members are class-level assignments and must be documented."""
+    source = (
+        '"""Mod."""\n'
+        "\n"
+        "from enum import Enum\n"
+        "\n"
+        "\n"
+        "class Kind(Enum):\n"
+        '    """Kinds.\n'
+        "\n"
+        "    Attributes:\n"
+        "        A: The first kind.\n"
+        '    """\n'
+        "\n"
+        '    A = "A"\n'
+        '    B = "B"\n'
+    )
+    messages, _ = _check(tmp_path, source)
+    assert messages == [
+        "sample.py:6: class 'Kind' does not document attribute(s) `B` "
+        "in its 'Attributes:' section"
+    ]
+
+
+def test_typed_attribute_form_is_accepted(tmp_path: Path) -> None:
+    """``name (type):`` entries satisfy the rule as well as ``name:``."""
+    source = (
+        '"""Mod."""\n'
+        "\n"
+        "\n"
+        "class A:\n"
+        '    """A class.\n'
+        "\n"
+        "    Attributes:\n"
+        "        flag (ClassVar[bool]): A documented constant.\n"
+        '    """\n'
+        "\n"
+        "    flag: bool = True\n"
+    )
+    messages, _ = _check(tmp_path, source)
+    assert messages == []
+
+
+def test_public_function_without_docstring(tmp_path: Path) -> None:
+    """Public functions need a docstring."""
+    messages, _ = _check(tmp_path, '"""Mod."""\n\n\ndef f() -> None:\n    pass\n')
+    assert messages == ["sample.py:4: function 'f' has no docstring"]
+
+
+def test_missing_args_section(tmp_path: Path) -> None:
+    """Parameters other than ``self`` require an ``Args:`` section."""
+    source = (
+        '"""Mod."""\n'
+        "\n"
+        "\n"
+        "class A:\n"
+        '    """A class."""\n'
+        "\n"
+        "    def run(self, times: int) -> None:\n"
+        '        """Run it."""\n'
+    )
+    messages, _ = _check(tmp_path, source)
+    assert messages == [
+        "sample.py:7: function 'run' takes parameters but has no 'Args:' section"
+    ]
+
+
+def test_missing_returns_section(tmp_path: Path) -> None:
+    """A ``return`` with a value requires a ``Returns:`` section."""
+    source = (
+        '"""Mod."""\n'
+        "\n"
+        "\n"
+        "def f() -> int:\n"
+        '    """Return one."""\n'
+        "    return 1\n"
+    )
+    messages, _ = _check(tmp_path, source)
+    assert messages == [
+        "sample.py:4: function 'f' returns a value but has no 'Returns:' section"
+    ]
+
+
+def test_missing_raises_section(tmp_path: Path) -> None:
+    """A ``raise`` requires a ``Raises:`` section."""
+    source = (
+        '"""Mod."""\n'
+        "\n"
+        "\n"
+        "def f() -> None:\n"
+        '    """Fail."""\n'
+        '    raise ValueError("bad")\n'
+    )
+    messages, _ = _check(tmp_path, source)
+    assert messages == [
+        "sample.py:4: function 'f' raises but has no 'Raises:' section"
+    ]
+
+
+def test_private_helpers_and_dunders_are_exempt(tmp_path: Path) -> None:
+    """Only public names and ``__init__`` are required to be documented."""
+    source = (
+        '"""Mod."""\n'
+        "\n"
+        "\n"
+        "class A:\n"
+        '    """A class."""\n'
+        "\n"
+        "    def __str__(self) -> str:\n"
+        '        return "a"\n'
+        "\n"
+        "    def _helper(self, value: int) -> int:\n"
+        "        return value\n"
+    )
+    messages, counts = _check(tmp_path, source)
+    assert messages == []
+    assert counts.functions == 0
+
+
+def test_init_requires_docstring_and_args(tmp_path: Path) -> None:
+    """``__init__`` is public for this rule even though it is a dunder."""
+    source = (
+        '"""Mod."""\n'
+        "\n"
+        "\n"
+        "class A:\n"
+        '    """A class.\n'
+        "\n"
+        "    Attributes:\n"
+        "        size: The stored size.\n"
+        '    """\n'
+        "\n"
+        "    def __init__(self, size: int) -> None:\n"
+        "        self.size = size\n"
+    )
+    messages, _ = _check(tmp_path, source)
+    assert messages == ["sample.py:11: function '__init__' has no docstring"]
+
+
+def test_nested_function_return_does_not_leak(tmp_path: Path) -> None:
+    """A nested ``return`` does not make the outer function a returning one."""
+    source = (
+        '"""Mod."""\n'
+        "\n"
+        "\n"
+        "def outer() -> None:\n"
+        '    """Do nothing visible."""\n'
+        "\n"
+        "    def inner() -> int:\n"
+        "        return 1\n"
+    )
+    messages, _ = _check(tmp_path, source)
+    assert messages == []
+
+
+def test_syntax_error_is_reported_not_raised(tmp_path: Path) -> None:
+    """An unparsable file becomes a violation instead of a crash."""
+    messages, _ = _check(tmp_path, '"""Mod."""\n\ndef broken(:\n')
+    assert len(messages) == 1
+    assert messages[0].startswith("sample.py:3: cannot parse file:")
+
+
+def test_cli_reports_summary_and_exit_codes(
+    tmp_path: Path, capsys: pytest.CaptureFixture[str]
+) -> None:
+    """The CLI prints ``N classes, M functions checked`` and sets the exit code."""
+    clean = tmp_path / "clean.py"
+    clean.write_text(PASSING_MODULE, encoding="utf-8")
+    assert check_docs.main([str(clean)]) == 0
+    assert "1 classes, 2 functions checked" in capsys.readouterr().out
+
+    broken = tmp_path / "broken.py"
+    broken.write_text("x = 1\n", encoding="utf-8")
+    assert check_docs.main([str(broken)]) == 1
+    output = capsys.readouterr().out
+    assert "module has no docstring" in output
+    assert "0 classes, 0 functions checked" in output
+
+
+def test_cli_missing_path_is_a_usage_error(
+    tmp_path: Path, capsys: pytest.CaptureFixture[str]
+) -> None:
+    """A path that does not exist exits 2 with a message on stderr."""
+    assert check_docs.main([str(tmp_path / "absent.py")]) == 2
+    assert "no such file or directory" in capsys.readouterr().err
+
+
+def test_repository_package_is_clean() -> None:
+    """The real ``minicalc`` package satisfies the standard it is checked against."""
+    violations, counts = check_docs.run(check_docs.default_targets(REPO_ROOT), REPO_ROOT)
+    assert [violation.format() for violation in violations] == []
+    assert counts.classes > 0
+    assert counts.functions > 0
```

## 6. Flagged for APC / Operator Attention

- [ ] **The package was already compliant.** The checker's first run over the merged
      tree reported zero violations (28 classes, 29 functions), so "fix every
      violation" had no compliance fixes to make. The docstring diff is deliberately
      a quality pass on the thin entries plus the three requested comments. If the APC
      expected a large mechanical rewrite, there was nothing left for it to rewrite —
      the evidence is the checker run and the existing `Attributes:` sections.
- [ ] **Prompt's decision range is stale.** The prompt cites "[D-01] through [D-16]";
      `docs/decisions/decision-log.md` actually contains [D-01]–[D-15], [D-17], [D-18],
      with [D-16] reserved for DOC-003. I read the live log. No action needed, but the
      prompt text should be corrected for the next agent.
- [ ] **Checker scope choices not fixed by the prompt** (all conservative, none
      recorded as a decision because no ID is reserved):
      1. Dunder methods other than `__init__` are exempt, per "no leading underscore".
         `__str__` and `__reduce__` were nevertheless given `Returns:` sections.
      2. Functions nested inside functions are not checked; they are treated as
         private implementation detail, and their `return`/`raise` do not leak into
         the enclosing function's requirements.
      3. Module-level constants (`limits.INT_MIN`, `limits.INT_MAX`,
         `limits.MAX_LINE_LENGTH`, `parser.MAX_DEPTH`, `ast_nodes.Op`) are not class
         attributes, so [D-11]'s attribute rule does not apply; they already carry
         `#:` comments. If the APC wants them checked too, that is a follow-up rule,
         not a violation today.
- [ ] **Test environment caveat.** No `pytest` was installed in any interpreter on
      this machine (system `python` 3.11.3, `py -3.12`, and the PyCharm venv all
      raised `ModuleNotFoundError: No module named 'pytest'`), and the 3.14.8 / pytest
      9.1.1 environment quoted in earlier status rows is not present. I installed
      pytest 9.2.0 into a throwaway venv **outside the repository**
      (`%TEMP%\opencode\venv-doc001`) and ran the suite with it. Nothing was added to
      the repo or to the system Python. The 439-test baseline matches [D-18], so the
      counts are comparable.
- [ ] **Python version coverage.** The suite was executed on CPython 3.11.3 (the venv
      interpreter). `scripts/check_docs.py` was additionally verified on 3.12. A 3.10
      run, which [D-02] allows, was not possible on this machine; the checker uses
      only syntax 3.10 supports (`from __future__ import annotations`, `X | Y` in
      annotations, `tuple[...]`).
