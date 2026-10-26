# TASK: CORE-001 — Shared vocabulary: limits, errors, tokens, AST

## Role & Worktree Instructions
- **Assigned agent:** Claude Code
- **Task ID:** CORE-001
- **Depends on:** ARCH-002
- **Worktree:** from the main checkout run `./scripts/task-worktree.sh start CORE-001`, then work only inside `../minicalc-CORE-001` on branch `task/CORE-001`. Never edit the main checkout.

## Orientation & Required Reading
Before writing any code, read these in order:
1. `docs/context/complete-context.md` (project background and rules)
2. `docs/tasks/status.md` (confirm CORE-001 is `open` and that every dependency below is `done`; if a dependency is not done, STOP and tell lukexodus)
3. `docs/decisions/decision-log.md` ([D-01] through [D-16]; never re-litigate a settled decision)
4. `docs/context/language-spec.md` (authoritative language behavior)
5. `docs/context/interface-contract.md` (authoritative Python signatures and file ownership)

Verify every assumption in this prompt against the files on disk (`ls`, `cat`, `grep`). If the prompt and the repository disagree, the repository is right: say so in your report.

## Context & Objectives
Every later task imports these four modules, so they must match `docs/context/interface-contract.md` sections 2 to 5 exactly (names, field order, defaults). Behavior of errors follows spec sections 2, 3, and 7.

## Specific Scope & Deliverables
1. **`minicalc/limits.py`:** `INT_MIN`, `INT_MAX`, `MAX_LINE_LENGTH`, `in_range(value)`.
2. **`minicalc/errors.py`:** `SourcePos` (frozen dataclass), `MiniCalcError` and the eight subclasses listed in the contract. Details:
   - `kind` ClassVar per class: `LexError` "Lexical error", `ParseError` "Syntax error", every `EvalError` subclass and `EvalError` itself "Runtime error".
   - `render(color=False)` first line: `Error: {kind} at line {line}, column {col}: {message}` (without a position: `Error: {kind}: {message}`). If both `pos` and `source_line` are set, add two more lines: the source line indented by 2 spaces (replace each tab in the source line with one space so columns align), then a caret line of 2 spaces + `col - 1` spaces + `^`.
   - `render(color=True)` wraps the leading `Error:` in bold red (`\x1b[1;31m` ... `\x1b[0m`) and the caret in red (`\x1b[31m` ... `\x1b[0m`). No other styling.
   - `with_source(source_line)` sets `source_line` and returns `self`.
   - `canonical()` returns `ERR <ClassName> <line>:<col>` using `type(self).__name__`. If `pos` is `None`, return `ERR <ClassName> ?:?`.
   - `MiniCalcError` must be picklable-safe and its `str()` must equal `message`.
3. **`minicalc/tokens.py`:** `TokenType` (all members from the contract) and frozen `Token`.
4. **`minicalc/ast_nodes.py`:** `Number`, `Name`, `Unary`, `Binary`, `Call`, `Assign`, the `Op` literal alias, and the `Node` union. `pos` is the last field of every node.
5. **Tests** (`tests/test_errors.py`, `tests/test_vocabulary.py`):
   - `in_range` at `INT_MIN - 1`, `INT_MIN`, `INT_MAX`, `INT_MAX + 1`.
   - `render` exact string for a sample error with caret under column 5; with `source_line=None`; with `pos=None`; with a tab in the source line; with `color=True`.
   - `canonical()` for each subclass; `issubclass` hierarchy for all eight; `str(err) == err.message`.
   - Frozen dataclasses raise `dataclasses.FrozenInstanceError` on assignment (SourcePos, Token, each AST node).
   - AST nodes are hashable and compare equal structurally; `Call.args` stores a tuple.

### Files you own (edit only these)
- `minicalc/limits.py`
- `minicalc/errors.py`
- `minicalc/tokens.py`
- `minicalc/ast_nodes.py`
- `tests/test_errors.py`
- `tests/test_vocabulary.py`

### What NOT to touch
- `minicalc/__init__.py`
- Any lexer, parser, evaluator, environment, interpreter, repl, or display file
- `tests/golden/`
- Do not edit `docs/context/language-spec.md` or `docs/context/interface-contract.md`. If you find an ambiguity or contradiction in them, do not guess: describe it under "Flagged for APC / Operator Attention" in your report.
- Do not edit another task's row in `docs/tasks/status.md`, and do not reuse a decision ID that is not reserved for you.

## Verification & Acceptance Criteria
Your work is complete when ALL of these hold:
- [ ] Public names and signatures match the contract exactly (`grep` or `inspect` evidence in the report).
- [ ] No imports outside the standard library; no circular imports among the four modules.
- [ ] The `render()` example from contract section 3 is reproduced exactly by a test.
- [ ] `pytest -q` passes (new tests included).
- [ ] No regression in previously merged tests.
- [ ] Every class you create or change has a docstring with an `Attributes:` section describing every class variable and instance attribute ([D-11]). Every module has a docstring. Every public function has a docstring.
- [ ] All assumptions verified against disk.

## Reserved Decision IDs
None reserved. If you must make a non-trivial design choice that the spec does not cover, do not invent a decision ID: describe the choice and your recommendation in the report and continue with the most conservative option.

## Output & Reporting Instructions
When the work is complete:
1. **Make exactly one commit** on `task/CORE-001`: `git add <files> && git commit -m "feat(CORE-001): add limits, errors, tokens and AST nodes"`.
2. **Patch file:** `mkdir -p patch && git diff HEAD~1 > patch/CORE-001-<agent-name>-shared-vocabulary.patch`.
3. **Report:** write `docs/reports/CORE-001-<agent-name>-shared-vocabulary.md` following `docs/reports/TASK-TEMPLATE.md`. Keep it short. It needs: Executive Summary, Implementation Details, Verification & Test Evidence (paste the real `pytest -q` output), a verbatim unified Git Diff (from `git diff HEAD~1`, with index lines), and "Flagged for APC / Operator Attention".
4. **Status:** edit only your own row in `docs/tasks/status.md`: set `needs-review` and link the report.
5. **Decision log:** nothing to append (no ID reserved).
6. **Validate:** `./scripts/validate-report.py docs/reports/CORE-001-<agent-name>-shared-vocabulary.md --require-patch`. Fix every issue.
7. **Bundle:** only if you changed shared docs, run `./scripts/apc-bundle.sh core`.
8. **Report back to lukexodus:** executive summary, test results, patch path, `git diff HEAD~1`, branch name, and worktree path. Do NOT merge, rebase, or delete the worktree.

Replace `<agent-name>` with your own name (for example `claude-code`, `gemini`, `opencode`, `cursor`).
