# TASK: FEAT-005 — Spec-derived golden test cases (independent audit)

## Role & Worktree Instructions
- **Assigned agent:** Gemini (must NOT be the agent that wrote the lexer, parser, or evaluator)
- **Task ID:** FEAT-005
- **Depends on:** CORE-002 (and the spec; NOT the implementation)
- **Worktree:** from the main checkout run `./scripts/task-worktree.sh start FEAT-005`, then work only inside `../minicalc-FEAT-005` on branch `task/FEAT-005`. Never edit the main checkout.

## Orientation & Required Reading
Before writing any code, read these in order:
1. `docs/context/complete-context.md` (project background and rules)
2. `docs/tasks/status.md` (confirm FEAT-005 is `open` and that every dependency below is `done`; if a dependency is not done, STOP and tell lukexodus)
3. `docs/decisions/decision-log.md` ([D-01] through [D-16]; never re-litigate a settled decision)
4. `docs/context/language-spec.md` (authoritative language behavior)
5. `docs/context/interface-contract.md` (authoritative Python signatures and file ownership)

Verify every assumption in this prompt against the files on disk (`ls`, `cat`, `grep`). If the prompt and the repository disagree, the repository is right: say so in your report.

## Context & Objectives
Independent verification: you write the expected behavior from the spec alone. Different model lineage plus no access to the implementation is what makes this a real check. **Do not read `minicalc/lexer.py`, `parser.py`, `evaluator.py`, or `builtins.py`, and never run the interpreter to produce expected output.** Derive every expected line by hand from the spec, and cross-check numeric results with a quick independent Python calculation (write it in a scratch file outside the repo). Many cases will fail until FEAT-001 to FEAT-003 are merged; that is expected and is the point.

## Specific Scope & Deliverables
Create `.mc` + `.out` pairs in `tests/golden/` following contract section 12 exactly. Each file focuses on one theme; state-carrying cases may rely on earlier lines in the same file. Required files and minimum coverage (about 150 statement lines in total):
- `arithmetic.mc`: `+ - *` with small and large operands, zero, negative results, parentheses, whitespace variants (`2+3`, `  2   +   3  `, tabs).
- `precedence.mc`: every precedence and associativity row of the spec, including `-2 ** 2`, `2 ** 3 ** 2`, `2 ** -1`, unary chains (`--5`, `-+-5`, `+5`), comparisons vs arithmetic.
- `division.mc`: the full `/`, `//`, `%` table with all sign combinations, divisor zero for each operator, `INT_MIN / -1` and `INT_MIN // -1` (use `-2147483647 - 1` for `INT_MIN`; parenthesize it where needed).
- `power.mc`: every `**` rule and edge case from spec section 5 (including `(-2) ** 31` valid, `(-2) ** 32` error, `2 ** 1000000000` error, `0 ** 0`, `1 ** 1000000`).
- `comparison.mc`: all six operators on equal, less, greater operands; negative numbers; chaining error `1 < 2 < 3`; parenthesized chain `(1 < 2) < 3`.
- `variables.mc`: assignment, reuse, reassignment, `ans` after expressions and assignments, `ans` unset error as the very first line, assignment to `ans` and to each built-in name, undefined variable, failed statement leaves `ans` and variables unchanged (assert by reading them after), case sensitivity (`X` vs `x`), underscore names.
- `builtins.mc`: `abs min max gcd` normal and edge cases, arity errors (`abs()`, `abs(1,2)`, `gcd(1)`, `min()`), unknown function, calling a variable, built-in name as a value, nested calls, argument errors (leftmost failing argument wins), arity-before-arguments rule, `abs(-2147483647 - 1)` range error.
- `range.mc`: `INT_MAX + 1`, `INT_MIN - 1`, `46341 * 46341`, `-INT_MIN`, literal `2147483647` ok, `2147483648` lex error, `99999999999` lex error, intermediate overflow that "comes back" in range (for example `2147483647 + 1 - 1` must still be an error at the first `+`).
- `lex_errors.mc`: every lexical-error row (decimals `3.14` and `3.`, `12abc`, `.5`, `@`, `$`, `:`, `!` alone, non-ASCII character), plus a 1001-character line (build it carefully; the expected column is 1001).
- `parse_errors.mc`: every parse-error row of the spec table, plus `x = y = 3`, `a + 1 = 2`, `max(1 2)`, `()`, `2 **`, unmatched `)`.
- `comments_whitespace.mc`: blank lines, comment-only lines, trailing comments, `#` inside an expression line, lines with only spaces; verify numbering of subsequent lines (the file line number is what appears in `ERR` lines).
- `demo.mc` + `demo.out`: a clean 12-to-15-line session that exercises variables, `ans`, built-ins, comparisons, and one error of each family; this becomes the presentation demo.
Rules for `.out`: one line per **statement** line only (blank and comment-only lines produce nothing); `OK <value>`, `OK <name>=<value>`, or `ERR <ClassName> <line>:<col>` with the real file line number. Put a `# ` comment line above every group naming the spec section it verifies.

### Files you own (edit only these)
- `tests/golden/*.mc` and `tests/golden/*.out` (except `smoke.*`)

### What NOT to touch
- `minicalc/` (do not even read the stage implementations)
- `tests/golden/smoke.*`
- `tests/test_golden.py`, `tests/golden_format.py`
- Do not edit `docs/context/language-spec.md` or `docs/context/interface-contract.md`. If you find an ambiguity or contradiction in them, do not guess: describe it under "Flagged for APC / Operator Attention" in your report.
- Do not edit another task's row in `docs/tasks/status.md`, and do not reuse a decision ID that is not reserved for you.

## Verification & Acceptance Criteria
Your work is complete when ALL of these hold:
- [ ] Every row of the spec tables (lexical errors, parse errors, worked examples, evaluation errors, built-ins) is covered by at least one line, and your report includes a coverage matrix: spec row -> file:line.
- [ ] Each expected numeric value was cross-checked with an independent Python calculation, recorded in the report.
- [ ] A section in the report lists every spec ambiguity you hit (with the line you chose and why). Do not edit the spec.
- [ ] `pytest tests/test_golden.py` runs without harness errors; failures are listed in the report with counts per file (they are expected before INT-001).
- [ ] `pytest -q` passes (new tests included), except for the items under "Known failing" below.
- [ ] No regression in previously merged tests.
- [ ] Every class you create or change has a docstring with an `Attributes:` section describing every class variable and instance attribute ([D-11]). Every module has a docstring. Every public function has a docstring.
- [ ] All assumptions verified against disk.

**Known failing:** Golden cases other than `smoke` will fail until FEAT-001, FEAT-002, and FEAT-003 are merged. That is expected; INT-001 resolves it.

## Reserved Decision IDs
None reserved. If you must make a non-trivial design choice that the spec does not cover, do not invent a decision ID: describe the choice and your recommendation in the report and continue with the most conservative option.

## Output & Reporting Instructions
When the work is complete:
1. **Make exactly one commit** on `task/FEAT-005`: `git add <files> && git commit -m "test(FEAT-005): add spec-derived golden cases"`.
2. **Patch file:** `mkdir -p patch && git diff HEAD~1 > patch/FEAT-005-<agent-name>-golden-cases.patch`.
3. **Report:** write `docs/reports/FEAT-005-<agent-name>-golden-cases.md` following `docs/reports/TASK-TEMPLATE.md`. Keep it short. It needs: Executive Summary, Implementation Details, Verification & Test Evidence (paste the real `pytest -q` output), a verbatim unified Git Diff (from `git diff HEAD~1`, with index lines), and "Flagged for APC / Operator Attention".
4. **Status:** edit only your own row in `docs/tasks/status.md`: set `needs-review` and link the report.
5. **Decision log:** nothing to append (no ID reserved).
6. **Validate:** `./scripts/validate-report.py docs/reports/FEAT-005-<agent-name>-golden-cases.md --require-patch`. Fix every issue.
7. **Bundle:** only if you changed shared docs, run `./scripts/apc-bundle.sh core`.
8. **Report back to lukexodus:** executive summary, test results, patch path, `git diff HEAD~1`, branch name, and worktree path. Do NOT merge, rebase, or delete the worktree.

Replace `<agent-name>` with your own name (for example `claude-code`, `gemini`, `opencode`, `cursor`).
