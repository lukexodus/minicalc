# Helper Scripts Guide — MiniCalc

This directory contains automation utilities that enforce the APC + Local Agent operational protocol.

---

## 1. `apc-bundle.sh` — Context Packaging Utility

Packages repository files into self-describing, verifiable `.tar.gz` archives for upload to the external APC AI session.

### Common Commands:
```bash
# Preview default 'core' bundle files and sizes
./scripts/apc-bundle.sh --list

# Estimate token count of the bundle
./scripts/apc-bundle.sh --tokens

# Package the core bundle
./scripts/apc-bundle.sh

# Package the dev bundle with an ad hoc file
./scripts/apc-bundle.sh dev --add path/to/extra-file.py

# Package including recent task reports
./scripts/apc-bundle.sh --with-reports
```

### Safety Features:
- Aborts on missing files.
- Automatically excludes secrets (`.env*`, `*.key`, `*.pem`, `*secret*`, `*token*`).
- Excludes large build and artifact folders (`.git/`, `.venv/`, `node_modules/`, `dist/`).
- Generates `MANIFEST.txt` with SHA256 hashes, timestamps, and git status.

---

## 2. `task-worktree.sh` — Worktree Lifecycle Helper

Enforces worktree isolation when running multiple local agents or tasks in parallel.

### Common Commands:
```bash
# Create an isolated task worktree and branch
./scripts/task-worktree.sh start CORE-001

# Inspect active worktrees
./scripts/task-worktree.sh list

# Review status inside a worktree
./scripts/task-worktree.sh status CORE-001

# Generate clean git diff from a worktree
./scripts/task-worktree.sh diff CORE-001

# Validate worktree state before operator commit
./scripts/task-worktree.sh handoff CORE-001

# Safely audit, merge worktree to current branch, and clean up
./scripts/task-worktree.sh merge CORE-001

# Clean up worktree manually after merge (if not using merge command)
./scripts/task-worktree.sh remove CORE-001
```

---

## 3. `validate-report.py` — Report Linter & Verification

Verifies that local agent task reports conform to the required schema, match `docs/tasks/status.md`, and contain valid unified git diffs.

### Common Commands:
```bash
# Validate the most recently written report:
./scripts/validate-report.py

# Validate a specific report file:
./scripts/validate-report.py docs/reports/CORE-001-agent-title.md

# Validate all reports in docs/reports/:
./scripts/validate-report.py --all
```

---

## 4. `manage-decisions.py` — Decision ID Allocator & Log Inspector

Prevents decision ID collisions when multiple parallel worktrees operate concurrently.

### Common Commands:
```bash
# Show next available Decision ID:
./scripts/manage-decisions.py next

# List all recorded decision IDs:
./scripts/manage-decisions.py list

# Check if a specific ID is available:
./scripts/manage-decisions.py check --id 42

# Reserve an ID in decision-log.md for an upcoming task:
./scripts/manage-decisions.py reserve --title "Select PostgreSQL over SQLite"
```
