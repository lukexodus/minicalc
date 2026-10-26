# TASK: FEAT-003 — Evaluator, environment, and built-ins

## Role & Worktree Instructions
- **Assigned agent:** Claude Code
- **Task ID:** FEAT-003
- **Depends on:** CORE-003
- **Worktree:** from the main checkout run `./scripts/task-worktree.sh start FEAT-003`, then work only inside `../minicalc-FEAT-003` on branch `task/FEAT-003`. Never edit the main checkout.

## Orientation & Required Reading
Before writing any code, read these in order:
1. `docs/context/complete-context.md` (project background and rules)
2. `docs/tasks/status.md` (confirm FEAT-003 is `open` and that every dependency below is `done`; if a dependency is not done, STOP and tell lukexodus)
3. `docs/decisions/decision-log.md` ([D-01] through [D-16]; never re-litigate a settled decision)
4. `docs/context/language-spec.md` (authoritative language behavior)
5. `docs/context/interface-contract.md` (authoritative Python signatures and file ownership)

Verify every assumption in this prompt against the files on disk (`ls`, `cat`, `grep`). If the prompt and the repository disagree, the repository is right: say so in your report.

## Context & Objectives
Implement the runtime semantics in `docs/context/language-spec.md` sections 4 to 7. You work in parallel with FEAT-001 and FEAT-002. Your tests build AST nodes by hand (using `ast_nodes` and `SourcePos`) so you do not depend on the lexer or parser.

## Specific Scope & Deliverables
1. **`minicalc/builtins.py`:** frozen `Builtin` dataclass, the `BUILTINS` dict (`abs` 1 arg, `min` 1+ args, `max` 1+ args, `gcd` 2 args), `is_reserved(name)`. `gcd` uses the iterative Euclid algorithm on absolute values and returns a non-negative result (`gcd(0, 0) == 0`). Each function takes plain ints and returns an int (range checking is the evaluator's job).
2. **`minicalc/environment.py`:** keep the CORE-003 `Environment` unless you find a defect; if you change it, say why in the report.
3. **Rewrite `minicalc/evaluator.py`** (remove the STUB marker). `Evaluator.evaluate(node)`:
   - Every produced value goes through one private helper `_checked(value, pos)` that raises `IntegerRangeError` at `pos` when `not in_range(value)`. Literals are already range-valid.
   - `Binary` evaluates left then right, then applies the operator. `+ - *`: plain integer ops. `/`: truncate toward zero using `abs(a) // abs(b)` with the sign applied (never `float`, never `int(a / b)`). `//`: Python `//`. `%`: Python `%`. For `/ // %`, a zero divisor raises `DivisionByZeroError` at the operator position **before** any range check. `**`: follow the spec rules exactly: negative exponent -> `DomainError`; `exp == 0` -> 1; base 0/1/-1 handled without computing a big power; when `abs(base) >= 2` and `exp > 31` raise `IntegerRangeError` immediately without computing the power; otherwise compute and `_checked`. Note `(-2) ** 31 == INT_MIN` is valid. Comparisons return 1 or 0.
   - `Unary`: `-` and `+`. `-x` is range-checked (`-INT_MIN` fails at the operator).
   - `Name`: `ans` and variables via `env.get`; a built-in name used as a value raises `UndefinedNameError` with a hint ("'abs' is a function; call it like abs(...)").
   - `Call`: unknown function name (including a variable name or `ans`) -> `CallError` at the name ("unknown function 'foo'" or "'x' is a variable, not a function"). Wrong arity -> `CallError`, checked **before** evaluating arguments. Then evaluate arguments left to right (first failing argument's error wins), call the built-in, `_checked` the result at the call's `pos` (`abs(INT_MIN)` fails).
   - `Assign`: `is_reserved(target)` -> `AssignmentError` at `node.pos` (checked first, before evaluating the right side). Evaluate the right side; only after success `env.set`. Return the value. Never mutate the environment on failure.
   - Unknown node type -> raise `TypeError` (programming error, not a `MiniCalcError`).
4. **Tests `tests/test_evaluator.py` and `tests/test_builtins.py`:** a helper `n(5)`, `b("+", n(1), n(2), col=3)` etc. that builds nodes. Cover: every row of the worked-examples table (use `pytest.mark.parametrize`); every evaluation-error example with class and column; truncation vs floor vs modulo table including negative operands and the identity `a == (a // b) * b + a % b` over a small grid; `**` edge cases (`0**0`, `0**5`, `1**1000000`, `(-1)**3`, `(-1)**4`, `2**30`, `2**31` error, `(-2)**31` valid, `(-2)**32` error, `2**-1` error, `3**-1` error, and `2**1000000000` completes in under 0.5 s: assert with `time.perf_counter`); `INT_MIN / -1` and `INT_MIN // -1` are range errors; `-INT_MIN` fails; built-ins for each arity violation; `gcd` signs and zeros; atomicity (failing assignment leaves variables untouched; assignment to `ans` and to `abs` fails; failed right side does not bind); `ans` unset error; name shadow errors; argument-order test with two failing arguments (leftmost wins).

### Files you own (edit only these)
- `minicalc/evaluator.py`
- `minicalc/builtins.py`
- `minicalc/environment.py` (only if a defect is found)
- `tests/test_evaluator.py`
- `tests/test_builtins.py`

### What NOT to touch
- `minicalc/lexer.py`, `parser.py`, `interpreter.py`
- `limits.py`, `errors.py`, `tokens.py`, `ast_nodes.py`
- `tests/golden/`
- Do not edit `docs/context/language-spec.md` or `docs/context/interface-contract.md`. If you find an ambiguity or contradiction in them, do not guess: describe it under "Flagged for APC / Operator Attention" in your report.
- Do not edit another task's row in `docs/tasks/status.md`, and do not reuse a decision ID that is not reserved for you.

## Verification & Acceptance Criteria
Your work is complete when ALL of these hold:
- [ ] Every row of the spec's worked-examples and evaluation-error tables is covered by a test with exact class and column.
- [ ] No use of `float`, `math.pow`, or `int(a / b)` in `evaluator.py` (`grep` evidence).
- [ ] `2 ** 1000000000` fails in under 0.5 s.
- [ ] Failed statements never change the environment (tested).
- [ ] `pytest -q` passes (new tests included).
- [ ] No regression in previously merged tests.
- [ ] Every class you create or change has a docstring with an `Attributes:` section describing every class variable and instance attribute ([D-11]). Every module has a docstring. Every public function has a docstring.
- [ ] All assumptions verified against disk.

## Reserved Decision IDs
None reserved. If you must make a non-trivial design choice that the spec does not cover, do not invent a decision ID: describe the choice and your recommendation in the report and continue with the most conservative option.

## Output & Reporting Instructions
When the work is complete:
1. **Make exactly one commit** on `task/FEAT-003`: `git add <files> && git commit -m "feat(FEAT-003): implement evaluator, built-ins and checked integer semantics"`.
2. **Patch file:** `mkdir -p patch && git diff HEAD~1 > patch/FEAT-003-<agent-name>-evaluator-builtins.patch`.
3. **Report:** write `docs/reports/FEAT-003-<agent-name>-evaluator-builtins.md` following `docs/reports/TASK-TEMPLATE.md`. Keep it short. It needs: Executive Summary, Implementation Details, Verification & Test Evidence (paste the real `pytest -q` output), a verbatim unified Git Diff (from `git diff HEAD~1`, with index lines), and "Flagged for APC / Operator Attention".
4. **Status:** edit only your own row in `docs/tasks/status.md`: set `needs-review` and link the report.
5. **Decision log:** nothing to append (no ID reserved).
6. **Validate:** `./scripts/validate-report.py docs/reports/FEAT-003-<agent-name>-evaluator-builtins.md --require-patch`. Fix every issue.
7. **Bundle:** only if you changed shared docs, run `./scripts/apc-bundle.sh core`.
8. **Report back to lukexodus:** executive summary, test results, patch path, `git diff HEAD~1`, branch name, and worktree path. Do NOT merge, rebase, or delete the worktree.

Replace `<agent-name>` with your own name (for example `claude-code`, `gemini`, `opencode`, `cursor`).
