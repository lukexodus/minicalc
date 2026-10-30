# MiniCalc

MiniCalc is a line-oriented programming language designed for integer arithmetic, developed as the final project for **CMPSC 132: Programming Languages**. Written in Python 3.10+ using only the standard library, MiniCalc implements a full language execution pipeline consisting of a hand-written lexical scanner, a precedence-aware recursive-descent parser, an Abstract Syntax Tree (AST) evaluator with checked 32-bit signed arithmetic, and an interactive Read-Eval-Print Loop (REPL). It combines robust error diagnostics with visual caret formatting, transactional statement execution, and zero runtime dependencies.

For the full specification and language manual, see the [Language Reference](docs/LANGUAGE.md). For presentation notes and demo scripts, see [Presentation Notes](docs/PRESENTATION.md).

---

## Requirements

- **Runtime:** Python 3.10 or higher.
- **Dependencies:** None. MiniCalc relies strictly on Python's standard library at runtime.
- **Development & Testing:** `pytest` (listed in `requirements-dev.txt`).

---

## Quick Start

MiniCalc supports three primary execution modes: interactive REPL, script file execution, and one-shot expression evaluation. You can launch MiniCalc either as an installed module (`python -m minicalc`) or through the root shim script (`python main.py`).

### 1. Interactive REPL
Start the interactive shell:
```bash
python -m minicalc
# or:
python main.py
```

### 2. Script File Execution
Execute a MiniCalc script file (`.mc`):
```bash
python -m minicalc examples/01_basics.mc
# or:
python main.py examples/06_showcase.mc
```

### 3. One-Shot Expression Mode
Evaluate a single expression from the command line:
```bash
python -m minicalc -e "2 + 3 * 4"
# Output:
# = 14
```

### Command-Line Options
MiniCalc provides standard command-line flags:
- `-e EXPR`, `--expr EXPR`: Evaluate a single expression and terminate.
- `--no-color`: Disable ANSI color escape codes (also automatically disabled when output is redirected or when `NO_COLOR` environment variable is set).
- `--version`: Display the version string (`MiniCalc 1.0.0`) and exit.
- `-h`, `--help`: Display the command-line usage summary.

---

## Exit Codes

MiniCalc returns deterministic process exit codes:
- `0`: Success. All statements executed cleanly.
- `1`: Language error. At least one MiniCalc error (lexical, syntax, or runtime) occurred during script execution or one-shot evaluation.
- `2`: Command-line usage or I/O error (such as an invalid flag or an unreadable file).

---

## Interactive REPL Transcript

Below is a verbatim interactive session transcript captured using MiniCalc's REPL driver:

```text
--------------------------------------------
MiniCalc 1.0  integer arithmetic language
Type :help for help, :quit to exit.
--------------------------------------------
minicalc> 2 + 3 * 4
= 14
minicalc> x = 7
x = 7
minicalc> ans * x
= 98
minicalc> abs(-42) + max(10, 20)
= 62
minicalc> gcd(48, 18)
= 6
minicalc> :vars
ans = 6
x   = 7
minicalc> :quit
```

Within the REPL, several meta-commands are available:
- `:help` — View available operators, built-in functions, and command usage.
- `:vars` — List currently defined variables and `ans`.
- `:clear` — Clear all user-defined variables (`ans` is preserved).
- `:quit` or `:q` — Terminate the interactive session cleanly (also exited via `Ctrl-D` / `Ctrl-C`).

---

## Features

- **Line-Oriented Syntax:** One statement per line with support for inline comments beginning with `#`.
- **Checked 32-Bit Integer Arithmetic:** Operates strictly within signed 32-bit limits (`-2,147,483,648` to `2,147,483,647`). Any overflow raises an `IntegerRangeError` rather than silently wrapping or expanding unbounded.
- **Rich Operator Suite:** Addition (`+`), subtraction (`-`), multiplication (`*`), truncating division (`/`), floor division (`//`), floored modulo (`%`), and right-associative exponentiation (`**`).
- **Relational Comparisons:** Non-chainable comparison operators (`==`, `!=`, `<`, `<=`, `>`, `>=`) returning `1` for true and `0` for false.
- **Variables & `ans`:** Case-sensitive identifiers with variable assignment (`var = expr`). The special keyword `ans` automatically tracks the result of the most recent successful expression.
- **Built-in Functions:** Built-in mathematical functions `abs(x)`, `min(a, b, ...)`, `max(a, b, ...)`, and `gcd(a, b)`.
- **Atomic Statement Semantics:** Statements are executed transactionally. If an error occurs during evaluation, variable assignments are rolled back and `ans` remains unchanged.
- **Accurate Diagnostic Carets:** Informative multi-line error messages with precise 1-based line and column pointers.

---

## Error Handling

MiniCalc detects and reports eight distinct classes of errors across the compilation and execution pipeline. Every error displays the source line and points an alignment caret (`^`) directly under the offending token.

### Syntax Error Example
```text
minicalc> 2 + * 3
Error: Syntax error at line 1, column 5: expected an expression, found '*'
  2 + * 3
      ^
```

### Runtime Error Example
```text
minicalc> 10 / 0
Error: Runtime error at line 1, column 4: division by zero
  10 / 0
     ^
```

In script mode, execution continues following an error so that all errors in a file can be inspected, exiting with status code `1` upon completion.

---

## Project Structure

```text
.
├── docs/
│   ├── context/
│   │   ├── interface-contract.md   # Python module and class interface contracts
│   │   └── language-spec.md        # Authoritative language specification
│   ├── LANGUAGE.md                 # Complete MiniCalc language reference & design evaluation
│   └── PRESENTATION.md             # Project presentation plan, demo script & Q&A
├── examples/
│   ├── 01_basics.mc                # Basic arithmetic, comments, and line orientation
│   ├── 02_precedence.mc            # Operator precedence, associativity, and comparisons
│   ├── 03_variables.mc             # Variables, assignment, and ans behavior
│   ├── 04_builtins.mc              # Built-in mathematical functions (abs, min, max, gcd)
│   ├── 05_errors.mc                # Catalog of all 8 error families (exits with code 1)
│   └── 06_showcase.mc              # Real-world computations: compound interest, gcd, powers
├── minicalc/
│   ├── __init__.py                 # Package version definition
│   ├── __main__.py                 # CLI entry point, argument parsing, and stream routing
│   ├── ast_nodes.py                # Frozen dataclass AST node definitions
│   ├── builtins.py                 # Mathematical built-in function handlers
│   ├── display.py                  # Terminal output formatting, banners, and ANSI color logic
│   ├── environment.py              # Symbol table environment for variables and ans
│   ├── errors.py                   # MiniCalcError hierarchy and visual caret rendering
│   ├── evaluator.py                # Tree-walking AST evaluator with checked 32-bit arithmetic
│   ├── interpreter.py              # Pipeline facade coordinating lexer, parser, and evaluator
│   ├── lexer.py                    # Hand-written regular lexical scanner
│   ├── limits.py                   # 32-bit integer boundaries and line limits
│   ├── parser.py                   # Precedence-aware recursive-descent parser
│   ├── repl.py                     # Interactive REPL loop and meta-command processor
│   └── tokens.py                   # Token types and token representations
├── scripts/check_docs.py           # Documentation and class variable docstring validator
├── tests/
│   ├── golden/                     # Golden test programs (*.mc) and expected outputs (*.out)
│   ├── conftest.py                 # Pytest fixtures and test discovery configuration
│   ├── golden_format.py            # Golden file format serializer and parser
│   ├── oracle.py                   # Independent differential testing oracle
│   ├── test_builtins.py            # Unit tests for built-in functions
│   ├── test_check_docs.py          # Unit tests for documentation checker script
│   ├── test_cli.py                 # Integration tests for CLI arguments and REPL
│   ├── test_differential.py       # Randomized differential tests against independent oracle
│   ├── test_display.py             # Unit tests for display formatting and ANSI styling
│   ├── test_environment.py         # Unit tests for variable storage and ans tracking
│   ├── test_errors.py              # Unit tests for error hierarchy and caret rendering
│   ├── test_evaluator.py           # Unit tests for AST evaluator and checked arithmetic
│   ├── test_golden.py              # Test suite running all golden test programs
│   ├── test_golden_format.py       # Unit tests for golden output serialization
│   ├── test_interpreter.py         # Unit tests for interpreter facade coordination
│   ├── test_lexer.py               # Unit tests for lexical scanner
│   ├── test_package.py             # Tests for package exports and versioning
│   ├── test_parser.py              # Unit tests for recursive-descent parser
│   └── test_vocabulary.py          # Unit tests for AST nodes, tokens, and bounds
├── main.py                         # Root entry point shim (python main.py)
├── pytest.ini                      # Pytest suite configuration
├── README.md                       # Project overview, quick start, and documentation manual
└── requirements-dev.txt            # Development dependencies (pytest)
```

---

## Running Tests

MiniCalc features an extensive automated test suite including unit tests, golden input/output tests, and randomized differential testing against an independent oracle.

1. **Install Test Dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Execute Full Test Suite:**
   ```bash
   pytest -q
   ```

3. **Verify Documentation Coverage:**
   MiniCalc includes an automated validator enforcing comprehensive class and function docstrings:
   ```bash
   python scripts/check_docs.py
   ```
