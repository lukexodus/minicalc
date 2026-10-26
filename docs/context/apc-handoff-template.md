# APC-to-APC Handoff Template

Use this template when an APC AI session is ending (credit limit reached, context window filled, or session reset) and a new APC AI instance needs to pick up the work. The new instance will have NO memory of the past conversation — this document, plus the repo files it points to, is the entire transfer.

**Fill in every section below.** A handoff that skips a section because "nothing happened there" should state so explicitly — leaving a section blank is ambiguous between "nothing happened" and "forgot to fill it in."

---

## 1. Orientation (Copy verbatim into first prompt)

You are the APC AI ("Analyzer, Planner, Controller") for MiniCalc. You have NO filesystem access to the project repo. You coordinate by writing standalone prompts that lukexodus relays to local coding agents (Claude Code, Gemini, opencode, Cursor) running on their machine, who DO have filesystem access and report back to you via pasted reports and git diffs.

Read, in this order, before taking any action:

1. `docs/context/complete-context.md` — full project orientation
2. `docs/decisions/decision-log.md` — every past decision and why
3. `docs/tasks/status.md` — live tracker of what is actually done right now
4. This document's Sections 2–5 below — what changed in the ending session

If lukexodus has pasted current file contents or uploaded an APC bundle archive, inspect those primary artifacts directly before asking for re-pastes.

---

## 2. What Changed This Session

[Fill in: a concise, plain-language summary of what was decided, built, discovered, or corrected during the session that is ending. Reference specific decision-log IDs [D-xx] or task IDs [TASK-xxx].]

---

## 3. What's Currently In-Flight (Active / Blocked)

[Fill in: any task that is currently `in-progress` or `blocked` in `docs/tasks/status.md`. Provide the tactical context so the incoming APC instance knows exactly what is happening beyond the one-line status entry. If nothing is in-flight, write "None — all current tasks are settled."]

---

## 4. What the New APC Instance Should Do First

[Fill in: the concrete, immediate next step — not "continue development", but an actionable instruction. Example: "Task INFRA-002 report from Gemini is pasted below; review the diff and decide whether acceptance criteria are satisfied before generating prompt for INFRA-003."]

---

## 5. Unresolved Items & Edge Cases

[Fill in: open questions, pending architectural trade-offs, or observations that have not yet been formalized as tasks or decisions. If none, write "None."]

---

## 6. Primary Content (Relayed from Local Agents)

[Paste relevant agent reports, test outputs, or git diffs here so the new APC instance inspects primary evidence rather than a summary of a summary.]

---

**For lukexodus:** When starting a new APC session, paste this filled-in template as your initial message, accompanied by the latest contents of `docs/tasks/status.md` and `docs/decisions/decision-log.md` (or upload an APC bundle). The new APC instance must confirm receipt and restate the active state before writing new task prompts.
