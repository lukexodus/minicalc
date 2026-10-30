# MiniCalc Language Reference

MiniCalc is a line-oriented, statically bounded integer arithmetic language designed for CMPSC 132 (Programming Languages). This document serves as the complete reference for the language's lexical conventions, syntax grammar, operator semantics, runtime model, diagnostic errors, and architectural design evaluations.

For module interfaces and implementation contracts, refer to the companion documents [Language Specification](context/language-spec.md) and [Interface Contract](context/interface-contract.md).

---

## 1. Lexical Conventions

MiniCalc processes source input line by line. Source files typically use the `.mc` extension and must be UTF-8 encoded.

### 1.1 Tokens

The language recognizes the following token classes:

| Token Name | Source Pattern | Description |
| :--- | :--- | :--- |
| `NUMBER` | `[0-9]+` | Non-negative decimal integer literals (range `0` to `2147483647`). |
| `IDENT` | `[A-Za-z_][A-Za-z0-9_]*` | Case-sensitive variable identifiers and built-in function names. |
| Arithmetic Ops | `+`, `-`, `*`, `/`, `//`, `%`, `**` | Arithmetic operators. Longest-match rule applies: `**` before `*`, `//` before `/`. |
| Relational Ops | `==`, `!=`, `<`, `<=`, `>`, `>=` | Comparison operators. Longest-match rule applies: `==` before `=`. |
| `ASSIGN` | `=` | Variable assignment operator. |
| Delimiters | `(`, `)`, `,` | Grouping parentheses and function argument separators. |
| `EOF` | End-of-line | Implicit terminator emitted at the end of every line (column `len(line) + 1`). |

### 1.2 Whitespace and Comments
- Whitespace characters (ASCII spaces, tabs, and carriage returns `\r`) serve solely to separate adjacent tokens and are otherwise discarded. Windows-style CRLF and Unix LF line endings are supported seamlessly.
- Comments begin with `#` and continue to the end of the line.
- Source line and column numbers are 1-based. Each tab character counts as a single column.
- MiniCalc strictly requires ASCII characters for all code tokens. Any non-ASCII character (such as curly quotes or accented letters) triggers an immediate lexical error at the offending column.

---

## 2. Grammar (EBNF)

MiniCalc expressions and statements are defined by the following Extended Backus-Naur Form (EBNF) grammar. In this specification, `[ ... ]` denotes optional constructs and `{ ... }` denotes zero or more repetitions.

```ebnf
line        = [ statement ] EOF ;
statement   = assignment | expression ;
assignment  = IDENT ASSIGN expression ;
expression  = additive [ compare_op additive ] ;      (* comparisons are non-associative *)
compare_op  = EQ | NE | LT | LE | GT | GE ;
additive    = term { ( PLUS | MINUS ) term } ;
term        = unary { ( STAR | SLASH | DSLASH | PERCENT ) unary } ;
unary       = ( MINUS | PLUS ) unary | power ;
power       = primary [ POW unary ] ;                 (* right-associative *)
primary     = NUMBER | IDENT | call | LPAREN expression RPAREN ;
call        = IDENT LPAREN [ expression { COMMA expression } ] RPAREN ;
```

A line containing only whitespace or comments yields an empty statement. A line is classified as an assignment if its first two tokens are `IDENT ASSIGN`.

---

## 3. Operator Precedence and Associativity

Operators are evaluated in order of priority from highest (Level 1) to lowest (Level 6):

| Level | Operators | Associativity | Description |
| :---: | :--- | :---: | :--- |
| **1** | `( )`, function calls | N/A | Grouping parentheses and function invocation |
| **2** | `**` | Right | Exponentiation (e.g., `2 ** 3 ** 2` is `2 ** (3 ** 2) = 512`) |
| **3** | `+`, `-` (unary) | Right (prefix) | Unary positive identity and negation |
| **4** | `*`, `/`, `//`, `%` | Left | Multiplication, truncating division, floor division, modulo |
| **5** | `+`, `-` (binary) | Left | Binary addition and subtraction |
| **6** | `==`, `!=`, `<`, `<=`, `>`, `>=` | None | Relational comparisons (cannot be chained without parentheses) |

### Key Precedence Implications
- **Exponentiation vs. Unary Minus:** Because `**` has higher precedence than unary `-`, an expression such as `-2 ** 2` parses as `-(2 ** 2)` and evaluates to `-4`. To square negative two, explicit grouping is required: `(-2) ** 2 == 4`.
- **Non-Chaining Comparisons:** Relational operators cannot be chained. Writing `1 < 2 < 3` results in a syntax error; it must be written using parentheses or decomposed into explicit sub-expressions.

---

## 4. Integer Model and Checked Arithmetic

MiniCalc values are strictly **signed 32-bit integers**:
$$\text{INT\_MIN} = -2,147,483,648 \quad (-2^{31})$$
$$\text{INT\_MAX} = 2,147,483,647 \quad (2^{31} - 1)$$

### Why 32-Bit Checked Arithmetic?
Standard Python integers feature arbitrary precision, which silently hides algorithmic overflow and can cause runaway CPU and memory consumption. MiniCalc enforces explicit signed 32-bit bounds on **every** intermediate and final calculation:
- If any operation computes a value outside $[-2,147,483,648, 2,147,483,647]$, an `IntegerRangeError` is raised immediately.
- Arithmetic never silently overflows or wraps around modulo $2^{32}$.
- Integer literals are non-negative; `-5` is parsed as unary negation applied to the literal `5`.
- Because the maximum literal value is $2,147,483,647$, the boundary value `INT_MIN` cannot be entered as a positive literal. In accordance with standard C conventions, it is written as `-2147483647 - 1`.
- Boolean types do not exist; comparison operators yield integer `1` (true) or `0` (false).

---

## 5. Operator Semantics

MiniCalc provides comprehensive arithmetic and comparison operators:

| Operator | Syntax | Semantics | Error Conditions |
| :--- | :--- | :--- | :--- |
| **Addition** | `a + b` | Standard addition | `IntegerRangeError` on overflow |
| **Subtraction** | `a - b` | Standard subtraction | `IntegerRangeError` on overflow |
| **Multiplication** | `a * b` | Standard multiplication | `IntegerRangeError` on overflow |
| **Truncating Division** | `a / b` | Integer division truncated toward zero (C-style) | `DivisionByZeroError` if $b=0$; `IntegerRangeError` for $\text{INT\_MIN} / -1$ |
| **Floor Division** | `a // b` | Integer division rounded toward negative infinity (Python-style) | `DivisionByZeroError` if $b=0$; `IntegerRangeError` for $\text{INT\_MIN} // -1$ |
| **Floored Modulo** | `a % b` | Modulo paired with `//`, satisfying $a = (a // b) \times b + a \% b$. Result takes the sign of $b$ | `DivisionByZeroError` if $b=0$; $\text{INT\_MIN} \% -1 = 0$ (in range) |
| **Exponentiation** | `a ** b` | Powers with non-negative exponent ($b \ge 0$) | `DomainError` if $b < 0$; `IntegerRangeError` on overflow |
| **Unary Minus** | `-a` | Arithmetic negation | `IntegerRangeError` for $-\text{INT\_MIN}$ |
| **Unary Plus** | `+a` | Arithmetic identity | None |
| **Comparisons** | `==`, `!=`, `<`, `<=`, `>`, `>=` | Relational test, yielding `1` (true) or `0` (false) | None |

### Exponentiation Rules
- $x^0 = 1$ for all integers $x$, including $0^0 = 1$.
- $0^b = 0$ for all $b > 0$.
- $1^b = 1$ for all $b \ge 0$.
- $(-1)^b$ evaluates to $1$ when $b$ is even and $-1$ when $b$ is odd.
- **Short-Circuit Overflow Guard:** When $|x| \ge 2$ and $b > 31$, MiniCalc raises `IntegerRangeError` immediately without computing the power. For example, `2 ** 1000000000` halts instantly in $O(1)$ time rather than exhausting memory.
- Negative exponents always raise `DomainError`, even for bases `0` and `1`.

### Worked Examples (Verified against Live Runtime)

The following table lists verified worked examples executed directly against the MiniCalc engine:

| Input Expression | Produced Result | Underlying Rule / Rationale |
| :--- | :---: | :--- |
| `2 + 3 * 4` | `14` | Multiplication binds tighter than addition |
| `(2 + 3) * 4` | `20` | Parentheses override default operator precedence |
| `10 - 3 - 2` | `5` | Subtraction is left-associative: `(10 - 3) - 2` |
| `-2 ** 2` | `-4` | `**` binds tighter than unary minus: `-(2 ** 2)` |
| `2 ** 3 ** 2` | `512` | `**` is right-associative: `2 ** (3 ** 2) = 2 ** 9` |
| `2 ** 30` | `1073741824` | Valid 32-bit positive power within bounds |
| `7 / 2` | `3` | Truncating division toward zero |
| `-7 / 2` | `-3` | Truncating division rounds toward zero |
| `7 // 2` | `3` | Floor division rounds toward negative infinity |
| `-7 // 2` | `-4` | Floor division rounds down to $-4$ |
| `-7 % 2` | `1` | Floored modulo takes the positive sign of the divisor $2$ |
| `7 % -2` | `-1` | Floored modulo takes the negative sign of the divisor $-2$ |
| `-7 % -2` | `-1` | Floored modulo with negative dividend and divisor |
| `5 > 3` | `1` | Comparison true evaluates to integer `1` |
| `5 == 4` | `0` | Comparison false evaluates to integer `0` |
| `2 + 3 == 5` | `1` | Arithmetic binds tighter than relational operators |
| `-2147483647 - 1` | `-2147483648` | Boundary representation of `INT_MIN` |

---

## 6. Variables, Environment, and `ans`

### 6.1 Variable Assignment and Usage
- Variables are assigned with `name = expression`. The assigned value is bound to `name` in the environment and echoed as `name = <value>`.
- Variable names are case-sensitive identifiers matching `[A-Za-z_][A-Za-z0-9_]*`.
- Referencing an identifier that has not yet been assigned raises an `UndefinedNameError`.

### 6.2 The Special Identifier `ans`
- `ans` is a built-in, read-only variable that stores the result of the **most recent successful expression**.
- **Assignments do not change `ans`:** Evaluating `x = 7` binds `x` but leaves `ans` holding the value of the expression evaluated prior to that assignment.
- `ans` is unset until the first successful expression has executed. Referencing `ans` prior to any successful expression raises an `UndefinedNameError`.
- `ans` cannot be reassigned; attempts to execute `ans = expr` raise an `AssignmentError`.

### 6.3 Atomic Statement Execution
MiniCalc statements execute transactionally:
- If an evaluation fails at any point during a statement (due to syntax, division by zero, overflow, or undefined names), the environment is left completely unmodified.
- No variable is updated, and `ans` retains its prior value.

---

## 7. Built-in Functions

MiniCalc includes four core mathematical functions. User-defined functions are deliberately excluded.

| Function | Arity | Description | Boundary Conditions |
| :--- | :---: | :--- | :--- |
| `abs(x)` | 1 | Absolute value of $x$. | `abs(-2147483647 - 1)` raises `IntegerRangeError` because $+2,147,483,648$ exceeds `INT_MAX`. |
| `min(a, b, ...)` | $\ge 1$ | Returns the smallest argument. | Arity checked prior to argument evaluation. |
| `max(a, b, ...)` | $\ge 1$ | Returns the largest argument. | Arity checked prior to argument evaluation. |
| `gcd(a, b)` | 2 | Greatest common divisor, always $\ge 0$. | $\text{gcd}(0, 0) = 0$. $\text{gcd}(\text{INT\_MIN}, 0)$ and $\text{gcd}(\text{INT\_MIN}, \text{INT\_MIN})$ raise `IntegerRangeError`. |

- Built-in names are reserved words. They cannot be assigned to (`abs = 5` raises `AssignmentError`) or used as values without arguments (`abs + 1` raises `UndefinedNameError`).
- Calling an undefined function or supplying the wrong number of arguments raises a `CallError`.
- Argument arity is validated before argument expressions are evaluated.

---

## 8. Error Catalog and Diagnostics

MiniCalc defines eight specialized error classes under the `MiniCalcError` hierarchy. Every diagnostic includes a descriptive message, the 1-based source position, the source line, and an alignment caret pointing to the error location.

Below are verbatim outputs captured from real runs:

### 1. `LexError`
Raised during lexical scanning for invalid tokens, unsupported decimals, or malformed numbers.
```text
Error: Lexical error at line 1, column 2: decimals are not supported; MiniCalc works with integers only
  3.14
   ^
```

### 2. `ParseError`
Raised during parsing for syntax violations, missing operands, unclosed parentheses, or chained comparisons.
```text
Error: Syntax error at line 1, column 5: expected an expression, found '*'
  2 + * 3
      ^
```

### 3. `DivisionByZeroError`
Raised during evaluation when division, floor division, or modulo has a divisor of zero.
```text
Error: Runtime error at line 1, column 4: division by zero
  10 / 0
     ^
```

### 4. `IntegerRangeError`
Raised when any arithmetic result or literal exceeds the signed 32-bit integer range.
```text
Error: Runtime error at line 1, column 12: integer result out of 32-bit range
  2147483647 + 1
             ^
```

### 5. `DomainError`
Raised when an operation receives an input outside its mathematical domain, such as a negative exponent.
```text
Error: Runtime error at line 1, column 3: negative exponent
  2 ** -1
    ^
```

### 6. `UndefinedNameError`
Raised when an unbound variable or unset `ans` is referenced, or a built-in is used as a bare value.
```text
Error: Runtime error at line 1, column 1: name 'unknown_var' is not defined
  unknown_var + 1
  ^
```

### 7. `CallError`
Raised when invoking an undefined function, calling a non-function, or providing an incorrect number of arguments.
```text
Error: Runtime error at line 1, column 1: unknown function 'foo'
  foo(1)
  ^
```

### 8. `AssignmentError`
Raised when attempting to assign a value to a reserved identifier (`ans` or built-in function names).
```text
Error: Runtime error at line 1, column 1: cannot assign to reserved name 'ans'
  ans = 42
  ^
```

---

## 9. Resource Limits and Boundary Behaviors

MiniCalc enforces strict execution limits to ensure safety and prevent denial-of-service conditions:
- **Maximum Line Length:** Input lines are capped at 1,000 characters (`limits.py`). Exceeding this limit immediately raises a `LexError` at column 1001.
- **Nesting Depth Limit:** The parser enforces a maximum expression nesting depth of 200 (`parser.MAX_DEPTH = 200`). An expression with 199 nested parentheses evaluates successfully, while 200 nested parentheses triggers a `ParseError` ("expression is nested too deeply").
- **Short-Circuit Exponentiation:** As detailed in Section 5, powers with $|base| \ge 2$ and exponent $> 31$ raise `IntegerRangeError` in $O(1)$ time without computing large values.

### Verified Architectural Edge Cases
1. **`ans` and Assignments:** `ans` updates only upon a successful *expression*. Successful assignments (`x = 7`) leave `ans` unchanged.
2. **Character Classification (`12é`):** Only ASCII letters and underscores immediately following digits trigger a multi-character numeric error at column 1 (`12abc`). Non-ASCII characters directly after digits are handled as illegal characters at their own column (`12é` raises `LexError` at column 3).
3. **`INT_MIN % -1`:** While `INT_MIN / -1` overflows 32-bit signed range (giving `IntegerRangeError`), `INT_MIN % -1` equals `0`, which is well within 32-bit range and executes without error.
4. **Negative Exponents:** Negative exponentiation is universally rejected as a `DomainError` across all bases, including `0` and `1`.
5. **Reserved Target Pre-Check:** Target name validity checks occur prior to evaluating the right-hand side of an assignment. Thus, `ans = 1 / 0` and `abs = 1 / 0` fail immediately with `AssignmentError` at column 1 rather than `DivisionByZeroError`.
6. **GCD Range Limits:** While mathematical GCD is non-negative, $\text{gcd}(\text{INT\_MIN}, 0)$ and $\text{gcd}(\text{INT\_MIN}, \text{INT\_MIN})$ equal $2,147,483,648$, which exceeds `INT_MAX`. Both properly raise `IntegerRangeError`.
7. **Parenthesis Depth Boundary:** 199 nested parentheses evaluate cleanly; 200 nested parentheses raise `ParseError`.

---

## 10. Non-Goals

The following features are intentionally excluded from MiniCalc v1.0 to keep the language focused, predictable, and robust:
- Floating-point arithmetic (all computations are exact 32-bit integers).
- Strings and character manipulation.
- User-defined functions and closures.
- Control flow constructs (such as `if`, `while`, or `for` loops).
- Multiple statements per line (semicolons are not supported).
- Unbounded big integers.
- Scoping hierarchies or namespaces.

---

## 11. Evaluation Against PL Design Criteria

MiniCalc was engineered in strict alignment with fundamental Programming Language design principles:

### 1. Readability
- **Claim:** MiniCalc code is intuitive, readable, and free of syntactic noise.
- **Design Choice:** Familiar standard mathematical infix notation, line-oriented structure (one statement per line), transparent `#` comment syntax, and clean spacing.
- **Evidence:** See `examples/01_basics.mc` and `tests/golden/comments_whitespace.mc`.

### 2. Writability
- **Claim:** Common arithmetic workflows and repetitive calculations require minimal boilerplate.
- **Design Choice:** Automatic `ans` result chaining, intuitive variable assignments, dual division operators (`/` for truncation, `//` for floor), and built-in functions (`abs`, `min`, `max`, `gcd`).
- **Evidence:** See `examples/03_variables.mc`, `examples/04_builtins.mc`, and `tests/golden/division.mc`.

### 3. Reliability
- **Claim:** Execution is deterministic, type-safe, and free from silent failures or undefined behavior.
- **Design Choice:** Checked signed 32-bit integer arithmetic with `IntegerRangeError` on overflow, strict domain checks, atomic statement rollback upon error, and multi-line visual diagnostics with carets.
- **Evidence:** See `tests/golden/range.mc`, `tests/golden/rulings.mc`, and `examples/05_errors.mc`.

### 4. Cost
- **Claim:** The language has near-zero overhead, fast startup, and bounded computational cost.
- **Design Choice:** Single-pass $O(N)$ lexical analyzer, linear recursive-descent parser, zero third-party dependencies, 1000-character line limit, recursion depth limit (200), and short-circuit exponentiation bounds.
- **Evidence:** See `tests/golden/power.mc`, `tests/test_lexer.py`, and `tests/test_parser.py`.

### 5. Orthogonality
- **Claim:** Core language constructs compose freely and uniformly without arbitrary special-case syntax rules.
- **Design Choice:** Any valid expression can appear wherever an expression is required: inside function arguments, as unary/binary operands, within grouping parentheses, or on the right side of an assignment.
- **Evidence:** See `examples/02_precedence.mc`, `tests/golden/precedence.mc`, and `tests/golden/builtins.mc`.

### 6. Simplicity
- **Claim:** The language has a minimal learning curve and an exceptionally small conceptual surface area.
- **Design Choice:** Exactly one data type (signed 32-bit integer), no implicit type coercions, a grammar of roughly a dozen production rules, and an absence of complex control flow structures.
- **Evidence:** See `examples/01_basics.mc`, `tests/golden/arithmetic.mc`, and `docs/context/language-spec.md`.

---

## 12. Design Decisions and Alternatives

### Why Python?
Python 3.10+ standard library was selected as the implementation runtime because it eliminates all compilation steps, complex toolchain installations, and platform-specific build configurations. A grader or user can execute MiniCalc immediately on any system with a standard Python installation.
- *Alternatives Considered:* Java was evaluated but rejected because it required approximately 1.8x more boilerplate code and a full JDK setup. C++ was evaluated but rejected due to portability overhead and undefined behavior on signed integer overflow.

### Why a Hand-Written Recursive-Descent Parser?
MiniCalc employs a hand-crafted lexer and recursive-descent parser rather than an external parser-generator library (such as PLY, Lark, or ANTLR). Hand-written parsing provides complete control over exact token coordinates (line and column numbers), allows tailoring error messages with precise diagnostic carets, maintains zero external dependencies, and is easy to explain and demonstrate.

### Why 32-Bit Checked Arithmetic?
Native Python integers have arbitrary precision and never overflow. Left unconstrained, Python integers would mask computational limits and permit resource exhaustion attacks (such as $2^{1000000}$). MiniCalc implements a strict 32-bit signed integer model with explicit range checks on every operation, providing the safety and predictability expected in systems programming languages.

### Why Truncating `/` plus Floor `//` and Floored `%`?
Programming languages and calculators diverge on division semantics: C, Java, and standard desktop calculators truncate toward zero (`/`), whereas Python and mathematical number theory floor toward negative infinity (`//`). MiniCalc provides both operators, pairing `//` with floored modulo `%` so that the foundational quotient-remainder identity $a = (a // b) \times b + a \% b$ holds unconditionally.

### Why Atomic Statements?
In interactive REPLs and scripting environments, an expression that fails midway (e.g., encountering division by zero after evaluating several terms) should not leave the system in a corrupted or partially modified state. MiniCalc treats every statement as a transactional unit: variable bindings are updated only upon complete success, and `ans` is preserved if any error occurs.
