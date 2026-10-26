# TASK: FEAT-004 — REPL, CLI, and display

## Role & Worktree Instructions
- **Assigned agent:** opencode or Cursor
- **Task ID:** FEAT-004
- **Depends on:** CORE-003
- **Worktree:** from the main checkout run `./scripts/task-worktree.sh start FEAT-004`, then work only inside `../minicalc-FEAT-004` on branch `task/FEAT-004`. Never edit the main checkout.

## Orientation & Required Reading
Before writing any code, read these in order:
1. `docs/context/complete-context.md` (project background and rules)
2. `docs/tasks/status.md` (confirm FEAT-004 is `open` and that every dependency below is `done`; if a dependency is not done, STOP and tell lukexodus)
3. `docs/decisions/decision-log.md` ([D-01] through [D-16]; never re-litigate a settled decision)
4. `docs/context/language-spec.md` (authoritative language behavior)
5. `docs/context/interface-contract.md` (authoritative Python signatures and file ownership)

Verify every assumption in this prompt against the files on disk (`ls`, `cat`, `grep`). If the prompt and the repository disagree, the repository is right: say so in your report.

## Context & Objectives
This task targets the rubric's Runtime criterion: "excellent user prompts, good use of symbols, spacing in output". Everything here talks to the `Interpreter` facade only (stable since CORE-003), so it can be built and tested before the real lexer, parser, and evaluator land. Behavior is defined by spec section 8, contract section 11, and [D-09].

## Specific Scope & Deliverables
1. **`minicalc/display.py`** (ASCII-safe; styling by ANSI color only):
   - `use_color(stream)`: true only if `stream.isatty()` and `"NO_COLOR"` is not in `os.environ`; tolerate streams without `isatty`.
   - `format_result(result, color=False)`: `= 42` for values, `x = 7` for assignments, `""` for empty. With color, the value is bold green.
   - `format_outcome(outcome, color=False)` for script mode: `line 3: = 42`, `line 4: x = 7`, empty -> `""`, error -> `outcome.error.render(color)`.
   - `banner(color=False)`: three lines: a rule of 44 `-` characters; `MiniCalc 1.0  integer arithmetic language`; `Type :help for help, :quit to exit.`; and another rule. Plain text must contain no ANSI codes.
   - `help_text(color=False)`: sections "Operators" (precedence table from the spec, high to low), "Functions" (`abs min max gcd` with arity), "Names" (`ans`, assignment), "Commands" (`:help :vars :clear :quit`), and 3 short examples. Aligned columns, blank line between sections.
2. **`minicalc/repl.py`** `Repl` per contract section 11 (`PROMPT = "minicalc> "`):
   - Prints the banner once, then loops reading with the injected `input_fn(PROMPT)`.
   - Blank line: no output. Line starting with `:` (after strip): meta-command, handled by the REPL and never sent to the interpreter. `:help`; `:vars` prints `ans` first if set, then variables sorted by name in aligned `name = value` rows, or `(no variables)`; `:clear` calls `env.clear()` and prints `Cleared N variable(s).`; `:quit` and `:q` exit. Unknown command prints `Unknown command ':foo'. Type :help for a list.` (not an error object).
   - Other lines: `interpreter.run_line`; print `format_result` (skip empty); on `MiniCalcError` print `err.render(color)` followed by a blank line.
   - `EOFError` (Ctrl-D) and `KeyboardInterrupt` (Ctrl-C) at the prompt print a newline and exit cleanly. `run()` returns 0.
3. **`minicalc/__main__.py`** `main(argv=None) -> int` using `argparse` (prog `minicalc`): optional positional `file`; `-e/--expr EXPR`; `--no-color`; `--version` (prints `MiniCalc 1.0.0`). File and `-e` together -> usage error. Behavior: no args -> REPL (exit 0 on clean exit); `file` -> read UTF-8 (unreadable or undecodable -> message on stderr, exit 2), `run_source`, print each non-empty `format_outcome` (results to stdout, errors to stderr), exit 1 if any error else 0; `-e` -> run the single expression, print `format_result`, exit 1 on a MiniCalc error (rendered to stderr). `if __name__ == "__main__": raise SystemExit(main())`.
4. **`main.py`** at the repo root: three-line shim calling `minicalc.__main__.main`.
5. **Tests `tests/test_cli.py`, `tests/test_display.py`:** drive `Repl` with a scripted iterator `input_fn` and a list-collecting `output_fn` (no real terminal). Because the real lexer, parser, and evaluator may not be merged yet, use a **fake interpreter** (a small class with `env` and `run_line`) for REPL and CLI logic tests, and add a second set of tests marked `@pytest.mark.integration` that use the real `Interpreter` and are expected to pass only after INT-001. Cover every command, EOF, Ctrl-C, blank lines, unknown command, exit codes 0/1/2, `NO_COLOR`, `use_color` with fake streams, exact banner and `:vars` output, and that no ANSI codes appear when `color=False`.

### Files you own (edit only these)
- `minicalc/display.py`
- `minicalc/repl.py`
- `minicalc/__main__.py`
- `main.py`
- `tests/test_cli.py`
- `tests/test_display.py`
- `pytest.ini` (only to register the `integration` marker)

### What NOT to touch
- `minicalc/interpreter.py` and all stage files
- `limits.py`, `errors.py`, `tokens.py`, `ast_nodes.py`
- Do not edit `docs/context/language-spec.md` or `docs/context/interface-contract.md`. If you find an ambiguity or contradiction in them, do not guess: describe it under "Flagged for APC / Operator Attention" in your report.
- Do not edit another task's row in `docs/tasks/status.md`, and do not reuse a decision ID that is not reserved for you.

## Verification & Acceptance Criteria
Your work is complete when ALL of these hold:
- [ ] `python -m minicalc --version` prints `MiniCalc 1.0.0`.
- [ ] `python -m minicalc -e 42` prints `= 42` and exits 0.
- [ ] No ANSI escape codes are emitted when stdout is not a TTY (tested).
- [ ] All non-integration tests pass; integration tests are explicitly marked.
- [ ] [D-14] is logged.
- [ ] `pytest -q` passes (new tests included), except for the items under "Known failing" below.
- [ ] No regression in previously merged tests.
- [ ] Every class you create or change has a docstring with an `Attributes:` section describing every class variable and instance attribute ([D-11]). Every module has a docstring. Every public function has a docstring.
- [ ] All assumptions verified against disk.

**Known failing:** Tests marked `integration` may fail until FEAT-001/002/003 are merged (INT-001 turns them green).

## Reserved Decision IDs
Reserved Decision ID: **[D-14]**. Log any REPL or display behavior that you had to fix because the spec was silent (exact wording of messages, spacing rules).

## Output & Reporting Instructions
When the work is complete:
1. **Make exactly one commit** on `task/FEAT-004`: `git add <files> && git commit -m "feat(FEAT-004): add REPL, CLI entry point and display formatting"`.
2. **Patch file:** `mkdir -p patch && git diff HEAD~1 > patch/FEAT-004-<agent-name>-repl-cli-display.patch`.
3. **Report:** write `docs/reports/FEAT-004-<agent-name>-repl-cli-display.md` following `docs/reports/TASK-TEMPLATE.md`. Keep it short. It needs: Executive Summary, Implementation Details, Verification & Test Evidence (paste the real `pytest -q` output), a verbatim unified Git Diff (from `git diff HEAD~1`, with index lines), and "Flagged for APC / Operator Attention".
4. **Status:** edit only your own row in `docs/tasks/status.md`: set `needs-review` and link the report.
5. **Decision log:** append the entry for your reserved ID to `docs/decisions/decision-log.md`, replacing the RESERVED placeholder text (edit only that entry).
6. **Validate:** `./scripts/validate-report.py docs/reports/FEAT-004-<agent-name>-repl-cli-display.md --require-patch`. Fix every issue.
7. **Bundle:** only if you changed shared docs, run `./scripts/apc-bundle.sh core`.
8. **Report back to lukexodus:** executive summary, test results, patch path, `git diff HEAD~1`, branch name, and worktree path. Do NOT merge, rebase, or delete the worktree.

Replace `<agent-name>` with your own name (for example `claude-code`, `gemini`, `opencode`, `cursor`).
