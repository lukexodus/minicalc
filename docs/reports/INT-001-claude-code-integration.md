# INT-001 — Integrate all tracks, full-suite green (Claude Code)

**Branch:** `task/INT-001` · **Worktree:** `/home/lukexodus/projects/minicalc-INT-001` · **Commit:** the single commit on `task/INT-001` (amended once to include this report)

## Executive Summary

All five Phase 2 tracks integrate without a code change. The merged tree produced **zero implementation-vs-spec failures**: every worked example and every error row in spec sections 2, 3, and 5 reproduces exactly, and all public signatures in `interface-contract.md` match through `inspect.signature`. The only work here was to pin the APC's Phase 2 rulings in [D-15] and in a new spec-derived golden file, then run the full verification battery. Result: **432 passed, 0 failed, 0 skipped** on Python 3.14.8 and 3.10.16.

The `ans` ruling and the six other Phase 2 rulings were applied to the spec by the operator (`44cd2c2`) before this task started; they are not part of this branch's diff.

## Implementation Details

- No change under `minicalc/`. Nothing needed fixing: the `ans` fix landed earlier as `7bff102`.
- **`tests/golden/rulings.mc` / `.out`** (new): one case per Phase 2 ruling. Expectations were written from the spec text and committed before the suite was run; the first run passed, which is the evidence that code and spec agree. Cases: `12é`; `INT_MIN % -1`; `1 ** -1`; `0 ** -1`; `gcd(INT_MIN, 0)`; `gcd(INT_MIN, INT_MIN)`; `ans = 1 / 0`; `abs = 1 / 0`; and `2 + 3 * 4` → `x = 7` → `ans * x` = `98`, which fails under the old `ans` rule.
- **`[D-15]`** replaced the reserved placeholder with nine numbered items: the seven APC rulings, the measured nesting boundary, the script-mode line-prefix reading, and a "no further discrepancies" entry. [D-08]'s `ans` wording is explicitly superseded.
- **`docs/tasks/status.md`**: INT-001 row only, set to `needs-review`.
- **`docs/context/repo-tree.txt`**: regenerated once, at the end, via `./scripts/apc-bundle.sh --list`.

## Verification & Test Evidence

### Full suite, zero skips (Python 3.14.8)

```
$ python -m pytest -q -rs
........................................................................ [ 50%]
........................................................................ [ 66%]
........................................................................ [ 83%]
........................................................................ [100%]
432 passed in 3.22s
```

No `-rs` skip lines. Golden suite collects all 14 `tests/golden/*.mc`, including `rulings`:

```
$ python -m pytest tests/test_golden.py --collect-only -q | grep golden_file | wc -l
14
```

### Oldest supported Python (3.10.16, `uv` venv)

```
$ /tmp/minicalc-v310/bin/python -m pytest -q -rs
432 passed in 1.77s
```

### Warnings as errors

```
$ python -W error -m pytest -q
432 passed in 1.98s
```

### Integration-marked tests unmarked against the real facade

```
$ python -m pytest -q -m integration
3 passed, 429 deselected in 1.93s
```

### Nesting boundary, measured

| Nesting | Result |
| --- | --- |
| 198 | OK |
| 199 | OK |
| 200 | `ERR ParseError 1:201` |
| 201 | `ERR ParseError 1:201` |

Matches `parser.MAX_DEPTH = 200`; the facade recursion fallback never fires first.

### Contract conformance (`inspect.signature`)

Every public name in `interface-contract.md` exists; missing: none. Signatures printed, all matching:

```
limits.in_range(value: int) -> bool
Lexer.__init__(self, source: 'str', line_no: 'int' = 1) -> 'None'
Lexer.tokenize(self) -> 'list[Token]'
Parser.__init__(self, tokens: 'list[Token]') -> 'None'
Parser.parse_statement(self) -> 'Node | None'
Environment.get(self, name: 'str', pos: 'SourcePos') -> 'int'
Environment.set(self, name: 'str', value: 'int') -> 'None'
Environment.record_result(self, value: 'int') -> 'None'
Environment.clear(self) -> 'None'
Environment.items(self) -> 'list[tuple[str, int]]'
Evaluator.__init__(self, env: 'Environment') -> 'None'
Evaluator.evaluate(self, node: 'Node') -> 'int'
Interpreter.__init__(self, env: 'Environment | None' = None) -> 'None'
Interpreter.run_line(self, source: 'str', line_no: 'int' = 1) -> 'Result'
Interpreter.run_source(self, text: 'str') -> 'list[LineOutcome]'
display.use_color(stream: 'TextIO') -> 'bool'
display.format_result(result: 'Result', color: 'bool' = False) -> 'str'
display.format_outcome(outcome: 'LineOutcome', color: 'bool' = False) -> 'str'
display.banner(color: 'bool' = False) -> 'str'
display.help_text(color: 'bool' = False) -> 'str'
Repl.__init__(self, interpreter, input_fn=input, output_fn=print, color: 'bool' = False) -> 'None'
Repl.run(self) -> 'int'
__main__.main(argv: 'list[str] | None' = None) -> 'int'
MiniCalcError.__init__(self, message: str, pos=..., source_line=...) -> None
MiniCalcError.with_source(self, source_line: str) -> 'MiniCalcError'
MiniCalcError.render(self, color: bool = False) -> str
MiniCalcError.canonical(self) -> str
is_reserved(name: 'str') -> 'bool'
values: -2147483648 2147483647 1000 | reserved: ['abs', 'gcd', 'max', 'min'] | Repl.PROMPT: 'minicalc> '
```

### Manual walkthrough — all three modes

Script mode, `tests/golden/demo.mc` (exit code 1, as the file contains errors):

```
$ python -m minicalc tests/golden/demo.mc
Error: Runtime error at line 10, column 7: division by zero
  x = 1 / 0
        ^
Error: Syntax error at line 12, column 4: expected an expression, found end of line
  2 +
     ^
Error: Lexical error at line 13, column 2: decimals are not supported; MiniCalc works with integers only
  3.14
   ^
line 2: x = 7
line 3: y = 3
line 4: = 23
line 5: = 30
line 6: = 49
line 7: = 1
line 8: = 7
line 9: = 1
line 11: = 7
line 14: = 7
line 15: = 10
exit=1
```

Script with an error continues after it and exits 1:

```
$ printf '2 +\n1 / 0\n3 + 3\n' > /tmp/err.mc && python -m minicalc /tmp/err.mc
Error: Syntax error at line 1, column 4: expected an expression, found end of line
  2 +
     ^
Error: Runtime error at line 2, column 3: division by zero
  1 / 0
    ^
line 3: = 6
exit=1
```

One-shot and `main.py`:

```
$ python -m minicalc -e "gcd(48, 18)"
= 6                          exit=0
$ python -m minicalc -e "2 +"
Error: Syntax error at line 1, column 4: expected an expression, found end of line
  2 +
     ^                       exit=1
$ python main.py -e "gcd(48, 18)"
= 6                          exit=0
```

Usage and version:

```
$ python -m minicalc /tmp/nope.mc
minicalc: cannot read '/tmp/nope.mc': [Errno 2] No such file or directory: '/tmp/nope.mc'
exit=2
$ python -m minicalc --bogus
usage: minicalc [-h] [-e EXPR] [--no-color] [--version] [file]
minicalc: error: unrecognized arguments: --bogus
exit=2
$ python -m minicalc --version
MiniCalc 1.0.0               exit=0
$ NO_COLOR=1 python -m minicalc -e "1 / 0"     # plain text, no escapes
Error: Runtime error at line 1, column 3: division by zero
  1 / 0
    ^
```

REPL through a pipe (banner, results, `:vars`, `:help`, `:clear`, division by zero, syntax error, `:quit`):

```
$ printf '2+3*4\nx = 7\nans * x\n:vars\n:help\n:clear\n:vars\n1 / 0\n2 +\n:q\n' | python -m minicalc
--------------------------------------------
MiniCalc 1.0  integer arithmetic language
Type :help for help, :quit to exit.
--------------------------------------------
minicalc> = 14
minicalc> x = 7
minicalc> = 98
minicalc> ans = 98
x   = 7
minicalc> Operators (highest to lowest)
  1  ( )                grouping, function calls
  2  **                 exponentiation (right-associative)
  3  - +                unary sign (prefix)
  4  * / // %           multiplication, division, modulo (left)
  5  + -                addition, subtraction (left)
  6  == != < <= > >=    comparison (cannot chain)

Functions
  abs(x)                absolute value
  min(a, b, ...)        smallest argument
  max(a, b, ...)        largest argument
  gcd(a, b)             greatest common divisor

Names
  x = 7                 assign the value to a name
  ans                   value of the last successful statement

Commands
  :help                 show this help
  :vars                 list ans and variables
  :clear                remove all variables and ans
  :quit, :q             exit the REPL

Examples
  2 + 3 * 4             = 14
  x = 7                 x = 7
  gcd(12, 18)           = 6
minicalc> Cleared 1 variable(s).
minicalc> (no variables)
minicalc> Error: Runtime error at line 1, column 3: division by zero
  1 / 0
    ^

minicalc> Error: Syntax error at line 1, column 4: expected an expression, found end of line
  2 +
     ^

minicalc> repl-exit=0
$ printf '' | python -m minicalc        # Ctrl-D at the prompt
ctrl-d-exit=0
```

Every error class renders with a caret line:

```
$ for e in "2 @" "2 + * 3" "1 / 0" "2147483647 + 1" "2 ** -1" "y" "foo(1)" "ans = 1"; do python -m minicalc -e "$e"; done
Error: Lexical error at line 1, column 3: illegal character '@'
  2 @
    ^
Error: Syntax error at line 1, column 5: expected an expression, found '*'
  2 + * 3
      ^
Error: Runtime error at line 1, column 3: division by zero
  1 / 0
    ^
Error: Runtime error at line 1, column 12: integer result out of 32-bit range
  2147483647 + 1
             ^
Error: Runtime error at line 1, column 3: negative exponent
  2 ** -1
    ^
Error: Runtime error at line 1, column 1: name 'y' is not defined
  y
  ^
Error: Runtime error at line 1, column 1: unknown function 'foo'
  foo(1)
  ^
Error: Runtime error at line 1, column 1: cannot assign to reserved name 'ans'
  ans = 1
  ^
```

### Crash check — 20,000 lines

Script kept out of the repo (over 60 lines) at `/tmp/int001_fuzz.py`; it seeds `random.Random(20261026)`, alternates token soup and grammar-generated expressions (nested calls, unary chains, all binary operators, assignments), runs them through one `run_source`, then replays the first 5,000 through fresh `Interpreter().run_line` calls, checking every produced value against `INT_MIN..INT_MAX`.

```
lines=20000 outcomes=20000 values_checked=5904 direct_ok=1318 foreign=0
fuzz-exit=0
real 0m4.403s
```

No exception other than `MiniCalcError` escaped; no out-of-range value.

### Spec table audit

A one-off script ran all 17 worked examples plus 35 error/edge rows from spec sections 2, 3, and 5. Zero mismatches. (The single line my first check flagged, `-2147483647 - 1 - 1`, was my own column arithmetic: the operator is at column 17, which is what the code reports.)

### Housekeeping

```
$ git status --short          # empty
$ git diff HEAD~1 --stat
 docs/decisions/decision-log.md | 19 ++++++++++++++-----
 docs/tasks/status.md           |  2 +-
 tests/golden/rulings.mc        | 12 ++++++++++++
 tests/golden/rulings.out       | 11 +++++++++++
```

No file outside INT-001's ownership was touched.

## Git Diff

```diff
diff --git c/docs/decisions/decision-log.md w/docs/decisions/decision-log.md
index 1722c09..d1836ed 100644
--- c/docs/decisions/decision-log.md
+++ w/docs/decisions/decision-log.md
@@ -115,11 +115,20 @@ This file exists so that across API-credit-limited handoffs between APC AI insta
 - **Reasoning:** The spec and contract fix behavior but not exact wording, column widths, or the handling of unexpected exceptions; these choices keep output aligned, ASCII-safe, deterministic, and testable without touching the facade.  
 - **Affects:** `minicalc/display.py`, `minicalc/repl.py`, `minicalc/__main__.py`, `main.py`, `tests/test_display.py`, `tests/test_cli.py`.
 
-**[D-15]** RESERVED for INT-001: resolution of cross-stage discrepancies found during integration.  
-- **Date / Session:** reserved 2026-10-26  
-- **Decision:** (to be written by the agent running INT-001)  
-- **Reasoning:** (to be written)  
-- **Affects:** (to be written)
+**[D-15]** Cross-stage discrepancies resolved during integration (INT-001).  
+- **Date / Session:** 2026-10-26, INT-001 integration session  
+- **Decision:** These rulings settle every seam discrepancy found between the merged tracks. The spec edit recording them is commit `44cd2c2` (`docs(spec): record Phase 2 rulings ...`), and `tests/golden/rulings.mc`/`.out` pins them (expectations written from the spec text before the code was run).  
+  1. **`ans` and assignments.** `ans` changes only on a successful *expression*. A successful assignment binds its variable and returns `kind="assign"` but leaves `ans` unchanged. This **supersedes** the "unset until the first successful statement" wording in [D-08] and the older spec section 6 text. Reason: the section 1 and interface-contract section 12 examples (`2 + 3 * 4`, `x = 7`, `ans * x` gives `98`) only hold this way. Found by FEAT-005. Affects `minicalc/interpreter.py` (commit `7bff102`).  
+  2. **`12é`.** Only an ASCII letter or `_` directly after digits triggers the "letter after digits" error at the start of the number. Any non-ASCII character is an ordinary illegal character at its own column, so `12é` is `LexError 1:3`. Spec section 2 now says "ASCII letter or `_`" and adds a `12é` row.  
+  3. **`INT_MIN % -1`** is `0` (the result is in range, unlike `INT_MIN / -1`). Spec section 5 `%` row updated.  
+  4. **Negative exponent** is a `DomainError` for every base, including `0` and `1`; that check precedes the `**` special cases. Spec section 5 updated.  
+  5. **Reserved assignment target.** The reserved-name check runs before the right side is evaluated, so `ans = 1 / 0` and `abs = 1 / 0` are `AssignmentError 1:1`, not `DivisionByZeroError`. Spec section 6 updated.  
+  6. **`gcd(INT_MIN, 0)` and `gcd(INT_MIN, INT_MIN)`** are `IntegerRangeError` at the call (the true result, 2147483648, is out of range). Spec section 6 built-in table updated.  
+  7. **Parenthesis nesting boundary, measured on disk** with the real parser: 199 nested parentheses evaluate; 200 is `ParseError 1:201` (`parser.MAX_DEPTH = 200`). Through the facade the recursion-limit fallback never fires first; [D-13]'s limit remains unchanged.  
+  8. **Script-mode line prefixes.** Spec section 8's "prefixed by the line number" is satisfied by `render()` naming the line ("at line N, column M") plus `line N: ` prefixes on results, per [D-14]. Script-mode errors go to stderr, so a caller that merges stdout and stderr may see error blocks before earlier results; this is a stream-buffering artifact of the [D-14] split, not a behavior mismatch. No code change.  
+  9. **No further discrepancies.** Every worked example and every error row in spec sections 2, 3, and 5 reproduces exactly (class and `line:col`), and all public signatures in `interface-contract.md` matched through `inspect.signature`.  
+- **Reasoning:** The spec is the arbiter; these are the questions the merged tracks answered differently or left open. Pinning each in both the spec and a golden file means a future regression shows up as a failing case rather than a rediscovered ambiguity.  
+- **Affects:** `docs/context/language-spec.md`, `tests/golden/rulings.mc`, `tests/golden/rulings.out`, `minicalc/interpreter.py`, DOC-002 (must document rulings 1–7).
 
 **[D-16]** RESERVED for DOC-003: final submission checklist outcomes and any cut-line decisions.  
 - **Date / Session:** reserved 2026-10-26  
diff --git c/docs/tasks/status.md w/docs/tasks/status.md
index ffc1569..215082a 100644
--- c/docs/tasks/status.md
+++ w/docs/tasks/status.md
@@ -45,7 +45,7 @@ Status: **open**
 
 | ID | Task | Status | Notes / Report |
 | :--- | :--- | :--- | :--- |
-| INT-001 | Integrate all tracks, full-suite green | `open` | Prompt: `docs/prompts/INT-001.md`. Reserved [D-15] |
+| INT-001 | Integrate all tracks, full-suite green | `needs-review` | Report: `docs/reports/INT-001-claude-code-integration.md`. 432 passed, 0 skipped on Python 3.10.16 and 3.14.8; [D-15] logged |
 | INT-002 | Differential test and independent audit | `open` | Prompt: `docs/prompts/INT-002.md` |
 
 ## Phase 4 — Documentation, Packaging & Release
diff --git c/tests/golden/rulings.mc w/tests/golden/rulings.mc
new file mode 100644
index 0000000..575fc31
--- /dev/null
+++ w/tests/golden/rulings.mc
@@ -0,0 +1,12 @@
+# Phase 2 rulings recorded in [D-15]; expectations written from the spec text
+12é
+(-2147483647 - 1) % -1
+1 ** -1
+0 ** -1
+gcd(-2147483647 - 1, 0)
+gcd(-2147483647 - 1, -2147483647 - 1)
+2 + 3 * 4
+x = 7
+ans * x
+ans = 1 / 0
+abs = 1 / 0
diff --git c/tests/golden/rulings.out w/tests/golden/rulings.out
new file mode 100644
index 0000000..ed6e291
--- /dev/null
+++ w/tests/golden/rulings.out
@@ -0,0 +1,11 @@
+ERR LexError 2:3
+OK 0
+ERR DomainError 4:3
+ERR DomainError 5:3
+ERR IntegerRangeError 6:1
+ERR IntegerRangeError 7:1
+OK 14
+OK x=7
+OK 98
+ERR AssignmentError 11:1
+ERR AssignmentError 12:1
```

The `docs/context/repo-tree.txt` regeneration and this report are in the same commit but omitted from the diff block above (the tree file is generated, and a report cannot contain its own bytes). The patch file covers the golden files only.

## Patch

`patch/INT-001-claude-code-integration.patch` — `git diff HEAD~1 -- tests/golden` (the task changed no implementation file).

## Flagged for APC / Operator Attention

1. **Script-mode stream order when piped.** Script-mode errors go to stderr and results to stdout ([D-14]); if a caller merges the two (`2>&1`), buffered stdout can surface after the error blocks. In a terminal the order is correct. Recorded as [D-15] item 8. No code change; say so if you want an explicit flush.
2. **Test count.** Master before this task had 431; the new `rulings` golden file makes 432. APC's expected 431 + ARCH-002 smoke is consistent with 432.
3. **`[D-08]` wording.** It still says `ans` is "unset until the first successful statement". [D-15] item 1 states the supersession rather than editing an older entry, as the addendum requires. If the operator prefers in-place correction of [D-08], that needs a separate instruction.
4. **No open ambiguities.** Nothing was left unresolved for a ruling.
