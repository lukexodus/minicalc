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

**[D-13]** RESERVED for FEAT-002: parser error-message wording conventions.  
- **Date / Session:** reserved 2026-10-26  
- **Decision:** (to be written by the agent running FEAT-002)  
- **Reasoning:** (to be written)  
- **Affects:** (to be written)

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

**[D-15]** RESERVED for INT-001: resolution of cross-stage discrepancies found during integration.  
- **Date / Session:** reserved 2026-10-26  
- **Decision:** (to be written by the agent running INT-001)  
- **Reasoning:** (to be written)  
- **Affects:** (to be written)

**[D-16]** RESERVED for DOC-003: final submission checklist outcomes and any cut-line decisions.  
- **Date / Session:** reserved 2026-10-26  
- **Decision:** (to be written by the agent running DOC-003)  
- **Reasoning:** (to be written)  
- **Affects:** (to be written)
