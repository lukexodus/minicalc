# Task Report: CORE-002 — Golden-test harness

**Date:** 2026-10-26
**Agent:** claude-code
**Task ID:** CORE-002
**Status:** needs-review
**Commit:** `test(CORE-002): add golden-test harness and smoke case` (single task commit on `task/CORE-002`)
**Worktree:** `../minicalc-CORE-002` (branch `task/CORE-002`)
**Patch File:** `patch/CORE-002-claude-code-golden-harness.patch`

---

## 1. Executive Summary

Built the golden-test harness against the fixed format in interface-contract
section 12. `tests/golden_format.py` converts a duck-typed outcome to
`OK <value>`, `OK <name>=<value>`, an error's `canonical()`, or `None`.
`tests/test_golden.py` discovers `tests/golden/*.mc`, runs each through one
fresh `Interpreter().run_source`, compares to `<stem>.out`, and produces a
readable per-index report naming the file line and source text. The suite
passes now with `test_golden.py` skipped because `minicalc.interpreter` does
not exist until CORE-003; after CORE-003 it will collect the `smoke` case.

`pytest -q` result: `59 passed, 1 skipped` (17 new tests plus the existing
ARCH-002 and CORE-001 suites, and the expected golden-harness skip).

---

## 2. Implementation Details

### 2.1 Changes Made

- `tests/golden_format.py`: `canonical_line(outcome)` duck-typed on
  `result` / `error`. Values and assignments format per contract section 12;
  errors delegate to `MiniCalcError.canonical()`; `empty` and a degenerate
  outcome return `None`; an out-of-contract kind raises `ValueError`.
- `tests/test_golden.py`: module-level guard using
  `importlib.util.find_spec("minicalc.interpreter")`; it skips only when the
  module file is genuinely absent, so a broken interpreter fails at collection
  instead of silently skipping. Sorted `.mc` discovery with
  file-stem ids, one fresh `Interpreter().run_source(text)` per file, missing
  `.out` failure with the path, trailing-blank-line trimming, and a mismatch
  report that shows index, file line, source text, expected, and actual for
  each differing index, plus the line counts.
- `tests/test_golden_format.py`: stand-ins via `types.SimpleNamespace` for
  value, assign, empty, missing, and unknown kinds; every real error class
  with a position; the `?:?` no-position fallback; error-over-result
  precedence.
- `tests/conftest.py`: `GOLDEN_DIR` only.
- `tests/golden/smoke.mc` / `smoke.out`: `42` → `OK 42`.

### 2.2 Conformance to Specifications & Decisions

- [D-10]: golden files are the conformance layer and double as the demo.
- Contract section 12: one output line per non-empty statement line; state
  carries across lines through a single `run_source`; error text never
  compared; `ERR <Class> <line>:<col>` with `?:?` fallback.
- Contract section 10: only `Interpreter.run_source` and the
  `LineOutcome.result` / `.error` shape are assumed.
- [D-11]: module docstrings and docstrings on every function, including
  private helpers. No classes were created.

---

## 3. Verification & Test Evidence

### 3.1 Test Execution

```text
$ python -m pytest -q
...........................................................              [100%]
59 passed, 1 skipped in 11.70s

$ python -m pytest -q -rs
SKIPPED [1] tests/test_golden.py:15: could not import 'minicalc.interpreter':
No module named 'minicalc.interpreter'
59 passed, 1 skipped in 10.46s
```

The skip is the documented, expected state until CORE-003. The other 59 tests
include ARCH-002 and CORE-001 regressions.

### 3.2 Mismatch and missing-`.out` behavior

Verified with temporary golden files (created and deleted, never committed)
and a local stub of `minicalc.interpreter`:

```text
--- zzwrong ---
Golden mismatch: tests/golden/zzwrong.mc
  index 0 (file line 1): source '41'
    expected: OK 42
    actual:   OK 41
Expected 1 line(s), got 1.

--- zzmissing ---
Missing golden expected file: tests/golden/zzmissing.out
```

Skip-guard check. With a temporary `minicalc/interpreter.py` that raises
`ImportError` internally, the suite now fails at collection instead of
reporting a skip:

```text
minicalc/interpreter.py:1: in <module>
    import definitely_missing_module
E   ModuleNotFoundError: No module named 'definitely_missing_module'
ERROR tests/test_golden.py
1 error in 10.22s
```

With the module genuinely absent, `python -m pytest -q -rs` reports
`59 passed, 1 skipped` and the skip message `minicalc.interpreter arrives in
CORE-003`.

### 3.3 Edge Cases & Negative Testing

- Comment-only and blank lines contribute no output and are excluded from
  index alignment while their outcomes remain available for source reporting.
- Errors take precedence if an outcome carries both `result` and `error`.
- `pos=None` errors render as `ERR <Class> ?:?`, matching CORE-001.
- A wrong count fails through the same report: missing expected/actual lines
  are named explicitly.

---

## 4. Decisions Recorded

None. No decision ID was reserved for CORE-002.

---

## 5. Unified Git Diff

```diff
diff --git c/tests/conftest.py w/tests/conftest.py
new file mode 100644
index 0000000..de7d75c
--- /dev/null
+++ w/tests/conftest.py
@@ -0,0 +1,6 @@
+"""Shared paths for the golden-test harness (CORE-002)."""
+
+from pathlib import Path
+
+#: Directory holding ``<stem>.mc`` inputs and ``<stem>.out`` expected outputs.
+GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
diff --git c/tests/golden/smoke.mc w/tests/golden/smoke.mc
new file mode 100644
index 0000000..d81cc07
--- /dev/null
+++ w/tests/golden/smoke.mc
@@ -0,0 +1 @@
+42
diff --git c/tests/golden/smoke.out w/tests/golden/smoke.out
new file mode 100644
index 0000000..5164008
--- /dev/null
+++ w/tests/golden/smoke.out
@@ -0,0 +1 @@
+OK 42
diff --git c/tests/golden_format.py w/tests/golden_format.py
new file mode 100644
index 0000000..079b7d5
--- /dev/null
+++ w/tests/golden_format.py
@@ -0,0 +1,44 @@
+"""Canonical golden-test formatting (CORE-002).
+
+The format is design-locked in ``docs/context/interface-contract.md`` section
+12: one expected line per non-empty statement line, in source order. Errors
+compare only the class name and ``line:col`` via ``MiniCalcError.canonical()``,
+never message text.
+"""
+
+from __future__ import annotations
+
+
+def canonical_line(outcome: object) -> str | None:
+    """Convert one interpreter outcome to its canonical golden line.
+
+    Duck-typed on ``outcome.result`` and ``outcome.error`` so the harness does
+    not depend on the concrete ``LineOutcome`` class from CORE-003.
+
+    Args:
+        outcome: Any object with ``result`` and ``error`` attributes.
+
+    Returns:
+        ``OK <value>`` for a value result, ``OK <name>=<value>`` for an
+        assignment, an error's ``canonical()`` string, or ``None`` when the
+        line produced no output.
+
+    Raises:
+        ValueError: If a result carries a kind outside the contract.
+    """
+    error = getattr(outcome, "error", None)
+    if error is not None:
+        return error.canonical()
+
+    result = getattr(outcome, "result", None)
+    if result is None:
+        return None
+
+    kind = result.kind
+    if kind == "value":
+        return f"OK {result.value}"
+    if kind == "assign":
+        return f"OK {result.name}={result.value}"
+    if kind == "empty":
+        return None
+    raise ValueError(f"unknown result kind: {kind!r}")
diff --git c/tests/test_golden.py w/tests/test_golden.py
new file mode 100644
index 0000000..95dc4ec
--- /dev/null
+++ w/tests/test_golden.py
@@ -0,0 +1,98 @@
+"""Run every ``tests/golden/<stem>.mc`` file against its ``<stem>.out`` (CORE-002).
+
+Skipped until CORE-003 provides ``minicalc.interpreter``. Each case runs the
+whole file through one fresh ``Interpreter`` so state carries across lines.
+"""
+
+from __future__ import annotations
+
+import importlib.util
+from pathlib import Path
+
+import pytest
+
+from golden_format import canonical_line
+
+if importlib.util.find_spec("minicalc.interpreter") is None:
+    pytest.skip("minicalc.interpreter arrives in CORE-003", allow_module_level=True)
+
+from minicalc.interpreter import Interpreter  # noqa: E402  (after the skip guard)
+
+GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
+MC_FILES = sorted(GOLDEN_DIR.glob("*.mc"))
+
+
+def _read_expected(path: Path) -> list[str]:
+    """Read a ``.out`` file and drop trailing blank lines.
+
+    Args:
+        path: The expected-output file.
+
+    Returns:
+        Expected lines in order, without a trailing blank block.
+    """
+    lines = path.read_text(encoding="utf-8").splitlines()
+    while lines and not lines[-1].strip():
+        lines.pop()
+    return lines
+
+
+def _format_mismatch(mc_path: Path, expected: list[str], actual: list[str],
+                     outcomes: list[object]) -> str:
+    """Build a readable report for a golden mismatch.
+
+    Args:
+        mc_path: The golden input file.
+        expected: Lines read from the ``.out`` file.
+        actual: Canonical lines produced by the interpreter.
+        outcomes: The interpreter outcomes that produced ``actual``.
+
+    Returns:
+        A multi-line failure message naming each differing index.
+    """
+    report = [f"Golden mismatch: {mc_path}"]
+    total = max(len(expected), len(actual))
+    for index in range(total):
+        want = expected[index] if index < len(expected) else "<missing expected line>"
+        got = actual[index] if index < len(actual) else "<missing actual line>"
+        if want == got:
+            continue
+        if index < len(outcomes):
+            outcome = outcomes[index]
+            line_no = getattr(outcome, "line_no", "?")
+            source = getattr(outcome, "source", "")
+            location = f"file line {line_no}"
+        else:
+            source = ""
+            location = "past end of source"
+        report.append(f"  index {index} ({location}): source {source!r}")
+        report.append(f"    expected: {want}")
+        report.append(f"    actual:   {got}")
+    report.append(f"Expected {len(expected)} line(s), got {len(actual)}.")
+    return "\n".join(report)
+
+
+@pytest.mark.parametrize("mc_path", MC_FILES, ids=[path.stem for path in MC_FILES])
+def test_golden_file(mc_path: Path) -> None:
+    """One golden input must reproduce its expected canonical output.
+
+    Args:
+        mc_path: The ``.mc`` file selected by the parametrization.
+    """
+    out_path = mc_path.with_suffix(".out")
+    if not out_path.is_file():
+        pytest.fail(f"Missing golden expected file: {out_path}", pytrace=False)
+
+    text = mc_path.read_text(encoding="utf-8")
+    outcomes = Interpreter().run_source(text)
+    actual = [line for line in (canonical_line(item) for item in outcomes) if line is not None]
+    kept_outcomes = [
+        outcome for outcome in outcomes if canonical_line(outcome) is not None
+    ]
+    expected = _read_expected(out_path)
+
+    if actual != expected:
+        pytest.fail(
+            _format_mismatch(mc_path, expected, actual, kept_outcomes),
+            pytrace=False,
+        )
diff --git c/tests/test_golden_format.py w/tests/test_golden_format.py
new file mode 100644
index 0000000..7c43dc9
--- /dev/null
+++ w/tests/test_golden_format.py
@@ -0,0 +1,93 @@
+"""Unit tests for the canonical golden-line formatter (CORE-002)."""
+
+from types import SimpleNamespace
+
+import pytest
+
+from golden_format import canonical_line
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
+
+
+def _result(kind: str, value: int | None = None, name: str | None = None) -> object:
+    """Build a duck-typed ``Result`` stand-in."""
+    return SimpleNamespace(kind=kind, value=value, name=name)
+
+
+def _outcome(result: object | None = None, error: BaseException | None = None) -> object:
+    """Build a duck-typed ``LineOutcome`` stand-in."""
+    return SimpleNamespace(result=result, error=error)
+
+
+def test_value_result() -> None:
+    """Expression results print as ``OK <value>``."""
+    assert canonical_line(_outcome(result=_result("value", 42))) == "OK 42"
+
+
+def test_assign_result() -> None:
+    """Assignments print as ``OK <name>=<value>``."""
+    assert canonical_line(_outcome(result=_result("assign", 7, "x"))) == "OK x=7"
+
+
+def test_empty_result() -> None:
+    """Blank and comment-only lines produce no golden line."""
+    assert canonical_line(_outcome(result=_result("empty"))) is None
+
+
+def test_missing_result_and_error_is_empty() -> None:
+    """A degenerate outcome with neither field is treated as no output."""
+    assert canonical_line(_outcome()) is None
+
+
+@pytest.mark.parametrize(
+    "error_cls",
+    [
+        MiniCalcError,
+        LexError,
+        ParseError,
+        EvalError,
+        DivisionByZeroError,
+        IntegerRangeError,
+        DomainError,
+        UndefinedNameError,
+        CallError,
+        AssignmentError,
+    ],
+)
+def test_errors_use_canonical_form(error_cls: type[MiniCalcError]) -> None:
+    """Every error class is formatted through ``canonical()``.
+
+    Args:
+        error_cls: The error class under test.
+    """
+    err = error_cls("message text is ignored", SourcePos(3, 5))
+    assert canonical_line(_outcome(error=err)) == f"ERR {error_cls.__name__} 3:5"
+
+
+def test_error_without_position_uses_fallback() -> None:
+    """The ``?:?`` canonical fallback is preserved."""
+    err = ParseError("no position")
+    assert canonical_line(_outcome(error=err)) == "ERR ParseError ?:?"
+
+
+def test_error_takes_precedence_over_result() -> None:
+    """If both fields are set, the error is reported."""
+    err = LexError("bad", SourcePos(1, 1))
+    assert canonical_line(_outcome(result=_result("value", 1), error=err)) == "ERR LexError 1:1"
+
+
+def test_unknown_kind_is_rejected() -> None:
+    """An out-of-contract result kind is a programming error, not silence."""
+    with pytest.raises(ValueError, match="unknown result kind"):
+        canonical_line(_outcome(result=_result("mystery")))

```

---

## 6. Flagged for APC / Operator Attention

- [x] **F1 — Agent lineage:** the prompt assigns this task to Gemini as an
  independent auditor; no Gemini agent was available in this session, so
  Claude Code implemented it. APC decision: formatter is mechanical plumbing;
  lineage independence is reserved for FEAT-005 (spec-derived cases) and
  INT-002 (differential oracle).
- [ ] **F2 — Import mechanism:** `test_golden.py` imports `golden_format`
  as a top-level module, relying on pytest's rootdir `tests/` insertion. It
  works under `python -m pytest` from the repo root; a future `tests/`
  package conversion would change this.
- [ ] **F3 — Unknown kinds:** `canonical_line` raises `ValueError` for an
  unknown `result.kind` instead of silently returning `None`. Conservative
  choice; any facade change should be caught by CORE-003 tests.
