# Decision Log

**Append-only.** Never edit or delete a past entry — if a decision changes, add a new entry that supersedes it and say so explicitly ("supersedes entry [D-xx]").

This file exists so that across API-credit-limited handoffs between APC AI instances and zero-memory local agent sessions, a settled question is **never re-litigated from scratch** because nobody could find the earlier reasoning. When in doubt about whether something belongs here: if re-deriving it would cost more than one paragraph of reasoning, it belongs here.

**Format for each entry:**
- **[D-xx]** Decision title
- **Date / Session:** When it was locked
- **Decision:** What was locked or selected
- **Reasoning:** Why this choice was made over alternatives
- **Affects:** Components, interfaces, or tasks impacted

**Reserved Decision IDs:** Decision IDs are reserved per task by the APC AI in the task prompt, not invented on the fly by local agents. This prevents ID collisions during concurrent worktree tasks.

---

**[D-01]** Architecture baseline and repository governance locked.  
- **Date / Session:** 2026-10-26, APC planning session 1  
- **Decision:** Adopted the APC + Local Agent orchestration model with the repository as sole source of truth, unified-diff reporting, reserved decision IDs, and per-task worktrees.  
- **Reasoning:** Decouples planning from implementation and prevents drift across agent sessions during a 4-day build.  
- **Affects:** All documents, tasks, and workflows.

**[D-02]** Implementation language and runtime.  
- **Date / Session:** 2026-10-26, APC planning session 1  
- **Decision:** Python 3.10 or newer. Runtime uses the standard library only. `pytest` is a development-only dependency. Console styling uses plain ANSI escape codes (no `rich`).  
- **Reasoning:** Shortest path to a correct, documented, runnable deliverable; the grader needs no build step or install. Zero runtime dependencies removes the main delivery risk. Considered Java (about 1.8x code, JDK needed) and C++ (about 2.2x code, overflow is undefined behavior).  
- **Affects:** Whole codebase, `display.py`, submission packaging.

**[D-03]** Language scope = option C.  
- **Date / Session:** 2026-10-26, APC planning session 1  
- **Decision:** MiniCalc v1.0 supports: integer literals, `+ - * / // % **`, unary `+ -`, parentheses, comparisons (`== != < <= > >=`), variables with assignment, `ans`, built-ins `abs min max gcd`, `#` comments, REPL, script and `-e` modes. Non-goals: floats, strings, user functions, control flow, multiple statements per line, big integers.  
- **Reasoning:** Covers the course requirements plus 'advanced features' for the Presentation criterion while keeping the grammar small enough to test and document in 4 days. Option D (control flow, functions) rejected as too risky for the schedule.  
- **Affects:** `language-spec.md`, all FEAT tasks.

**[D-04]** Front-end architecture.  
- **Date / Session:** 2026-10-26, APC planning session 1  
- **Decision:** Hand-written lexer and recursive-descent parser with a precedence-aware grammar (see spec section 3). AST nodes are frozen dataclasses. Source is processed one line at a time; one statement per line. No parser-generator library.  
- **Reasoning:** Best for explaining the full pipeline in the presentation, gives full control over error messages and positions, and is smaller than learning a library for this grammar size.  
- **Affects:** `lexer.py`, `parser.py`, `ast_nodes.py`.

**[D-05]** Integer model: signed 32-bit with checked arithmetic.  
- **Date / Session:** 2026-10-26, APC planning session 1  
- **Decision:** Values are signed 32-bit integers. Every produced value is range-checked and raises `IntegerRangeError` instead of wrapping. Literals above 2147483647 are rejected by the lexer. `INT_MIN` is written `-2147483647 - 1`. `**` short-circuits to a range error when `|base| >= 2` and `exp > 31`.  
- **Reasoning:** Python ints are unbounded, which would hide overflow; an explicit range gives a defensible reliability story and prevents runaway computation.  
- **Affects:** `limits.py`, `lexer.py`, `evaluator.py`.

**[D-06]** Operator semantics and precedence.  
- **Date / Session:** 2026-10-26, APC planning session 1  
- **Decision:** `/` truncates toward zero; `//` floors; `%` is floored modulo paired with `//`; `**` is right-associative and binds tighter than unary minus (`-2 ** 2 == -4`); comparisons are non-associative and yield 1 or 0; negative exponent is a `DomainError`. Full table in spec sections 3 and 5.  
- **Reasoning:** Truncating `/` matches calculators and C-family languages; floor `//` and `%` match Python and the identity `a == (a // b) * b + a % b`. Both common intents are expressible.  
- **Affects:** `parser.py`, `evaluator.py`, tests.

**[D-07]** Error model.  
- **Date / Session:** 2026-10-26, APC planning session 1  
- **Decision:** `MiniCalcError` hierarchy (spec section 7). Each error carries `SourcePos` (line, col). `render()` prints a message plus source line plus caret. Errors never crash the REPL. Statements are atomic: a failed statement changes no variable and not `ans`. Golden tests compare only the error class and `line:col`, never message text.  
- **Reasoning:** Positioned, categorized errors satisfy 'handle errors like incorrect format' and the Runtime criterion; not comparing message text lets parallel authors word messages freely.  
- **Affects:** `errors.py`, all stages, golden tests.

**[D-08]** Names, `ans`, and reserved words.  
- **Date / Session:** 2026-10-26, APC planning session 1  
- **Decision:** Identifiers `[A-Za-z_][A-Za-z0-9_]*`, case-sensitive. `ans` is read-only and unset until the first successful statement. Reserved: `ans`, `abs`, `min`, `max`, `gcd`. Built-in names cannot be assigned or used as values. No user-defined functions.  
- **Reasoning:** Prevents shadowing bugs and keeps evaluation rules trivial to specify.  
- **Affects:** `environment.py`, `builtins.py`, `evaluator.py`.

**[D-09]** Interface (CLI/REPL) contract.  
- **Date / Session:** 2026-10-26, APC planning session 1  
- **Decision:** Modes: REPL (default), script file, `-e EXPR`. Prompt `minicalc> `. Results print `= <v>` or `<name> = <v>`. Meta-commands `:help :vars :clear :quit :q`. Exit codes 0 / 1 (a MiniCalc error occurred in script or `-e` mode) / 2 (usage). ANSI colors only on a TTY with `NO_COLOR` unset. Script mode continues after errors.  
- **Reasoning:** Directly targets the Runtime criterion (prompts, symbols, spacing) and makes behavior scriptable and testable.  
- **Affects:** `repl.py`, `display.py`, `__main__.py`, `main.py`.

**[D-10]** Test strategy.  
- **Date / Session:** 2026-10-26, APC planning session 1  
- **Decision:** `pytest`. Layers: unit tests per module, golden tests (`tests/golden`, format in interface-contract section 12), and a randomized differential test whose oracle is written from the spec only, by an agent that did not write the evaluator.  
- **Reasoning:** Independent verification catches shared misunderstandings; golden files double as the demo script for the presentation.  
- **Affects:** `tests/`, FEAT-005, INT-002.

**[D-11]** Documentation standard.  
- **Date / Session:** 2026-10-26, APC planning session 1  
- **Decision:** Every module has a docstring. Every class has a docstring with an `Attributes:` section describing every class variable and instance attribute. Every public function has a docstring with `Args:`/`Returns:`/`Raises:` as applicable. `scripts/check_docs.py` enforces this and must pass before submission.  
- **Reasoning:** The Documentation criterion explicitly requires descriptions of all class variables for the top band.  
- **Affects:** All code, DOC-001.

**[D-12]** Submission packaging.  
- **Date / Session:** 2026-10-26, APC planning session 1  
- **Decision:** The submission ZIP contains `minicalc/`, `tests/`, `examples/`, `main.py`, `README.md`, `docs/LANGUAGE.md` (and design docs it references). It excludes `.git/`, worktrees, `patch/`, `docs/reports/`, `docs/prompts/`, bundles, and caches. Built by `scripts/make_submission.py`, verified by unzipping into a clean directory and running the tests.  
- **Reasoning:** Graders need a clean, runnable, documented source tree, not orchestration artifacts. Verified unzip-and-run removes the largest delivery risk.  
- **Affects:** DOC-003.

**[D-13]** Parser error-message wording conventions (FEAT-002).  
- **Date / Session:** 2026-10-26, FEAT-002 implementation (Claude Code)  
- **Decision:** Messages are lowercase and name what was expected and what was found, using the token's quoted lexeme or `end of line` for `EOF`. The settled templates, one per line:
  - `expected an expression, found <token>`
  - `expected ')', found <token>`
  - `expected ',' or ')', found <token>`
  - `expected end of line, found <token>`
  - `comparison operators cannot be chained; add parentheses`
  - `left side of '=' must be a name`
  - `chained assignment is not supported`
  - `expression is nested too deeply`
- **Reasoning:** One consistent "expected/found" shape makes diagnostics predictable and actionable; naming the lexeme lets users see the exact offending punctuation. The two assignment rules are distinct messages because they diagnose different mistakes (a non-name left side vs. a second assignment). Golden tests compare class and position only ([D-07]), so wording stays free to improve.  
- **Affects:** `parser.py`, FEAT-004 (display of parser errors), DOC-002 (language documentation), FEAT-005 (golden cases).

**[D-14]** REPL/display wording, spacing, and foreign-exception behavior not fixed by the spec (FEAT-004).  
- **Date / Session:** 2026-10-26, FEAT-004 implementation session  
- **Decision:** Locked these details:  
  - The banner is four lines: a 44-character `-` rule, `MiniCalc 1.0  integer arithmetic language`, `Type :help for help, :quit to exit.`, and another rule. Color styles the title bold cyan and the hint dim. (The task prompt calls it "three lines" but enumerates four; the four enumerated lines were implemented.)  
  - Values are bold green (`ESC[1;32m`) in results and script outcomes; assignment names stay plain. Help section headings are bold cyan. `:vars` and `:clear` output is unstyled.  
  - `help_text()` has five sections separated by blank lines: Operators (highest to lowest precedence), Functions, Names, Commands, Examples. Rows are indented two spaces, use a 20-character left field, then two spaces before the description; each section ends with a blank line except the last.  
  - `:vars` prints `ans` first when set, then `Environment.items()` (sorted by name), left-padding names to the longest shown name. `(no variables)` is printed only when both `ans` and variables are empty. `:clear` counts variables only (not `ans`) and prints `Cleared N variable(s).` with the literal `(s)`.  
  - Unknown meta-commands print `Unknown command '<command>'. Type :help for a list.` as plain text, not as an error object. Commands are matched on the stripped line and are case-sensitive.  
  - EOF and `KeyboardInterrupt` at the prompt print one blank line and exit 0. A `StopIteration` from an injected input iterator is treated like EOF so scripted input cannot loop forever.  
  - Foreign exceptions print one line `Internal error: <Type>: <message>` (or `Internal error: <Type>` when the message is empty) through the REPL's configured output, and the REPL continues. Script mode reports the same line on stderr and exits 1; because `run_source` is one facade call, a foreign exception aborts the remaining script lines, while per-outcome formatting errors are caught and the loop continues. `-e` reports it on stderr and exits 1. No traceback is shown.  
  - Unreadable or non-UTF-8 script files print `minicalc: cannot read '<path>': <detail>` on stderr and exit 2. An empty `-e` result prints nothing rather than a blank line.  
- **Reasoning:** The spec and contract fix behavior but not exact wording, column widths, or the handling of unexpected exceptions; these choices keep output aligned, ASCII-safe, deterministic, and testable without touching the facade.  
- **Affects:** `minicalc/display.py`, `minicalc/repl.py`, `minicalc/__main__.py`, `main.py`, `tests/test_display.py`, `tests/test_cli.py`.

**[D-15]** Cross-stage discrepancies resolved during integration (INT-001).  
- **Date / Session:** 2026-10-26, INT-001 integration session  
- **Decision:** These rulings settle every seam discrepancy found between the merged tracks. The spec edit recording them is commit `44cd2c2` (`docs(spec): record Phase 2 rulings ...`), and `tests/golden/rulings.mc`/`.out` pins them (expectations written from the spec text before the code was run).  
  1. **`ans` and assignments.** `ans` changes only on a successful *expression*. A successful assignment binds its variable and returns `kind="assign"` but leaves `ans` unchanged. This **supersedes** the "unset until the first successful statement" wording in [D-08] and the older spec section 6 text. Reason: the section 1 and interface-contract section 12 examples (`2 + 3 * 4`, `x = 7`, `ans * x` gives `98`) only hold this way. Found by FEAT-005. Affects `minicalc/interpreter.py` (commit `7bff102`).  
  2. **`12é`.** Only an ASCII letter or `_` directly after digits triggers the "letter after digits" error at the start of the number. Any non-ASCII character is an ordinary illegal character at its own column, so `12é` is `LexError 1:3`. Spec section 2 now says "ASCII letter or `_`" and adds a `12é` row.  
  3. **`INT_MIN % -1`** is `0` (the result is in range, unlike `INT_MIN / -1`). Spec section 5 `%` row updated.  
  4. **Negative exponent** is a `DomainError` for every base, including `0` and `1`; that check precedes the `**` special cases. Spec section 5 updated.  
  5. **Reserved assignment target.** The reserved-name check runs before the right side is evaluated, so `ans = 1 / 0` and `abs = 1 / 0` are `AssignmentError 1:1`, not `DivisionByZeroError`. Spec section 6 updated.  
  6. **`gcd(INT_MIN, 0)` and `gcd(INT_MIN, INT_MIN)`** are `IntegerRangeError` at the call (the true result, 2147483648, is out of range). Spec section 6 built-in table updated.  
  7. **Parenthesis nesting boundary, measured on disk** with the real parser: 199 nested parentheses evaluate; 200 is `ParseError 1:201` (`parser.MAX_DEPTH = 200`). Through the facade the recursion-limit fallback never fires first; [D-13]'s limit remains unchanged.  
  8. **Script-mode line prefixes.** Spec section 8's "prefixed by the line number" is satisfied by `render()` naming the line ("at line N, column M") plus `line N: ` prefixes on results, per [D-14]. Script-mode errors go to stderr, so a caller that merges stdout and stderr may see error blocks before earlier results; this is a stream-buffering artifact of the [D-14] split, not a behavior mismatch. No code change.  
  9. **No further discrepancies.** Every worked example and every error row in spec sections 2, 3, and 5 reproduces exactly (class and `line:col`), and all public signatures in `interface-contract.md` matched through `inspect.signature`.  
- **Reasoning:** The spec is the arbiter; these are the questions the merged tracks answered differently or left open. Pinning each in both the spec and a golden file means a future regression shows up as a failing case rather than a rediscovered ambiguity.  
- **Affects:** `docs/context/language-spec.md`, `tests/golden/rulings.mc`, `tests/golden/rulings.out`, `minicalc/interpreter.py`, DOC-002 (must document rulings 1–7).

**[D-16]** Final submission ZIP packaging, verification, exclusions, determinism, and cut-line outcome (DOC-003).  
- **Date / Session:** 2026-10-30, DOC-003 implementation session (Gemini)  
- **Decision:** Locked submission packaging and delivery specifications:  
  1. **Packaging Builder (`scripts/make_submission.py`):** Packages the deliverable codebase into a clean, deterministic ZIP archive under a single top-level directory (`MiniCalc-CMPSC132-FinalProject/`) using standard forward slashes.  
  2. **Shipped Manifest:** Includes `minicalc/` (all modules), `tests/` (unit tests, golden tests, differential test harness, excluding internal tests), `examples/` (`01_basics.mc` through `06_showcase.mc`), `main.py`, `README.md`, `requirements-dev.txt`, `pytest.ini`, `docs/LANGUAGE.md`, `docs/PRESENTATION.md`, `docs/context/language-spec.md`, `docs/context/interface-contract.md`, and `scripts/check_docs.py`.  
  3. **Exclusion List:** Excludes `.git/`, worktrees, `patch/`, `docs/reports/`, `docs/prompts/`, `docs/tasks/`, `docs/decisions/`, `docs/guide/`, all other scripts (`make_submission.py`, `task-worktree.sh`, `apc-bundle.sh`, `manage-decisions.py`), build caches (`__pycache__`, `.pytest_cache`, `*.pyc`), `dist/`, `*.zip`, `.venv`, and `tests/test_make_submission.py`.  
  4. **`test_make_submission.py` Exclusion:** `tests/test_make_submission.py` specifically tests `scripts/make_submission.py`. Because `make_submission.py` is an internal orchestration script excluded from the final shipping ZIP, shipping `test_make_submission.py` would cause the test suite in the unpacked ZIP to fail with an import error. Therefore, `tests/test_make_submission.py` is excluded from the ZIP and this exclusion is asserted in its own unit test.  
  5. **Archive Determinism & 5 MB Cap:** All archive members use fixed timestamps (`2026-10-30 00:00:00`), standard UNIX file mode permissions (`0o644`), standard zip deflate compression, and lexicographically sorted member ordering. Independent builds produce byte-identical archives with matching SHA-256 hashes. The builder strictly enforces a 5 MB upper size cap (the built archive is ~119 KB).  
  6. **Automated Verification (`--verify`):** Extracts the archive into a fresh temporary directory and verifies that `pytest -q`, `scripts/check_docs.py`, one-shot CLI execution, `examples/01_basics.mc` (exit 0), `examples/05_errors.mc` (exit 1), and a clean scan of shipped documentation for excluded paths all pass cleanly.  
  7. **Cut-Line Outcome:** None. Zero features or planned deliverables were cut. All language requirements, grammar operators, 32-bit checked integer semantics, built-in functions, REPL and CLI modes, documentation standards, and verification suites were fully implemented and pass all tests.  
- **Reasoning:** Graders require an unencumbered, runnable, and verifiable project archive containing only the language implementation, documentation, and tests, free of development orchestration artifacts. Verifying the unpacked archive end-to-end eliminates packaging defects prior to final submission.  
- **Affects:** `scripts/make_submission.py`, `tests/test_make_submission.py`, `docs/guide/SUBMISSION-CHECKLIST.md`, and final distribution artifacts.

**[D-17]** Post-integration fixes: `ans` help wording and deterministic merged-stream order (FIX-001).  
- **Date / Session:** 2026-10-26, FIX-001 implementation session (Claude Code)  
- **Decision:** Two post-integration fixes.  
  1. **`ans` wording (Item A).** The `:help` Names row now reads `value of the last successful expression` (previously `... statement`), matching [D-15] item 1 and spec section 6. A repo-wide search for stale `ans` phrasing found: `minicalc/display.py:167` and `tests/test_cli.py:25` (**fixed**); `minicalc/environment.py:4`, `minicalc/environment.py:18-19`, `minicalc/environment.py:43`, `minicalc/environment.py:60`, `minicalc/environment.py:63`, `tests/test_evaluator.py:294`, and `tests/test_environment.py:24` (**not fixed here** — outside FIX-001's file scope; flagged in the report for a follow-up or DOC-001). The remaining code hits say "successful statement" or "evaluate a statement first" and imply an assignment can set `ans`.  
  2. **Stream order (Item B).** Script mode and `-e` mode now flush stdout before every write to stderr and flush stderr immediately after, via `_write_stderr` in `minicalc/__main__.py`. Which stream receives what ([D-14]) and all exit codes are unchanged; only flushing changed. A merged `2>&1` capture now shows results and errors in source-line order. This refines the "stream-buffering artifact" reading in [D-15] item 8 without changing the underlying split.  
  3. **[D-15] item 9 ("no further discrepancies") was incomplete** because of Item A: it missed the stale `ans` help text in `minicalc/display.py:167` (and the matching CLI test docstring).  
- **Reasoning:** [D-15] item 1 settles that only successful expressions update `ans`; shipping help text that says "statement" contradicts the spec to users. A misordered merged demo capture is a presentation risk, so explicit flushing is cheaper and safer than relying on buffer behaviour.  
- **Affects:** `minicalc/display.py`, `minicalc/__main__.py`, `tests/test_cli.py`, DOC-002 (help wording), and the unfixed hits listed above.

**[D-18]** Remaining stale `ans` wording and context-doc decision state (FIX-002).  
- **Date / Session:** 2026-10-26, FIX-002 implementation session (Claude Code)  
- **Decision:** Finished the wording and context-doc cleanup FIX-001 flagged.  
  1. **Wording fixes (Items A–C).** Changed every stale "statement" phrase about `ans` to "expression": `minicalc/environment.py:4` (module docstring), `:18` (class attribute docstring), `:60` (`record_result` docstring), `:63` (its `value` arg), and the user-visible error at `:43`, which now reads `ans has no value yet; evaluate an expression first` (one word changed). `tests/test_environment.py:24` asserts the new message; `tests/test_evaluator.py:294` now describes the undefined state in terms of a successful *expression*. `docs/context/complete-context.md:48` now reads `Locked decisions [D-01] to [D-15], [D-17], and [D-18]; [D-16] reserved for DOC-003`. Verified on disk before editing that `Environment.record_result` is called only from `minicalc/interpreter.py:111`, after the `isinstance(node, Assign)` early return, so only successful expression results update `ans`; assignments never do. No CLI or REPL test pinned the old message. No non-allowed hit remained in the Section 2D sweep; a broader grep found stale decision-count statements in `docs/tasks/high-level-tasks.md:15` and `docs/tasks/status.md:17` (both historical ARCH-001 rows) and `docs/prompts/ARCH-002.md:34`, which were listed in the report but not edited (out of scope).  
  2. **Ownership exception.** The APC authorized FIX-002 to edit `minicalc/environment.py`, whose original owner is CORE-003 (stub) then FEAT-003 (full) per `interface-contract.md` section 1, and `docs/context/complete-context.md`, a shared APC/operator context document with no per-task owner. Both edits are wording/status-only and are made now because DOC-001 (docstrings across the package) must not start until the wording is settled.  
  3. **INT-002 independence note.** INT-002's oracle independence is procedural, not lineage-based (the agent was Claude Code, not Gemini). The oracle was saved before any implementation file other than `limits.py` was opened. The agent then read `evaluator.py:80-169` and `parser.py:235-264` only to place its mutants, and disclosed this. Compensating check by the APC, run on the combined tree (INT-001 + FIX-001 + INT-002, 439 tests, Python 3.10.20 and 3.12.3): four APC-chosen mutants (`//` truncating instead of flooring; `%` taking the sign of the dividend; `<=` mutated to `<`; the `(-1) ** n` parity flipped) each made `tests/test_differential.py` fail, and the unmutated tree passes. The differential test compares value or error class only; error positions are covered by the golden files and the spec-table audit.  
  4. **No non-Claude lineage.** FEAT-005 was also written by Claude Code, so no non-Claude lineage reviewed any task; independence rests on process (spec-first expectations, isolated oracle) and on the APC's own checks.  
- **Reasoning:** [D-15] item 1 and spec section 6 settle that only successful expressions update `ans`. Leaving "statement" in user-visible text or in class docstrings contradicts the spec and would mislead DOC-001, which rewrites package docstrings. The context doc's decision range had been stale since [D-13].  
- **Affects:** `minicalc/environment.py`, `tests/test_environment.py`, `tests/test_evaluator.py`, `docs/context/complete-context.md`, DOC-001 (docstring baseline), DOC-002 (help/language docs).
