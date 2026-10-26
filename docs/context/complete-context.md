# Complete Context — MiniCalc

Primary orientation file for the APC AI (Analyzer, Planner, Controller) and all local coding agents. Read this before any task spec.

---

## 1. What this project is

MiniCalc is a small programming language for integer arithmetic: lexer, recursive-descent parser, AST evaluator, and an interactive REPL, written in Python. It is the final project for **CMPSC 132: Programming Languages** (1st semester, A.Y. 2025-2026).

### Core Objectives
1. **Primary goal:** a working language that processes integer arithmetic, rejects malformed input with clear errors, prints correct results, follows the PL evaluation criteria, and is fully documented.
2. **Success metrics (graded by the course rubric, 5 criteria x 20 pts):**
   - *Requirements:* 90-100% of requirements met.
   - *Delivery:* submitted **before the deadline**. Each hour late costs a rubric band.
   - *Documentation:* every class variable described, clearly and effectively.
   - *Runtime:* no errors, excellent prompts, good use of symbols and spacing in output.
   - *Presentation:* deep understanding, all requirements correct, advanced features or optimizations.
3. **Key constraints:**
   - **Hard deadline: Oct 30, 2026, 17:00.** Internal target: submitted by Oct 30, 12:00.
   - Group of 3 to 5 students.
   - Submission is a ZIP of source code with documentation, shared via Google Drive link posted in the MVLE Course Final Project Submission Thread.
   - Runtime must work with a plain `python` install: standard library only ([D-02]).

---

## 2. System architecture & components

Pipeline, one statement per line:

```
source line -> Lexer -> [Token] -> Parser -> AST -> Evaluator(Environment) -> int
                                                          ^
                              Interpreter (facade) wraps all stages; Repl/CLI use only the facade
```

- **`minicalc/`**: implementation (see `docs/context/interface-contract.md` section 1 for the per-file owner map).
- **`tests/`**: unit tests, golden tests (`tests/golden/*.mc` + `.out`), differential test.
- **`docs/`**: context, tasks, decisions, reports, prompts, final user documentation.
- **`scripts/`**: framework tooling (worktrees, bundles, validators) plus `check_docs.py` and `make_submission.py`.

## 3. Interfaces and contracts (authoritative)

| Document | Defines |
| :--- | :--- |
| `docs/context/language-spec.md` | Grammar, precedence, integer model, operator semantics, errors, CLI behavior |
| `docs/context/interface-contract.md` | Python classes, signatures, file ownership, golden-test format |
| `docs/decisions/decision-log.md` | Locked decisions [D-01] to [D-15], [D-17], and [D-18]; [D-16] reserved for DOC-003 |

If code disagrees with these, the code is wrong unless a newer decision says otherwise. Report discrepancies; do not silently work around them.

## 4. Project structure

```text
├── AGENTS.md
├── main.py                       # shim: python main.py
├── minicalc/                     # source package
├── tests/
├── examples/                     # sample .mc programs (DOC-002)
├── docs/
│   ├── context/                  # this file, language-spec.md, interface-contract.md, ...
│   ├── tasks/                    # high-level-tasks.md, status.md
│   ├── decisions/decision-log.md
│   ├── reports/                  # one report per task
│   ├── prompts/                  # standalone task prompts (one file per task ID)
│   └── guide/
├── patch/
└── scripts/
```

## 5. The coordination model

Operator **lukexodus** relays work between the **APC AI** (external chat, no filesystem access, plans and reviews) and **local coding agents** (full filesystem, zero memory across sessions). The repository is the sole source of truth. Changes travel as unified diffs. Concurrent tasks use worktrees `task/<TASK-ID>`. Every task ends with a report that passes `./scripts/validate-report.py`.

### Lean-mode adaptations for a 4-day schedule
- Reports stay short (the validator's required sections only). Quality of the code matters more than report prose.
- Skip `apc-bundle.sh --tokens` unless a bundle upload fails. Use `core` bundles only.
- Merge order follows task dependencies in `docs/tasks/high-level-tasks.md`. Merge small and often.
- The Google Drive submission ZIP excludes governance artifacts by default ([D-12]).

## 6. Open items & active risks

- **R1 Schedule:** 4 days total. Cut line is defined in `high-level-tasks.md` section "Cut line".
- **R2 Parallel-edit conflicts:** mitigated by one-owner-per-file ([interface-contract] section 1).
- **R3 Rubric drift:** documentation criterion requires every class variable described. Enforced by `scripts/check_docs.py` (DOC-001).
- **R4 Late delivery:** upload and link-sharing check scheduled on Oct 30 morning, not afternoon.
- **Open:** group size and member-to-task assignment (operator to fill in `high-level-tasks.md` section "Assignment").
