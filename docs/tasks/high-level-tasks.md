# High-Level Tasks & Roadmap — MiniCalc

Phased macro plan. Live state is in `docs/tasks/status.md`; this file changes only when the plan changes. Calendar: **today is Mon Oct 26, 2026; deadline Fri Oct 30, 2026, 17:00** (internal submit target: Oct 30, 12:00).

Token figures are rough estimates of agent *output* per task (code + tests + report), plus or minus 40%. Reading context and revision rounds add 30 to 50%.

---

## Phase 0 — Design Lock & Bootstrap (Mon Oct 26)

**Purpose:** freeze what is being built so parallel work cannot diverge.

| ID | Deliverable | Owner | Est. tokens |
| :--- | :--- | :--- | :--- |
| ARCH-001 | Design lock: `language-spec.md`, `interface-contract.md`, decisions [D-01..D-12], roadmap, status, task prompts | APC AI | done in planning session |
| ARCH-002 | Repo bootstrap: git init, drop in seed pack, package skeleton, `pytest` config, `.gitignore`, first commit, verify tooling | any agent | 1.5k |

**Exit gate:** seed pack committed; `pytest -q` runs (zero tests collected is acceptable); `./scripts/task-worktree.sh start TEST-000` works and is cleaned up; operator confirms the spec.

---

## Phase 1 — Shared Infrastructure & Contracts (Mon Oct 26 to Tue Oct 27 AM)

**Purpose:** put the shared vocabulary in code and prove the pipeline end to end before real features.

| ID | Deliverable | Depends on | Est. tokens |
| :--- | :--- | :--- | :--- |
| CORE-001 | `limits.py`, `errors.py`, `tokens.py`, `ast_nodes.py` + unit tests | ARCH-002 | 2.5k |
| CORE-002 | Golden-test harness (`tests/conftest.py`, `tests/test_golden.py`) + canonical format | CORE-001 | 2k |
| CORE-003 | Walking skeleton: stub lexer/parser/evaluator/environment + real `interpreter.py` facade; `42` runs end to end | CORE-001, CORE-002 | 2.5k |

**Exit gate:** golden test `smoke.mc` (`42` -> `OK 42`) passes through the full pipeline; facade API matches the contract exactly.

---

## Phase 2 — Parallel Feature Tracks (Tue Oct 27)

**Purpose:** five independent tracks, each in its own worktree, each owning separate files.

| ID | Track | Owns | Depends on | Est. tokens |
| :--- | :--- | :--- | :--- | :--- |
| FEAT-001 | Full lexer | `lexer.py`, `tests/test_lexer.py` | CORE-003 | 2.5k |
| FEAT-002 | Full parser | `parser.py`, `tests/test_parser.py` | CORE-003 | 3.5k |
| FEAT-003 | Evaluator, environment, built-ins | `evaluator.py`, `environment.py`, `builtins.py`, `tests/test_evaluator.py` | CORE-003 | 3.5k |
| FEAT-004 | REPL, CLI, display | `repl.py`, `display.py`, `__main__.py`, `main.py`, `tests/test_cli.py` | CORE-003 | 3k |
| FEAT-005 | Spec-derived golden cases (auditor role, different model lineage) | `tests/golden/*` | CORE-002 (spec only, not the code) | 3k |

**Exit gate:** each track passes its own tests against the contract; FEAT-005 cases exist for every spec table row.

---

## Phase 3 — Integration & Verification (Wed Oct 28)

| ID | Deliverable | Depends on | Est. tokens |
| :--- | :--- | :--- | :--- |
| INT-001 | Merge all tracks, run the full suite and golden cases, fix cross-stage mismatches (log in [D-15]) | FEAT-001..005 | 2k |
| INT-002 | Randomized differential test against a spec-derived oracle; independent audit report | INT-001 (oracle written earlier, from spec only) | 2.5k |

**Exit gate:** `pytest -q` fully green; all golden cases pass; differential test finds zero mismatches over at least 2,000 random expressions; manual REPL walkthrough recorded in the INT-001 report.

---

## Phase 4 — Documentation, Packaging & Release (Wed Oct 28 PM to Fri Oct 30)

| ID | Deliverable | Depends on | Est. tokens |
| :--- | :--- | :--- | :--- |
| DOC-001 | Docstrings with `Attributes:` on every class; `scripts/check_docs.py` | INT-001 (code stable) | 3k |
| DOC-002 | `README.md`, `docs/LANGUAGE.md` (grammar, semantics, PL evaluation criteria), `examples/*.mc`, presentation notes | spec; polish after INT-001 | 4k |
| DOC-003 | `scripts/make_submission.py`, verified clean unzip-and-run, upload checklist | DOC-001, DOC-002 | 2k |

**Exit gate:** `check_docs.py` passes; the submission ZIP unzips into an empty folder and `pytest -q` passes there; Drive link opens in an incognito window.

---

## Schedule

| Day | Target |
| :--- | :--- |
| Mon Oct 26 | ARCH-001 (done), ARCH-002, CORE-001, CORE-002. Stretch: CORE-003 |
| Tue Oct 27 | CORE-003 (if not done), FEAT-001 to FEAT-005 in parallel |
| Wed Oct 28 | INT-001, INT-002, DOC-001, DOC-002 draft |
| Thu Oct 29 | DOC-002 final, DOC-003, rehearse the demo, buffer for fixes |
| Fri Oct 30 | AM: final checks, build ZIP, upload to Drive, post link on MVLE. **Submit by 12:00.** Hard deadline 17:00 |

## Critical path

```
ARCH-002 -> CORE-001 -> CORE-003 -> FEAT-001/002/003 -> INT-001 -> DOC-001 -> DOC-003 -> submit
              CORE-002 ----^         FEAT-004, FEAT-005 ----^   DOC-002 ----^
```

## Cut line (if behind at end of Wed Oct 28)

Cut in this order, recording each in [D-16]. **Never cut:** error handling, the Attributes docs, packaging.
1. INT-002 differential test (keep the audit report only).
2. Breadth of FEAT-005 beyond one case per spec table row.
3. REPL meta-commands `:vars` and `:clear`.
4. Built-ins `min`, `max`, `gcd` (keep `abs`).
5. Comparison operators.

Any cut needs a spec edit by the APC AI so code, tests, and docs stay consistent.

## Assignment (operator fills in)

| Task | Suggested agent | Human owner |
| :--- | :--- | :--- |
| ARCH-002, CORE-001, CORE-003, FEAT-003 | Claude Code (lead implementer) | TBD |
| FEAT-001, FEAT-002 | Claude Code or opencode | TBD |
| FEAT-004, DOC-001, DOC-002, DOC-003 | opencode / Cursor | TBD |
| CORE-002, FEAT-005, INT-002 | Gemini (independent auditor lineage) | TBD |
| INT-001 | Claude Code | TBD |
