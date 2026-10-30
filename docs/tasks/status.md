# Task Status

Live tracker. The plan lives in `docs/tasks/high-level-tasks.md`. Update your own row when your task status changes.

**Status values:** `open`, `in-progress` (note agent/branch), `blocked` (state the blocker), `needs-review` (waiting for APC / lukexodus), `done` (must link the report).

Last updated: 2026-10-26 (APC planning session 1).

---

## Phase 0 — Design Lock & Bootstrap

Status: **done**

| ID | Task | Status | Notes / Report |
| :--- | :--- | :--- | :--- |
| ARCH-001 | Design lock: spec, interface contract, decisions D-01..D-12, roadmap, prompts | `done` | Accepted by APC review; spec confirmed by operator |
| ARCH-002 | Repo bootstrap, package skeleton, pytest config, first commit | `done` | Report: `docs/reports/ARCH-002-claude-code-bootstrap-skeleton.md`. Merged to master; all tooling checks pass on Python 3.14.8 / pytest 9.1.1 |

## Phase 1 — Shared Infrastructure & Contracts

Status: **done**

| ID | Task | Status | Notes / Report |
| :--- | :--- | :--- | :--- |
| CORE-001 | `limits.py`, `errors.py`, `tokens.py`, `ast_nodes.py` + tests | `done` | Report: `docs/reports/CORE-001-claude-code-shared-vocabulary.md`. Merged; 42 tests pass; verified on Python 3.10 and 3.12 by APC |
| CORE-002 | Golden-test harness | `done` | Report: `docs/reports/CORE-002-claude-code-golden-harness.md`. Merged; skip guard requires a genuinely absent interpreter |
| CORE-003 | Walking skeleton and `Interpreter` facade | `done` | Report: `docs/reports/CORE-003-claude-code-walking-skeleton.md`. Merged; 77 passed, 0 skipped |

## Phase 2 — Parallel Feature Tracks

Status: **done**

| ID | Task | Status | Notes / Report |
| :--- | :--- | :--- | :--- |
| FEAT-001 | Full lexer | `done` | Report: `docs/reports/FEAT-001-claude-code-lexer.md`. Merged |
| FEAT-002 | Full parser | `done` | Report: `docs/reports/FEAT-002-claude-code-parser.md`. Merged; [D-13] logged |
| FEAT-003 | Evaluator, environment, built-ins | `done` | Report: `docs/reports/FEAT-003-claude-code-evaluator.md`. Merged |
| FEAT-004 | REPL, CLI, display | `done` | Report: `docs/reports/FEAT-004-claude-code-repl-cli.md`. Merged; [D-14] logged |
| FEAT-005 | Spec-derived golden cases | `done` | Report: `docs/reports/FEAT-005-golden-cases.md`. Merged; ans ruling applied |

## Phase 3 — Integration & Verification

Status: **open**

| ID | Task | Status | Notes / Report |
| :--- | :--- | :--- | :--- |
| INT-001 | Integrate all tracks, full-suite green | `done` | Report: `docs/reports/INT-001-claude-code-integration.md`. Merged `c3a40a3`; accepted by APC audit; [D-15] logged |
| INT-002 | Differential test and independent audit | `done` | Report: `docs/reports/INT-002-claude-code-differential-audit.md`. Merged; accepted; 5,600 comparisons + 160 state lines, zero mismatches; 3 agent mutants + 4 APC mutants detected |
| FIX-001 | Post-integration fixes: `ans` help wording, script-mode stream order | `done` | Report: `docs/reports/FIX-001-claude-code-post-integration-fixes.md`. Merged `0b5b9b9`; accepted; [D-17] logged |
| FIX-002 | Remaining stale `ans` wording and context-doc decision state | `done` | Report: `docs/reports/FIX-002-claude-code-remaining-ans-wording.md`. Merged `78d4260`; accepted by APC audit; [D-18] logged |

## Phase 4 — Documentation, Packaging & Release

Status: **open**

| ID | Task | Status | Notes / Report |
| :--- | :--- | :--- | :--- |
| DOC-001 | Class `Attributes:` docstrings and `check_docs.py` | `needs-review` | Report: `docs/reports/DOC-001-opencode-class-docs.md`. Checker reports 0 violations on the merged tree (28 classes, 29 functions); 457 tests pass (439 pre-existing unchanged + 18 new) |
| DOC-002 | README, LANGUAGE.md, examples, presentation notes | `open` | Prompt: `docs/prompts/DOC-002.md` |
| DOC-003 | Submission ZIP builder and verified delivery | `open` | Prompt: `docs/prompts/DOC-003.md`. Reserved [D-16] |
