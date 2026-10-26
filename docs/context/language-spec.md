# MiniCalc Language Specification (v1.0, design-locked)

Authoritative definition of the MiniCalc language. Every implementation task, test, and the final documentation derive from this file. If code and this spec disagree, either the code is wrong or a new decision-log entry supersedes this spec. It is never silently "fixed" in code.

Related: `docs/context/interface-contract.md` (Python module and class contracts), `docs/decisions/decision-log.md` ([D-02] to [D-12]).

---

## 1. Overview

MiniCalc is a line-oriented language for integer arithmetic. One line holds at most one statement. A statement is either an expression or an assignment.

```
minicalc> 2 + 3 * 4
= 14
minicalc> x = 7
x = 7
minicalc> ans * x
= 98
```

Source file extension: `.mc`. Encoding: UTF-8.

## 2. Lexical structure

| Token | Pattern | Notes |
| :--- | :--- | :--- |
| `NUMBER` | `[0-9]+` | Decimal digits only, value 0 to 2147483647 |
| `IDENT` | `[A-Za-z_][A-Za-z0-9_]*` | Case-sensitive |
| `PLUS` `MINUS` `STAR` `SLASH` `DSLASH` `PERCENT` `POW` | `+ - * / // % **` | Longest match: `**` before `*`, `//` before `/` |
| `EQ` `NE` `LT` `LE` `GT` `GE` | `== != < <= > >=` | Longest match |
| `ASSIGN` | `=` | A single `=`; `==` is `EQ` |
| `LPAREN` `RPAREN` `COMMA` | `( ) ,` | |
| `EOF` | end of the line | Always the last token. Column is `len(line) + 1` |

- Whitespace (space, tab, carriage return) separates tokens and is otherwise ignored. A trailing `\r` from Windows line endings is therefore harmless.
- `#` starts a comment that runs to the end of the line.
- Columns and lines are 1-based. Tabs count as one column.

Only ASCII digits and letters are valid. Any non-ASCII character (for example a non-breaking space or a curly quote pasted from a document) is an illegal character.

### Lexical errors (`LexError`)

| Input | Error condition | Reported column |
| :--- | :--- | :--- |
| `3.14`, `3.` | Decimals are not supported (integers only) | the `.` |
| `12abc` | ASCII letter or `_` directly after digits | start of the number |
| `12é` | Non-ASCII character directly after digits (an illegal character like any other) | the `é` |
| `99999999999` | Literal greater than 2147483647 | start of the number |
| `2 @ 3`, `$x`, `:` | Illegal character | the character |
| `3 ! 4` | `!` not followed by `=` | the `!` |
| a line longer than 1000 characters | Line too long | column 1001 |

## 3. Grammar (EBNF)

Lowest precedence first. `[ ]` optional, `{ }` zero or more.

```ebnf
line        = [ statement ] EOF ;
statement   = assignment | expression ;
assignment  = IDENT ASSIGN expression ;
expression  = additive [ compare_op additive ] ;      (* non-associative *)
compare_op  = EQ | NE | LT | LE | GT | GE ;
additive    = term { ( PLUS | MINUS ) term } ;
term        = unary { ( STAR | SLASH | DSLASH | PERCENT ) unary } ;
unary       = ( MINUS | PLUS ) unary | power ;
power       = primary [ POW unary ] ;                 (* right-associative *)
primary     = NUMBER | IDENT | call | LPAREN expression RPAREN ;
call        = IDENT LPAREN [ expression { COMMA expression } ] RPAREN ;
```

An empty line or a comment-only line yields no statement. A line is an assignment when its first two tokens are `IDENT ASSIGN`.

### Precedence and associativity (high to low)

| Level | Operators | Associativity |
| :--- | :--- | :--- |
| 1 | `( )`, function calls | n/a |
| 2 | `**` | right |
| 3 | unary `-` `+` | right (prefix) |
| 4 | `*` `/` `//` `%` | left |
| 5 | `+` `-` | left |
| 6 | `==` `!=` `<` `<=` `>` `>=` | none (cannot chain) |

Consequence of the grammar: `-2 ** 2` parses as `-(2 ** 2)` and equals `-4`. `2 ** -1` parses, then fails at evaluation (negative exponent).

### Syntax errors (`ParseError`)

| Input | Error condition | Reported column |
| :--- | :--- | :--- |
| `2 +` | Expected an expression, found end of line | EOF column |
| `2 + * 3` | Expected an expression, found `*` | the `*` |
| `(2 + 3` | Missing `)` | the EOF column |
| `2 3` | Unexpected token after a complete expression | the `3` |
| `1 < 2 < 3` | Comparison operators cannot be chained | the second `<` |
| `max(1,` | Expected an expression after `,` | the EOF column |
| `)` | Expected an expression, found `)` | the `)` |
| `= 5` | Expected an expression, found `=` | the `=` |
| `5 = 3` | Left side of `=` must be a name | the `=` |

## 4. Values and the integer model

- The only value type is a **signed 32-bit integer**: range `INT_MIN = -2147483648` to `INT_MAX = 2147483647`.
- **Every** intermediate and final result is range-checked. Leaving the range raises `IntegerRangeError` at the position of the operator (or call) that produced it. Results never wrap around.
- Number literals are non-negative. `-5` is unary minus applied to `5`.
- `INT_MIN` cannot be written as a literal (the literal `2147483648` is out of range). Write `-2147483647 - 1`, the same way C does it.
- Booleans do not exist. Comparisons yield `1` (true) or `0` (false).

## 5. Operator semantics

| Operator | Meaning | Errors |
| :--- | :--- | :--- |
| `a + b`, `a - b`, `a * b` | Ordinary integer arithmetic | Range |
| `a / b` | Division **truncated toward zero** | `b == 0` is `DivisionByZeroError`. `INT_MIN / -1` is a range error |
| `a // b` | **Floor** division (rounds toward negative infinity) | Same as `/` |
| `a % b` | Floored modulo, paired with `//`: `a == (a // b) * b + a % b`. Result takes the sign of `b` | `b == 0` is `DivisionByZeroError`. `INT_MIN % -1` is `0` (the result is in range) |
| `a ** b` | Exponentiation, `b >= 0` | `b < 0` is `DomainError`. Overflow is `IntegerRangeError` |
| `-a`, `+a` | Negation, identity | `-INT_MIN` is a range error |
| `==` `!=` `<` `<=` `>` `>=` | Comparison, result `1` or `0` | none |

`**` rules: `x ** 0 == 1` (including `0 ** 0`), `0 ** n == 0` for `n > 0`, `1 ** n == 1`, `(-1) ** n` is `1` or `-1` by parity. Otherwise, when `|x| >= 2` and `b > 31`, raise `IntegerRangeError` immediately **without computing the power**, because `2 ** 1000000000` must fail instantly and never hang. A negative exponent is a `DomainError` for every base, including `0` and `1`; that check comes before the special cases above.

### Worked examples (verified)

| Input | Result | Why |
| :--- | :--- | :--- |
| `2 + 3 * 4` | `14` | `*` binds tighter than `+` |
| `(2 + 3) * 4` | `20` | Parentheses |
| `10 - 3 - 2` | `5` | Left associative |
| `-2 ** 2` | `-4` | `**` binds tighter than unary minus |
| `2 ** 3 ** 2` | `512` | Right associative: `2 ** 9` |
| `2 ** 30` | `1073741824` | In range |
| `7 / 2` | `3` | Truncation |
| `-7 / 2` | `-3` | Truncation toward zero |
| `7 // 2` | `3` | Floor |
| `-7 // 2` | `-4` | Floor toward negative infinity |
| `-7 % 2` | `1` | Floored modulo, sign of divisor |
| `7 % -2` | `-1` | Floored modulo, sign of divisor |
| `-7 % -2` | `-1` | Floored modulo |
| `5 > 3` | `1` | Comparison |
| `5 == 4` | `0` | Comparison |
| `2 + 3 == 5` | `1` | Arithmetic binds tighter than comparison |
| `-2147483647 - 1` | `-2147483648` | `INT_MIN` |

Evaluation errors for the same table: `5 / 0` gives `DivisionByZeroError` at the `/`. `2 ** 31` gives `IntegerRangeError` at the `**`. `2 ** -1` gives `DomainError` at the `**`. `2147483647 + 1` gives `IntegerRangeError` at the `+`.

## 6. Names, variables, `ans`, built-ins

- **Variables:** `x = <expression>` evaluates the right side, then binds `x`. The statement's result is the assigned value. A name that was never assigned raises `UndefinedNameError` at the name's position.
- **`ans`:** read-only. Holds the value of the most recent *successful expression*. Assignments do not change `ans` (see the section 1 example, where `ans * x` after `x = 7` uses the earlier `14`). Before any successful expression it is unset, and reading it raises `UndefinedNameError`. A failed statement does not change `ans` or any variable (atomic statements).
- **Reserved names:** `ans` and every built-in function name. Assigning to one raises `AssignmentError` at the target name. The check happens before the right side is evaluated, so `ans = 1 / 0` is an `AssignmentError` at `ans`, not a `DivisionByZeroError`.
- **Built-in functions** (the only functions in v1.0; there are no user-defined functions):

| Function | Arity | Result |
| :--- | :--- | :--- |
| `abs(x)` | 1 | Absolute value. `abs(INT_MIN)` is a range error |
| `min(a, b, ...)` | 1 or more | Smallest argument |
| `max(a, b, ...)` | 1 or more | Largest argument |
| `gcd(a, b)` | 2 | Greatest common divisor, always `>= 0`. `gcd(0, 0) == 0`. `gcd(INT_MIN, 0)` and `gcd(INT_MIN, INT_MIN)` are range errors (the true result, 2147483648, is out of range) |

- Calling an unknown function (`foo(1)`), calling a variable (`x(1)`), or passing the wrong number of arguments raises `CallError`, reported at the function name. Using a built-in name without parentheses (`abs + 1`) raises `UndefinedNameError`.
- Arity is checked first, before any argument is evaluated. Then arguments are evaluated left to right, and the first argument that fails determines the call's error.

## 7. Error model

| Class | Raised by | Typical cause |
| :--- | :--- | :--- |
| `LexError` | lexer | Illegal character, bad number format, literal out of range |
| `ParseError` | parser | Malformed syntax |
| `DivisionByZeroError` | evaluator | `/`, `//`, `%` with zero divisor |
| `IntegerRangeError` | evaluator | Result outside 32-bit range |
| `DomainError` | evaluator | Negative exponent |
| `UndefinedNameError` | evaluator | Unset variable, unset `ans`, built-in used as a value |
| `CallError` | evaluator | Unknown function, non-function call, wrong arity |
| `AssignmentError` | evaluator | Assigning to `ans` or a built-in name |

All inherit from `MiniCalcError`. **Resource safety net:** a `RecursionError` from pathological nesting must never escape; the facade converts it to a `ParseError` (nesting while parsing) or `EvalError` (while evaluating) with a clear message. The 1000-character line limit keeps legitimate input far below this. Errors never terminate the REPL. In file mode, execution continues after an error and the process exit code is `1` if any error occurred.

Error position (`line:col`) rules:
- `LexError`, `ParseError`: as tabulated in sections 2 and 3.
- Evaluation errors: the column of the operator for binary and unary operations, the function name for calls, the name for variables and assignment targets.

## 8. Interface behavior (summary; full contract in `interface-contract.md`)

- **REPL:** `python -m minicalc`. Prompt `minicalc> `. Expression result prints `= <value>`. Assignment prints `<name> = <value>`. Errors print a styled multi-line message with a caret under the error column. Meta-commands (REPL only, start with `:`): `:help`, `:vars`, `:clear`, `:quit` (and `:q`). `Ctrl-D` or `Ctrl-C` at the prompt exits cleanly.
- **Script:** `python -m minicalc file.mc` runs each line, printing results and errors prefixed by the line number.
- **One-shot:** `python -m minicalc -e "1 + 2"`.
- **Exit codes:** `0` success, `1` at least one MiniCalc error occurred, `2` usage error (bad arguments, unreadable file).
- **Color:** ANSI styling only when stdout is a TTY and `NO_COLOR` is unset. Output is plain text otherwise.

## 9. Non-goals (v1.0)

Floating point, strings, user-defined functions, control flow (`if`, `while`), multiple statements per line, big integers, and variable scoping. These are out of scope by [D-03].

## 10. PL evaluation criteria mapping (seed for DOC-002)

| Criterion | MiniCalc design choice that serves it |
| :--- | :--- |
| Readability | Familiar infix notation, one statement per line, consistent operator set, comments with `#` |
| Writability | `ans`, variables, and built-ins shorten common work. `/` truncates and `//` floors, so both common intents are expressible |
| Reliability | Strong typing (single integer type), explicit range checking with no silent wraparound, atomic statements, positioned error messages |
| Cost | Hand-written single-pass lexer and parser (O(n)), no dependencies, instant startup, pow short-circuit prevents runaway computation |
| Orthogonality | Every expression form can appear wherever an expression is allowed (arguments, operands, right side of assignment) |
| Simplicity | Small fixed grammar (about a dozen rules) and a single value type |
