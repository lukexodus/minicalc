# MiniCalc Presentation & Defense Plan

This document outlines the presentation plan, live demonstration script, slide structure, and defense Q&A for MiniCalc, developed for **CMPSC 132: Programming Languages**.

---

## 1. 60-Second Elevator Pitch

"Good day! We present **MiniCalc**, a line-oriented programming language designed for integer arithmetic. While small in syntax, MiniCalc is engineered with full production rigor: it features a hand-written lexical scanner, a recursive-descent parser with formal operator precedence, an AST evaluator with strictly checked 32-bit signed arithmetic, and an interactive REPL with visual diagnostic carets. 

Unlike standard Python where integers expand unboundedly and hide overflow, MiniCalc guarantees that every operation stays within 32-bit limits, raising an immediate error on overflow or domain violation. Crucially, statements execute atomically—a failed calculation never corrupts variables or the `ans` accumulator. Built with zero runtime dependencies using only the Python standard library, MiniCalc achieves high reliability, complete documentation of all components, and verified correctness across unit, golden, and differential test suites."

---

## 2. Team Members & Speaker Allocation Table

### Group Members
- Adrian Luke A. Labasan
- Alejandrei Jazz F. Lopez
- Geila May C. Rigayen
- Melvie Jeanna O. Abad

| Section / Slide | Topic | Assigned Speaker | Target Time |
| :--- | :--- | :--- | :---: |
| Slide 1 | Introduction, Architecture & Project Scope | *(leave blank for speaker)* | 1.0 min |
| Slide 2 | Language Features & PL Design Criteria | *(leave blank for speaker)* | 1.5 min |
| Slide 3 | Grammar, Precedence & Recursive Descent | *(leave blank for speaker)* | 1.5 min |
| Slide 4 | Checked Integer Model & Error Handling | *(leave blank for speaker)* | 1.5 min |
| Slide 5 | Live Demonstration (`tests/golden/demo.mc`) | *(leave blank for speaker)* | 2.0 min |
| Slide 6 | Verification, Testing & Extensibility | *(leave blank for speaker)* | 1.5 min |
| Q&A | Defense & Evaluator Questions | All Team Members | ~3.0 min |

---

## 3. Live Demonstration Script

The live demonstration uses the verified test file `tests/golden/demo.mc` to showcase variable assignment, expression evaluation, `ans` tracking, built-ins, and multi-family error handling with diagnostic carets.

### Command Execution
```bash
python -m minicalc tests/golden/demo.mc
```

### Script Source (`tests/golden/demo.mc`)
```text
# MiniCalc demo session: variables, ans, built-ins, comparisons, one error per family
x = 7
y = 3
x * y + 2
ans + x
max(x, y) ** 2
min(x, y) == y
abs(-x)
gcd(x, y)
x = 1 / 0
x
2 +
3.14
ans
max(abs(-10), 3)
```

### Real Captured Output
```text
line 2: x = 7
line 3: y = 3
line 4: = 23
line 5: = 30
line 6: = 49
line 7: = 1
line 8: = 7
line 9: = 1
Error: Runtime error at line 10, column 7: division by zero
  x = 1 / 0
        ^
line 11: = 7
Error: Syntax error at line 12, column 4: expected an expression, found end of line
  2 +
     ^
Error: Lexical error at line 13, column 2: decimals are not supported; MiniCalc works with integers only
  3.14
   ^
line 14: = 7
line 15: = 10
```

### Talking Points During Demo
1. **Lines 2–3 (Variables):** Variable assignments (`x = 7`, `y = 3`) echo cleanly with line prefixes.
2. **Lines 4–5 (`ans` Accumulator):** `x * y + 2` yields `23`. Next line `ans + x` uses `23 + 7 = 30`, proving expression chaining.
3. **Lines 6–9 (Built-ins & Comparisons):** `max(7, 3) ** 2 = 49`; relational comparison `min(7, 3) == 3` yields integer `1` (true); `abs(-7) = 7`; `gcd(7, 3) = 1`.
4. **Line 10 (Division by Zero & Atomic Statements):** `x = 1 / 0` triggers a `DivisionByZeroError` with an exact caret at column 7.
5. **Line 11 (State Preservation):** Evaluating `x` shows `x = 7`, demonstrating that the failed assignment in line 10 did not overwrite `x`.
6. **Lines 12–13 (Syntax and Lexical Errors):** Shows `ParseError` on incomplete expression `2 +` and `LexError` on unsupported floating decimal `3.14`.
7. **Line 14 (`ans` Preservation):** `ans` still evaluates to `7` (from `abs(-x)` on line 8), proving errors do not corrupt `ans`.
8. **Line 15 (Function Composition):** Nested calls `max(abs(-10), 3)` evaluate cleanly to `10`.

---

## 4. 6-Slide Outline (Mapped to Grading Rubric)

### Slide 1: Introduction & Architecture (Rubric: Requirements & Delivery)
- **Title:** MiniCalc: A Verified Arithmetic Programming Language
- **Context:** CMPSC 132 Final Project; team project delivered on time.
- **Pipeline Architecture:**
  $$\text{Source Line} \longrightarrow \text{Lexer} \longrightarrow [\text{Token}] \longrightarrow \text{Parser} \longrightarrow \text{AST} \longrightarrow \text{Evaluator}(\text{Environment}) \longrightarrow \text{Result}$$
- **Zero Runtime Dependencies:** Python 3.10+ standard library only; cross-platform without installation overhead.

### Slide 2: Language Features & Expressiveness (Rubric: Requirements & PL Criteria)
- **Features:** Integer arithmetic (`+ - * / // % **`), comparisons (`== != < <= > >=`), variables, read-only `ans`, built-ins (`abs min max gcd`).
- **PL Evaluation Criteria:**
  - *Readability:* Mathematical infix notation, line orientation, `#` comments.
  - *Writability:* `ans` chaining, built-in functions, dual division modes.
  - *Orthogonality:* Expressions nest uniformly across calls, operands, and assignments.
  - *Simplicity:* One value type (32-bit signed int), small fixed grammar.

### Slide 3: Grammar, Precedence & Parser Architecture (Rubric: Presentation)
- **EBNF Grammar:** Structured explicitly into 6 precedence tiers.
- **Precedence Hierarchy:** Calls/Parens $\to$ Exponentiation (`**`) $\to$ Unary (`+ -`) $\to$ Multiplicative (`* / // %`) $\to$ Additive (`+ -`) $\to$ Relational (`== != < <= > >=`).
- **Hand-Written Recursive Descent:** Modular methods per non-terminal (`parse_additive`, `parse_term`, `parse_power`, `parse_unary`).
- **Right-Associativity:** Direct recursion handles `2 ** 3 ** 2 == 512`.

### Slide 4: Checked Integer Model & Error Diagnostics (Rubric: Runtime & Reliability)
- **32-Bit Range:** Strict enforcement $[-2^{31}, 2^{31} - 1]$ on every intermediate operation.
- **Preventing Denial-of-Service:** Power short-circuit (`|base| >= 2` and `exp > 31`) rejects massive exponents instantly in $O(1)$.
- **Diagnostic Carets:** 8 specialized error classes under `MiniCalcError`; 1-based line:column coordinates with visual carets.
- **Atomic Execution:** Errors rollback all modifications, preserving variable and `ans` state.

### Slide 5: Quality Assurance & Verification (Rubric: Documentation & Testing)
- **Documentation Standard:** Every class variable and function fully documented; validated automatically by `scripts/check_docs.py`.
- **Three-Tier Testing Pyramid:**
  1. *Unit Tests:* Comprehensive tests for lexer, parser, evaluator, environment, CLI, and errors.
  2. *Golden Tests:* Specification-derived `.mc` / `.out` test suites covering arithmetic, edge cases, and rulings.
  3. *Differential Testing:* Randomized differential test against an independently written oracle.

### Slide 6: Summary & Live Demonstration (Rubric: Presentation & Runtime)
- **Execution Proof:** Real-time demonstration with `tests/golden/demo.mc`.
- **Clean Interface:** REPL with meta-commands (`:help`, `:vars`, `:clear`, `:quit`), `--no-color` support, and script runners.
- **Future Extensibility:** Clean AST separation provides a direct path for future additions (e.g., float types, user functions).

---

## 5. Defense Q&A: 12 Likely Questions & Concise Answers

### Q1: Why choose a hand-written recursive-descent parser instead of a parser generator like Lark or PLY?
**Answer:** A hand-written recursive-descent parser gives us total control over token coordinates, customized error diagnostics, and caret positioning. It avoids heavy third-party dependencies, conforms to our standard-library-only requirement, and makes the grammar transformations easy to trace and defend.

### Q2: How does the grammar encode operator precedence without ambiguity?
**Answer:** Precedence is encoded structurally into the stratification of grammar rules. Each precedence level corresponds to a separate non-terminal rule: `expression` handles comparisons, `additive` handles `+` and `-`, `term` handles `* / // %`, `unary` handles prefix signs, and `power` handles `**`. Lower-precedence rules call higher-precedence rules, naturally enforcing the correct evaluation order in the parse tree.

### Q3: Why does `-2 ** 2` evaluate to `-4` instead of `4`?
**Answer:** In MiniCalc, as in Python, mathematics, and our EBNF grammar, exponentiation (`**`) binds tighter than unary minus. The expression is parsed as `-(2 ** 2) = -4`. To square negative two, explicit parentheses are required: `(-2) ** 2 == 4`.

### Q4: How does MiniCalc detect and handle integer overflow?
**Answer:** Native Python integers have unbounded precision. To maintain a strict 32-bit integer model, MiniCalc checks every intermediate result against `INT_MIN` ($-2,147,483,648$) and `INT_MAX` ($2,147,483,647$) using `limits.in_range()`. If a value falls outside this range, an `IntegerRangeError` is raised immediately, preventing silent wraparound.

### Q5: What are atomic statements and how are they implemented?
**Answer:** Atomic statement execution means a statement either completes successfully or leaves the program environment completely unchanged. In `Interpreter.run_line`, the right-hand side is evaluated before variable binding occurs, and `ans` is only updated after a successful expression. If an exception occurs, the assignment never takes effect and `ans` remains intact.

### Q6: What does the differential test prove, and what does it NOT prove?
**Answer:** The differential test cross-checks MiniCalc's evaluator against an independently developed specification oracle across 5,600+ randomized expressions. It proves that the evaluated values and error classes match the specification across thousands of generated inputs. However, it does **not** compare error message phrasing or caret coordinates (which are verified separately by our golden test suite), and the oracle was written from the specification rather than being an external commercial interpreter.

### Q7: How are source positions captured and rendered with visual carets?
**Answer:** Every `Token` emitted by the lexer stores a `SourcePos` dataclass containing 1-based `line` and `col` values. When an error is raised, the offending token's `pos` is attached to `MiniCalcError`. The `render()` method extracts the source line and computes an indentation margin of $2 + (\text{col} - 1)$ spaces before placing the caret `^`.

### Q8: How does `ans` behave across expressions and variable assignments?
**Answer:** `ans` is updated only upon the evaluation of a successful *expression*. Variable assignments (`x = 5`) do not update `ans`. If an expression fails, `ans` retains its previous value. Prior to any successful expression, reading `ans` raises an `UndefinedNameError`.

### Q9: How would you extend MiniCalc to support floating-point numbers?
**Answer:** We would add a `FLOAT` token type in the lexer for decimal literals (`[0-9]+\.[0-9]+`), introduce a `Value` union or float type in AST nodes and the evaluator, implement IEEE 754 precision rules, adjust `/` to return floating-point values, and define type promotion rules when mixing integers and floats.

### Q10: How would you extend MiniCalc to support user-defined functions?
**Answer:** We would extend the grammar with function definition syntax (`def f(x) = expr`), add a `FunctionDef` AST node, enhance the `Environment` with a frame-based call stack for local variable scoping, and evaluate function bodies by creating a child environment populated with argument bindings.

### Q11: Why provide both truncating division `/` and flooring division `//`?
**Answer:** Truncating division (`/`) rounds toward zero, matching C, Java, and conventional desk calculators. Flooring division (`//`) rounds toward negative infinity and pairs with floored modulo (`%`), guaranteeing the mathematical identity $a = (a // b) \times b + a \% b$. Providing both allows users to select the exact division semantics appropriate for their calculation.

### Q12: How does the exponentiation guard protect against denial-of-service?
**Answer:** If $|base| \ge 2$, any exponent greater than 31 will overflow 32-bit signed limits (since $2^{31} > \text{INT\_MAX}$). Rather than attempting to compute massive values like $2^{1000000000}$ (which would freeze CPU or exhaust RAM), MiniCalc inspects the exponent first and raises `IntegerRangeError` in $O(1)$ time without computing the power.
