# Complete Context — MiniCalc

Welcome to MiniCalc. This document is the primary orientation file for both
the APC AI (Analyzer, Planner, Controller) and all local coding agents. Read this
before reading individual task specs.

---

## 1. What this project is

MiniCalc is a small integer-arithmetic programming language (lexer, recursive-descent parser, evaluator, REPL) built in Python for the CMPSC 132 Programming Languages final project.

### Core Objectives
1. **Primary Goal:** [Specify the main deliverable or objective]
2. **Success Metrics:** [Define quantitative or qualitative success criteria]
3. **Key Constraints:** [Tech stack limits, performance budgets, dependencies]

---

## 2. System Architecture & Components

[Provide an architectural overview of how the system is organized. Detail the core modules or layers.]

- **`minicalc`**: Core implementation logic.
- **`tests/`**: Unit, integration, and conformance suites.
- **`docs/`**: Context, tasks, decision records, and per-task reports.
- **`scripts/`**: Automation, deployment, bundling, and workflow helpers.

---

## 3. Data Sources, Interfaces, and External Contracts

[Document key data formats, schemas, API contracts, or protocols that agents must adhere to.]
- Canonical schemas or data structures
- Input/output contracts
- External APIs or hardware requirements

---

## 4. Project Structure & Where Things Live

```text
├── AGENTS.md                   # Operational constitution for local agents
├── docs/
│   ├── context/
│   │   ├── complete-context.md # This orientation document
│   │   ├── apc-handoff-template.md # Template for inter-session APC handoffs
│   │   ├── apc-bundle-quickref.md  # Bundle command reference
│   │   └── repo-tree.txt       # Auto-generated snapshot of repository layout
│   ├── tasks/
│   │   ├── high-level-tasks.md # Phased macro plan & roadmap
│   │   └── status.md           # Live per-task status tracker
│   ├── decisions/
│   │   └── decision-log.md     # Append-only immutable architectural decision log
│   ├── reports/                # Completed task reports (one per task)
│   └── prompts/                # Standalone prompt archive
├── scripts/
│   ├── apc-bundle.sh           # Safe packaging tool for APC context bundles
│   └── task-worktree.sh        # Git worktree management script for parallel tasks
├── minicalc                 # Source code
└── tests/                      # Automated test suites
```

---

## 5. The Coordination Model (Why this setup exists)

This project is coordinated by lukexodus relaying work between two distinct entities:

1. **The APC AI ("Analyzer, Planner, Controller")**:
   - High-reasoning AI running in an external chat or API session (Claude Web, ChatGPT, Gemini, etc.).
   - Has **NO filesystem access** to this repository.
   - Plans phases, designs architecture, inspects reports/diffs, enforces consistency, reserves decision IDs, and generates **STANDALONE PROMPTS**.
   - Ephemeral memory: Context resets across sessions or when credit limits are reached. Handoffs are managed via `apc-handoff-template.md`.
2. **Local Coding Agents** (Claude Code, Gemini, opencode, Cursor, etc.):
   - Run on lukexodus's local machine with **full filesystem access and CLI execution**.
   - Implement features, run tests, verify assumptions against actual files, and generate unified git diffs.
   - Ephemeral memory: Each invocation is zero-memory. Agents must consult repo files to discover state.

### Key Operational Rules:
- **The Repo is the Sole Source of Truth (SSOT):** No chat transcript or AI memory is authoritative. If a statement conflicts with what is on disk, the disk is right.
- **Deltas, Not Full Files:** Code and documentation changes are reported as unified git diffs (`git diff`) to conserve context and prevent merge hazards.
- **Mandatory Reporting:** Every completed task must generate a dedicated report file in `docs/reports/`. An undocumented task is equivalent to a task that never happened.
- **Isolated Parallel Worktrees:** Concurrent tasks must operate in dedicated git worktrees (`task/<TASK-ID>`).

---

## 6. Open Items & Active Risks

[List known ambiguities, unresolved design choices, or active risks being investigated.]
- Open Item 1: ...
- Open Item 2: ...
