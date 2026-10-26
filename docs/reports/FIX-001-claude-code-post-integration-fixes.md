# FIX-001 — Post-integration fixes: `ans` help wording and merged-stream order (Claude Code)

**Branch:** `task/FIX-001` · **Worktree:** `/home/lukexodus/projects/minicalc-FIX-001` · **Commit:** the single commit on `task/FIX-001` (amended once to include this report and the patch file)

## Executive Summary

Two post-integration defects are fixed.

1. **Item A — stale `ans` wording.** The `:help` Names row said `value of the last successful statement`; it now says `value of the last successful expression`, matching [D-15] item 1 and spec section 6. A repo-wide search found the same stale phrasing in one other in-scope location (`tests/test_cli.py:25`) and in several out-of-scope files (listed under "Flagged" below; not edited because [Section 3] limits FIX-001's editable files).
2. **Item B — merged-stream order.** Script mode and `-e` mode now flush stdout before every stderr write and flush stderr immediately after (`_write_stderr` in `minicalc/__main__.py`). The [D-14] stream split and every exit code are unchanged. A `2>&1` capture of `tests/golden/demo.mc` now shows results and errors in source-line order.

Result: **434 passed, 0 skipped** on the default interpreter (Python 3.14.8) and on Python 3.10.16; `-W error` is green. The new merged-stream test fails on the unfixed code (`[2, 4, 1, 3, 5]`) and passes after the fix.

## Implementation Details

- **`minicalc/display.py`** — help row changed from `value of the last successful statement` to `value of the last successful expression`. The 20-character left field and ASCII-only layout are untouched.
- **`minicalc/__main__.py`** — added `_write_stderr(line)`, which calls `sys.stdout.flush()`, then `print(line, file=sys.stderr, flush=True)`. Every stderr write in script mode, `-e` mode, the file/`-e` usage conflict, and the top-level internal-error path now goes through it. No other behavior changed: same streams, same messages, same exit codes. REPL behaviour is untouched (it writes results and errors through the same stream, so it has no ordering problem).
- **`tests/test_cli.py`** — updated the `FakeEnvironment` attribute docstring; added two `integration` tests:
  - `test_merged_streams_keep_source_line_order` runs `python -m minicalc <script>` with `stderr=subprocess.STDOUT` and asserts the captured marker sequence is `[1, 2, 3, 4, 5]`.
  - `test_separate_streams_keep_results_and_errors_split` asserts the unmerged case still puts results on stdout, errors on stderr, with exit code 1.
- **`docs/decisions/decision-log.md`** — appended [D-17] (older entries untouched).
- **`docs/tasks/status.md`** — added the FIX-001 row under Phase 3, status `needs-review`.
- No new source or test files; no golden file, spec, contract, or `repo-tree.txt` change.

## Verification & Test Evidence

### Baseline before any change

```
$ python -m pytest -q -rs
432 passed in 3.43s
```

(Python 3.14.8; zero skip lines.)

### Full suite after the fix — default interpreter

```
$ python -m pytest -q -rs
........................................................................ [ 66%]
........................................................................ [ 82%]
........................................................................ [ 99%]
..                                                                       [100%]
434 passed in 3.67s
```

### Full suite after the fix — Python 3.10.16 (oldest supported)

```
$ /tmp/minicalc-v310/bin/python --version
Python 3.10.16
$ /tmp/minicalc-v310/bin/python -m pytest -q -rs
........................................................................ [ 66%]
........................................................................ [ 82%]
........................................................................ [ 99%]
..                                                                       [100%]
434 passed in 1.60s
```

### Warnings as errors

```
$ python -W error -m pytest -q
........................................................................ [ 99%]
..                                                                       [100%]
434 passed in 2.75s
```

### Item A — `:help` before and after

Before:

```
Names
  x = 7                 assign the value to a name
  ans                   value of the last successful statement

Commands
```

After:

```
Names
  x = 7                 assign the value to a name
  ans                   value of the last successful expression

Commands
```

### Item B — new test fails before the fix, passes after

The only source change needed for this proof is `minicalc/__main__.py`; it was temporarily restored to `HEAD` and the single test re-run, then the fixed file was restored.

Against the unfixed `__main__.py`:

```
$ python -m pytest tests/test_cli.py::test_merged_streams_keep_source_line_order -q
F                                                                        [100%]
=================================== FAILURES ===================================
__________________ test_merged_streams_keep_source_line_order __________________
...
>       assert markers == [1, 2, 3, 4, 5]
E       assert [2, 4, 1, 3, 5] == [1, 2, 3, 4, 5]
E
E         At index 0 diff: 2 != 1
tests/test_cli.py:622: AssertionError
=========================== short test summary info ============================
FAILED tests/test_cli.py::test_merged_streams_keep_source_line_order - assert...
1 failed in 2.46s
```

Against the fixed `__main__.py`:

```
$ python -m pytest tests/test_cli.py::test_merged_streams_keep_source_line_order -q
.                                                                        [100%]
1 passed in 1.82s
```

### Item B — merged-stream demo before and after

Before (`python -m minicalc tests/golden/demo.mc 2>&1`): all three error blocks for lines 10, 12, 13 came before every result for lines 2-9; exit code 1.

```
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
EXIT=1
```

After: results and errors are in source-line order; exit code is still 1.

```
$ python -m minicalc tests/golden/demo.mc 2>&1
line 2: x = 7
line 3: y = 3
line 4: = 23
line 5: = 30
line 6: = 49
line 7: = 1
line 8: = 7
line 9: = 1
Error: Runtime error at line 10, column 7: division by zero
  x = 1 / 0
        ^
line 11: = 7
Error: Syntax error at line 12, column 4: expected an expression, found end of line
  2 +
     ^
Error: Lexical error at line 13, column 2: decimals are not supported; MiniCalc works with integers only
  3.14
   ^
line 14: = 7
line 15: = 10
EXIT=1
```

### Separate-pipe case

The new `test_separate_streams_keep_results_and_errors_split` passes: stdout is exactly `["line 1: = 2", "line 3: = 4"]`, stderr contains `at line 2,`, and the exit code is 1. Existing CLI tests that assert the stdout/stderr split also remain green.

### One-shot checks

```
$ python -m minicalc -e "gcd(48, 18)"
= 6
EXIT=0

$ python -m minicalc -e "2 +"
Error: Syntax error at line 1, column 4: expected an expression, found end of line
  2 +
     ^
EXIT=1

$ python -m minicalc --version
MiniCalc 1.0.0
EXIT=0

$ python -m minicalc /tmp/definitely-missing-fix001.mc
minicalc: cannot read '/tmp/definitely-missing-fix001.mc': [Errno 2] No such file or directory: '/tmp/definitely-missing-fix001.mc'
EXIT=2

$ NO_COLOR=1 python -m minicalc -e "1 + 2"
= 3
EXIT=0
```

### Crash check — 5,000 random lines through `Interpreter.run_source`

Seeded (`random.seed(20261026`), mixing token soup and grammar-shaped expressions:

```
lines=5000 errors=2540 out_of_range=0
OK: only MiniCalcError outcomes, every produced value in 32-bit range
```

No exception escaped; every produced value was within `[INT_MIN, INT_MAX]`.

### Housekeeping

- `git status` clean after the single commit; only the files listed in Implementation Details plus this report and the patch file are in the commit.
- `./scripts/validate-report.py docs/reports/FIX-001-claude-code-post-integration-fixes.md --require-patch` passes.

## Git Diff

```diff
diff --git c/minicalc/__main__.py w/minicalc/__main__.py
index 35f3e0d..a1246f3 100644
--- c/minicalc/__main__.py
+++ w/minicalc/__main__.py
@@ -49,6 +49,20 @@ def _build_parser() -> argparse.ArgumentParser:
     return parser
 
 
+def _write_stderr(line: str) -> None:
+    """Write one error line to stderr without reordering merged streams.
+
+    Pending stdout is flushed first so that, when stdout and stderr share a
+    pipe or file (``2>&1``), results produced earlier still appear before this
+    error. Stderr is flushed immediately so the error keeps its place.
+
+    Args:
+        line: The complete line to write, without a trailing newline.
+    """
+    sys.stdout.flush()
+    print(line, file=sys.stderr, flush=True)
+
+
 def _internal_error(exc: BaseException) -> str:
     """Describe an unexpected exception on one line.
 
@@ -81,10 +95,10 @@ def _run_expression(interpreter: Interpreter, expr: str, color: bool) -> int:
             print(formatted)
         return 0
     except MiniCalcError as error:
-        print(error.render(color), file=sys.stderr)
+        _write_stderr(error.render(color))
         return 1
     except Exception as exc:
-        print(_internal_error(exc), file=sys.stderr)
+        _write_stderr(_internal_error(exc))
         return 1
 
 
@@ -104,13 +118,13 @@ def _run_file(interpreter: Interpreter, path: str, color: bool) -> int:
         with open(path, "r", encoding="utf-8") as handle:
             text = handle.read()
     except (OSError, UnicodeError) as exc:
-        print(f"minicalc: cannot read '{path}': {exc}", file=sys.stderr)
+        _write_stderr(f"minicalc: cannot read '{path}': {exc}")
         return 2
 
     try:
         outcomes = interpreter.run_source(text)
     except Exception as exc:
-        print(_internal_error(exc), file=sys.stderr)
+        _write_stderr(_internal_error(exc))
         return 1
 
     exit_code = 0
@@ -120,12 +134,12 @@ def _run_file(interpreter: Interpreter, path: str, color: bool) -> int:
             if not formatted:
                 continue
             if outcome.error is not None:
-                print(formatted, file=sys.stderr)
+                _write_stderr(formatted)
                 exit_code = 1
             else:
                 print(formatted)
         except Exception as exc:
-            print(_internal_error(exc), file=sys.stderr)
+            _write_stderr(_internal_error(exc))
             exit_code = 1
     return exit_code
 
@@ -147,10 +161,10 @@ def main(argv: list[str] | None = None) -> int:
         return exc.code if isinstance(exc.code, int) else 0
 
     if args.file is not None and args.expr is not None:
+        sys.stdout.flush()
         parser.print_usage(sys.stderr)
-        print(
-            "minicalc: error: a file and -e/--expr cannot be used together",
-            file=sys.stderr,
+        _write_stderr(
+            "minicalc: error: a file and -e/--expr cannot be used together"
         )
         return 2
 
@@ -164,7 +178,7 @@ def main(argv: list[str] | None = None) -> int:
     try:
         return Repl(interpreter, color=color).run()
     except Exception as exc:
-        print(_internal_error(exc), file=sys.stderr)
+        _write_stderr(_internal_error(exc))
         return 1
 
 
diff --git c/minicalc/display.py w/minicalc/display.py
index 39c2133..ff2053f 100644
--- c/minicalc/display.py
+++ w/minicalc/display.py
@@ -164,7 +164,7 @@ def help_text(color: bool = False) -> str:
     ]
     names = [
         ("x = 7", "assign the value to a name"),
-        ("ans", "value of the last successful statement"),
+        ("ans", "value of the last successful expression"),
     ]
     commands = [
         (":help", "show this help"),
diff --git c/tests/test_cli.py w/tests/test_cli.py
index 98951f9..128156a 100644
--- c/tests/test_cli.py
+++ w/tests/test_cli.py
@@ -6,6 +6,10 @@ the full lexer, parser, and evaluator are still landing. The
 expected to pass only after INT-001.
 """
 
+import re
+import subprocess
+import sys
+from pathlib import Path
 from types import SimpleNamespace
 
 import pytest
@@ -22,7 +26,7 @@ class FakeEnvironment:
 
     Attributes:
         variables: User-defined name-to-value bindings.
-        ans: Value of the last successful statement, or ``None``.
+        ans: Value of the last successful expression, or ``None``.
     """
 
     def __init__(
@@ -592,3 +596,46 @@ def test_cli_script_arithmetic_with_real_interpreter(
         "line 2: x = 7",
         "line 3: = 98",
     ]
+
+
+@pytest.mark.integration
+def test_merged_streams_keep_source_line_order(tmp_path: Path) -> None:
+    """With ``2>&1``, results and errors keep their source-line order."""
+    script = tmp_path / "interleaved.mc"
+    script.write_text("1 + 1\n1 / 0\n2 + 2\n2 +\n3 + 3\n", encoding="utf-8")
+    root = Path(__file__).resolve().parents[1]
+    completed = subprocess.run(
+        [sys.executable, "-m", "minicalc", str(script)],
+        stdout=subprocess.PIPE,
+        stderr=subprocess.STDOUT,
+        cwd=root,
+        text=True,
+        check=False,
+    )
+    assert completed.returncode == 1
+    markers = [
+        int(first or second)
+        for first, second in re.findall(
+            r"line (\d+):|at line (\d+),", completed.stdout
+        )
+    ]
+    assert markers == [1, 2, 3, 4, 5]
+
+
+@pytest.mark.integration
+def test_separate_streams_keep_results_and_errors_split(tmp_path: Path) -> None:
+    """Without merging, results stay on stdout and errors stay on stderr."""
+    script = tmp_path / "split.mc"
+    script.write_text("1 + 1\n1 / 0\n2 + 2\n", encoding="utf-8")
+    root = Path(__file__).resolve().parents[1]
+    completed = subprocess.run(
+        [sys.executable, "-m", "minicalc", str(script)],
+        stdout=subprocess.PIPE,
+        stderr=subprocess.PIPE,
+        cwd=root,
+        text=True,
+        check=False,
+    )
+    assert completed.returncode == 1
+    assert completed.stdout.splitlines() == ["line 1: = 2", "line 3: = 4"]
+    assert "at line 2," in completed.stderr
```

The docs-only changes ([D-17], the status row, and this report) are in the commit but are not part of the patch file, per repo convention.

## Patch

`patch/FIX-001-claude-code-post-integration-fixes.patch` (generated from `git diff HEAD~1` limited to `minicalc/` and `tests/`).

## Flagged for APC / Operator Attention

1. **Prompt scope conflict, Item A.** Section 1 says "Fix every hit in code, docstrings, comments and tests", but Section 3 limits editable files and gate 5 requires "no file outside Section 3 edited". Those cannot both hold: stale hits exist outside the allowed files. To satisfy the mandatory gate and the one-owner-per-file rule ([interface-contract] section 1), FIX-001 fixed only the allowed hits and lists the rest here, each with file:line and prior text:
   - `minicalc/environment.py:4` — "updated after each successful statement" (module docstring).
   - `minicalc/environment.py:18-19` — "Value of the last successful statement" (class attribute docstring).
   - `minicalc/environment.py:43` — user-visible error `"ans has no value yet; evaluate a statement first"`; an assignment is a statement, so this text implies an assignment satisfies it.
   - `minicalc/environment.py:60` — "Record the value of a successful statement as `ans`" (method docstring).
   - `minicalc/environment.py:63` — "The statement's value."
   - `tests/test_evaluator.py:294` — "``ans`` is undefined before the first successful statement."
   - `tests/test_environment.py:24` — pins the `environment.py:43` message exactly.
   - `docs/prompts/CORE-003.md:27` — historical prompt that specifies the same message; not edited because it is a historical prompt, not code/tests.
   These are a good fit for DOC-001 (which already owns docstring work) or a small follow-up. **Confirmation requested by the caller:** the REPL help text was **not** the only stale `ans` phrase.
2. **`[D-08]` is still stale on disk.** `docs/decisions/decision-log.md:62` says "`ans` is read-only and unset until the first successful statement", which [D-15] item 1 explicitly supersedes. Left untouched as instructed (no edits to older entries).
3. **`docs/context/complete-context.md:48` is stale.** It says "Locked decisions [D-01] to [D-12], reserved [D-13] to [D-16]"; [D-13] through [D-17] are now all written. Left untouched (not in FIX-001's file scope).

No other spec or decision-log contradiction was observed in the files read for this task.
