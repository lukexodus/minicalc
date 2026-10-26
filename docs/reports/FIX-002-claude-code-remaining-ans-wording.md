# FIX-002 — Remaining stale `ans` wording and context-doc cleanup

**Agent:** Claude Code · **Branch:** `task/FIX-002` · **Worktree:** `/home/lukexodus/projects/minicalc-FIX-002`
**Commit:** the single commit on `task/FIX-002` (amended once to include this report and the patch file)
**Patch:** `patch/FIX-002-claude-code-remaining-ans-wording.patch`

## Executive Summary

FIX-002 finished the wording cleanup FIX-001 flagged but could not perform within its file scope, and corrected the stale decision-state line in `docs/context/complete-context.md`. The `ans` error message is now exactly `ans has no value yet; evaluate an expression first`; every stale "statement" phrase about `ans` in `minicalc/environment.py` and the two tests now says "expression". No behaviour changed: `record_result` is still called only for successful expression results, never assignments.

- Baseline verified before editing: Python 3.14.8 and 3.10.16, **439 passed, 0 skipped**; `[D-17]` present, `[D-18]` absent.
- All Section 5 gates pass: 439 passed (default and 3.10), `-W error` green, before/after CLI evidence captured, sweep shows only allowed leftovers, 20,000-line crash check clean, and only allowed files were edited.
- `[D-18]` was appended and the FIX-002 row added under Phase 3 with status `needs-review`.

## Implementation Details

### Precondition: where `record_result` is called

Before changing any wording, `grep -rn 'record_result'` showed exactly one implementation call site: `minicalc/interpreter.py:111`. It sits after the `isinstance(node, Assign)` early return:

```python
if isinstance(node, Assign):
    return Result("assign", value, node.target)
self.env.record_result(value)
```

So only successful expression results update `ans`; assignments never do. This matches spec section 6 and `interface-contract.md:201`. The change is therefore wording-only.

### A. `minicalc/environment.py`

Verified line numbers on disk before editing (all matched the prompt):

- `:4` module docstring — "successful statement" → "successful expression".
- `:18` class attribute docstring — "last successful statement" → "last successful expression".
- `:43` user-visible error — `ans has no value yet; evaluate a statement first` → `ans has no value yet; evaluate an expression first`.
- `:60` `record_result` docstring — "successful statement" → "successful expression".
- `:63` `value` arg — "The statement's value." → "The expression's value."

No other source file was touched.

### B. Tests

- `tests/test_environment.py:24` — exact-message assertion updated to the new text.
- `tests/test_evaluator.py:294` — docstring now reads "``ans`` is undefined before any successful expression."

Finding: no CLI or REPL test pins the old message. The only exact-message assertion is `tests/test_environment.py:24`; `grep -rn 'no value yet' tests/ minicalc/` now returns only that assertion and `environment.py:43`. The CLI output is checked by running the real command below.

### C. `docs/context/complete-context.md`

Line 48 previously stated `Locked decisions [D-01] to [D-12], reserved [D-13] to [D-16]`. It now states the real state:

```text
| `docs/decisions/decision-log.md` | Locked decisions [D-01] to [D-15], [D-17], and [D-18]; [D-16] reserved for DOC-003 |
```

Read from the live decision log: D-01..D-15 written, D-17 written, D-18 written by this task, D-16 still reserved for DOC-003. Other docs under `docs/` with decision-count statements were **not** edited (out of scope) and are listed under Flagged below.

### D. Repo-wide sweep

After the edits, all five search terms were re-run across the tree (excluding `.git`/`__pycache__`). Every remaining hit is an allowed leftover:

| Term | Hits | Location |
| :--- | :--- | :--- |
| `successful statement` | 31 | `docs/reports/**` (20), `patch/**` (8), `docs/decisions/decision-log.md:62` [D-08], `:121` [D-15], `:142` [D-17] |
| `evaluate a statement` | 7 | `docs/reports/**` (3), `patch/**` (2), `docs/prompts/CORE-003.md:27`, `docs/decisions/decision-log.md:142` [D-17] |
| `last statement` | 0 | — |
| `first successful` | 8 | `docs/reports/**` (5), `patch/**` (1), `docs/decisions/decision-log.md:62` [D-08], `:121` [D-15] |
| `statement's value` | 3 | `docs/reports/**` (2), `patch/**` (1) |

Zero hits outside `docs/reports/`, `patch/`, the three allowed decision entries ([D-08], [D-15], [D-17]), and `docs/prompts/CORE-003.md`.

These counts are from the sweep run immediately after the source/test/doc edits and **before this report and its patch file existed**. Both artifacts necessarily quote the old wording in their before/after and diff sections, so a later re-run also matches them; they live under the allowed `docs/reports/` and `patch/` paths. Re-running the five greps after the amend still produces zero hits outside the allowed categories.

## Verification & Test Evidence

### Test runs (final tree)

```text
$ python --version
Python 3.14.8
$ python -m pytest -q -rs
439 passed in 4.39s

$ /tmp/minicalc-v310/bin/python --version
Python 3.10.16
$ /tmp/minicalc-v310/bin/python -m pytest -q -rs
439 passed in 2.54s

$ python -W error -m pytest -q
439 passed in 4.12s
```

No skips on either interpreter. File count is unchanged (no new tests; only one assertion and one docstring updated).

### Before / after CLI evidence

Before:

```text
$ python -m minicalc -e "ans"
Error: Runtime error at line 1, column 1: ans has no value yet; evaluate a statement first
  ans
  ^
EXIT=1

$ printf 'x = 5\nans\n' > /tmp/fix002_before.mc && python -m minicalc /tmp/fix002_before.mc
line 1: x = 5
Error: Runtime error at line 2, column 1: ans has no value yet; evaluate a statement first
  ans
  ^
EXIT=1
```

After:

```text
$ python -m minicalc -e "ans"
Error: Runtime error at line 1, column 1: ans has no value yet; evaluate an expression first
  ans
  ^
EXIT=1

$ printf 'x = 5\nans\n' > /tmp/fix002_after.mc && python -m minicalc /tmp/fix002_after.mc
line 1: x = 5
Error: Runtime error at line 2, column 1: ans has no value yet; evaluate an expression first
  ans
  ^
EXIT=1
```

The two-line script confirms that the successful assignment `x = 5` does not set `ans`, so line 2 still reports the expression message.

### Crash check — 20,000 random lines through `Interpreter.run_source`

Seeded `random.Random(20261026)`, mixing token soup and grammar-generated expressions (including assignments, all binary operators, calls, and malformed input). Script kept outside the repo at `/tmp/fix002_fuzz.py`:

```text
lines=20000 values_checked=5904 direct_ok=1318 foreign=0
exit=0
```

No exception escaped `run_source` (including `MiniCalcError`, which the facade promises not to raise), every produced value was checked against `[INT_MIN, INT_MAX]`, and the first 5,000 lines were also replayed through fresh `Interpreter().run_line` calls with the same range check.

### Housekeeping

Before the report/patch amendment, `git status --short` showed only the six allowed files:

```text
 M docs/context/complete-context.md
 M docs/decisions/decision-log.md
 M docs/tasks/status.md
 M minicalc/environment.py
 M tests/test_environment.py
 M tests/test_evaluator.py
```

```text
 docs/context/complete-context.md |  2 +-
 docs/decisions/decision-log.md   | 10 ++++++++++
 docs/tasks/status.md             |  1 +
 minicalc/environment.py          | 10 +++++-----
 tests/test_environment.py        |  2 +-
 tests/test_evaluator.py          |  2 +-
 6 files changed, 19 insertions(+), 8 deletions(-)
```

The single commit additionally contains this report and the patch file; `git status` is clean after the amend. The docs-only changes ([D-18], the status row, `complete-context.md`, and this report) are in the commit but are not part of the patch file, per repo convention.

## Git Diff

Verbatim `git diff HEAD~1 -- minicalc/ tests/` (identical to the patch file), including index lines:

```diff
diff --git c/minicalc/environment.py w/minicalc/environment.py
index f817fe9..6180a53 100644
--- c/minicalc/environment.py
+++ w/minicalc/environment.py
@@ -1,7 +1,7 @@
 """Variable storage and the special ``ans`` binding (CORE-003).
 
 The environment is the only mutable state in the interpreter. ``ans`` is a
-separate read-only binding updated after each successful statement; it is not
+separate read-only binding updated after each successful expression; it is not
 part of ``variables``.
 """
 
@@ -15,7 +15,7 @@ class Environment:
 
     Attributes:
         variables: User-defined name-to-value bindings.
-        ans: Value of the last successful statement, or ``None`` before the
+        ans: Value of the last successful expression, or ``None`` before the
             first success.
     """
 
@@ -40,7 +40,7 @@ class Environment:
         if name == "ans":
             if self.ans is None:
                 raise UndefinedNameError(
-                    "ans has no value yet; evaluate a statement first", pos
+                    "ans has no value yet; evaluate an expression first", pos
                 )
             return self.ans
         if name in self.variables:
@@ -57,10 +57,10 @@ class Environment:
         self.variables[name] = value
 
     def record_result(self, value: int) -> None:
-        """Record the value of a successful statement as ``ans``.
+        """Record the value of a successful expression as ``ans``.
 
         Args:
-            value: The statement's value.
+            value: The expression's value.
         """
         self.ans = value
 
diff --git c/tests/test_environment.py w/tests/test_environment.py
index 1ddbd32..91680ff 100644
--- c/tests/test_environment.py
+++ w/tests/test_environment.py
@@ -21,7 +21,7 @@ def test_unset_ans_message() -> None:
     env = Environment()
     with pytest.raises(UndefinedNameError) as info:
         env.get("ans", POS)
-    assert str(info.value) == "ans has no value yet; evaluate a statement first"
+    assert str(info.value) == "ans has no value yet; evaluate an expression first"
     assert info.value.pos == POS
 
 
diff --git c/tests/test_evaluator.py w/tests/test_evaluator.py
index fed5392..ac8bb97 100644
--- c/tests/test_evaluator.py
+++ w/tests/test_evaluator.py
@@ -291,7 +291,7 @@ def test_unset_variable_error_at_name() -> None:
 
 
 def test_unset_ans_error() -> None:
-    """``ans`` is undefined before the first successful statement."""
+    """``ans`` is undefined before any successful expression."""
     with pytest.raises(UndefinedNameError) as info:
         evaluate(nm("ans", 2))
     assert info.value.pos == p(2)
```

## Items Flagged for APC Attention

1. **`[D-08]` remains stale on disk.** `docs/decisions/decision-log.md:62` still says `ans` is "unset until the first successful statement", which [D-15] item 1 explicitly supersedes. Left untouched per the append-only rule and the Section 2D allowlist. No new action; this is the same known item FIX-001 flagged.
2. **Stale decision-count statements outside scope.** `docs/prompts/ARCH-002.md:34` says `manage-decisions.py list` shows "[D-01] through [D-16]; `next` prints [D-17]" (both now used). `docs/tasks/high-level-tasks.md:15` and `docs/tasks/status.md:17` describe ARCH-001 as delivering "decisions [D-01..D-12]". These are historical rows/prompts recording the planning session, not current state; only `complete-context.md` was editable here and was fixed.
3. **Python version used for the local 3.10 gate.** The venv at `/tmp/minicalc-v310` is **Python 3.10.16** (not 3.10.20 as in the APC's [D-18] compensating-check note). Both runs are 439 passed; the version difference is recorded, not resolved here.
4. **No CLI/REPL test pinned the old message** (this was a possible finding requested by the prompt) — nothing else needed updating.
5. **Spec/contracts are consistent with the new wording.** `docs/context/language-spec.md:150` and `docs/context/interface-contract.md:201` already say "successful expression"; no contradiction found there.
