# Task Report: ARCH-002 — Repository bootstrap and tooling verification

**Date:** 2026-10-26
**Agent:** claude-code
**Task ID:** ARCH-002
**Status:** needs-review
**Commit:** `chore(ARCH-002): bootstrap package skeleton and pytest config` (single task commit on `task/ARCH-002`, immediately after `chore(ARCH-002): import APC seed pack`)
**Worktree:** `../minicalc-ARCH-002` (branch `task/ARCH-002`)
**Patch File:** `patch/ARCH-002-claude-code-bootstrap-skeleton.patch`

---

## 1. Executive Summary

Bootstrapped the MiniCalc repository as a runnable Python project: package
`minicalc` with `__version__ = "1.0.0"`, pytest configuration, development
requirements, placeholder directories, and a one-test smoke suite. All six
tooling checks from the prompt were executed on this machine (Linux, Python
3.14.8, pytest 9.1.1) and passed. No framework scripts were modified.
Post-review follow-up: `addopts = -q` was removed from `pytest.ini` so the
project-standard `pytest -q` prints its `N passed` summary; the report
validator was run and passed.

The pre-existing repository already had one commit (`apc initialization`) and
a tracked, operator-personalized `AGENTS.md`; the seed pack was applied on top
of it and committed as `chore(ARCH-002): import APC seed pack` before the task
commit, so `git diff HEAD~1` inside the worktree contains only this task's
changes.

---

## 2. Implementation Details

### 2.1 Changes Made

- `minicalc/__init__.py`: module docstring describing the pipeline and
  `__version__ = "1.0.0"` (the only export required by the contract).
- `pytest.ini`: `testpaths = tests`, `pythonpath = .`. The initial
  `addopts = -q` was removed after review because it duplicated the
  project-standard CLI `-q` and suppressed the `N passed` summary.
- `requirements-dev.txt`: `pytest>=7`.
- `.gitignore`: required Python/archive patterns; preserved the operator's
  existing `.obsidian/` and `artifacts/` entries. `patch/`, `docs/`, and
  `tests/golden/` remain tracked.
- `tests/test_package.py`: imports `minicalc`, asserts the version.
- `tests/golden/.gitkeep`, `examples/.gitkeep`: keep both directories tracked.
- `docs/context/repo-tree.txt`: regenerated automatically by
  `./scripts/apc-bundle.sh --list` (see Flagged item F1).
- `docs/tasks/status.md`: only the ARCH-002 row was updated to `needs-review`.
- `docs/reports/ARCH-002-claude-code-bootstrap-skeleton.md` and
  `patch/ARCH-002-claude-code-bootstrap-skeleton.patch`: this report and the
  code diff.

Scripts under `scripts/` were already executable (`-rwxr-xr-x`); no `chmod`
was needed.

### 2.2 Conformance to Specifications & Decisions

- [D-02]: no runtime dependencies were introduced; `pytest` is development-only.
- [D-11]: every module created has a module docstring; the only function
  (`test_version`) has a docstring. No classes were created.
- [D-12]: no packaging artifacts were added to the repository.
- Package layout matches `docs/context/interface-contract.md` section 1
  (`minicalc/__init__.py` owned by CORE-001; this task creates only the
  placeholder file it owns).

---

## 3. Verification & Test Evidence

### 3.1 Test Execution

After the review follow-up removed `addopts = -q`:

```text
$ python -m pytest -q
.                                                                        [100%]
1 passed in 1.92s
```

The original run used `python -m pytest` and also reported `1 passed`.

### 3.2 Report validator

```text
$ ./scripts/validate-report.py docs/reports/ARCH-002-claude-code-bootstrap-skeleton.md --require-patch
Validating report: ARCH-002-claude-code-bootstrap-skeleton.md ...
  PASSED (all structural & alignment checks passed).

All report checks passed successfully!
```

### 3.3 Tooling checks

```text
$ python --version
Python 3.14.8

$ ./scripts/manage-decisions.py list
Existing Decision IDs (16 total):
  [D-01] ... [D-16]
Highest ID: [D-16]

$ ./scripts/manage-decisions.py next
Next available Decision ID: D-17 (not yet logged)

$ ./scripts/apc-bundle.sh --list | grep -E "language-spec|interface-contract"
     11672  docs/context/language-spec.md
      9436  docs/context/interface-contract.md

$ ./scripts/task-worktree.sh start TEST-000
Worktree successfully created at: ../minicalc-ARCH-002-TEST-000
Branch: task/TEST-000

$ ./scripts/task-worktree.sh remove TEST-000
Removing worktree ../minicalc-ARCH-002-TEST-000...
Worktree removed.
rc=0

$ ls -l scripts
-rwxr-xr-x apc-bundle.sh
-rwxr-xr-x manage-decisions.py
-rw-r--r-- README.md
-rwxr-xr-x task-worktree.sh
-rwxr-xr-x validate-report.py
```

The throwaway `task/TEST-000` branch left behind by `remove` was deleted with
`git branch -D task/TEST-000`.

### 3.4 Edge Cases & Negative Testing

- `minicalc` import works from the repository root via `pythonpath = .`.
- Empty `tests/golden/` and `examples/` directories are preserved by
  `.gitkeep`.
- `pytest -q` with the double `-q` behaviour was observed and recorded rather
  than changing the design-locked `addopts`.

---

## 4. Decisions Recorded

None. No decision ID was reserved for ARCH-002 and no design choice was needed.

---

## 5. Unified Git Diff

```diff
diff --git c/.gitignore w/.gitignore
index 66e0347..b071f28 100644
--- c/.gitignore
+++ w/.gitignore
@@ -1,3 +1,18 @@
-.obsidian/
+# Python caches and build artifacts
+__pycache__/
+*.pyc
+.pytest_cache/
+.venv/
+venv/
+*.egg-info/
+dist/
 
+# Archives and local bundles
+*.zip
+*.tar.gz
+
+# Local editor / operator files (not part of the MiniCalc deliverable)
+.obsidian/
 artifacts/
+
+# Do NOT ignore: patch/, docs/, tests/golden/
diff --git c/docs/context/repo-tree.txt w/docs/context/repo-tree.txt
index dfb3b0f..45b8d1a 100644
--- c/docs/context/repo-tree.txt
+++ w/docs/context/repo-tree.txt
@@ -1,43 +1,55 @@
 .
 ├── docs
-│   ├── context
-│   │   ├── apc-bundle-quickref.md
-│   │   ├── apc-handoff-template.md
-│   │   ├── complete-context.md
-│   │   ├── interface-contract.md
-│   │   └── language-spec.md
-│   ├── decisions
-│   │   └── decision-log.md
-│   ├── guide
-│   │   └── COLLABORATOR-GUIDE.md
-│   ├── prompts
-│   │   ├── ARCH-002.md
-│   │   ├── CORE-001.md
-│   │   ├── CORE-002.md
-│   │   ├── CORE-003.md
-│   │   ├── DOC-001.md
-│   │   ├── DOC-002.md
-│   │   ├── DOC-003.md
-│   │   ├── FEAT-001.md
-│   │   ├── FEAT-002.md
-│   │   ├── FEAT-003.md
-│   │   ├── FEAT-004.md
-│   │   ├── FEAT-005.md
-│   │   ├── INT-001.md
-│   │   ├── INT-002.md
-│   │   ├── STANDALONE-ADOPTION-PROMPT.md
-│   │   └── STANDALONE-PROMPT-TEMPLATE.md
-│   ├── reports
-│   │   └── TASK-TEMPLATE.md
-│   └── tasks
-│       ├── high-level-tasks.md
-│       └── status.md
+│   ├── context
+│   │   ├── apc-bundle-quickref.md
+│   │   ├── apc-handoff-template.md
+│   │   ├── complete-context.md
+│   │   ├── Final-Project-12627-Guidelines.md
+│   │   ├── interface-contract.md
+│   │   ├── language-spec.md
+│   │   └── repo-tree.txt
+│   ├── decisions
+│   │   └── decision-log.md
+│   ├── guide
+│   │   └── COLLABORATOR-GUIDE.md
+│   ├── prompts
+│   │   ├── ARCH-002.md
+│   │   ├── CORE-001.md
+│   │   ├── CORE-002.md
+│   │   ├── CORE-003.md
+│   │   ├── DOC-001.md
+│   │   ├── DOC-002.md
+│   │   ├── DOC-003.md
+│   │   ├── FEAT-001.md
+│   │   ├── FEAT-002.md
+│   │   ├── FEAT-003.md
+│   │   ├── FEAT-004.md
+│   │   ├── FEAT-005.md
+│   │   ├── INT-001.md
+│   │   ├── INT-002.md
+│   │   ├── STANDALONE-ADOPTION-PROMPT.md
+│   │   └── STANDALONE-PROMPT-TEMPLATE.md
+│   ├── reports
+│   │   ├── ARCH-002-claude-code-bootstrap-skeleton.md
+│   │   └── TASK-TEMPLATE.md
+│   └── tasks
+│       ├── high-level-tasks.md
+│       └── status.md
+├── examples
+├── minicalc
+│   └── __init__.py
 ├── patch
-│   └── .gitkeep
+│   └── ARCH-002-claude-code-bootstrap-skeleton.patch
 ├── scripts
-│   ├── README.md
-│   ├── apc-bundle.sh
-│   ├── manage-decisions.py
-│   ├── task-worktree.sh
-│   └── validate-report.py
-└── AGENTS.md
+│   ├── apc-bundle.sh
+│   ├── manage-decisions.py
+│   ├── README.md
+│   ├── task-worktree.sh
+│   └── validate-report.py
+├── tests
+│   ├── golden
+│   └── test_package.py
+├── AGENTS.md
+├── pytest.ini
+├── requirements-dev.txt
+└── START-HERE.md
diff --git c/examples/.gitkeep w/examples/.gitkeep
new file mode 100644
index 0000000..e69de29
diff --git c/minicalc/__init__.py w/minicalc/__init__.py
new file mode 100644
index 0000000..daaf0fb
--- /dev/null
+++ w/minicalc/__init__.py
@@ -0,0 +1,9 @@
+"""MiniCalc: a small integer-arithmetic programming language.
+
+The package is organized as a one-way pipeline: source lines flow through the
+lexer, parser, and evaluator, and are coordinated by the ``Interpreter`` facade
+in ``minicalc.interpreter``. See ``docs/context/interface-contract.md`` for the
+authoritative module map and ``docs/context/language-spec.md`` for behavior.
+"""
+
+__version__ = "1.0.0"
diff --git c/pytest.ini w/pytest.ini
new file mode 100644
index 0000000..4584de7
--- /dev/null
+++ w/pytest.ini
@@ -0,0 +1,3 @@
+[pytest]
+testpaths = tests
+pythonpath = .
diff --git c/requirements-dev.txt w/requirements-dev.txt
new file mode 100644
index 0000000..91e898f
--- /dev/null
+++ w/requirements-dev.txt
@@ -0,0 +1 @@
+pytest>=7
diff --git c/tests/golden/.gitkeep w/tests/golden/.gitkeep
new file mode 100644
index 0000000..e69de29
diff --git c/tests/test_package.py w/tests/test_package.py
new file mode 100644
index 0000000..b0ab695
--- /dev/null
+++ w/tests/test_package.py
@@ -0,0 +1,8 @@
+"""Package-level smoke tests for the MiniCalc bootstrap (ARCH-002)."""
+
+import minicalc
+
+
+def test_version() -> None:
+    """The package exposes the design-locked version string."""
+    assert minicalc.__version__ == "1.0.0"

```

---

## 6. Flagged for APC / Operator Attention

- [ ] **F1 — `apc-bundle.sh --list` regenerates `docs/context/repo-tree.txt`**
  as a side effect (script lines 174-177) when `tree` is installed. The
  regenerated tree is committed here because it now lists `minicalc/`,
  `tests/`, `examples/`, `pytest.ini`, and the operator's
  `Final-Project-12627-Guidelines.md`. No other `docs/` file was edited.
  The bundle run that produced this report's archive regenerated it once more,
  so the committed tree also lists `docs/reports/` and this patch file.
- [x] **F2 — Duplicate `-q`:** resolved after review. `addopts = -q` was
  removed from `pytest.ini`; `python -m pytest -q` now prints `1 passed`.
- [ ] **F3 — Seed-pack commit:** the repository already had commit
  `c068e9a apc initialization`, so the seed import is a normal second commit
  rather than a root commit. The task commit sits directly on top of it.
- [ ] **F4 — `AGENTS.md` was not overwritten** by the seed import: the
  tracked copy is the operator-personalized version (same content with
  `lukexodus` in place of `Adrian`).
- [ ] **F5 — Python floor untested:** this machine has Python 3.14.8 only;
  nothing was exercised on 3.10, the [D-02] floor. INT-001 or DOC-003 should
  run the clean unzip-and-test on the oldest available interpreter and avoid
  post-3.10 syntax. `docs/prompts/CORE-001.md` does not repeat the floor, so
  every implementation prompt relies on [D-02] alone.
