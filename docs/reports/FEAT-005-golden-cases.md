# Task Report: FEAT-005 — Spec-derived golden test cases (independent audit)

**Date:** 2026-10-26  
**Agent:** claude-code  
**Task ID:** FEAT-005  
**Status:** needs-review  
**Commit:** single amended task commit on `task/FEAT-005` (parent `353b400`; exact HEAD hash reported to APC)  
**Patch File:** `patch/FEAT-005-golden-cases.patch`

---

## 1. Executive Summary

This task is an independent, specification-derived golden-test audit. I did not read
`minicalc/lexer.py`, `minicalc/parser.py`, `minicalc/evaluator.py`, or
`minicalc/builtins.py`, and I did not run the interpreter to produce any expected
output. All 262 expected result lines (174 `OK` values and 88 `ERR` class/position
lines) were written by hand from `docs/context/language-spec.md` and then
cross-checked twice with scratch Python tools outside the repository: a
spec-derived oracle covering every line, and a direct Python-arithmetic/state
simulation covering every `OK` value.

The 12 new case families cover every lexical-error and parse-error table row, every
worked example, every precedence/associativity row, all operator and range rules,
all four built-ins and their error rules, `ans`/variable/atomicity behavior, and
comment/whitespace line numbering. The one requested APC addition—a failed
assignment leaves the variable unchanged—is covered explicitly in
`tests/golden/variables.mc:26-28` and `:34-35`.

During review, APC resolved the `ans` ambiguity: `ans` is updated only by successful
**expression** statements; a successful assignment binds its variable but does not
change `ans`. This matches the spec section 1 example (`2 + 3 * 4` leaves `ans=14`,
then `x = 7`, then `ans * x` gives `98`) and contract section 12 `basic.out`. Every
case was re-audited under this ruling; only two expectations changed
(`variables.mc:10` and `:12`, both `21` -> `20`). No other file reads `ans` after an
assignment.

Current results are exactly the expected pre-integration state: the golden harness
reports **11 failed, 2 passed** (`smoke`, `lex_errors`), and the full suite reports
**11 failed, 78 passed, 0 skipped**. No existing test regressed. The 11 failures are
all non-smoke golden files whose statements the CORE-003 walking skeleton cannot
yet parse or evaluate; INT-001/FEAT-001..003 are expected to resolve them. No
spec-vs-implementation disagreement could be assessed while those stages are stubs;
the cases are frozen and should not be changed to match implementation behavior.

---

## 2. Implementation Details

### 2.1 Changes Made

- `tests/golden/arithmetic.{mc,out}`: `+ - *`, whitespace/tab variants, zero,
  negatives, parentheses, `INT_MIN`, large in-range operands (23 statements).
- `tests/golden/precedence.{mc,out}`: precedence levels 2-6, left/right
  associativity, unary chains, comparisons vs arithmetic (23 statements).
- `tests/golden/division.{mc,out}`: full `/`, `//`, `%` sign matrix, zero divisor
  for each operator, `INT_MIN / -1`, `INT_MIN // -1`, identity check, `INT_MIN % -1`
  (26 statements).
- `tests/golden/power.{mc,out}`: every `**` rule, `0 ** 0`, `1 ** n`,
  `(-1) ** n` parity, `(-2) ** 31`, `(-2) ** 32`, `2 ** 1000000000`,
  negative exponents (25 statements).
- `tests/golden/comparison.{mc,out}`: all six operators on equal/less/greater and
  negative operands, three chaining-error shapes, parenthesized chains
  (27 statements).
- `tests/golden/variables.{mc,out}`: assignment/reuse/reassignment, unset `ans`,
  `ans` after successful expressions (assignments do not change it), reserved
  targets, undefined names, case sensitivity,
  underscore names, and atomic-failure checks (failed RHS, parse failure, lex
  failure, failed new-variable assignment) (37 statements).
- `tests/golden/builtins.{mc,out}`: `abs/min/max/gcd` normal and edge cases, nested
  calls, unknown function, calling a variable, built-in as a value, every arity
  error shape, arity-before-arguments, leftmost failing argument, `abs(INT_MIN)`,
  and range failure inside an argument (36 statements).
- `tests/golden/range.{mc,out}`: `INT_MAX + 1`, `INT_MIN - 1`, `46341 * 46341`,
  `-INT_MIN`, in-range boundaries, out-of-range literal, and overflow that "comes
  back" at the first operator (13 statements).
- `tests/golden/lex_errors.{mc,out}`: every lexical-error row plus `.5`, a second
  out-of-range literal, `!` alone, two visible non-ASCII characters, and a
  1001-character line (14 statements).
- `tests/golden/parse_errors.{mc,out}`: every parse-error row plus `x = y = 3`,
  `a + 1 = 2`, `max(1 2)`, `()`, `2 **`, `x =`, double `)`, `min(1,)`, and an
  unclosed parenthesized expression (18 statements).
- `tests/golden/comments_whitespace.{mc,out}`: blank lines, comment-only lines,
  trailing/inline `#`, spaces-only and tab-only lines, and a later error whose
  reported line proves file numbering (6 statements).
- `tests/golden/demo.{mc,out}`: a 14-statement presentation session with variables,
  `ans`, built-ins, comparisons, and one runtime, one parse, and one lexical error
  (14 statements).

### 2.2 Conformance to Specifications & Decisions

- Output format follows interface-contract section 12 exactly: one canonical line
  per non-empty, non-comment statement, `OK <value>`, `OK <name>=<value>`, or
  `ERR <ClassName> <line>:<col>`; error message text is never compared.
- `[D-07]`: positioned errors and atomic statements; the cases assert class and
  `line:col` only, and failures are followed by reads of `ans`/variables.
- `[D-08]`: `ans` and the four built-in names are reserved; cases cover assignment
  to each, and built-ins used as values.
- `[D-10]`: independent golden layer; expected values were not generated by the
  implementation under test.
- APC ruling (post-review): `ans` is updated only by successful expression
  statements; assignments bind their variable but do not change `ans`. Re-derived
  against spec section 1 and contract section 12 `basic.out`.
- Independence: no implementation modules were opened; expected values were
  hand-derived and independently recomputed (section 3.2).

### 2.3 Coverage Matrix

Every row below names at least one source line; `file:line` is the file line in the
`.mc` (comments and blanks included, matching the `ERR` line numbering).

**A. Lexical errors (spec section 2)**

| Spec row | Case | `file:line` |
| :--- | :--- | :--- |
| `3.14`, `3.` report the `.` | `3.14`, `3.` | `lex_errors.mc:2`, `:3` |
| `.5` decimals unsupported | `.5` | `lex_errors.mc:4` |
| `12abc` reports start of number | `12abc` | `lex_errors.mc:5` |
| literal > 2147483647 reports start | `99999999999`, `12345678901234567890` | `lex_errors.mc:6`, `:7` |
| illegal char `@`, `$`, `:` | `2 @ 3`, `$x`, `:` | `lex_errors.mc:8`, `:9`, `:10` |
| `!` not followed by `=` | `3 ! 4`, `!` | `lex_errors.mc:11`, `:12` |
| line > 1000 chars reports column 1001 | 1001-char line | `lex_errors.mc:15` |
| non-ASCII character is illegal | `2 × 3`, `2 “ 3` | `lex_errors.mc:13`, `:14` |

**B. Parse errors (spec section 3)**

| Spec row | `file:line` |
| :--- | :--- |
| `2 +` expected expression at EOF | `parse_errors.mc:2` |
| `2 + * 3` at `*` | `parse_errors.mc:3` |
| `(2 + 3` missing `)` at EOF | `parse_errors.mc:4` |
| `2 3` unexpected token | `parse_errors.mc:5` |
| `1 < 2 < 3` at second `<` | `parse_errors.mc:6` |
| `max(1,` expected expression at EOF | `parse_errors.mc:7` |
| `)` expected expression | `parse_errors.mc:8` |
| `= 5` expected expression | `parse_errors.mc:9` |
| `5 = 3` left side must be a name | `parse_errors.mc:10` |
| extras: `x = y = 3`, `a + 1 = 2`, `max(1 2)` | `parse_errors.mc:11-13` |
| extras: `()`, `2 **`, `x =` | `parse_errors.mc:14-16` |
| extras: `(2 + 3))`, `min(1,)`, `2 * (3 + 4` | `parse_errors.mc:17-19` |

**C. Worked examples (spec section 5 table)**

| Example | Result | `file:line` |
| :--- | :--- | :--- |
| `2 + 3 * 4` | 14 | `arithmetic.mc:6` |
| `(2 + 3) * 4` | 20 | `arithmetic.mc:7` |
| `10 - 3 - 2` | 5 | `arithmetic.mc:9` |
| `-2 ** 2` | -4 | `precedence.mc:13` |
| `2 ** 3 ** 2` | 512 | `precedence.mc:12` |
| `2 ** 30` | 1073741824 | `power.mc:11` |
| `7 / 2` | 3 | `division.mc:2` |
| `-7 / 2` | -3 | `division.mc:3` |
| `7 // 2` | 3 | `division.mc:6` |
| `-7 // 2` | -4 | `division.mc:7` |
| `-7 % 2` | 1 | `division.mc:11` |
| `7 % -2` | -1 | `division.mc:12` |
| `-7 % -2` | -1 | `division.mc:13` |
| `5 > 3` | 1 | `comparison.mc:19` |
| `5 == 4` | 0 | `comparison.mc:20` |
| `2 + 3 == 5` | 1 | `comparison.mc:21` |
| `-2147483647 - 1` | INT_MIN | `arithmetic.mc:20`, `range.mc:5` |

**D. Precedence and associativity table (spec section 3)**

| Level | Covered by |
| :--- | :--- |
| 1 `( )`, calls | `arithmetic.mc:7`, `builtins.mc:18-19` |
| 2 `**` right | `precedence.mc:12` |
| 3 unary `-`/`+` right (prefix) | `precedence.mc:16-19` |
| 4 `* / // %` left | `precedence.mc:8-11` |
| 5 `+ -` left | `precedence.mc:9` (`arithmetic.mc:9`) |
| 6 comparisons non-associative | `comparison.mc:22`, `:24`, `:26` |

**E. Operator semantics and integer model (spec sections 4-5)**

| Rule | `file:line` |
| :--- | :--- |
| `+ - *` and range | `arithmetic.mc:2-24`; `range.mc:2-14` |
| `/` truncates toward zero | `division.mc:2-5`, `:17-18` |
| `//` floors | `division.mc:6-9`, `:19-20` |
| `%` floored, sign of `b`, identity | `division.mc:10-13`, `:21` |
| zero divisor for `/ // %` | `division.mc:22-24` |
| `INT_MIN / -1`, `INT_MIN // -1` | `division.mc:25-26` |
| `**` with `b >= 0`; `b < 0` DomainError | `power.mc:2`, `:17-19` |
| `x ** 0 == 1` including `0 ** 0` | `power.mc:3-4` |
| `0 ** n == 0`; `1 ** n == 1` | `power.mc:5-7` |
| `(-1) ** n` by parity | `power.mc:8-10` |
| `|x| >= 2` and `b > 31` fails immediately | `power.mc:14`, `:16` |
| `(-2) ** 31` valid; `(-2) ** 32` range | `power.mc:13`, `:15` |
| unary `-`, `+`; `-INT_MIN` range | `precedence.mc:16-19`, `range.mc:8` |
| all six comparisons yield 1/0 | `comparison.mc:2-21`, `:23-28` |
| every intermediate result checked | `range.mc:3`, `:10` (overflow "comes back") |
| `INT_MIN` written as `-2147483647 - 1` | `range.mc:5` |
| literal 2147483648 rejected | `range.mc:9`, `lex_errors.mc:6` |

**F. Built-ins (spec section 6)**

| Rule | `file:line` |
| :--- | :--- |
| `abs(x)`, including `abs(INT_MIN)` range | `builtins.mc:2-5` |
| `min` 1+ args | `builtins.mc:6`, `:8`, `:10`, `:22` |
| `max` 1+ args | `builtins.mc:7`, `:9`, `:21` |
| `gcd(a,b)`, `gcd(0,0)==0`, result >= 0 | `builtins.mc:11-17` |
| nested calls | `builtins.mc:18-19` |
| unknown function `foo(1)` | `builtins.mc:25` |
| calling a variable `x(1)` | `builtins.mc:24` |
| wrong arity (`abs()`, `abs(1,2)`, `gcd(1)`, `gcd(1,2,3)`, `min()`) | `builtins.mc:28-32` |
| built-in used as a value | `builtins.mc:26-27` |
| arity checked before arguments | `builtins.mc:35` |
| arguments left to right; leftmost failure wins | `builtins.mc:33-34` |
| range error inside an argument | `builtins.mc:37` |

**G. Names, variables, `ans` (spec section 6)**

| Rule | `file:line` |
| :--- | :--- |
| assignment, reuse, reassignment | `variables.mc:3-8`, `:25` |
| `ans` unset before first success | `variables.mc:2` |
| `ans` after successful expressions; assignment does not change it | `variables.mc:5`, `:8`, `:10`, `:12`, `:28`, `:33`, `:38` (proof at `:9-10`) |
| `ans` is read-only | `variables.mc:24` |
| assignment to every built-in name | `variables.mc:20-23` |
| undefined variable | `variables.mc:11`, `:35` |
| atomic failure leaves variable and `ans` unchanged | `variables.mc:26-28`, `:29-30`, `:31-33`, `:34-35` |
| case sensitivity `X` vs `x` | `variables.mc:13-16` |
| underscore names | `variables.mc:17-19`, `:36-37` |

**H. Error classes (spec section 7)**

| Class | `file:line` |
| :--- | :--- |
| `LexError` | `lex_errors.mc:2-15`; `variables.mc:31`; `range.mc:9`; `demo.mc:13` |
| `ParseError` | `parse_errors.mc:2-19`; `variables.mc:29`; `comparison.mc:22,24,26`; `demo.mc:12` |
| `DivisionByZeroError` | `division.mc:22-24`; `variables.mc:26,34`; `builtins.mc:33,34,36`; `demo.mc:10` |
| `IntegerRangeError` | `range.mc:3,4,6,8,10,11,14`; `power.mc:14-16,23,25`; `builtins.mc:5,37` |
| `DomainError` | `power.mc:17-19`; `precedence.mc:15` |
| `UndefinedNameError` | `variables.mc:2,11,35`; `builtins.mc:26,27` |
| `CallError` | `builtins.mc:24,25,28-32,35` |
| `AssignmentError` | `variables.mc:20-24` |

**I. Comments, whitespace, line numbering (spec section 2)**

| Rule | `file:line` |
| :--- | :--- |
| blank lines produce nothing | `comments_whitespace.mc:3`, `:14` |
| comment-only lines produce nothing | `comments_whitespace.mc:2`, `:9`, `:15` |
| trailing/inline `#` comment | `comments_whitespace.mc:5-6` |
| spaces-only line | `comments_whitespace.mc:4` |
| tab-only line | `comments_whitespace.mc:10` |
| later error keeps real file line number | `comments_whitespace.mc:12` |
| spaces/tabs separate tokens | `arithmetic.mc:4-5` |

### 2.4 Independent Calculation Evidence

Two scratch tools, both outside the repository and neither importing `minicalc`,
were run after the expected files were written and frozen.

1. `/tmp/feat005_oracle.py` — an independent lexer/parser/evaluator derived only
   from the spec. It reproduced **all 262** expected lines exactly:

```text
OK arithmetic.mc (23 lines)
OK precedence.mc (23 lines)
OK division.mc (26 lines)
OK power.mc (25 lines)
OK comparison.mc (27 lines)
OK variables.mc (37 lines)
OK builtins.mc (36 lines)
OK range.mc (13 lines)
OK lex_errors.mc (14 lines)
OK parse_errors.mc (18 lines)
OK comments_whitespace.mc (6 lines)
OK demo.mc (14 lines)
```

2. `/tmp/feat005_numbers.py` — direct Python arithmetic (AST rewrite makes `/`
   truncate immediately; Python's `//`, `%`, `**`, unary and comparisons match the
   spec) with independent `ans`/variable state tracking. It reproduced all **174
   `OK` values**:

```text
arithmetic.mc: 23 OK values reproduced by direct Python eval
precedence.mc: 22 OK values reproduced by direct Python eval
division.mc: 21 OK values reproduced by direct Python eval
power.mc: 17 OK values reproduced by direct Python eval
comparison.mc: 24 OK values reproduced by direct Python eval
variables.mc: 25 OK values reproduced by direct Python eval
builtins.mc: 21 OK values reproduced by direct Python eval
range.mc: 5 OK values reproduced by direct Python eval
lex_errors.mc: 0 OK values reproduced by direct Python eval
parse_errors.mc: 0 OK values reproduced by direct Python eval
comments_whitespace.mc: 5 OK values reproduced by direct Python eval
demo.mc: 11 OK values reproduced by direct Python eval
TOTAL OK values: 174
```

Boundary calculations explicitly checked: `2**30 = 1073741824`;
`(-2)**31 = -2147483648` (INT_MIN) while `2**31 = 2147483648 > INT_MAX`;
`3**19 = 1162261467` while `3**20 = 3486784401 > INT_MAX`;
`46340**2 = 2147395600` while `46341**2 = 2147488281 > INT_MAX`;
`trunc(-7,2) = -3`, `trunc(7,-2) = -3`; `-7//2 = -4`, `-7%2 = 1`, `7%-2 = -1`;
`math.gcd(-12,18) = 6`, `math.gcd(0,0) = 0`; and `-2147483648 % -1 = 0`.

### 2.5 APC Ruling: `ans` and Assignments (RESOLVED)

Spec section 6 as originally written said `ans` "holds the value of the most recent
successful statement (expression or assignment)". That contradicts spec section 1
(`2 + 3 * 4` -> `ans=14`, then `x = 7`, then `ans * x` -> `98`) and contract
section 12's `basic.out` (`OK 14`, `OK x=7`, `OK 98`): both require the assignment
not to overwrite `ans`. APC resolved the ambiguity in favour of the examples:
**`ans` is updated only by successful expression statements; assignments bind their
variable but leave `ans` unchanged.**

Full re-audit under the ruling (every case that reads `ans`):

| Source line | Old | New | Reasoning |
| :--- | :--- | :--- | :--- |
| `variables.mc:9` `y = ans + 1` | `OK y=21` | `OK y=21` (unchanged) | `ans` is 20 from the expression on line 7; assignment result 21 does not change `ans`. |
| `variables.mc:10` `ans` | `OK 21` | **`OK 20`** | Should observe the expression-set `ans` from line 7; line 9's assignment did not update it. |
| `variables.mc:11` `z + 1` | `ERR UndefinedNameError` | unchanged | Failed statement; `ans` stays 20. |
| `variables.mc:12` `ans` | `OK 21` | **`OK 20`** | Still the line-7 expression value. |
| `variables.mc:28`, `:33`, `:38` | `OK 42`, `OK 42`, `OK 3` | unchanged | Each `ans` read follows a successful **expression** (lines 27, 32, 37), which does set `ans`. |
| `demo.mc:5` `ans + x` | `OK 30` | unchanged | `ans=23` comes from the expression on line 4; the assignments on lines 2-3 do not set it. 23 + x(7) = 30. |
| `demo.mc:14` `ans` | `OK 7` | unchanged | `ans=7` comes from the expression on line 11; lines 12-13 are errors. |

No other `.mc` file reads `ans` (`builtins.mc` contains `x = 5` but never reads
`ans`). The only changed expectations are therefore the `OK 21` results for
`variables.mc:10` and `:12`, now `OK 20`. Both scratch checkers were updated to the
ruling and reproduced all 262 lines and all 174 `OK` values again. This worktree was
not rebased, so its local `docs/context/language-spec.md` still carries the old
"(expression or assignment)" parenthetical; it is deliberately not edited here.

---

## 3. Verification & Test Evidence

### 3.1 Test Execution

Commands executed after the revised cases were frozen. The APC-ruling revision
changed only two `variables.out` expectations (for `variables.mc:10` and `:12`);
no expectation was adjusted to match implementation behavior.

```bash
python -m pytest tests/test_golden.py -q
python -m pytest -q
```

Golden harness output (tail):

```text
FFFFFF.FFFF.F                                                            [100%]
=========================== short test summary info ============================
FAILED tests/test_golden.py::test_golden_file[arithmetic] - Failed: Golden mi...
FAILED tests/test_golden.py::test_golden_file[builtins] - Failed: Golden mism...
FAILED tests/test_golden.py::test_golden_file[comments_whitespace] - Failed: ...
FAILED tests/test_golden.py::test_golden_file[comparison] - Failed: Golden mi...
FAILED tests/test_golden.py::test_golden_file[demo] - Failed: Golden mismatch...
FAILED tests/test_golden.py::test_golden_file[division] - Failed: Golden mism...
FAILED tests/test_golden.py::test_golden_file[parse_errors] - Failed: Golden ...
FAILED tests/test_golden.py::test_golden_file[power] - Failed: Golden mismatc...
FAILED tests/test_golden.py::test_golden_file[precedence] - Failed: Golden mi...
FAILED tests/test_golden.py::test_golden_file[range] - Failed: Golden mismatc...
FAILED tests/test_golden.py::test_golden_file[variables] - Failed: Golden mis...
11 failed, 2 passed in 1.50s
```

Full suite output (tail):

```text
..............................FFFFFF.FFFF.F............................. [ 80%]
.................                                                        [100%]
=========================== short test summary info ============================
FAILED tests/test_golden.py::test_golden_file[arithmetic] - Failed: Golden mi...
FAILED tests/test_golden.py::test_golden_file[builtins] - Failed: Golden mism...
FAILED tests/test_golden.py::test_golden_file[comments_whitespace] - Failed: ...
FAILED tests/test_golden.py::test_golden_file[comparison] - Failed: Golden mi...
FAILED tests/test_golden.py::test_golden_file[demo] - Failed: Golden mismatch...
FAILED tests/test_golden.py::test_golden_file[division] - Failed: Golden mism...
FAILED tests/test_golden.py::test_golden_file[parse_errors] - Failed: Golden ...
FAILED tests/test_golden.py::test_golden_file[power] - Failed: Golden mismatc...
FAILED tests/test_golden.py::test_golden_file[precedence] - Failed: Golden mi...
FAILED tests/test_golden.py::test_golden_file[range] - Failed: Golden mismatc...
FAILED tests/test_golden.py::test_golden_file[variables] - Failed: Golden mis...
11 failed, 78 passed in 0.98s
```

The two passing golden files are `smoke` and `lex_errors`. The failures are the
expected pre-FEAT-001/002/003 state; the harness itself ran without errors.

### 3.2 Failure Counts Per File

"Matched" lines are expected lines that happen to agree with the CORE-003 stub
today; they do not affect the frozen expectations.

| File | Statement lines | Mismatched | Matched | Notes |
| :--- | ---: | ---: | ---: | :--- |
| `arithmetic.mc` | 23 | 23 | 0 | stub lexes numbers only |
| `precedence.mc` | 23 | 23 | 0 | all `LexError` at stub |
| `division.mc` | 26 | 26 | 0 | all `LexError` at stub |
| `power.mc` | 25 | 25 | 0 | all `LexError` at stub |
| `comparison.mc` | 27 | 27 | 0 | all `LexError` at stub |
| `variables.mc` | 37 | 37 | 0 | all `LexError` at stub |
| `builtins.mc` | 36 | 36 | 0 | all `LexError` at stub |
| `range.mc` | 13 | 11 | 2 | `2147483647` and out-of-range literal pass |
| `lex_errors.mc` | 14 | 0 | 14 | passes |
| `parse_errors.mc` | 18 | 17 | 1 | `2 3` parse case passes |
| `comments_whitespace.mc` | 6 | 6 | 0 | all `LexError` at stub |
| `demo.mc` | 14 | 13 | 1 | `3.14` lexical case passes |

### 3.3 Edge Cases & Negative Testing

- Atomicity: failed assignment, failed parse, failed lex, and failed assignment to
  a previously undefined name are each followed by reads proving neither a variable
  nor `ans` changed (`variables.mc:26-35`).
- `INT_MIN` is never written as a literal: `-2147483647 - 1` is used, and
  `2147483648` is asserted to be a `LexError`.
- `INT_MIN / -1` and `INT_MIN // -1` assert range errors; `INT_MIN % -1` asserts
  `OK 0` (see ambiguity 3).
- `2 ** 1000000000` asserts immediate range failure (no hang).
- `abs(INT_MIN)` and a range error inside `max`'s second argument assert error
  position at the function name / `**` operator.
- Arity-before-arguments uses `abs(1 / 0, 2)`: `CallError`, not division-by-zero.
- Comparison chaining is asserted for `<`, `==`, and `< ==` shapes.
- The 1001-character line was constructed as `1 + 1` plus 996 trailing spaces, so
  it is non-blank and length-check-before-tokenization is unambiguous.

---

## 4. Decisions Recorded

None. No decision ID was reserved for FEAT-005; the two non-trivial choices are
recorded under "Flagged for APC / Operator Attention" instead.

---

## 5. Unified Git Diff

Verbatim `git diff HEAD~1 -- tests/golden` (the frozen case files; this is also the
content of `patch/FEAT-005-golden-cases.patch`):

```diff
diff --git c/tests/golden/arithmetic.mc w/tests/golden/arithmetic.mc
new file mode 100644
index 0000000..f68a276
--- /dev/null
+++ w/tests/golden/arithmetic.mc
@@ -0,0 +1,24 @@
+# Spec section 5: + - * on small/large operands, zero, negatives, parentheses, whitespace
+2 + 3
+2+3
+  2   +   3  
+	2	+	3
+2 + 3 * 4
+(2 + 3) * 4
+2 * (3 + 4)
+10 - 3 - 2
+2 - 5
+-3 + 1
+-2 * 3
+5 * 0
+0 + 0
+0 - 5
+0 * 2147483647
+2147483647 + 0
+2147483647 - 2147483647
+-2147483647 + 2147483647
+-2147483647 - 1
+((1))
+-(2 + 3)
+2 * 3 + 4 * 5
+100000 * 20000
diff --git c/tests/golden/arithmetic.out w/tests/golden/arithmetic.out
new file mode 100644
index 0000000..602823d
--- /dev/null
+++ w/tests/golden/arithmetic.out
@@ -0,0 +1,23 @@
+OK 5
+OK 5
+OK 5
+OK 5
+OK 14
+OK 20
+OK 14
+OK 5
+OK -3
+OK -2
+OK -6
+OK 0
+OK 0
+OK -5
+OK 0
+OK 2147483647
+OK 0
+OK 0
+OK -2147483648
+OK 1
+OK -5
+OK 26
+OK 2000000000
diff --git c/tests/golden/builtins.mc w/tests/golden/builtins.mc
new file mode 100644
index 0000000..a46e84a
--- /dev/null
+++ w/tests/golden/builtins.mc
@@ -0,0 +1,37 @@
+# Spec section 6: abs/min/max/gcd, arity, argument order, reserved names
+abs(5)
+abs(-5)
+abs(0)
+abs(-2147483647 - 1)
+min(3, 1, 2)
+max(3, 1, 2)
+min(5)
+max(-3, -7)
+min(0, -1)
+gcd(12, 18)
+gcd(0, 0)
+gcd(0, 5)
+gcd(-12, 18)
+gcd(12, -18)
+gcd(-12, -18)
+gcd(17, 5)
+max(min(3, 5), abs(-2))
+gcd(abs(-12), max(8, 6))
+abs(-3) + abs(3)
+max(2147483647, -1)
+min(2147483647, 0)
+x = 5
+x(1)
+foo(1)
+abs + 1
+gcd
+abs()
+abs(1, 2)
+gcd(1)
+gcd(1, 2, 3)
+min()
+max(1 / 0, 2 / 0)
+gcd(1 / 0, 2)
+abs(1 / 0, 2)
+min(1 / 0)
+max(abs(-1), 2 ** 31)
diff --git c/tests/golden/builtins.out w/tests/golden/builtins.out
new file mode 100644
index 0000000..bc6c57b
--- /dev/null
+++ w/tests/golden/builtins.out
@@ -0,0 +1,36 @@
+OK 5
+OK 5
+OK 0
+ERR IntegerRangeError 5:1
+OK 1
+OK 3
+OK 5
+OK -3
+OK -1
+OK 6
+OK 0
+OK 5
+OK 6
+OK 6
+OK 6
+OK 1
+OK 3
+OK 4
+OK 6
+OK 2147483647
+OK 0
+OK x=5
+ERR CallError 24:1
+ERR CallError 25:1
+ERR UndefinedNameError 26:1
+ERR UndefinedNameError 27:1
+ERR CallError 28:1
+ERR CallError 29:1
+ERR CallError 30:1
+ERR CallError 31:1
+ERR CallError 32:1
+ERR DivisionByZeroError 33:7
+ERR DivisionByZeroError 34:7
+ERR CallError 35:1
+ERR DivisionByZeroError 36:7
+ERR IntegerRangeError 37:16
diff --git c/tests/golden/comments_whitespace.mc w/tests/golden/comments_whitespace.mc
new file mode 100644
index 0000000..7048680
--- /dev/null
+++ w/tests/golden/comments_whitespace.mc
@@ -0,0 +1,15 @@
+# Spec section 2: blank lines, comments, whitespace-only lines, line numbering
+# comment-only line
+
+    
+2 + 3 # trailing comment
+2 + 3#no space before hash
+4 + 5
+   # indented comment
+#
+	
+7 * 6
+2 +
+10 - 3
+
+# final comment
diff --git c/tests/golden/comments_whitespace.out w/tests/golden/comments_whitespace.out
new file mode 100644
index 0000000..6b44912
--- /dev/null
+++ w/tests/golden/comments_whitespace.out
@@ -0,0 +1,6 @@
+OK 5
+OK 5
+OK 9
+OK 42
+ERR ParseError 12:4
+OK 7
diff --git c/tests/golden/comparison.mc w/tests/golden/comparison.mc
new file mode 100644
index 0000000..c120e60
--- /dev/null
+++ w/tests/golden/comparison.mc
@@ -0,0 +1,28 @@
+# Spec section 5: comparisons on equal/less/greater operands; non-associative
+3 == 3
+3 == 4
+3 != 4
+3 != 3
+3 < 4
+4 < 3
+3 < 3
+3 <= 3
+4 <= 3
+3 > 2
+2 > 3
+3 >= 3
+2 >= 3
+-1 < 0
+-5 > -3
+-2 == -2
+-2147483647 - 1 < 0
+5 > 3
+5 == 4
+2 + 3 == 5
+1 < 2 < 3
+(1 < 2) < 3
+1 == 1 == 1
+(1 == 1) == 1
+2 < 3 == 1
+-1 >= -1
+0 == 0
diff --git c/tests/golden/comparison.out w/tests/golden/comparison.out
new file mode 100644
index 0000000..39f5c53
--- /dev/null
+++ w/tests/golden/comparison.out
@@ -0,0 +1,27 @@
+OK 1
+OK 0
+OK 1
+OK 0
+OK 1
+OK 0
+OK 0
+OK 1
+OK 0
+OK 1
+OK 0
+OK 1
+OK 0
+OK 1
+OK 0
+OK 1
+OK 1
+OK 1
+OK 0
+OK 1
+ERR ParseError 22:7
+OK 1
+ERR ParseError 24:8
+OK 1
+ERR ParseError 26:7
+OK 1
+OK 1
diff --git c/tests/golden/demo.mc w/tests/golden/demo.mc
new file mode 100644
index 0000000..8700dab
--- /dev/null
+++ w/tests/golden/demo.mc
@@ -0,0 +1,15 @@
+# MiniCalc demo session: variables, ans, built-ins, comparisons, one error per family
+x = 7
+y = 3
+x * y + 2
+ans + x
+max(x, y) ** 2
+min(x, y) == y
+abs(-x)
+gcd(x, y)
+x = 1 / 0
+x
+2 +
+3.14
+ans
+max(abs(-10), 3)
diff --git c/tests/golden/demo.out w/tests/golden/demo.out
new file mode 100644
index 0000000..07ac7b0
--- /dev/null
+++ w/tests/golden/demo.out
@@ -0,0 +1,14 @@
+OK x=7
+OK y=3
+OK 23
+OK 30
+OK 49
+OK 1
+OK 7
+OK 1
+ERR DivisionByZeroError 10:7
+OK 7
+ERR ParseError 12:4
+ERR LexError 13:2
+OK 7
+OK 10
diff --git c/tests/golden/division.mc w/tests/golden/division.mc
new file mode 100644
index 0000000..3b135c5
--- /dev/null
+++ w/tests/golden/division.mc
@@ -0,0 +1,27 @@
+# Spec section 5: / truncates toward zero, // floors, % is floored modulo (all signs)
+7 / 2
+-7 / 2
+7 / -2
+-7 / -2
+7 // 2
+-7 // 2
+7 // -2
+-7 // -2
+7 % 2
+-7 % 2
+7 % -2
+-7 % -2
+0 / 5
+0 // 5
+0 % 5
+7 / 2 * 2
+-7 / 2 * 2
+7 // 2 * 2
+-7 // 2 * 2
+(-7 // 2) * 2 + (-7 % 2)
+1 / 0
+1 // 0
+1 % 0
+(-2147483647 - 1) / -1
+(-2147483647 - 1) // -1
+(-2147483647 - 1) % -1
diff --git c/tests/golden/division.out w/tests/golden/division.out
new file mode 100644
index 0000000..7b25441
--- /dev/null
+++ w/tests/golden/division.out
@@ -0,0 +1,26 @@
+OK 3
+OK -3
+OK -3
+OK 3
+OK 3
+OK -4
+OK -4
+OK 3
+OK 1
+OK 1
+OK -1
+OK -1
+OK 0
+OK 0
+OK 0
+OK 6
+OK -6
+OK 6
+OK -8
+OK -7
+ERR DivisionByZeroError 22:3
+ERR DivisionByZeroError 23:3
+ERR DivisionByZeroError 24:3
+ERR IntegerRangeError 25:19
+ERR IntegerRangeError 26:19
+OK 0
diff --git c/tests/golden/lex_errors.mc w/tests/golden/lex_errors.mc
new file mode 100644
index 0000000..9708b7b
--- /dev/null
+++ w/tests/golden/lex_errors.mc
@@ -0,0 +1,15 @@
+# Spec section 2: lexical errors (decimals, bad numbers, illegal chars, long line)
+3.14
+3.
+.5
+12abc
+99999999999
+12345678901234567890
+2 @ 3
+$x
+:
+3 ! 4
+!
+2 × 3
+2 “ 3
+1 + 1                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
diff --git c/tests/golden/lex_errors.out w/tests/golden/lex_errors.out
new file mode 100644
index 0000000..360b153
--- /dev/null
+++ w/tests/golden/lex_errors.out
@@ -0,0 +1,14 @@
+ERR LexError 2:2
+ERR LexError 3:2
+ERR LexError 4:1
+ERR LexError 5:1
+ERR LexError 6:1
+ERR LexError 7:1
+ERR LexError 8:3
+ERR LexError 9:1
+ERR LexError 10:1
+ERR LexError 11:3
+ERR LexError 12:1
+ERR LexError 13:3
+ERR LexError 14:3
+ERR LexError 15:1001
diff --git c/tests/golden/parse_errors.mc w/tests/golden/parse_errors.mc
new file mode 100644
index 0000000..057fdf4
--- /dev/null
+++ w/tests/golden/parse_errors.mc
@@ -0,0 +1,19 @@
+# Spec section 3: parse errors (all table rows plus common extras)
+2 +
+2 + * 3
+(2 + 3
+2 3
+1 < 2 < 3
+max(1,
+)
+= 5
+5 = 3
+x = y = 3
+a + 1 = 2
+max(1 2)
+()
+2 **
+x =
+(2 + 3))
+min(1,)
+2 * (3 + 4
diff --git c/tests/golden/parse_errors.out w/tests/golden/parse_errors.out
new file mode 100644
index 0000000..2db0760
--- /dev/null
+++ w/tests/golden/parse_errors.out
@@ -0,0 +1,18 @@
+ERR ParseError 2:4
+ERR ParseError 3:5
+ERR ParseError 4:7
+ERR ParseError 5:3
+ERR ParseError 6:7
+ERR ParseError 7:7
+ERR ParseError 8:1
+ERR ParseError 9:1
+ERR ParseError 10:3
+ERR ParseError 11:7
+ERR ParseError 12:7
+ERR ParseError 13:7
+ERR ParseError 14:2
+ERR ParseError 15:5
+ERR ParseError 16:4
+ERR ParseError 17:8
+ERR ParseError 18:7
+ERR ParseError 19:11
diff --git c/tests/golden/power.mc w/tests/golden/power.mc
new file mode 100644
index 0000000..432d800
--- /dev/null
+++ w/tests/golden/power.mc
@@ -0,0 +1,26 @@
+# Spec section 5: ** rules (zero, one, -1, overflow, negative exponent, short-circuit)
+2 ** 3
+2 ** 0
+0 ** 0
+0 ** 5
+0 ** 31
+1 ** 1000000
+(-1) ** 1000000
+(-1) ** 1000001
+(-1) ** 0
+2 ** 30
+(-2) ** 30
+(-2) ** 31
+2 ** 31
+(-2) ** 32
+2 ** 1000000000
+2 ** -1
+1 ** -1
+0 ** -1
+2 ** 3 ** 2
+-2 ** 2
+3 ** 19
+3 ** 20
+(-3) ** 19
+(-3) ** 20
+(-2) ** 0
diff --git c/tests/golden/power.out w/tests/golden/power.out
new file mode 100644
index 0000000..0638875
--- /dev/null
+++ w/tests/golden/power.out
@@ -0,0 +1,25 @@
+OK 8
+OK 1
+OK 1
+OK 0
+OK 0
+OK 1
+OK 1
+OK -1
+OK 1
+OK 1073741824
+OK 1073741824
+OK -2147483648
+ERR IntegerRangeError 14:3
+ERR IntegerRangeError 15:6
+ERR IntegerRangeError 16:3
+ERR DomainError 17:3
+ERR DomainError 18:3
+ERR DomainError 19:3
+OK 512
+OK -4
+OK 1162261467
+ERR IntegerRangeError 23:3
+OK -1162261467
+ERR IntegerRangeError 25:6
+OK 1
diff --git c/tests/golden/precedence.mc w/tests/golden/precedence.mc
new file mode 100644
index 0000000..d316e1a
--- /dev/null
+++ w/tests/golden/precedence.mc
@@ -0,0 +1,24 @@
+# Spec section 3: precedence levels 1-6 and associativity
+2 + 3 * 4
+2 * 3 + 4
+2 + 3 * 4 ** 2
+2 ** 3 * 2
+2 * 3 ** 2
+(2 + 3) * 4
+100 / 10 / 2
+10 - 3 - 2
+20 // 6 // 2
+100 % 30 % 7
+2 ** 3 ** 2
+-2 ** 2
+(-2) ** 2
+2 ** -1
+--5
+-+-5
++5
+---5
+2 ** 0 ** 5
+-2 ** 0
+2 + 3 == 5
+2 * 3 > 5
+2 + 3 < 4 * 2
diff --git c/tests/golden/precedence.out w/tests/golden/precedence.out
new file mode 100644
index 0000000..b917cae
--- /dev/null
+++ w/tests/golden/precedence.out
@@ -0,0 +1,23 @@
+OK 14
+OK 10
+OK 50
+OK 16
+OK 18
+OK 20
+OK 5
+OK 5
+OK 1
+OK 3
+OK 512
+OK -4
+OK 4
+ERR DomainError 15:3
+OK 5
+OK 5
+OK 5
+OK -5
+OK 1
+OK -1
+OK 1
+OK 1
+OK 1
diff --git c/tests/golden/range.mc w/tests/golden/range.mc
new file mode 100644
index 0000000..c235fe3
--- /dev/null
+++ w/tests/golden/range.mc
@@ -0,0 +1,14 @@
+# Spec sections 4-5: 32-bit boundaries and checked intermediate results
+2147483647
+2147483647 + 1
+(-2147483647 - 1) - 1
+-2147483647 - 1
+46341 * 46341
+46340 * 46340
+-(-2147483647 - 1)
+2147483648
+2147483647 + 1 - 1
+-2147483647 - 2
+2147483646 + 1
+-2147483647 - 1 + 1
+-46341 * 46341
diff --git c/tests/golden/range.out w/tests/golden/range.out
new file mode 100644
index 0000000..8b2b41f
--- /dev/null
+++ w/tests/golden/range.out
@@ -0,0 +1,13 @@
+OK 2147483647
+ERR IntegerRangeError 3:12
+ERR IntegerRangeError 4:19
+OK -2147483648
+ERR IntegerRangeError 6:7
+OK 2147395600
+ERR IntegerRangeError 8:1
+ERR LexError 9:1
+ERR IntegerRangeError 10:12
+ERR IntegerRangeError 11:13
+OK 2147483647
+OK -2147483647
+ERR IntegerRangeError 14:8
diff --git c/tests/golden/variables.mc w/tests/golden/variables.mc
new file mode 100644
index 0000000..f93a050
--- /dev/null
+++ w/tests/golden/variables.mc
@@ -0,0 +1,38 @@
+# Spec section 6: variables, ans, reserved names, atomic statements, case sensitivity
+ans
+x = 7
+x + 1
+ans
+x = 10
+x * 2
+ans
+y = ans + 1
+ans
+z + 1
+ans
+X = 1
+x = 2
+X
+x
+_a = 5
+_A = 6
+_a + _A
+abs = 1
+min = 1
+max = 1
+gcd = 1
+ans = 1
+x = 42
+x = 1 / 0
+x
+ans
+y = 2 +
+y
+x = 99999999999
+x
+ans
+new_var = 1 / 0
+new_var
+_ = 3
+_
+ans
diff --git c/tests/golden/variables.out w/tests/golden/variables.out
new file mode 100644
index 0000000..810f670
--- /dev/null
+++ w/tests/golden/variables.out
@@ -0,0 +1,37 @@
+ERR UndefinedNameError 2:1
+OK x=7
+OK 8
+OK 8
+OK x=10
+OK 20
+OK 20
+OK y=21
+OK 20
+ERR UndefinedNameError 11:1
+OK 20
+OK X=1
+OK x=2
+OK 1
+OK 2
+OK _a=5
+OK _A=6
+OK 11
+ERR AssignmentError 20:1
+ERR AssignmentError 21:1
+ERR AssignmentError 22:1
+ERR AssignmentError 23:1
+ERR AssignmentError 24:1
+OK x=42
+ERR DivisionByZeroError 26:7
+OK 42
+OK 42
+ERR ParseError 29:8
+OK 21
+ERR LexError 31:5
+OK 42
+OK 42
+ERR DivisionByZeroError 34:13
+ERR UndefinedNameError 35:1
+OK _=3
+OK 3
+OK 3
```

---

## 6. Flagged for APC / Operator Attention

- [x] **`ans` and assignments (RESOLVED by APC ruling).** `ans` is updated only by
      successful expressions; assignments bind but do not change `ans`. This
      resolves the contradiction between spec section 6 and the section 1 /
      contract `basic.out` examples. Re-audit changed exactly two expectations:
      `variables.mc:10` and `:12` now expect `OK 20` instead of `OK 21` (see
      section 2.5). No other case assumed assignment updated `ans`.
- [ ] **`.out` comments vs harness.** The FEAT-005 prompt says to put a `# ` comment
      above every group, but interface-contract section 12 and `tests/test_golden.py`
      compare the `.out` file literally line-for-line. A comment in `.out` would
      therefore always fail. I put group comments in the `.mc` files only and kept
      `.out` as canonical result lines only; recommend clarifying the prompt.
- [ ] **Negative exponent on 0/1.** Spec section 5's operator row says `b < 0` is a
      `DomainError`, but the `**` rules also say `1 ** n == 1` and `0 ** n == 0`
      without an exponent restriction. I chose `DomainError` for `1 ** -1` and
      `0 ** -1` (`power.mc:18-19`), matching the operator row. Confirm.
- [ ] **`INT_MIN % -1`.** The spec lists range errors only for `INT_MIN / -1` and
      `INT_MIN // -1`; `%` only lists divisor-zero. I chose `OK 0`
      (`division.mc:27`). The floor identity cannot be evaluated through
      `a // b` without overflowing, so an implementation that derives `%` from
      `//` would disagree. Confirm `OK 0` is intended.
- [ ] **Reserved-target error ordering.** The spec does not say whether
      `ans = <failing expression>` raises `AssignmentError` or the RHS error. No
      case depends on that ordering; recommend stating it.
- [ ] **`ans` "as the very first line".** `variables.mc` has its spec-section
      comment on line 1 and `ans` as the first *statement* on line 2. Comment lines
      produce no statement, so `ans` is still unset there; confirm this satisfies
      the intent.
- [ ] **No spec-vs-implementation disagreement can be assessed yet.** The current
      tree only has the CORE-003 walking skeleton, so non-smoke cases fail with
      `LexError`. Once FEAT-001/002/003 land, rerun the harness without editing
      these expectations; any mismatch at that point is an implementation or spec
      issue to record in `[D-15]`.
- [ ] **Coverage volume.** The prompt suggested about 150 statement lines; the
      frozen suite has 262 (174 `OK`, 88 `ERR`). This was intentional to cover
      every table row and all sign combinations.
