# TASK: FEAT-001 — Full lexer

## Role & Worktree Instructions
- **Assigned agent:** Claude Code or opencode
- **Task ID:** FEAT-001
- **Depends on:** CORE-003
- **Worktree:** from the main checkout run `./scripts/task-worktree.sh start FEAT-001`, then work only inside `../minicalc-FEAT-001` on branch `task/FEAT-001`. Never edit the main checkout.

## Orientation & Required Reading
Before writing any code, read these in order:
1. `docs/context/complete-context.md` (project background and rules)
2. `docs/tasks/status.md` (confirm FEAT-001 is `open` and that every dependency below is `done`; if a dependency is not done, STOP and tell lukexodus)
3. `docs/decisions/decision-log.md` ([D-01] through [D-16]; never re-litigate a settled decision)
4. `docs/context/language-spec.md` (authoritative language behavior)
5. `docs/context/interface-contract.md` (authoritative Python signatures and file ownership)

Verify every assumption in this prompt against the files on disk (`ls`, `cat`, `grep`). If the prompt and the repository disagree, the repository is right: say so in your report.

## Context & Objectives
Replace the CORE-003 stub with the complete lexer defined by `docs/context/language-spec.md` section 2. You work in parallel with FEAT-002 (parser) and FEAT-003 (evaluator); you share only the contract. Tests must not import the parser or evaluator.

## Specific Scope & Deliverables
1. **Rewrite `minicalc/lexer.py`** (remove the STUB marker). One left-to-right pass, O(n), single index scan (no regex backtracking tricks required; a small regex for numbers/identifiers is fine).
   - Tokens: every `TokenType` in the contract. Longest match: `**` before `*`, `//` before `/`, `==` `!=` `<=` `>=` before their single-character prefixes. A lone `=` is `ASSIGN`. A lone `!` is a `LexError` at the `!`.
   - Identifiers `[A-Za-z_][A-Za-z0-9_]*`; digits `[0-9]+` using explicit ASCII ranges. **Do not use `str.isdigit()`, `isalpha()`, or `isalnum()`** (they accept non-ASCII characters; those must be illegal characters).
   - `NUMBER.value` is an `int`; `lexeme` keeps the source text (leading zeros allowed: `007` has value 7).
   - Every `Token.pos` is `SourcePos(line_no, col)` with 1-based columns; a tab counts as one column. `EOF` has lexeme `""` and column `len(source) + 1` (even when a comment is present).
   - Whitespace: space, tab, `\r`. A `#` ends tokenization (rest of the line is a comment).
2. **Errors (exact positions from spec section 2 table):**
   - `3.14`, `3.` -> `LexError` at the `.`. A `.` anywhere else (for example `.5`) is an illegal character at the `.`.
   - `12abc` or `9_` -> `LexError` at the start of the number.
   - Literal above `INT_MAX` -> `LexError` at the start of the number. `2147483647` is accepted.
   - Any other character (`@ $ : ; ' " [ ] { } ~ & | ^ \` and every non-ASCII character) -> `LexError` "illegal character" at that column.
   - Line longer than `MAX_LINE_LENGTH` -> `LexError` at column 1001, checked before scanning.
   - Messages must be helpful and human-readable (for example "decimals are not supported; MiniCalc works with integers only"; "illegal character '@'"), and must show the offending character where relevant. Message wording is free; class and position are not.
3. **Tests `tests/test_lexer.py`** (table-driven with `pytest.mark.parametrize`; build expected `(TokenType, lexeme)` lists): every operator and its longest-match neighbors (`2**3`, `2*3`, `7//2`, `7/2`, `a==b`, `a=b`, `a!=b`, `a<=b`, `a<b`), whitespace and tab handling, comment-only line, trailing comment after tokens, empty and whitespace-only line (only `EOF`), identifiers (`_x`, `x1`, `abs`), `007`, columns for a multi-token line, EOF column with and without a trailing comment, `\r` handling, every lexical-error row in the spec table with exact class and column, non-ASCII digit (for example `٣`) and a non-breaking space are illegal characters, and a 1001-character line. Add a property-style test: for random printable-ASCII strings (seeded `random.Random(0)`, 500 samples) `tokenize()` either returns a list ending in `EOF` or raises `LexError`, never any other exception.

### Files you own (edit only these)
- `minicalc/lexer.py`
- `tests/test_lexer.py`

### What NOT to touch
- `minicalc/parser.py`, `evaluator.py`, `environment.py`, `interpreter.py`
- `limits.py`, `errors.py`, `tokens.py`, `ast_nodes.py`
- `tests/golden/`
- Do not edit `docs/context/language-spec.md` or `docs/context/interface-contract.md`. If you find an ambiguity or contradiction in them, do not guess: describe it under "Flagged for APC / Operator Attention" in your report.
- Do not edit another task's row in `docs/tasks/status.md`, and do not reuse a decision ID that is not reserved for you.

## Verification & Acceptance Criteria
Your work is complete when ALL of these hold:
- [ ] Every lexical-error row of the spec table is covered by a test asserting class and column.
- [ ] `str.isdigit`/`isalpha`/`isalnum` do not appear in `lexer.py` (`grep` evidence in the report).
- [ ] The fuzz-style test passes and never lets a non-`LexError` exception escape.
- [ ] `Lexer` signature unchanged from the contract.
- [ ] `pytest -q` passes (new tests included).
- [ ] No regression in previously merged tests.
- [ ] Every class you create or change has a docstring with an `Attributes:` section describing every class variable and instance attribute ([D-11]). Every module has a docstring. Every public function has a docstring.
- [ ] All assumptions verified against disk.

## Reserved Decision IDs
None reserved. If you must make a non-trivial design choice that the spec does not cover, do not invent a decision ID: describe the choice and your recommendation in the report and continue with the most conservative option.

## Output & Reporting Instructions
When the work is complete:
1. **Make exactly one commit** on `task/FEAT-001`: `git add <files> && git commit -m "feat(FEAT-001): implement full lexer"`.
2. **Patch file:** `mkdir -p patch && git diff HEAD~1 > patch/FEAT-001-<agent-name>-full-lexer.patch`.
3. **Report:** write `docs/reports/FEAT-001-<agent-name>-full-lexer.md` following `docs/reports/TASK-TEMPLATE.md`. Keep it short. It needs: Executive Summary, Implementation Details, Verification & Test Evidence (paste the real `pytest -q` output), a verbatim unified Git Diff (from `git diff HEAD~1`, with index lines), and "Flagged for APC / Operator Attention".
4. **Status:** edit only your own row in `docs/tasks/status.md`: set `needs-review` and link the report.
5. **Decision log:** nothing to append (no ID reserved).
6. **Validate:** `./scripts/validate-report.py docs/reports/FEAT-001-<agent-name>-full-lexer.md --require-patch`. Fix every issue.
7. **Bundle:** only if you changed shared docs, run `./scripts/apc-bundle.sh core`.
8. **Report back to lukexodus:** executive summary, test results, patch path, `git diff HEAD~1`, branch name, and worktree path. Do NOT merge, rebase, or delete the worktree.

Replace `<agent-name>` with your own name (for example `claude-code`, `gemini`, `opencode`, `cursor`).
