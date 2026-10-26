# Task Status

Live tracker. The plan lives in `docs/tasks/high-level-tasks.md`. Update your own row when your task status changes.

**Status values:** `open`, `in-progress` (note agent/branch), `blocked` (state the blocker), `needs-review` (waiting for APC / lukexodus), `done` (must link the report).

Last updated: 2026-10-26 (APC planning session 1).

---

## Phase 0 — Design Lock & Bootstrap

Status: **in progress**

| ID | Task | Status | Notes / Report |
| :--- | :--- | :--- | :--- |
| ARCH-001 | Design lock: spec, interface contract, decisions D-01..D-12, roadmap, prompts | `needs-review` | Delivered by APC AI in the seed pack. lukexodus reviews, then marks `done`. No agent report required |
| ARCH-002 | Repo bootstrap, package skeleton, pytest config, first commit | `needs-review` | Report: `docs/reports/ARCH-002-claude-code-bootstrap-skeleton.md`. All tooling checks pass on Python 3.14.8 / pytest 9.1.1 |

## Phase 1 — Shared Infrastructure & Contracts

Status: **open**

| ID | Task | Status | Notes / Report |
| :--- | :--- | :--- | :--- |
| CORE-001 | `limits.py`, `errors.py`, `tokens.py`, `ast_nodes.py` + tests | `open` | Prompt: `docs/prompts/CORE-001.md` |
| CORE-002 | Golden-test harness | `open` | Prompt: `docs/prompts/CORE-002.md` |
| CORE-003 | Walking skeleton and `Interpreter` facade | `open` | Prompt: `docs/prompts/CORE-003.md`. Exit gate for Phase 1 |

## Phase 2 — Parallel Feature Tracks

Status: **open**

| ID | Task | Status | Notes / Report |
| :--- | :--- | :--- | :--- |
| FEAT-001 | Full lexer | `open` | Prompt: `docs/prompts/FEAT-001.md` |
| FEAT-002 | Full parser | `open` | Prompt: `docs/prompts/FEAT-002.md`. Reserved [D-13] |
| FEAT-003 | Evaluator, environment, built-ins | `open` | Prompt: `docs/prompts/FEAT-003.md` |
| FEAT-004 | REPL, CLI, display | `open` | Prompt: `docs/prompts/FEAT-004.md`. Reserved [D-14] |
| FEAT-005 | Spec-derived golden cases | `open` | Prompt: `docs/prompts/FEAT-005.md` |

## Phase 3 — Integration & Verification

Status: **open**

| ID | Task | Status | Notes / Report |
| :--- | :--- | :--- | :--- |
| INT-001 | Integrate all tracks, full-suite green | `open` | Prompt: `docs/prompts/INT-001.md`. Reserved [D-15] |
| INT-002 | Differential test and independent audit | `open` | Prompt: `docs/prompts/INT-002.md` |

## Phase 4 — Documentation, Packaging & Release

Status: **open**

| ID | Task | Status | Notes / Report |
| :--- | :--- | :--- | :--- |
| DOC-001 | Class `Attributes:` docstrings and `check_docs.py` | `open` | Prompt: `docs/prompts/DOC-001.md` |
| DOC-002 | README, LANGUAGE.md, examples, presentation notes | `open` | Prompt: `docs/prompts/DOC-002.md` |
| DOC-003 | Submission ZIP builder and verified delivery | `open` | Prompt: `docs/prompts/DOC-003.md`. Reserved [D-16] |
