# TASK: CORE-002 — Golden-test harness

## Role & Worktree Instructions
- **Assigned agent:** Gemini (independent auditor lineage) or any
- **Task ID:** CORE-002
- **Depends on:** CORE-001
- **Worktree:** from the main checkout run `./scripts/task-worktree.sh start CORE-002`, then work only inside `../minicalc-CORE-002` on branch `task/CORE-002`. Never edit the main checkout.

## Orientation & Required Reading
Before writing any code, read these in order:
1. `docs/context/complete-context.md` (project background and rules)
2. `docs/tasks/status.md` (confirm CORE-002 is `open` and that every dependency below is `done`; if a dependency is not done, STOP and tell lukexodus)
3. `docs/decisions/decision-log.md` ([D-01] through [D-16]; never re-litigate a settled decision)
4. `docs/context/language-spec.md` (authoritative language behavior)
5. `docs/context/interface-contract.md` (authoritative Python signatures and file ownership)

Verify every assumption in this prompt against the files on disk (`ls`, `cat`, `grep`). If the prompt and the repository disagree, the repository is right: say so in your report.

## Context & Objectives
Golden tests are the project's main correctness net and the demo script for the presentation. Their format is fixed in `docs/context/interface-contract.md` section 12. This task builds the runner only; FEAT-005 writes the real cases. The harness must not depend on how the lexer, parser, or evaluator are written, only on the public `Interpreter.run_source` facade (built in CORE-003).

## Specific Scope & Deliverables
1. **`tests/golden_format.py`:** `canonical_line(outcome) -> str | None`, duck-typed on `outcome.result` / `outcome.error`:
   - error present: `outcome.error.canonical()`.
   - `result.kind == "value"`: `OK <value>`.
   - `result.kind == "assign"`: `OK <name>=<value>`.
   - `result.kind == "empty"`: return `None` (no output line).
2. **`tests/test_golden.py`:**
   - At module top: `pytest.importorskip("minicalc.interpreter")` so the file is skipped until CORE-003 lands.
   - Discover `tests/golden/*.mc` sorted by name; parametrize one test per file (ids = file stem).
   - Read the `.mc` as UTF-8, run it through ONE fresh `Interpreter().run_source(text)`, build the actual list with `canonical_line`, drop `None`s.
   - Read `<stem>.out` (a missing `.out` is a test failure with a clear message), split lines, ignore trailing blank lines.
   - On mismatch, fail with a readable report: for every differing index show the expected line, the actual line, the file line number, and the source text of that line. Also fail if the counts differ.
3. **`tests/test_golden_format.py`:** unit tests for `canonical_line` using `types.SimpleNamespace` stand-ins for results and real `MiniCalcError` subclasses from CORE-001 (value, assign, empty, each error kind).
4. **Smoke case:** `tests/golden/smoke.mc` containing the single line `42`, and `tests/golden/smoke.out` containing `OK 42`.
5. **`tests/conftest.py`:** only a `GOLDEN_DIR` constant (a `pathlib.Path`) and a `read_golden_pair(stem)` helper if you need one. Keep it tiny.

### Files you own (edit only these)
- `tests/golden_format.py`
- `tests/test_golden.py`
- `tests/test_golden_format.py`
- `tests/conftest.py`
- `tests/golden/smoke.mc`
- `tests/golden/smoke.out`

### What NOT to touch
- `minicalc/` (read-only for you)
- Any other file under `tests/golden/`
- Do not edit `docs/context/language-spec.md` or `docs/context/interface-contract.md`. If you find an ambiguity or contradiction in them, do not guess: describe it under "Flagged for APC / Operator Attention" in your report.
- Do not edit another task's row in `docs/tasks/status.md`, and do not reuse a decision ID that is not reserved for you.

## Verification & Acceptance Criteria
Your work is complete when ALL of these hold:
- [ ] `test_golden_format.py` passes now.
- [ ] `test_golden.py` is reported as skipped (module not found) before CORE-003 and shows 1 collected case `smoke` after CORE-003 is merged.
- [ ] A deliberately wrong `.out` (try it locally, do not commit it) produces a readable diff that names the file line and source text.
- [ ] `pytest -q` passes (new tests included), except for the items under "Known failing" below.
- [ ] No regression in previously merged tests.
- [ ] Every class you create or change has a docstring with an `Attributes:` section describing every class variable and instance attribute ([D-11]). Every module has a docstring. Every public function has a docstring.
- [ ] All assumptions verified against disk.

**Known failing:** `tests/test_golden.py` is skipped until CORE-003 is merged. That is expected.

## Reserved Decision IDs
None reserved. If you must make a non-trivial design choice that the spec does not cover, do not invent a decision ID: describe the choice and your recommendation in the report and continue with the most conservative option.

## Output & Reporting Instructions
When the work is complete:
1. **Make exactly one commit** on `task/CORE-002`: `git add <files> && git commit -m "test(CORE-002): add golden-test harness and smoke case"`.
2. **Patch file:** `mkdir -p patch && git diff HEAD~1 > patch/CORE-002-<agent-name>-golden-harness.patch`.
3. **Report:** write `docs/reports/CORE-002-<agent-name>-golden-harness.md` following `docs/reports/TASK-TEMPLATE.md`. Keep it short. It needs: Executive Summary, Implementation Details, Verification & Test Evidence (paste the real `pytest -q` output), a verbatim unified Git Diff (from `git diff HEAD~1`, with index lines), and "Flagged for APC / Operator Attention".
4. **Status:** edit only your own row in `docs/tasks/status.md`: set `needs-review` and link the report.
5. **Decision log:** nothing to append (no ID reserved).
6. **Validate:** `./scripts/validate-report.py docs/reports/CORE-002-<agent-name>-golden-harness.md --require-patch`. Fix every issue.
7. **Bundle:** only if you changed shared docs, run `./scripts/apc-bundle.sh core`.
8. **Report back to lukexodus:** executive summary, test results, patch path, `git diff HEAD~1`, branch name, and worktree path. Do NOT merge, rebase, or delete the worktree.

Replace `<agent-name>` with your own name (for example `claude-code`, `gemini`, `opencode`, `cursor`).
