# MiniCalc Interface Contract (design-locked)

Canonical Python-level contract between modules. Parallel tasks (FEAT-001 to FEAT-005) build against this file, not against each other's code. Behavior is defined by `docs/context/language-spec.md`. A signature change needs a new decision-log entry.

Python: 3.10+. Runtime: standard library only ([D-02]). Every class carries a docstring with an `Attributes:` section describing **every** class and instance variable ([D-11]).

---

## 1. Package layout and file ownership

```text
minicalc/
  __init__.py        CORE-001   exports __version__ only
  __main__.py        FEAT-004   CLI entry point
  limits.py          CORE-001   INT_MIN, INT_MAX, in_range()
  errors.py          CORE-001   SourcePos, MiniCalcError hierarchy
  tokens.py          CORE-001   TokenType, Token
  ast_nodes.py       CORE-001   AST dataclasses
  lexer.py           CORE-003 (stub) -> FEAT-001 (full)
  parser.py          CORE-003 (stub) -> FEAT-002 (full)
  environment.py     CORE-003 (stub) -> FEAT-003 (full)
  builtins.py        FEAT-003
  evaluator.py       CORE-003 (stub) -> FEAT-003 (full)
  interpreter.py     CORE-003   facade, stable from CORE-003 onward
  display.py         FEAT-004   formatting and ANSI styling
  repl.py            FEAT-004   interactive loop and meta-commands
main.py              FEAT-004   `python main.py` shim
tests/
  conftest.py        CORE-002
  golden/*.mc|*.out  CORE-002 (harness) + FEAT-005 (cases)
  test_*.py          owned by the task that creates them
```

Rule: **one owner per file at a time.** A task edits only the files listed for it in its prompt.

## 2. `limits.py`

```python
INT_MIN: int = -2_147_483_648
INT_MAX: int = 2_147_483_647
MAX_LINE_LENGTH: int = 1000
def in_range(value: int) -> bool: ...        # INT_MIN <= value <= INT_MAX
```

## 3. `errors.py`

```python
@dataclass(frozen=True)
class SourcePos:
    line: int   # 1-based
    col: int    # 1-based

class MiniCalcError(Exception):
    kind: ClassVar[str] = "Error"            # overridden per subclass, e.g. "Syntax error"
    message: str
    pos: SourcePos | None
    source_line: str | None                  # the offending line, for caret rendering
    def __init__(self, message: str, pos: SourcePos | None = None,
                 source_line: str | None = None) -> None: ...
    def with_source(self, source_line: str) -> "MiniCalcError": ...   # returns self after setting source_line
    def render(self, color: bool = False) -> str: ...                 # multi-line, caret under col
    def canonical(self) -> str: ...          # "ERR <ClassName> <line>:<col>"  (golden format)

class LexError(MiniCalcError): ...           # kind = "Lexical error"
class ParseError(MiniCalcError): ...         # kind = "Syntax error"
class EvalError(MiniCalcError): ...          # base of runtime errors, kind = "Runtime error"
class DivisionByZeroError(EvalError): ...
class IntegerRangeError(EvalError): ...
class DomainError(EvalError): ...
class UndefinedNameError(EvalError): ...
class CallError(EvalError): ...
class AssignmentError(EvalError): ...
```

`render()` layout (plain, `color=False`):

```
Error: Syntax error at line 1, column 5: expected an expression, found '*'
  2 + * 3
      ^
```

The caret line is indented to align under `col` (2 spaces of margin plus `col - 1` spaces). If `pos` or `source_line` is `None`, render the first line only.

## 4. `tokens.py`

```python
class TokenType(Enum):
    NUMBER; IDENT
    PLUS; MINUS; STAR; SLASH; DSLASH; PERCENT; POW
    EQ; NE; LT; LE; GT; GE; ASSIGN
    LPAREN; RPAREN; COMMA
    EOF

@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str            # exact source text ("" for EOF)
    pos: SourcePos
    value: int | None = None   # set for NUMBER only
```

## 5. `ast_nodes.py`

All nodes are `@dataclass(frozen=True)` and carry `pos: SourcePos` as the **last** field.

```python
Op = Literal["+","-","*","/","//","%","**","==","!=","<","<=",">",">="]

Number(value: int, pos)
Name(ident: str, pos)                       # pos = the identifier
Unary(op: Literal["-","+"], operand: Node, pos)       # pos = the operator
Binary(op: Op, left: Node, right: Node, pos)          # pos = the operator
Call(func: str, args: tuple[Node, ...], pos)          # pos = the function name
Assign(target: str, value: Node, pos)                 # pos = the target name

Node = Number | Name | Unary | Binary | Call | Assign
```

`args` is a tuple (immutable). `Assign` appears only at the top of a statement.

## 6. `lexer.py`

```python
class Lexer:
    def __init__(self, source: str, line_no: int = 1) -> None: ...
    def tokenize(self) -> list[Token]: ...   # always ends with one EOF token; raises LexError
```

`source` is one line with no trailing newline. A line longer than `MAX_LINE_LENGTH` raises `LexError` at column `MAX_LINE_LENGTH + 1`. `line_no` is stamped on every `SourcePos`.

## 7. `parser.py`

```python
class Parser:
    def __init__(self, tokens: list[Token]) -> None: ...
    def parse_statement(self) -> Node | None: ...   # None for an empty line (only EOF); raises ParseError
```

The parser consumes the whole token list. Any leftover token after a complete statement is a `ParseError`.

## 8. `environment.py` and `builtins.py`

```python
class Environment:
    variables: dict[str, int]
    ans: int | None
    def get(self, name: str, pos: SourcePos) -> int: ...      # name == "ans" handled here; raises UndefinedNameError
    def set(self, name: str, value: int) -> None: ...
    def record_result(self, value: int) -> None: ...          # sets ans
    def clear(self) -> None: ...                              # empties variables and ans
    def items(self) -> list[tuple[str, int]]: ...             # sorted by name

@dataclass(frozen=True)
class Builtin:
    name: str
    min_args: int
    max_args: int | None          # None = unbounded
    fn: Callable[..., int]
    doc: str

BUILTINS: dict[str, Builtin]      # abs, min, max, gcd
def is_reserved(name: str) -> bool: ...   # "ans" or a built-in name
```

## 9. `evaluator.py`

```python
class Evaluator:
    def __init__(self, env: Environment) -> None: ...
    def evaluate(self, node: Node) -> int: ...   # raises EvalError subclasses; never mutates env on failure
```

`evaluate` handles `Assign` too (binds the variable only after the right side succeeded). Range checking happens inside `evaluate` for every produced value.

## 10. `interpreter.py` (the stable facade)

```python
@dataclass(frozen=True)
class Result:
    kind: Literal["value", "assign", "empty"]
    value: int | None = None
    name: str | None = None          # set when kind == "assign"

@dataclass(frozen=True)
class LineOutcome:
    line_no: int
    source: str
    result: Result | None
    error: MiniCalcError | None      # exactly one of result/error is not None

class Interpreter:
    env: Environment
    def __init__(self, env: Environment | None = None) -> None: ...
    def run_line(self, source: str, line_no: int = 1) -> Result: ...      # raises MiniCalcError (with source_line attached)
    def run_source(self, text: str) -> list[LineOutcome]: ...             # splits lines, never raises MiniCalcError
```

`Interpreter.__init__` raises the interpreter recursion limit to at least 4000 if it is lower, and `run_line` converts any escaping `RecursionError` into a `ParseError` or `EvalError` (spec section 7).

`run_line` on a successful expression calls `env.record_result(value)`; a successful assignment binds its variable and returns `kind="assign"` but does **not** update `ans`. On any error the environment is unchanged and the raised error has `source_line` set. `run_source` numbers lines from 1 and continues after errors.

## 11. `display.py` and `repl.py`

```python
def use_color(stream: TextIO) -> bool: ...                    # isatty() and "NO_COLOR" not in os.environ
def format_result(result: Result, color: bool = False) -> str:  # "= 42"  or  "x = 7"  or  ""
def format_outcome(outcome: LineOutcome, color: bool = False) -> str:   # script mode, "line 3: = 42" / error block
def banner(color: bool = False) -> str: ...
def help_text(color: bool = False) -> str: ...

class Repl:
    PROMPT: ClassVar[str] = "minicalc> "
    def __init__(self, interpreter: Interpreter, input_fn: Callable[[str], str] = input,
                 output_fn: Callable[[str], None] = print, color: bool = False) -> None: ...
    def run(self) -> int: ...      # returns 0 on clean exit
```

`input_fn` and `output_fn` are injectable so the REPL is testable without a terminal.

`__main__.main(argv: list[str] | None = None) -> int` implements section 8 of the spec (REPL, script, `-e`, exit codes).

## 12. Golden test format (defined here so FEAT-005 and CORE-002 agree)

- Input `tests/golden/<name>.mc`: one MiniCalc line per line (blank and comment lines allowed).
- Expected `tests/golden/<name>.out`: one line **per non-empty statement line**, in order, in canonical form:
  - expression: `OK <value>`
  - assignment: `OK <name>=<value>`
  - error: `ERR <ClassName> <line>:<col>` (the error message text is **not** compared)
- The harness runs the whole file through one `Interpreter` via `run_source`, so state carries across lines.
- Example. `tests/golden/basic.mc`:

```
# basic arithmetic
2 + 3 * 4
x = 7
ans * x
2 +
```

`tests/golden/basic.out` (comment line 1 produces nothing; the failing statement is on file line 5, EOF column is `len("2 +") + 1 = 4`):

```
OK 14
OK x=7
OK 98
ERR ParseError 5:4
```
