# AGENTS.md

You are a local coding agent (Claude Code, Gemini, opencode, Cursor, or similar)
working on this repository. **Before doing anything else, read
`docs/context/complete-context.md` in full.** It explains what this project
is, how work is coordinated, and where everything lives. This file covers
the operational rules for working in this repo.

## The one rule that matters most

**You have no memory across sessions. Neither does the AI planning your
tasks (the "APC AI" — Analyzer, Planner, Controller; see `complete-context.md`).**
Anything you learn, decide, or build that isn't written into this repo's files
is lost the moment this session ends. Write it down. When in doubt, write it
down anyway — a redundant note costs almost nothing; a lost finding costs a
future agent having to re-derive it from scratch, or worse, silently redoing
work already done.

**This repo is the sole source of truth, always — never the APC AI, never
any chat transcript, never any AI's stated memory of a past conversation.**
The APC AI has no filesystem access and no persistent memory across its own
sessions; if something it says ever conflicts with what's actually in a
repo file, the repo file is correct and the APC AI's statement is stale.
This applies to you too: if a task prompt or a piece of relayed context
seems to assume something about this repo that you can check directly (you
have filesystem access; the APC AI does not), check it, and say so in your
report if it was wrong — don't silently defer to a prompt's assumption over
what you can see yourself.

## Before editing a shared doc — confirm you have its live content

A delta is only trustworthy if it's computed against the file's actual
current state. **If you (or the APC AI) are about to edit a shared doc
(`docs/decisions/decision-log.md`, `docs/tasks/status.md`, `AGENTS.md`,
`docs/context/complete-context.md`, or anything else multiple agents touch)
and don't have freshly-verified current content for it — not "probably still looks
like this," actually current — get that content first.** For a local agent,
this is trivial: just read the file, since you have live filesystem access.
For the APC AI specifically, which has NO filesystem access, this means asking
lukexodus to paste or upload the file's current content before proposing
an edit, rather than editing from whatever content it last saw.

Skipping this check produces a diff that looks authoritative but isn't —
it's a diff against a remembered guess, not the real file, and applying it
risks silently reverting or conflicting with a change another agent already
made.

## Reporting changes efficiently — send deltas, not full files

**When you edit or add to a file that already exists in the repo (shared
docs, implementation code, tests), relay your change back to lukexodus /
the APC AI as a diff or a clear before/after excerpt of just the changed part —
not the full resulting file.** A full-file paste forces whoever's reading it to
hunt for what actually changed, which exhausts context windows and defeats the
purpose of scannable reports. A standard unified diff (`git diff` output) is the
canonical format for this.

**Exceptions, where a full file is appropriate:**
- You created a brand-new file (there's no "before" to diff against).
- The change is a near-total rewrite where a diff would be longer and
  harder to read than the whole file.
- You're asked explicitly for full content.

If you're ever unsure which applies, default to the diff.

## Before starting any task

0. If you will run alongside another task or agent, follow 'Parallel work and worktrees' first.
1. Read `docs/context/complete-context.md` if you haven't already this session.
2. Check `docs/tasks/status.md` for the current state of all tasks — don't start
   work that's already marked `done` or `in-progress` by someone else.
3. Check `docs/decisions/decision-log.md` for any past decisions relevant to your
   task. If you must make an architectural or implementation choice not covered,
   note the reserved decision ID from your prompt and record it in the log before finishing.
4. Run `./scripts/apc-bundle.sh --list` or inspect `docs/context/repo-tree.txt` if
   you need orientation on existing repository layout.

## Parallel work and worktrees

When multiple tasks run concurrently:
1. **Check status:** Run `git worktree list` and `git status --short`. If another task
   is in progress in this checkout, or the working tree is dirty with files you did not
   create, do not start in the main checkout.
2. **Dedicated task worktrees:** Any task running concurrently must use its own
   worktree: `git worktree add ../minicalc-<TASK-ID> -b task/<TASK-ID>` from
   the main checkout (or via `./scripts/task-worktree.sh start <TASK-ID>`).
   Use the exact task ID from `docs/tasks/status.md`. Never reuse a worktree across tasks.
3. **Shared doc editing:** Only one agent may edit a given shared doc (`status.md`,
   `decision-log.md`, `AGENTS.md`) at a time. In a worktree, edit only your own rows
   and your own appended decision entries, and re-read the file immediately before writing.
4. **Reserved decision IDs:** Decision IDs are reserved per task by the APC, not
   chosen on the fly by the agent. If a reserved ID is already used in the file, stop
   and report the conflict; do not renumber unilaterally.
5. **Verbatim diffs:** Diffs pasted into a report must come from `git diff` run in the
   worktree that made the change, and must include index lines. Never retype diffs.
6. **Handoff upon completion:** When the task is finished: do not merge, rebase, or
   delete the worktree yourself. Leave the branch and worktree for lukexodus,
   and state the branch name and worktree path in your report. (The operator audits,
   merges, and cleans up via `./scripts/task-worktree.sh merge <TASK-ID>` from the main checkout).
7. **Protected operations:** Never run `git worktree remove`, `git clean -fd`,
   `git reset --hard`, `git checkout --` or `git stash` in a worktree you did not create
   in this session, or in the main checkout without explicit instructions.
8. **Shared `.git` safety:** Worktrees share the `.git` directory. Never commit a file
   that exists only in a worktree's untracked state without listing it in the report.
9. **Clean live runs:** Before executing tests or benchmarks, confirm that the run uses
   a clean worktree at the commit the report names.

## While working

- If a prompt or task description seems to assume something about a file's format or
  content that you can verify directly, **verify it** before proceeding, and report
  the result even if it confirms the assumption was correct. Silence reads as
  "nobody checked."
- If you find something that contradicts what's written in `docs/context/complete-context.md`,
  `docs/decisions/decision-log.md`, or existing specifications, do not silently work
  around it. Note the discrepancy clearly in your report.
- Run tests regularly using `pytest -q`.

## After finishing any task (The 4 Unit-of-Work Deliverables)

For every completed unit of work, you must produce four concrete deliverables:

1. **Commit your changes:**
   - Stage and commit all task changes on your task branch/worktree with a concise, conventional message:
     ```bash
     git add <modified/new files>
     git commit -m "<type>(<task-id>): <concise description of work>"
     ```
   - Never leave your worktree with uncommitted changes upon task completion.

2. **Generate the patch file (in `patch/`):**
   - Export a standalone patch file representing the unit of work:
     ```bash
     mkdir -p patch
     git diff HEAD~1 > patch/<task-id>-<agent-name>-<short-slug>.patch
     ```
   - This provides an inspectable, portable patch file stored directly in the repository.

3. **Write the report file (`docs/reports/`):**
   - Location: `docs/reports/<task-id>-<agent-name>-<short-slug>.md`
     - `<task-id>` matches the ID in `docs/tasks/status.md` (e.g., `CORE-001`)
     - `<agent-name>` is whichever agent you are (e.g. `claude-code`, `gemini`, `opencode`)
     - `<short-slug>` is a concise hyphenated summary (e.g. `add-auth-middleware`)
     - Example: `docs/reports/CORE-001-claude-code-add-auth-middleware.md`
   - **Never append to another agent's report file.** One file per completed task, written once by the agent that completed it.
   - **What to include:** Executive summary, implementation details, test outputs/verification, unified git diff, patch file reference, and items flagged for APC AI attention.
   - **Update `docs/tasks/status.md`** to reflect your task's new status (`done`, `blocked`, or `needs-review`) with a link to your report file.
   - **Record decisions in `docs/decisions/decision-log.md`** under the reserved ID.
   - **Validate your report:** Run `./scripts/validate-report.py` to ensure your report file passes structure checks, diff checks, and status alignment before handoff.

4. **Build a fresh bundle if needed:**
   - If this task modified shared contracts, context documents, multiple files, or if requested by the APC AI, package an updated snapshot:
     ```bash
     ./scripts/apc-bundle.sh [profile]
     ```
   - This ensures the external APC AI can be refreshed with live file state upon receiving the handoff.

## Recommended agent-role split

- **Lead Implementation Agent (e.g., Claude Code):** Best for first-draft implementation
  of core infrastructure, complex features, refactoring, and integration harness.
- **Review / Verification Agent (e.g., Gemini):** Best for independent review, edge-case
  auditing, test suite verification, and cross-checking claims against filesystem ground truth.
- **Specialized / Alternate Agents (e.g., opencode, Cursor):** Modular tasks, doc generation,
  parallel subcomponents.

## Standalone prompts

You may receive a task as a "standalone prompt" written by the APC AI and relayed by
lukexodus. These prompts assume zero memory of prior conversations — treat them
as self-contained instructions. If a prompt assumes context you don't have and can't find
in this repo, say so in your report rather than guessing.
