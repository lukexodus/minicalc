# Task Report: INT-002 — Differential test and independent audit

**Date:** 2026-10-26  
**Agent:** claude-code  
**Task ID:** INT-002  
**Status:** needs-review  
**Branch:** `task/INT-002`  
**Worktree:** `/home/lukexodus/projects/minicalc-INT-002`  
**Commit:** the single commit on `task/INT-002` (amended once to include this report and the patch)  
**Patch File:** `patch/INT-002-claude-code-differential-audit.patch`  

---

## 1. Executive Summary

Added a spec-only reference implementation (`tests/oracle.py`) and a seeded differential test (`tests/test_differential.py`). The test generates **2,800 expression trees per rendering** (fully parenthesized and minimally parenthesized), evaluates each tree with the oracle, runs the same source through the real `Interpreter`, and compares only the value or error class. Result: **5,600 comparisons, zero mismatches**, in **1.19 s** (limit 15 s). Eight seeded 20-line variable-state sequences (**160 lines**, every fifth line forced to fail) likewise matched, including variable and `ans` state after every line, which verifies atomicity and the `ans` ruling.

All three required mutants were detected and then reverted; `git diff` after restoration is empty and the restored tree passes **437 tests** (432 pre-existing + 5 new). No implementation change was needed or made.

## 2. Independence Certification

The oracle was written from `docs/context/language-spec.md` and the decision log, not from the implementation. Exact file timeline:

**Before `tests/oracle.py` was created and saved**, the only `minicalc` source file opened was:

- `minicalc/limits.py` — read in full for `INT_MIN` / `INT_MAX` only (explicitly permitted by the task).

Other files read before that point were non-implementation context: `docs/context/complete-context.md`, `AGENTS.md`, `docs/tasks/status.md`, `docs/decisions/decision-log.md`, `docs/context/language-spec.md`, `docs/context/interface-contract.md`, `docs/prompts/INT-002.md`, `docs/reports/TASK-TEMPLATE.md`, `tests/conftest.py`, and `pytest.ini`. Directory listings showed the golden file names; **no golden `.mc`/`.out` content was opened**. A baseline `pytest -q` run (432 passed) imported the package but displayed no implementation source.

**After `tests/oracle.py` was complete and saved**, I opened exactly two implementation files, only to locate the three mutation edit points required by the task:

- `minicalc/evaluator.py` — grep plus `Read` of lines 80-169 (`_binary`, `_power`).
- `minicalc/parser.py` — grep plus `Read` of lines 235-264 (`_unary`, `_power`).

No mismatch existed, so these reads were not needed to explain a result; they were used solely to apply and revert the mutants. They did not shape `tests/oracle.py` or `tests/test_differential.py` (both were already saved). `minicalc/lexer.py`, `interpreter.py`, `builtins.py`, `environment.py`, `errors.py`, `ast_nodes.py`, and `tokens.py` were never opened. Runtime imports of `minicalc.errors` and `minicalc.interpreter` from the test file displayed no source.

## 3. Method

### 3.1 Oracle (`tests/oracle.py`)

A standalone expression-tree evaluator with its own node types. It imports only `INT_MIN` / `INT_MAX` from `minicalc.limits`. It implements truncating `/`, floor `//`, floored `%` (including `INT_MIN % -1 == 0`), right-associative `**` with the negative-exponent check before all base special cases and the `|base| >= 2 and exp > 31` short-circuit, comparisons yielding 0/1, unary range behavior, `abs`/`min`/`max`/`gcd`, arity-before-arguments call semantics, and statement atomicity. The reserved-target check precedes RHS evaluation, and `ans` changes only on a successful expression. Spec fixed tables are exported as `PHASE2_RULING_CASES`, `PHASE2_LEX_CASES` (`12é` → `LexError` at column 3), and `SPEC_WORKED_CASES`.

Two reference printers render the same tree: `render_full` parenthesizes every operation; `render_minimal` uses the spec precedence/associativity table (comparison 1, additive 2, multiplicative 3, unary 4, power 5, primary 6). Negative constants are emitted as unary-minus expressions; `INT_MIN` is emitted as `((-2147483647) - 1)` because `2147483648` is not a literal.

### 3.2 Generated expressions

Fixed seeds `(20261026, 1729, 314159, 271828, 161803)` × 7 categories × 80 expressions = **2,800 trees per rendering**. Categories: additive, multiplicative, division, power, comparison, unary, builtin_call. Leaf magnitudes are mixed across small values (zero-heavy), values around 46,340, values around the 32-bit boundary, and powers of two. Division nodes force a zero divisor 20-30% of the time; power exponents include 0-4, 30-33, large values, negative unary expressions, and right-nested powers. Each tree is rendered both ways and both sources are compared with the same oracle result. Mismatch messages print seed, category, rendering, source, oracle outcome, and actual outcome.

### 3.3 Variable-state sequences

Eight fixed seeds × 20 lines. Lines mix variable assignments, reserved-target assignments (`ans`, `abs`, `min`, `gcd`), expressions over bound/unbound names and `ans`, plus a forced failure every fifth line (`1 / 0`, negative exponent, `INT_MAX + 1`, undefined name, `ans = 1 / 0`, `abs = <undefined>`). After every line, `env.variables` and `env.ans` are compared with the oracle state, so a failed statement must change neither.

## 4. Implementation Details

- `tests/oracle.py` (new): self-contained reference semantics, renderers, and spec-derived fixed-case tables. Only `INT_MIN`/`INT_MAX` imported from `minicalc`.
- `tests/test_differential.py` (new): seeded generator, dual rendering, generated comparison suite, fixed spec/Phase-2 checks, `ans`/atomicity sequence, and variable-state sequences.
- `docs/tasks/status.md`: only the INT-002 row changed to `needs-review` with the report link.
- No file under `minicalc/`, `tests/golden/`, the spec, or the contract was changed.

## 5. Results

### 5.1 Generated expressions

```
seeds=5 categories=7 per_category=80
full:    2800 expressions, 1729 expected errors, 1071 expected values
minimal: 2800 expressions, 1729 expected errors, 1071 expected values
per category: additive 400, multiplicative 400, division 400, power 400,
              comparison 400, unary 400, builtin_call 400 (each rendering)
elapsed: 1.19s
```

### 5.2 Variable-state

```
variable-state summary: 8 sequences x 20 lines = 160 lines checked
```

Zero value/error mismatches and zero state mismatches.

### 5.3 Fixed spec cases

All 21 `SPEC_WORKED_CASES`, all 8 `PHASE2_RULING_CASES`, the `12é` lexical case (class `LexError`, column 3), and the five-line `ans`/atomicity sequence passed.

### 5.4 Mismatches

**None.** No real implementation-vs-spec mismatch was found in the generated, state, or fixed suites.

## 6. Mutation Results

Each mutant was applied to the checked-out worktree only, the differential suite was run, and the original file was restored from an out-of-repo backup.

| # | Mutant | Detected | Selected evidence |
| :-- | :--- | :--- | :--- |
| A | `/` floors instead of truncating (`evaluator.py`) | Yes — 2 failed, 3 passed | `seed=20261026 category=additive rendering=full`, source `(((+(-2147483647)) / (10 / (-2147483646))) - gcd((2147483646 * 46339), gcd(1, 8)))`: oracle `DivisionByZeroError`, actual `IntegerRangeError`. Also `-7 / 2`: expected `-3`, got `-4`. |
| B | `%` uses truncated remainder (`evaluator.py`) | Yes — 2 failed, 3 passed | `seed=20261026 category=additive rendering=full`, source `((abs(2147483647) + ((-46340) % (-2147483646))) - ((46340 + (-2)) - (2147483646 % (-1073741824))))`: oracle `2147390967`, actual `IntegerRangeError`. Also `-7 % 2`: expected `1`, got `-1`. |
| C | `**` left-associative (`parser.py`) | Yes — 4 failed, 1 passed | `2 ** 3 ** 2`: expected `512`, got `64`. Also `0 ** -1`: expected `DomainError`, got `ParseError` (the left-assoc loop parses the exponent as a primary). |

Restoration evidence:

```
b39ecf3a... evaluator.py (restored) == b39ecf3a... /tmp/int002-backup/evaluator.py
86b48863... parser.py    (restored) == 86b48863... /tmp/int002-backup/parser.py
$ git status --short
?? tests/oracle.py
?? tests/test_differential.py
$ git diff
(no output)
```

No mutant was committed.

## 7. Verification & Test Evidence

Full suite on restored code:

```
$ python -m pytest -q
........................................................................ [ 49%]
........................................................................ [ 65%]
........................................................................ [ 82%]
........................................................................ [ 98%]
.....                                                                    [100%]
437 passed in 3.48s
```

Differential suite:

```
$ python -m pytest -q -s tests/test_differential.py
5 passed in 2.89s
```

(Counts and timing printed in section 5.1.)

## 8. Residual Risks

- **Procedural, not institutional, independence.** The oracle was written before any implementation file (other than `limits.py`) was opened, but this run was performed by claude-code, which authored the evaluator/parser in FEAT-002/FEAT-003. The prompt assigned INT-002 to Gemini for that reason. Nothing prevents prior knowledge from influencing wording, though the oracle uses its own tree types and was saved before implementation files were opened. A non-author rerun or a targeted oracle review would restore the letter of the requirement.
- **Operand error order.** The spec fixes evaluation order explicitly only for call arguments. The oracle assumes binary operands are evaluated left to right (matching observed behavior); no mismatch exposed this. If a future implementation changes error precedence, the spec is silent.
- **Rendering scope.** Negative constants are conservatively parenthesized (e.g. `(-46340)`), and `INT_MIN` is emitted as `((-2147483647) - 1)`. This tests operator precedence but treats constants as primary atoms by construction.
- **Coverage boundaries.** The suite targets evaluator semantics; it does not fuzz lexical or parser error positions beyond the fixed spec/Phase-2 cases. Fixed seeds make runs deterministic but bounded; adding seeds is mechanical if more coverage is wanted.
- **Platform.** Timing and results were measured on Python 3.14.8 only.
- **Non-trivial choices (no decision ID reserved):** the state test compares `UndefinedNameError`/`CallError`/`AssignmentError` in addition to the three evaluator errors named in the prompt; this strengthens atomicity and reserved-name checks. The patch/diff is scoped to the two test files per repo reporting convention.

## 9. Unified Git Diff

Verbatim `git diff HEAD~1 -- tests/oracle.py tests/test_differential.py` (also the content of the patch file):

```diff
diff --git c/tests/oracle.py w/tests/oracle.py
new file mode 100644
index 0000000..59582e5
--- /dev/null
+++ w/tests/oracle.py
@@ -0,0 +1,588 @@
+"""Independent reference semantics for MiniCalc (INT-002).
+
+This module is a second, spec-only implementation of MiniCalc evaluation. It
+was written from ``docs/context/language-spec.md`` (sections 2-7) and the
+decision-log rulings in [D-05], [D-06], [D-07], [D-08], and [D-15] before any
+``minicalc`` implementation module was opened. The only import from the
+``minicalc`` package is ``INT_MIN`` and ``INT_MAX`` from ``limits.py``.
+
+Evaluation is over a small private expression tree (:class:`Const`,
+:class:`Var`, :class:`UnaryOp`, :class:`BinaryOp`, :class:`CallOp`, and
+:class:`AssignStmt`). :func:`evaluate` returns an ``int`` or raises
+:class:`OracleError` carrying the spec's error class name. :func:`execute`
+adds the statement layer (assignment, ``ans``, reserved names, atomicity).
+
+Phase 2 rulings encoded here ([D-15], spec sections 2, 5, and 6):
+
+- ``ans`` changes only on a successful expression, never on an assignment.
+- ``INT_MIN % -1`` is ``0``.
+- A negative exponent is ``DomainError`` for every base, including ``0``,
+  ``1``, and ``-1``; that check precedes the ``**`` special cases.
+- ``gcd(INT_MIN, 0)`` and ``gcd(INT_MIN, INT_MIN)`` are
+  ``IntegerRangeError`` (the true result is 2147483648, out of range).
+- The reserved-name check on an assignment target runs before the right side
+  is evaluated, so ``ans = 1 / 0`` is ``AssignmentError``.
+- ``12é`` is a ``LexError`` at column 3 (recorded in
+  :data:`PHASE2_LEX_CASES` for the lexical-ruling check).
+
+Reference renderers are provided for the differential test. Both render the
+same tree; :func:`render_full` parenthesizes every operation, while
+:func:`render_minimal` uses the spec precedence/associativity table.
+"""
+
+from __future__ import annotations
+
+import math
+from dataclasses import dataclass, field
+from typing import Union
+
+from minicalc.limits import INT_MAX, INT_MIN
+
+#: Names that cannot be assigned ([D-08] and spec section 6).
+RESERVED_NAMES = frozenset({"ans", "abs", "min", "max", "gcd"})
+
+#: Names of the built-in functions (the only callables in v1.0).
+BUILTIN_NAMES = frozenset({"abs", "min", "max", "gcd"})
+
+#: Comparison operators. They are non-associative and yield 1 or 0.
+COMPARISON_OPS = frozenset({"==", "!=", "<", "<=", ">", ">="})
+
+#: Arithmetic operators handled by :func:`_apply_binary`.
+BINARY_OPS = frozenset({"+", "-", "*", "/", "//", "%", "**"}) | COMPARISON_OPS
+
+#: Source text for the smallest 32-bit value, which cannot be a literal.
+INT_MIN_SOURCE = "-2147483647 - 1"
+
+
+class OracleError(Exception):
+    """A spec error class reported by the reference evaluator.
+
+    Attributes:
+        kind: The spec's error class name, for example ``"DomainError"``.
+    """
+
+    def __init__(self, kind: str) -> None:
+        """Initialize the error with a spec class name.
+
+        Args:
+            kind: The error class name from spec section 7.
+        """
+        super().__init__(kind)
+        self.kind = kind
+
+    def __repr__(self) -> str:
+        """Return a diagnostic representation naming the error class."""
+        return f"OracleError({self.kind!r})"
+
+
+@dataclass(frozen=True)
+class Const:
+    """An integer value used as a leaf of the reference tree.
+
+    Attributes:
+        value: The semantic integer value, already within the signed 32-bit
+            range. Negative values are rendered by the printers as unary
+            minus expressions, because MiniCalc has no negative literals.
+    """
+
+    value: int
+
+
+@dataclass(frozen=True)
+class Var:
+    """A name reference (a variable, ``ans``, or a bare built-in name).
+
+    Attributes:
+        name: The identifier text as written in source.
+    """
+
+    name: str
+
+
+@dataclass(frozen=True)
+class UnaryOp:
+    """A prefix unary operation.
+
+    Attributes:
+        op: ``"-"`` or ``"+"``.
+        operand: The child expression tree.
+    """
+
+    op: str
+    operand: "Node"
+
+
+@dataclass(frozen=True)
+class BinaryOp:
+    """A binary operation.
+
+    Attributes:
+        op: One of the arithmetic or comparison operators in
+            :data:`BINARY_OPS`.
+        left: The left operand tree.
+        right: The right operand tree.
+    """
+
+    op: str
+    left: "Node"
+    right: "Node"
+
+
+@dataclass(frozen=True)
+class CallOp:
+    """A function call written as ``func(arg, ...)``.
+
+    Attributes:
+        func: The function name as written (a built-in or an unknown name).
+        args: The argument trees, in source order.
+    """
+
+    func: str
+    args: tuple["Node", ...]
+
+
+@dataclass(frozen=True)
+class AssignStmt:
+    """An assignment statement ``target = value``.
+
+    Attributes:
+        target: The identifier being bound.
+        value: The right-hand expression tree.
+    """
+
+    target: str
+    value: "Node"
+
+
+#: The reference expression tree union.
+Node = Union[Const, Var, UnaryOp, BinaryOp, CallOp]
+
+
+@dataclass
+class OracleState:
+    """Reference environment state for one interpreter session.
+
+    Attributes:
+        variables: Bound user variables, name to signed 32-bit value.
+        ans: The value of the most recent successful expression, or ``None``
+            when no expression has succeeded yet.
+    """
+
+    variables: dict[str, int] = field(default_factory=dict)
+    ans: int | None = None
+
+
+def _check_range(value: int) -> int:
+    """Return ``value`` if it is a signed 32-bit integer, else raise.
+
+    Args:
+        value: A value produced by an operation.
+
+    Returns:
+        The same value, unchanged.
+
+    Raises:
+        OracleError: ``"IntegerRangeError"`` when the value is outside
+            ``INT_MIN..INT_MAX``.
+    """
+    if not INT_MIN <= value <= INT_MAX:
+        raise OracleError("IntegerRangeError")
+    return value
+
+
+def _apply_binary(op: str, left: int, right: int) -> int:
+    """Apply a binary operator with the spec's exact integer semantics.
+
+    Args:
+        op: The operator text.
+        left: The already-evaluated left operand.
+        right: The already-evaluated right operand.
+
+    Returns:
+        The signed 32-bit result.
+
+    Raises:
+        OracleError: ``"DivisionByZeroError"`` for a zero divisor,
+            ``"DomainError"`` for a negative exponent, or
+            ``"IntegerRangeError"`` when a result leaves the range.
+    """
+    if op == "+":
+        return _check_range(left + right)
+    if op == "-":
+        return _check_range(left - right)
+    if op == "*":
+        return _check_range(left * right)
+    if op in ("/", "//", "%"):
+        if right == 0:
+            raise OracleError("DivisionByZeroError")
+        if op == "/":
+            # Truncate toward zero without using float arithmetic.
+            quotient = abs(left) // abs(right)
+            if (left < 0) != (right < 0):
+                quotient = -quotient
+            return _check_range(quotient)
+        if op == "//":
+            # Python's // is floor division, as the spec requires.
+            return _check_range(left // right)
+        # Python's % is floored modulo; INT_MIN % -1 is 0, in range.
+        return _check_range(left % right)
+    if op == "**":
+        if right < 0:
+            # This check precedes every base special case ([D-15] ruling 4).
+            raise OracleError("DomainError")
+        if right == 0:
+            return 1
+        if left == 0:
+            return 0
+        if left == 1:
+            return 1
+        if left == -1:
+            return 1 if right % 2 == 0 else -1
+        if abs(left) >= 2 and right > 31:
+            # Short-circuit before computing: 2 ** 1000000000 must not hang.
+            raise OracleError("IntegerRangeError")
+        return _check_range(left**right)
+    if op == "==":
+        return 1 if left == right else 0
+    if op == "!=":
+        return 1 if left != right else 0
+    if op == "<":
+        return 1 if left < right else 0
+    if op == "<=":
+        return 1 if left <= right else 0
+    if op == ">":
+        return 1 if left > right else 0
+    if op == ">=":
+        return 1 if left >= right else 0
+    raise ValueError(f"unknown binary operator: {op!r}")
+
+
+#: Arity table for the built-ins: name -> (minimum, maximum); ``None`` means
+#: unbounded maximum.
+_BUILTIN_ARITY: dict[str, tuple[int, int | None]] = {
+    "abs": (1, 1),
+    "min": (1, None),
+    "max": (1, None),
+    "gcd": (2, 2),
+}
+
+
+def _apply_call(func: str, args: tuple["Node", ...], state: OracleState) -> int:
+    """Evaluate a call: arity first, then arguments left to right.
+
+    Args:
+        func: The function name as written.
+        args: The argument trees.
+        state: The environment used to evaluate arguments.
+
+    Returns:
+        The signed 32-bit call result.
+
+    Raises:
+        OracleError: ``"CallError"`` for an unknown function or wrong arity,
+            plus any error raised while evaluating an argument or computing
+            the result.
+    """
+    if func not in _BUILTIN_ARITY:
+        # Unknown function, or a name that is not callable (spec section 6).
+        raise OracleError("CallError")
+    minimum, maximum = _BUILTIN_ARITY[func]
+    if len(args) < minimum or (maximum is not None and len(args) > maximum):
+        raise OracleError("CallError")
+    values = [evaluate(arg, state) for arg in args]
+    if func == "abs":
+        if values[0] == INT_MIN:
+            raise OracleError("IntegerRangeError")
+        return _check_range(abs(values[0]))
+    if func == "min":
+        return _check_range(min(values))
+    if func == "max":
+        return _check_range(max(values))
+    # gcd: math.gcd is always non-negative; the result is range-checked, so
+    # gcd(INT_MIN, 0) and gcd(INT_MIN, INT_MIN) raise IntegerRangeError.
+    return _check_range(math.gcd(values[0], values[1]))
+
+
+def evaluate(node: "Node", state: OracleState) -> int:
+    """Evaluate a reference expression tree.
+
+    Binary operands and call arguments are evaluated left to right; that is
+    the natural source order and the order the spec fixes explicitly for call
+    arguments.
+
+    Args:
+        node: The expression tree to evaluate.
+        state: The reference environment used for name lookup.
+
+    Returns:
+        The signed 32-bit integer result.
+
+    Raises:
+        OracleError: A spec evaluation error class name.
+    """
+    if isinstance(node, Const):
+        return _check_range(node.value)
+    if isinstance(node, Var):
+        if node.name == "ans":
+            if state.ans is None:
+                raise OracleError("UndefinedNameError")
+            return state.ans
+        if node.name in state.variables:
+            return state.variables[node.name]
+        # Unset variables and bare built-in names are both undefined values.
+        raise OracleError("UndefinedNameError")
+    if isinstance(node, UnaryOp):
+        value = evaluate(node.operand, state)
+        if node.op == "+":
+            return value
+        return _check_range(-value)
+    if isinstance(node, BinaryOp):
+        left = evaluate(node.left, state)
+        right = evaluate(node.right, state)
+        return _apply_binary(node.op, left, right)
+    if isinstance(node, CallOp):
+        return _apply_call(node.func, node.args, state)
+    raise TypeError(f"unknown node: {node!r}")
+
+
+def execute(stmt: Union["Node", AssignStmt], state: OracleState) -> tuple[str, int | None, str | None]:
+    """Execute one statement against reference state, atomically.
+
+    A successful expression updates ``ans``. A successful assignment binds
+    its target and leaves ``ans`` unchanged. A failing statement changes
+    neither variables nor ``ans``.
+
+    Args:
+        stmt: An :class:`AssignStmt` or an expression tree.
+        state: The reference environment, mutated only on success.
+
+    Returns:
+        A ``(kind, value, name)`` tuple where ``kind`` is ``"value"`` or
+        ``"assign"``; ``name`` is the assignment target or ``None``.
+
+    Raises:
+        OracleError: ``"AssignmentError"`` when the target is reserved (the
+            check precedes right-side evaluation), or any expression error.
+    """
+    if isinstance(stmt, AssignStmt):
+        if stmt.target in RESERVED_NAMES:
+            raise OracleError("AssignmentError")
+        value = evaluate(stmt.value, state)
+        state.variables[stmt.target] = value
+        return ("assign", value, stmt.target)
+    value = evaluate(stmt, state)
+    state.ans = value
+    return ("value", value, None)
+
+
+#: Precedence strength used by the minimal renderer. Larger binds tighter:
+#: comparison 1, additive 2, multiplicative 3, unary 4, power 5, primary 6.
+_PRECEDENCE: dict[str, int] = {
+    "==": 1,
+    "!=": 1,
+    "<": 1,
+    "<=": 1,
+    ">": 1,
+    ">=": 1,
+    "+": 2,
+    "-": 2,
+    "*": 3,
+    "/": 3,
+    "//": 3,
+    "%": 3,
+    "**": 5,
+}
+
+_PRIMARY_PRECEDENCE = 6
+_UNARY_PRECEDENCE = 4
+
+
+def _literal_text(value: int) -> str:
+    """Render an integer value as valid MiniCalc source.
+
+    Negative constants are rendered as unary minus expressions. ``INT_MIN``
+    is rendered as ``((-2147483647) - 1)`` because ``2147483648`` is not a
+    valid literal.
+
+    Args:
+        value: An in-range integer value.
+
+    Returns:
+        Source text for a primary expression evaluating to ``value``.
+    """
+    if value == INT_MIN:
+        return "((-2147483647) - 1)"
+    if value < 0:
+        return f"(-{-value})"
+    return str(value)
+
+
+def _node_precedence(node: "Node") -> int:
+    """Return the binding strength of a reference tree node.
+
+    Args:
+        node: The tree node.
+
+    Returns:
+        The precedence strength used by :func:`_render_minimal`.
+    """
+    if isinstance(node, (Const, Var, CallOp)):
+        return _PRIMARY_PRECEDENCE
+    if isinstance(node, UnaryOp):
+        return _UNARY_PRECEDENCE
+    if isinstance(node, BinaryOp):
+        return _PRECEDENCE[node.op]
+    raise TypeError(f"unknown node: {node!r}")
+
+
+def _render_full(node: "Node") -> str:
+    """Render a tree with every operation parenthesized.
+
+    Args:
+        node: The tree node.
+
+    Returns:
+        Fully parenthesized MiniCalc source.
+    """
+    if isinstance(node, Const):
+        return _literal_text(node.value)
+    if isinstance(node, Var):
+        return node.name
+    if isinstance(node, UnaryOp):
+        return f"({node.op}{_render_full(node.operand)})"
+    if isinstance(node, BinaryOp):
+        return f"({_render_full(node.left)} {node.op} {_render_full(node.right)})"
+    if isinstance(node, CallOp):
+        args = ", ".join(_render_full(arg) for arg in node.args)
+        return f"{node.func}({args})"
+    raise TypeError(f"unknown node: {node!r}")
+
+
+def _render_operand(node: "Node", required: int) -> str:
+    """Render an operand, parenthesizing it when its precedence is too low.
+
+    Args:
+        node: The operand tree.
+        required: The minimum unparenthesized precedence strength.
+
+    Returns:
+        MiniCalc source for the operand.
+    """
+    text = _render_minimal(node)
+    if _node_precedence(node) < required:
+        return f"({text})"
+    return text
+
+
+def _render_minimal(node: "Node") -> str:
+    """Render a tree using the spec precedence and associativity table.
+
+    Args:
+        node: The tree node.
+
+    Returns:
+        Minimally parenthesized MiniCalc source.
+    """
+    if isinstance(node, Const):
+        return _literal_text(node.value)
+    if isinstance(node, Var):
+        return node.name
+    if isinstance(node, UnaryOp):
+        # Grammar: unary = (MINUS | PLUS) unary | power.
+        return f"{node.op}{_render_operand(node.operand, _UNARY_PRECEDENCE)}"
+    if isinstance(node, BinaryOp):
+        op = node.op
+        if op in COMPARISON_OPS:
+            # Grammar: additive [compare_op additive].
+            left = _render_operand(node.left, 2)
+            right = _render_operand(node.right, 2)
+        elif op in ("+", "-"):
+            # Left associative: the left child may share the level.
+            left = _render_operand(node.left, 2)
+            right = _render_operand(node.right, 3)
+        elif op in ("*", "/", "//", "%"):
+            # Left associative: the left child may share the level.
+            left = _render_operand(node.left, 3)
+            right = _render_operand(node.right, 4)
+        elif op == "**":
+            # Right associative; the left side is a primary, the right side
+            # is a unary (which includes another power).
+            left = _render_operand(node.left, _PRIMARY_PRECEDENCE)
+            right = _render_operand(node.right, _UNARY_PRECEDENCE)
+        else:
+            raise ValueError(f"unknown binary operator: {op!r}")
+        return f"{left} {op} {right}"
+    if isinstance(node, CallOp):
+        args = ", ".join(_render_minimal(arg) for arg in node.args)
+        return f"{node.func}({args})"
+    raise TypeError(f"unknown node: {node!r}")
+
+
+def render_full(node: "Node") -> str:
+    """Render a reference tree with every operation parenthesized.
+
+    Args:
+        node: The expression tree.
+
+    Returns:
+        A fully parenthesized MiniCalc expression.
+    """
+    return _render_full(node)
+
+
+def render_minimal(node: "Node") -> str:
+    """Render a reference tree with minimal parentheses.
+
+    Args:
+        node: The expression tree.
+
+    Returns:
+        A MiniCalc expression using the spec precedence table.
+    """
+    return _render_minimal(node)
+
+
+#: Fixed spec rulings from [D-15] and spec sections 2, 5, and 6. An integer
+#: expectation is a successful value; a string is the expected error class.
+PHASE2_RULING_CASES: tuple[tuple[str, object], ...] = (
+    (f"({INT_MIN_SOURCE}) % -1", 0),
+    ("0 ** -1", "DomainError"),
+    ("1 ** -1", "DomainError"),
+    ("(-1) ** -1", "DomainError"),
+    (f"gcd({INT_MIN_SOURCE}, 0)", "IntegerRangeError"),
+    (f"gcd({INT_MIN_SOURCE}, {INT_MIN_SOURCE})", "IntegerRangeError"),
+    ("ans = 1 / 0", "AssignmentError"),
+    ("abs = 1 / 0", "AssignmentError"),
+)
+
+#: Lexical ruling from [D-15] ruling 2: (source, error class, 1-based column).
+PHASE2_LEX_CASES: tuple[tuple[str, str, int], ...] = (
+    ("12é", "LexError", 3),
+)
+
+#: Worked examples from spec sections 3 and 5, used as a fixed sanity check
+#: for truncation, floor division, floored modulo, power associativity, and
+#: range/domain errors. An integer is a value; a string is an error class.
+SPEC_WORKED_CASES: tuple[tuple[str, object], ...] = (
+    ("2 + 3 * 4", 14),
+    ("(2 + 3) * 4", 20),
+    ("10 - 3 - 2", 5),
+    ("-2 ** 2", -4),
+    ("2 ** 3 ** 2", 512),
+    ("2 ** 30", 1073741824),
+    ("7 / 2", 3),
+    ("-7 / 2", -3),
+    ("7 // 2", 3),
+    ("-7 // 2", -4),
+    ("-7 % 2", 1),
+    ("7 % -2", -1),
+    ("-7 % -2", -1),
+    ("5 > 3", 1),
+    ("5 == 4", 0),
+    ("2 + 3 == 5", 1),
+    (INT_MIN_SOURCE, INT_MIN),
+    ("5 / 0", "DivisionByZeroError"),
+    ("2 ** 31", "IntegerRangeError"),
+    ("2 ** -1", "DomainError"),
+    ("2147483647 + 1", "IntegerRangeError"),
+)
diff --git c/tests/test_differential.py w/tests/test_differential.py
new file mode 100644
index 0000000..de39214
--- /dev/null
+++ w/tests/test_differential.py
@@ -0,0 +1,681 @@
+"""Differential test for MiniCalc (INT-002).
+
+This test generates seeded random expression trees, renders each tree to
+MiniCalc source in two ways (fully parenthesized and minimally parenthesized
+per the spec table), and compares the real ``Interpreter`` against
+:mod:`tests.oracle`, a reference evaluator written from the language spec
+only.
+
+The comparison is by value or error class, never by message text. Fixed spec
+rulings ([D-15]) and the spec's worked examples are checked separately, and
+seeded variable-state sequences verify assignment atomicity and ``ans``.
+"""
+
+from __future__ import annotations
+
+import random
+import time
+from collections import Counter
+from typing import Union
+
+import pytest
+
+from minicalc.errors import MiniCalcError
+from minicalc.interpreter import Interpreter
+from minicalc.limits import INT_MAX, INT_MIN
+
+import oracle
+
+
+#: Fixed seeds for the generated expression suite.
+SEEDS: tuple[int, ...] = (20261026, 1729, 314159, 271828, 161803)
+
+#: Expressions generated per category per seed, for each rendering.
+PER_CATEGORY = 80
+
+#: Top-level categories used for generation and reporting.
+CATEGORIES: tuple[str, ...] = (
+    "additive",
+    "multiplicative",
+    "division",
+    "power",
+    "comparison",
+    "unary",
+    "builtin_call",
+)
+
+#: The minimum number of generated expressions required per rendering.
+MIN_EXPRESSIONS_PER_RENDERING = 2000
+
+#: The required upper bound on total generated-suite runtime, in seconds.
+MAX_RUNTIME_SECONDS = 15.0
+
+#: At most this many mismatches are collected before the assertion fails.
+MAX_MISMATCHES = 10
+
+#: Fixed seeds for variable-state sequences.
+STATE_SEEDS: tuple[int, ...] = (101, 202, 303, 404, 505, 606, 707, 808)
+
+#: Lines per variable-state sequence.
+SEQUENCE_LENGTH = 20
+
+#: User variable names used by state sequences.
+VAR_NAMES: tuple[str, ...] = ("v0", "v1", "v2", "v3", "v4")
+
+#: A generated statement is either an expression tree or an assignment.
+Statement = Union[oracle.Node, oracle.AssignStmt]
+
+#: Bit patterns deliberately spread around the overflow boundaries.
+_SMALL = tuple(range(0, 11))
+_SQRT = (46339, 46340, 46341, 46342, -46340, -46341)
+_NEAR = (
+    INT_MAX,
+    INT_MAX - 1,
+    INT_MIN,
+    INT_MIN + 1,
+    2**30,
+    -(2**30),
+    2**31 - 2,
+    -(2**31) + 2,
+)
+_POWERS = (
+    0,
+    1,
+    2,
+    4,
+    8,
+    16,
+    32,
+    64,
+    128,
+    256,
+    512,
+    1024,
+    2**20,
+    2**30,
+    -1,
+    -2,
+    -4,
+    -8,
+    -16,
+    -32,
+    -64,
+    -128,
+    -256,
+    -512,
+    -1024,
+)
+
+
+def _random_constant(rng: random.Random) -> int:
+    """Draw a constant from a mixture of magnitudes.
+
+    The buckets are small values (zero-heavy), values around ``sqrt(2**31)``,
+    values around the 32-bit boundary, and powers of two. This makes overflow,
+    zero divisors, and special power bases all common.
+
+    Args:
+        rng: The seeded random source.
+
+    Returns:
+        An in-range signed 32-bit integer.
+    """
+    bucket = rng.random()
+    if bucket < 0.30:
+        return rng.choice(_SMALL)
+    if bucket < 0.55:
+        return rng.choice(_SQRT)
+    if bucket < 0.80:
+        return rng.choice(_NEAR)
+    return rng.choice(_POWERS)
+
+
+def _leaf(rng: random.Random, allow_vars: bool) -> oracle.Node:
+    """Return a leaf node, optionally allowing names.
+
+    Args:
+        rng: The seeded random source.
+        allow_vars: When true, emit variables, ``ans``, undefined names, and
+            bare built-in names as well as constants.
+
+    Returns:
+        A :class:`oracle.Const` or :class:`oracle.Var` leaf.
+    """
+    if not allow_vars:
+        return oracle.Const(_random_constant(rng))
+    bucket = rng.random()
+    if bucket < 0.30:
+        return oracle.Const(_random_constant(rng))
+    if bucket < 0.55:
+        return oracle.Var(rng.choice(VAR_NAMES))
+    if bucket < 0.70:
+        return oracle.Var("ans")
+    if bucket < 0.85:
+        return oracle.Var(rng.choice(("never_set_a", "never_set_b")))
+    if bucket < 0.93:
+        # A bare built-in name is an undefined value (spec section 6).
+        return oracle.Var("abs")
+    return oracle.Const(_random_constant(rng))
+
+
+def _random_exponent(rng: random.Random, depth: int, allow_vars: bool) -> oracle.Node:
+    """Build an exponent tree, including negative and huge exponents.
+
+    Args:
+        rng: The seeded random source.
+        depth: Remaining expression depth for a random exponent.
+        allow_vars: Whether names are allowed in a random exponent.
+
+    Returns:
+        An expression tree used as a ``**`` right operand.
+    """
+    bucket = rng.random()
+    if bucket < 0.55:
+        return oracle.Const(rng.randint(0, 4))
+    if bucket < 0.70:
+        return oracle.Const(rng.choice((30, 31, 32, 33, 62, 100, 1000, INT_MAX)))
+    if bucket < 0.85:
+        return oracle.UnaryOp("-", oracle.Const(rng.randint(1, 5)))
+    return random_expr(rng, max(0, depth - 1), allow_vars)
+
+
+def _random_call(rng: random.Random, depth: int, allow_vars: bool) -> oracle.CallOp:
+    """Build a built-in call, with a small share of invalid calls.
+
+    Args:
+        rng: The seeded random source.
+        depth: Remaining expression depth for arguments.
+        allow_vars: Whether names are allowed in arguments.
+
+    Returns:
+        A :class:`oracle.CallOp` node.
+    """
+
+    def argument() -> oracle.Node:
+        return random_expr(rng, max(0, depth - 1), allow_vars)
+
+    bucket = rng.random()
+    if bucket < 0.32:
+        return oracle.CallOp("abs", (argument(),))
+    if bucket < 0.55:
+        return oracle.CallOp("min", tuple(argument() for _ in range(rng.randint(1, 3))))
+    if bucket < 0.78:
+        return oracle.CallOp("max", tuple(argument() for _ in range(rng.randint(1, 3))))
+    if bucket < 0.94:
+        return oracle.CallOp("gcd", (argument(), argument()))
+    if bucket < 0.97:
+        return oracle.CallOp("foo", (argument(),))
+    return oracle.CallOp("abs", (argument(), argument()))
+
+
+def random_expr(rng: random.Random, depth: int, allow_vars: bool = False) -> oracle.Node:
+    """Build a random expression tree of bounded depth.
+
+    Args:
+        rng: The seeded random source.
+        depth: Maximum remaining depth; zero produces a leaf.
+        allow_vars: Whether name leaves are allowed.
+
+    Returns:
+        An expression tree.
+    """
+    if depth <= 0:
+        return _leaf(rng, allow_vars)
+    bucket = rng.random()
+    if bucket < 0.28:
+        return oracle.BinaryOp(
+            rng.choice(("+", "-", "*")),
+            random_expr(rng, depth - 1, allow_vars),
+            random_expr(rng, depth - 1, allow_vars),
+        )
+    if bucket < 0.48:
+        op = rng.choice(("/", "//", "%"))
+        right = random_expr(rng, depth - 1, allow_vars)
+        if rng.random() < 0.20:
+            right = oracle.Const(0)
+        return oracle.BinaryOp(
+            op, random_expr(rng, depth - 1, allow_vars), right
+        )
+    if bucket < 0.62:
+        return oracle.BinaryOp(
+            "**",
+            random_expr(rng, depth - 1, allow_vars),
+            _random_exponent(rng, depth, allow_vars),
+        )
+    if bucket < 0.74:
+        return oracle.UnaryOp(
+            rng.choice(("-", "+")), random_expr(rng, depth - 1, allow_vars)
+        )
+    if bucket < 0.88:
+        return _random_call(rng, depth, allow_vars)
+    if bucket < 0.96:
+        return oracle.BinaryOp(
+            rng.choice(sorted(oracle.COMPARISON_OPS)),
+            random_expr(rng, depth - 1, allow_vars),
+            random_expr(rng, depth - 1, allow_vars),
+        )
+    return _leaf(rng, allow_vars)
+
+
+def generate_expression(rng: random.Random, category: str) -> oracle.Node:
+    """Build an expression whose root belongs to ``category``.
+
+    Args:
+        rng: The seeded random source.
+        category: One of :data:`CATEGORIES`.
+
+    Returns:
+        An expression tree.
+
+    Raises:
+        ValueError: If ``category`` is unknown.
+    """
+    if category == "additive":
+        return oracle.BinaryOp(
+            rng.choice(("+", "-")), random_expr(rng, 2), random_expr(rng, 2)
+        )
+    if category == "multiplicative":
+        return oracle.BinaryOp("*", random_expr(rng, 2), random_expr(rng, 2))
+    if category == "division":
+        right = random_expr(rng, 2)
+        if rng.random() < 0.30:
+            right = oracle.Const(0)
+        return oracle.BinaryOp(
+            rng.choice(("/", "//", "%")), random_expr(rng, 2), right
+        )
+    if category == "power":
+        if rng.random() < 0.30:
+            # Guarantee right-nested powers, which distinguish left- and
+            # right-associative parsing.
+            exponent: oracle.Node = oracle.BinaryOp(
+                "**", random_expr(rng, 1), oracle.Const(rng.randint(0, 4))
+            )
+        else:
+            exponent = _random_exponent(rng, 2, False)
+        return oracle.BinaryOp("**", random_expr(rng, 2), exponent)
+    if category == "comparison":
+        return oracle.BinaryOp(
+            rng.choice(sorted(oracle.COMPARISON_OPS)),
+            random_expr(rng, 2),
+            random_expr(rng, 2),
+        )
+    if category == "unary":
+        return oracle.UnaryOp(rng.choice(("-", "+")), random_expr(rng, 2))
+    if category == "builtin_call":
+        return _random_call(rng, 2, False)
+    raise ValueError(f"unknown category: {category!r}")
+
+
+def _oracle_value_outcome(tree: oracle.Node) -> tuple[object, ...]:
+    """Evaluate a tree with the reference evaluator in a fresh state.
+
+    Args:
+        tree: The expression tree.
+
+    Returns:
+        ``("value", result)`` or ``("error", error_class)``.
+    """
+    state = oracle.OracleState()
+    try:
+        return ("value", oracle.evaluate(tree, state))
+    except oracle.OracleError as exc:
+        return ("error", exc.kind)
+
+
+def _actual_value_outcome(interp: Interpreter, source: str) -> tuple[object, ...]:
+    """Run one line through the real interpreter.
+
+    Args:
+        interp: The interpreter session.
+        source: MiniCalc source text.
+
+    Returns:
+        ``("value", result)``, ``("assign", value, name)``, or
+        ``("error", class_name, message)``.
+    """
+    try:
+        result = interp.run_line(source)
+    except MiniCalcError as exc:
+        return ("error", type(exc).__name__, str(exc))
+    except Exception as exc:  # pragma: no cover - defensive diagnostics only
+        return ("error", f"{type(exc).__name__}", str(exc))
+    if result.kind == "value":
+        return ("value", result.value)
+    if result.kind == "assign":
+        return ("assign", result.value, result.name)
+    return ("empty", None)
+
+
+def _matches(expected: tuple[object, ...], actual: tuple[object, ...]) -> bool:
+    """Compare outcomes by value or error class only.
+
+    Args:
+        expected: Oracle outcome.
+        actual: Interpreter outcome.
+
+    Returns:
+        True when the outcomes agree.
+    """
+    if expected[0] == "error" and actual[0] == "error":
+        return expected[1] == actual[1]
+    return expected == actual
+
+
+def _format_outcome(outcome: tuple[object, ...]) -> str:
+    """Format an outcome for a mismatch message.
+
+    Args:
+        outcome: A value, assignment, or error tuple.
+
+    Returns:
+        A compact human-readable string.
+    """
+    if outcome[0] == "error":
+        return f"{outcome[1]} ({outcome[2]})" if len(outcome) > 2 else str(outcome[1])
+    return repr(outcome)
+
+
+def _render(tree: oracle.Node, renderer) -> str:
+    """Render a tree with the supplied reference renderer.
+
+    Args:
+        tree: The expression tree.
+        renderer: ``oracle.render_full`` or ``oracle.render_minimal``.
+
+    Returns:
+        MiniCalc source text.
+    """
+    return renderer(tree)
+
+
+def test_generated_expressions_match_oracle() -> None:
+    """Compare thousands of generated expressions in both renderings.
+
+    The oracle tree is rendered fully parenthesized and minimally
+    parenthesized; both sources must produce the oracle value or error class.
+    """
+    started = time.perf_counter()
+    interp = Interpreter()
+    counts: dict[str, Counter[str]] = {
+        "full": Counter(),
+        "minimal": Counter(),
+    }
+    error_counts: dict[str, Counter[str]] = {
+        "full": Counter(),
+        "minimal": Counter(),
+    }
+    mismatches: list[str] = []
+
+    for seed in SEEDS:
+        for category_index, category in enumerate(CATEGORIES):
+            rng = random.Random(seed * 1000 + category_index)
+            for _ in range(PER_CATEGORY):
+                tree = generate_expression(rng, category)
+                expected = _oracle_value_outcome(tree)
+                for rendering, renderer in (
+                    ("full", oracle.render_full),
+                    ("minimal", oracle.render_minimal),
+                ):
+                    source = _render(tree, renderer)
+                    actual = _actual_value_outcome(interp, source)
+                    counts[rendering][category] += 1
+                    if expected[0] == "error":
+                        error_counts[rendering][category] += 1
+                    if not _matches(expected, actual):
+                        mismatches.append(
+                            f"seed={seed} category={category} rendering={rendering}\n"
+                            f"  source:  {source}\n"
+                            f"  oracle:  {_format_outcome(expected)}\n"
+                            f"  actual:  {_format_outcome(actual)}"
+                        )
+                        if len(mismatches) >= MAX_MISMATCHES:
+                            break
+                if len(mismatches) >= MAX_MISMATCHES:
+                    break
+            if len(mismatches) >= MAX_MISMATCHES:
+                break
+        if len(mismatches) >= MAX_MISMATCHES:
+            break
+
+    elapsed = time.perf_counter() - started
+    print("\ndifferential generated-expression summary:")
+    print(
+        f"  seeds={len(SEEDS)} categories={len(CATEGORIES)} "
+        f"per_category={PER_CATEGORY}"
+    )
+    for rendering in ("full", "minimal"):
+        total = counts[rendering].total()
+        errors = error_counts[rendering].total()
+        print(
+            f"  {rendering}: {total} expressions, {errors} expected errors, "
+            f"{total - errors} expected values"
+        )
+        print(f"    per category: {dict(sorted(counts[rendering].items()))}")
+    print(f"  elapsed: {elapsed:.3f}s")
+
+    assert not mismatches, "differential mismatches:\n" + "\n\n".join(mismatches)
+    for rendering in ("full", "minimal"):
+        assert counts[rendering].total() >= MIN_EXPRESSIONS_PER_RENDERING
+    assert elapsed < MAX_RUNTIME_SECONDS, (
+        f"generated suite took {elapsed:.3f}s, "
+        f"limit is {MAX_RUNTIME_SECONDS:.1f}s"
+    )
+
+
+def _forced_failure(rng: random.Random) -> Statement:
+    """Build a statement guaranteed to fail for a known spec reason.
+
+    Args:
+        rng: The seeded random source.
+
+    Returns:
+        A failing expression or assignment statement.
+    """
+    kind = rng.choice(
+        (
+            "div0",
+            "domain",
+            "range",
+            "undefined",
+            "reserved_ans",
+            "reserved_abs",
+            "undefined_operand",
+        )
+    )
+    if kind == "div0":
+        return oracle.BinaryOp("/", oracle.Const(_random_constant(rng)), oracle.Const(0))
+    if kind == "domain":
+        return oracle.BinaryOp(
+            "**",
+            oracle.Const(_random_constant(rng)),
+            oracle.UnaryOp("-", oracle.Const(rng.randint(1, 3))),
+        )
+    if kind == "range":
+        return oracle.BinaryOp(
+            "+", oracle.Const(INT_MAX), oracle.Const(rng.randint(1, 5))
+        )
+    if kind == "undefined":
+        return oracle.Var("never_set_a")
+    if kind == "reserved_ans":
+        # The reserved-name check precedes right-side evaluation.
+        return oracle.AssignStmt(
+            "ans", oracle.BinaryOp("/", oracle.Const(1), oracle.Const(0))
+        )
+    if kind == "reserved_abs":
+        # Still AssignmentError even though the right side is undefined.
+        return oracle.AssignStmt("abs", oracle.Var("never_set_b"))
+    return oracle.BinaryOp("+", oracle.Var("never_set_b"), oracle.Const(1))
+
+
+def generate_state_line(rng: random.Random, index: int) -> Statement:
+    """Generate one line of a variable-state sequence.
+
+    Every fifth line is a forced failure so each 20-line sequence exercises
+    atomicity and ``ans`` on errors.
+
+    Args:
+        rng: The seeded random source.
+        index: Zero-based line index inside the sequence.
+
+    Returns:
+        An expression tree or assignment statement.
+    """
+    if index % 5 == 3:
+        return _forced_failure(rng)
+    bucket = rng.random()
+    if bucket < 0.40:
+        return oracle.AssignStmt(rng.choice(VAR_NAMES), random_expr(rng, 2, True))
+    if bucket < 0.50:
+        return oracle.AssignStmt(
+            rng.choice(("ans", "abs", "min", "gcd")), random_expr(rng, 2, True)
+        )
+    return random_expr(rng, 2, True)
+
+
+def _render_statement(stmt: Statement) -> str:
+    """Render a statement as MiniCalc source.
+
+    Args:
+        stmt: An expression tree or assignment statement.
+
+    Returns:
+        MiniCalc source text.
+    """
+    if isinstance(stmt, oracle.AssignStmt):
+        return f"{stmt.target} = {oracle.render_minimal(stmt.value)}"
+    return oracle.render_minimal(stmt)
+
+
+def _oracle_statement_outcome(
+    stmt: Statement, state: oracle.OracleState
+) -> tuple[object, ...]:
+    """Execute one statement on reference state.
+
+    Args:
+        stmt: The statement.
+        state: The reference environment, mutated only on success.
+
+    Returns:
+        An outcome tuple matching :func:`_actual_value_outcome`.
+    """
+    try:
+        kind, value, name = oracle.execute(stmt, state)
+    except oracle.OracleError as exc:
+        return ("error", exc.kind)
+    if kind == "value":
+        return ("value", value)
+    return ("assign", value, name)
+
+
+def test_variable_state_sequences_match_oracle() -> None:
+    """Check seeded 20-line sequences, including failures and atomicity.
+
+    After every line, both the variables and ``ans`` are compared with the
+    oracle state. A failed line must change neither.
+    """
+    mismatches: list[str] = []
+    lines_checked = 0
+
+    for seed in STATE_SEEDS:
+        rng = random.Random(seed)
+        interp = Interpreter()
+        state = oracle.OracleState()
+        for index in range(SEQUENCE_LENGTH):
+            stmt = generate_state_line(rng, index)
+            source = _render_statement(stmt)
+            expected = _oracle_statement_outcome(stmt, state)
+            actual = _actual_value_outcome(interp, source)
+            lines_checked += 1
+            if not _matches(expected, actual):
+                mismatches.append(
+                    f"seed={seed} line={index + 1} sequence\n"
+                    f"  source:  {source}\n"
+                    f"  oracle:  {_format_outcome(expected)}\n"
+                    f"  actual:  {_format_outcome(actual)}"
+                )
+            actual_variables = dict(interp.env.variables)
+            actual_ans = interp.env.ans
+            if actual_variables != state.variables or actual_ans != state.ans:
+                mismatches.append(
+                    f"seed={seed} line={index + 1} state mismatch\n"
+                    f"  source:  {source}\n"
+                    f"  oracle variables: {state.variables} ans={state.ans}\n"
+                    f"  actual variables: {actual_variables} ans={actual_ans}"
+                )
+                # The sequence is meaningless once state diverges.
+                break
+            if len(mismatches) >= MAX_MISMATCHES:
+                break
+        if len(mismatches) >= MAX_MISMATCHES:
+            break
+
+    print(
+        f"\nvariable-state summary: {len(STATE_SEEDS)} sequences x "
+        f"{SEQUENCE_LENGTH} lines = {lines_checked} lines checked"
+    )
+    assert not mismatches, "variable-state mismatches:\n" + "\n\n".join(mismatches)
+
+
+def _assert_fixed_source(source: str, expected: object) -> None:
+    """Run one fixed source line on a fresh interpreter and compare.
+
+    Args:
+        source: MiniCalc source text.
+        expected: An integer value, or an expected error class name.
+
+    Raises:
+        AssertionError: When the outcome differs.
+    """
+    interp = Interpreter()
+    if isinstance(expected, int):
+        result = interp.run_line(source)
+        assert result.kind == "value", f"{source!r}: kind={result.kind!r}"
+        assert result.value == expected, (
+            f"{source!r}: expected {expected}, got {result.value}"
+        )
+        return
+    with pytest.raises(MiniCalcError) as info:
+        interp.run_line(source)
+    actual = type(info.value).__name__
+    assert actual == expected, f"{source!r}: expected {expected}, got {actual}"
+
+
+def test_spec_worked_examples() -> None:
+    """Check every fixed worked example recorded in the spec."""
+    for source, expected in oracle.SPEC_WORKED_CASES:
+        _assert_fixed_source(source, expected)
+
+
+def test_phase2_rulings() -> None:
+    """Check the Phase 2 rulings recorded in the spec ([D-15])."""
+    for source, expected in oracle.PHASE2_RULING_CASES:
+        _assert_fixed_source(source, expected)
+    for source, expected_class, column in oracle.PHASE2_LEX_CASES:
+        interp = Interpreter()
+        with pytest.raises(MiniCalcError) as info:
+            interp.run_line(source)
+        assert type(info.value).__name__ == expected_class
+        assert info.value.pos is not None
+        assert info.value.pos.col == column
+
+
+def test_ans_and_atomicity_ruling() -> None:
+    """Check that only successful expressions update ``ans``."""
+    interp = Interpreter()
+    first = interp.run_line("2 + 3 * 4")
+    assert first.kind == "value" and first.value == 14
+    assert interp.env.ans == 14
+
+    assigned = interp.run_line("x = 7")
+    assert assigned.kind == "assign" and assigned.name == "x" and assigned.value == 7
+    assert interp.env.ans == 14, "a successful assignment must not change ans"
+
+    second = interp.run_line("ans * x")
+    assert second.kind == "value" and second.value == 98
+    assert interp.env.ans == 98
+
+    with pytest.raises(MiniCalcError) as info:
+        interp.run_line("1 / 0")
+    assert type(info.value).__name__ == "DivisionByZeroError"
+    assert interp.env.ans == 98, "a failing expression must not change ans"
+    assert interp.env.variables == {"x": 7}, "a failing line must not change variables"
```

## 10. Patch

`patch/INT-002-claude-code-differential-audit.patch` — the same verbatim diff of the two new test files.

## 11. Flagged for APC / Operator Attention

- [ ] **Agent-assignment conflict.** The task prompt names Gemini as the assigned agent and requires an agent that did not author the evaluator/parser; this run was claude-code, which authored them in earlier tasks. Independence was enforced procedurally (oracle saved before implementation files were opened), but the operator may want a non-author review or rerun to satisfy the prompt literally.
- [ ] **Post-oracle implementation reads.** `minicalc/evaluator.py` and `minicalc/parser.py` were opened only after the oracle was saved, solely to place and revert the three mutants. This is required by the mutation step but is broader than the user note's "only to explain a concrete mismatch"; no mismatch existed and these reads did not affect the oracle or tests.
- [ ] **INT-001 status discrepancy.** The prompt says to stop unless dependencies are `done`; `docs/tasks/status.md` still marks INT-001 `needs-review`, although commit `c3a40a3` is on master and the baseline suite was green. I proceeded per the operator's explicit "INT-001 is merged" instruction. The APC may want to close INT-001's row.
- [ ] **No real mismatches.** Nothing needs implementation triage from this audit.
- [ ] **No decision ID used.** No ID was reserved; the non-trivial choices are listed under Residual Risks as instructed.
