# TASK: FEAT-002 — Full parser

## Role & Worktree Instructions
- **Assigned agent:** Claude Code or opencode
- **Task ID:** FEAT-002
- **Depends on:** CORE-003
- **Worktree:** from the main checkout run `./scripts/task-worktree.sh start FEAT-002`, then work only inside `../minicalc-FEAT-002` on branch `task/FEAT-002`. Never edit the main checkout.

## Orientation & Required Reading
Before writing any code, read these in order:
1. `docs/context/complete-context.md` (project background and rules)
2. `docs/tasks/status.md` (confirm FEAT-002 is `open` and that every dependency below is `done`; if a dependency is not done, STOP and tell lukexodus)
3. `docs/decisions/decision-log.md` ([D-01] through [D-16]; never re-litigate a settled decision)
4. `docs/context/language-spec.md` (authoritative language behavior)
5. `docs/context/interface-contract.md` (authoritative Python signatures and file ownership)

Verify every assumption in this prompt against the files on disk (`ls`, `cat`, `grep`). If the prompt and the repository disagree, the repository is right: say so in your report.

## Context & Objectives
Replace the CORE-003 stub with the complete parser for the grammar in `docs/context/language-spec.md` section 3. You work in parallel with FEAT-001 and FEAT-003. Build tokens by hand in your tests (or via the `Lexer` stub only for trivial input); do not depend on the full lexer. This task also owns the parser's error-message conventions.

## Specific Scope & Deliverables
1. **Rewrite `minicalc/parser.py`** (remove the STUB marker). Hand-written recursive descent, one method per grammar rule, named after the rule (`_expression`, `_additive`, `_term`, `_unary`, `_power`, `_primary`, `_call_args`). Left-associative levels use loops, not recursion. Documented grammar in the class docstring.
   - `parse_statement()` returns `None` when the only token is `EOF`; otherwise an `Assign` or any expression node. Assignment is recognized when the first two tokens are `IDENT ASSIGN`.
   - Node `pos` rules from the contract: `Binary`/`Unary` at the operator token, `Call` at the function-name token, `Name` and `Assign.target` at the identifier, `Number` at the literal.
   - `unary = (MINUS|PLUS) unary | power`; `power = primary [POW unary]` so `-2 ** 2` is `Unary(-, Binary(**, 2, 2))` and `2 ** 3 ** 2` is `2 ** (3 ** 2)`; `2 ** -1` parses.
   - Comparison is non-associative: after one comparison, if the next token is another comparison operator raise `ParseError` at that token (message must tell the user to add parentheses).
   - After a complete statement any remaining token other than `EOF` is a `ParseError` at that token. Special messages for `ASSIGN` in that position: if the left side was not a bare name (`5 = 3`, `a + 1 = 2`) -> "left side of '=' must be a name"; if it was a chained assignment (`x = y = 3`) -> "chained assignment is not supported". Position is the offending `=` token in both cases.
2. **Error table** (class `ParseError`, exact column rules from spec section 3): `2 +` at EOF col; `2 + * 3` at `*`; `(2 + 3` at EOF col; `2 3` at `3`; `1 < 2 < 3` at the second `<`; `max(1,` at EOF col; `max(1,)` at `)`; `)` at `)`; `= 5` at `=`; `x =` at EOF col; `f(1 2)` at `2` (message: expected ',' or ')'); `()` at `)`; `2 ** ` at EOF col. Messages name what was expected and what was found, using the token's lexeme, or "end of line" for `EOF`.
3. **Depth safety:** limit nesting to `MAX_DEPTH = 200` recursive entries into `_expression`; exceeding it raises `ParseError` "expression is nested too deeply" at the current token. Also catch `RecursionError` inside `parse_statement` and convert it the same way.
4. **Tests `tests/test_parser.py`:** build token lists with a small helper `toks("2 + 3")` that you write in the test file from `Token`/`TokenType` using a trivial whitespace split plus a lookup table (do not import the lexer). Cover: every precedence and associativity row in the spec; AST shape and every `pos` rule (assert `pos` fields); assignment vs expression; calls with 0, 1, and many arguments and nested calls; parenthesized comparison inside a comparison `(1 < 2) < 3`; every row of the error table with exact column; depth limit (300 nested parens fails cleanly; 100 succeeds); a seeded random-token-sequence test (500 samples) proving `parse_statement` either returns a node/`None` or raises `ParseError`, never any other exception.

### Files you own (edit only these)
- `minicalc/parser.py`
- `tests/test_parser.py`

### What NOT to touch
- `minicalc/lexer.py`, `evaluator.py`, `environment.py`, `interpreter.py`
- `limits.py`, `errors.py`, `tokens.py`, `ast_nodes.py`
- `tests/golden/`
- Do not edit `docs/context/language-spec.md` or `docs/context/interface-contract.md`. If you find an ambiguity or contradiction in them, do not guess: describe it under "Flagged for APC / Operator Attention" in your report.
- Do not edit another task's row in `docs/tasks/status.md`, and do not reuse a decision ID that is not reserved for you.

## Verification & Acceptance Criteria
Your work is complete when ALL of these hold:
- [ ] `-2 ** 2`, `2 ** 3 ** 2`, `10 - 3 - 2`, and `2 + 3 == 5` produce the exact AST shapes implied by the spec (assert them).
- [ ] Every row of the spec parse-error table is tested with exact column.
- [ ] No parser method recurses for left-associative chains (a 5000-term `1+1+...` token list parses without `RecursionError`).
- [ ] [D-13] is logged.
- [ ] `pytest -q` passes (new tests included).
- [ ] No regression in previously merged tests.
- [ ] Every class you create or change has a docstring with an `Attributes:` section describing every class variable and instance attribute ([D-11]). Every module has a docstring. Every public function has a docstring.
- [ ] All assumptions verified against disk.

## Reserved Decision IDs
Reserved Decision ID: **[D-13]** (parser error-message wording conventions). Log the message templates you settled on (one line each) so FEAT-004 and DOC-002 can quote them.

## Output & Reporting Instructions
When the work is complete:
1. **Make exactly one commit** on `task/FEAT-002`: `git add <files> && git commit -m "feat(FEAT-002): implement full recursive-descent parser"`.
2. **Patch file:** `mkdir -p patch && git diff HEAD~1 > patch/FEAT-002-<agent-name>-full-parser.patch`.
3. **Report:** write `docs/reports/FEAT-002-<agent-name>-full-parser.md` following `docs/reports/TASK-TEMPLATE.md`. Keep it short. It needs: Executive Summary, Implementation Details, Verification & Test Evidence (paste the real `pytest -q` output), a verbatim unified Git Diff (from `git diff HEAD~1`, with index lines), and "Flagged for APC / Operator Attention".
4. **Status:** edit only your own row in `docs/tasks/status.md`: set `needs-review` and link the report.
5. **Decision log:** append the entry for your reserved ID to `docs/decisions/decision-log.md`, replacing the RESERVED placeholder text (edit only that entry).
6. **Validate:** `./scripts/validate-report.py docs/reports/FEAT-002-<agent-name>-full-parser.md --require-patch`. Fix every issue.
7. **Bundle:** only if you changed shared docs, run `./scripts/apc-bundle.sh core`.
8. **Report back to lukexodus:** executive summary, test results, patch path, `git diff HEAD~1`, branch name, and worktree path. Do NOT merge, rebase, or delete the worktree.

Replace `<agent-name>` with your own name (for example `claude-code`, `gemini`, `opencode`, `cursor`).
