# TASK: ARCH-002 — Repository bootstrap and tooling verification

## Role & Worktree Instructions
- **Assigned agent:** any (Claude Code recommended)
- **Task ID:** ARCH-002
- **Depends on:** ARCH-001 (the seed pack, already reviewed by lukexodus)
- **Worktree:** from the main checkout run `./scripts/task-worktree.sh start ARCH-002`, then work only inside `../minicalc-ARCH-002` on branch `task/ARCH-002`. Never edit the main checkout.

## Orientation & Required Reading
Before writing any code, read these in order:
1. `docs/context/complete-context.md` (project background and rules)
2. `docs/tasks/status.md` (confirm ARCH-002 is `open` and that every dependency below is `done`; if a dependency is not done, STOP and tell lukexodus)
3. `docs/decisions/decision-log.md` ([D-01] through [D-16]; never re-litigate a settled decision)
4. `docs/context/language-spec.md` (authoritative language behavior)
5. `docs/context/interface-contract.md` (authoritative Python signatures and file ownership)

Verify every assumption in this prompt against the files on disk (`ls`, `cat`, `grep`). If the prompt and the repository disagree, the repository is right: say so in your report.

## Context & Objectives
The APC seed pack (governance docs, spec, contract, decision log, prompts, scripts) has been copied into the repository root by lukexodus. This task turns it into a working Python project skeleton and proves the framework tooling works, so every later task starts from a clean, verified base.

## Specific Scope & Deliverables
1. **Initial commit of the seed pack.** If the repo has no commits, run `git init` and commit everything as one root commit: `chore(ARCH-002): import APC seed pack`. This commit is separate from, and before, your task commit.
2. **Skeleton (your single task commit):**
   - `minicalc/__init__.py` with a module docstring and `__version__ = "1.0.0"`.
   - `pytest.ini`: `testpaths = tests`, `addopts = -q`, `pythonpath = .`.
   - `requirements-dev.txt`: `pytest>=7`.
   - `.gitignore`: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.venv/`, `venv/`, `*.egg-info/`, `dist/`, `*.zip`, `*.tar.gz`. Do NOT ignore `patch/`, `docs/`, or `tests/golden/`.
   - `tests/test_package.py`: imports `minicalc`, asserts `__version__ == "1.0.0"`.
   - `tests/golden/.gitkeep`, `examples/.gitkeep`.
3. **Tooling verification (record the real output of each in the report):**
   - `python --version` is 3.10 or newer (if older, stop and report).
   - `pytest -q` passes with 1 test.
   - `./scripts/manage-decisions.py list` shows [D-01] through [D-16]; `next` prints [D-17].
   - `./scripts/apc-bundle.sh --list` includes `docs/context/language-spec.md` and `docs/context/interface-contract.md`.
   - `./scripts/task-worktree.sh start TEST-000`, then `./scripts/task-worktree.sh remove TEST-000` works cleanly.
   - Scripts under `scripts/` are executable (`chmod +x` if not, and mention it).
4. If any framework script fails on this machine (for example on Windows), document the exact error and a working workaround in the report. Do not rewrite the scripts.

### Files you own (edit only these)
- `minicalc/__init__.py`
- `pytest.ini`
- `requirements-dev.txt`
- `.gitignore`
- `tests/test_package.py`
- `tests/golden/.gitkeep`
- `examples/.gitkeep`

### What NOT to touch
- Everything under `docs/` except your own status row and your report
- `scripts/` (verify only)
- Any other file under `minicalc/`
- Do not edit `docs/context/language-spec.md` or `docs/context/interface-contract.md`. If you find an ambiguity or contradiction in them, do not guess: describe it under "Flagged for APC / Operator Attention" in your report.
- Do not edit another task's row in `docs/tasks/status.md`, and do not reuse a decision ID that is not reserved for you.

## Verification & Acceptance Criteria
Your work is complete when ALL of these hold:
- [ ] `pytest -q` reports 1 passed.
- [ ] Git history is: one `chore(ARCH-002): import APC seed pack` commit, then your single task commit.
- [ ] All six tooling checks in step 3 are evidenced in the report.
- [ ] `pytest -q` passes (new tests included).
- [ ] No regression in previously merged tests.
- [ ] Every class you create or change has a docstring with an `Attributes:` section describing every class variable and instance attribute ([D-11]). Every module has a docstring. Every public function has a docstring.
- [ ] All assumptions verified against disk.

## Reserved Decision IDs
None reserved. If you must make a non-trivial design choice that the spec does not cover, do not invent a decision ID: describe the choice and your recommendation in the report and continue with the most conservative option.

## Output & Reporting Instructions
When the work is complete:
1. **Make exactly one commit** on `task/ARCH-002`: `git add <files> && git commit -m "chore(ARCH-002): bootstrap package skeleton and pytest config"`.
2. **Patch file:** `mkdir -p patch && git diff HEAD~1 > patch/ARCH-002-<agent-name>-bootstrap-skeleton.patch`.
3. **Report:** write `docs/reports/ARCH-002-<agent-name>-bootstrap-skeleton.md` following `docs/reports/TASK-TEMPLATE.md`. Keep it short. It needs: Executive Summary, Implementation Details, Verification & Test Evidence (paste the real `pytest -q` output), a verbatim unified Git Diff (from `git diff HEAD~1`, with index lines), and "Flagged for APC / Operator Attention".
4. **Status:** edit only your own row in `docs/tasks/status.md`: set `needs-review` and link the report.
5. **Decision log:** nothing to append (no ID reserved).
6. **Validate:** `./scripts/validate-report.py docs/reports/ARCH-002-<agent-name>-bootstrap-skeleton.md --require-patch`. Fix every issue.
7. **Bundle:** only if you changed shared docs, run `./scripts/apc-bundle.sh core`.
8. **Report back to lukexodus:** executive summary, test results, patch path, `git diff HEAD~1`, branch name, and worktree path. Do NOT merge, rebase, or delete the worktree.

Replace `<agent-name>` with your own name (for example `claude-code`, `gemini`, `opencode`, `cursor`).
