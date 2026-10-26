# START HERE — MiniCalc APC seed pack

Produced by the APC AI in planning session 1 (Mon Oct 26, 2026). This folder is the repository root, ready to commit.

## Do this now (about 10 minutes)
1. Create your project repo folder (for example `minicalc`) and copy **everything in this folder** into it, including hidden files.
2. Read `docs/context/language-spec.md` and `docs/tasks/high-level-tasks.md`. Reply to the APC AI with any change you want. Changes go through the APC AI so spec, contract, and prompts stay consistent.
3. Open `docs/prompts/ARCH-002.md`, paste it into a local coding agent (Claude Code recommended) at the repo root, and let it run. It creates the git history and verifies the tooling.
4. Then run CORE-001 and CORE-002 (they can run in parallel worktrees), then CORE-003. Each prompt is in `docs/prompts/<TASK-ID>.md`.
5. After each task: `./scripts/task-worktree.sh handoff <TASK-ID>`, send the report summary and `git diff` to the APC AI, then `./scripts/task-worktree.sh merge <TASK-ID>`.

## Reading order for any new APC session
`docs/prompts/STANDALONE-ADOPTION-PROMPT.md` first, then upload the core bundle: `./scripts/apc-bundle.sh core` (about 20k tokens).

## Delete this file after step 3 if you do not want it in the repo (it is not shipped in the submission ZIP).
