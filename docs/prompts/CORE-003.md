# TASK: CORE-003 — Walking skeleton and the Interpreter facade

## Role & Worktree Instructions
- **Assigned agent:** Claude Code
- **Task ID:** CORE-003
- **Depends on:** CORE-001, CORE-002
- **Worktree:** from the main checkout run `./scripts/task-worktree.sh start CORE-003`, then work only inside `../minicalc-CORE-003` on branch `task/CORE-003`. Never edit the main checkout.

## Orientation & Required Reading
Before writing any code, read these in order:
1. `docs/context/complete-context.md` (project background and rules)
2. `docs/tasks/status.md` (confirm CORE-003 is `open` and that every dependency below is `done`; if a dependency is not done, STOP and tell lukexodus)
3. `docs/decisions/decision-log.md` ([D-01] through [D-16]; never re-litigate a settled decision)
4. `docs/context/language-spec.md` (authoritative language behavior)
5. `docs/context/interface-contract.md` (authoritative Python signatures and file ownership)

Verify every assumption in this prompt against the files on disk (`ls`, `cat`, `grep`). If the prompt and the repository disagree, the repository is right: say so in your report.

## Context & Objectives
Phase 1 exit gate: prove the whole pipeline end to end with the thinnest possible stages, and lock the `Interpreter` facade that the REPL, CLI, and tests use. FEAT-001, FEAT-002, and FEAT-003 later replace the stub stages file by file without touching the facade. The facade is final in this task.

## Specific Scope & Deliverables
1. **Stubs** (first line of each file after the docstring: `# STUB (CORE-003): replaced wholesale by <TASK>`). Public signatures must already match the contract:
   - `minicalc/lexer.py` (`Lexer`): handles whitespace (space, tab, `\r`), `#` comments, `NUMBER` (digits only, with the range check against `INT_MAX`), `EOF` (column `len(source) + 1`), and the `MAX_LINE_LENGTH` check. Any other character raises `LexError` ("illegal character") at its column.
   - `minicalc/parser.py` (`Parser`): returns `None` for only-EOF; returns `Number` for `NUMBER EOF`; anything else raises `ParseError` at the offending token.
   - `minicalc/evaluator.py` (`Evaluator`): `evaluate(Number)` returns the value after `in_range`; any other node raises `EvalError("not implemented yet")` with the node's `pos`.
2. **`minicalc/environment.py`:** the FULL `Environment` from contract section 8 (it is small): `variables`, `ans`, `get`, `set`, `record_result`, `clear`, `items`. `get("ans", pos)` returns `ans` or raises `UndefinedNameError` ("ans has no value yet; evaluate a statement first"); unknown names raise `UndefinedNameError` ("name 'x' is not defined"). `items()` is sorted by name and excludes `ans`.
3. **`minicalc/interpreter.py`: the REAL, final facade** (`Result`, `LineOutcome`, `Interpreter`) per contract section 10:
   - `run_line`: Lexer, Parser, then if the node is `None` return `Result("empty")`; otherwise `Evaluator.evaluate`; `kind` is `"assign"` (with `name`) for an `Assign` node, else `"value"`; call `env.record_result(value)` only after success.
   - On any `MiniCalcError`: call `with_source(source)` and re-raise.
   - Convert a `RecursionError` into `ParseError` (if raised while parsing) or `EvalError` (while evaluating) with the message "expression is too deeply nested", positioned at column 1.
   - `__init__` raises the recursion limit to at least 4000 only if currently lower (use `sys.getrecursionlimit` / `sys.setrecursionlimit`).
   - `run_source`: split with `str.splitlines()`, number lines from 1, call `run_line(line, n)` for each, build `LineOutcome`s. Blank and comment-only lines produce an outcome with `Result("empty")`. Never raise `MiniCalcError`.
4. **Tests `tests/test_interpreter.py`:** run through the facade only: value line; empty line; comment-only line; error carries `source_line`; a failed line leaves `ans` and variables unchanged (use a lex error); `run_source` numbering and continue-after-error; `\r\n` input; recursion safety net (monkeypatch the Evaluator to recurse infinitely and assert an `EvalError`, not a crash); line longer than 1000 chars gives `LexError` at column 1001.
5. Confirm `tests/test_golden.py` now collects and passes `smoke`.

### Files you own (edit only these)
- `minicalc/lexer.py`
- `minicalc/parser.py`
- `minicalc/evaluator.py`
- `minicalc/environment.py`
- `minicalc/interpreter.py`
- `tests/test_interpreter.py`
- `tests/test_environment.py`

### What NOT to touch
- `minicalc/limits.py`, `errors.py`, `tokens.py`, `ast_nodes.py` (read-only; report any needed change)
- `minicalc/builtins.py`, `display.py`, `repl.py`, `__main__.py`
- `tests/golden/` except to read `smoke`
- Do not edit `docs/context/language-spec.md` or `docs/context/interface-contract.md`. If you find an ambiguity or contradiction in them, do not guess: describe it under "Flagged for APC / Operator Attention" in your report.
- Do not edit another task's row in `docs/tasks/status.md`, and do not reuse a decision ID that is not reserved for you.

## Verification & Acceptance Criteria
Your work is complete when ALL of these hold:
- [ ] `python -c "from minicalc.interpreter import Interpreter; print(Interpreter().run_line('42'))"` prints `Result(kind='value', value=42, name=None)`.
- [ ] `pytest -q` passes including golden `smoke`.
- [ ] The three stub files each carry the STUB marker naming the task that will replace them.
- [ ] Public signatures in `interpreter.py` and `environment.py` match the contract exactly.
- [ ] `pytest -q` passes (new tests included).
- [ ] No regression in previously merged tests.
- [ ] Every class you create or change has a docstring with an `Attributes:` section describing every class variable and instance attribute ([D-11]). Every module has a docstring. Every public function has a docstring.
- [ ] All assumptions verified against disk.

## Reserved Decision IDs
None reserved. If you must make a non-trivial design choice that the spec does not cover, do not invent a decision ID: describe the choice and your recommendation in the report and continue with the most conservative option.

## Output & Reporting Instructions
When the work is complete:
1. **Make exactly one commit** on `task/CORE-003`: `git add <files> && git commit -m "feat(CORE-003): add walking skeleton and Interpreter facade"`.
2. **Patch file:** `mkdir -p patch && git diff HEAD~1 > patch/CORE-003-<agent-name>-walking-skeleton.patch`.
3. **Report:** write `docs/reports/CORE-003-<agent-name>-walking-skeleton.md` following `docs/reports/TASK-TEMPLATE.md`. Keep it short. It needs: Executive Summary, Implementation Details, Verification & Test Evidence (paste the real `pytest -q` output), a verbatim unified Git Diff (from `git diff HEAD~1`, with index lines), and "Flagged for APC / Operator Attention".
4. **Status:** edit only your own row in `docs/tasks/status.md`: set `needs-review` and link the report.
5. **Decision log:** nothing to append (no ID reserved).
6. **Validate:** `./scripts/validate-report.py docs/reports/CORE-003-<agent-name>-walking-skeleton.md --require-patch`. Fix every issue.
7. **Bundle:** only if you changed shared docs, run `./scripts/apc-bundle.sh core`.
8. **Report back to lukexodus:** executive summary, test results, patch path, `git diff HEAD~1`, branch name, and worktree path. Do NOT merge, rebase, or delete the worktree.

Replace `<agent-name>` with your own name (for example `claude-code`, `gemini`, `opencode`, `cursor`).
