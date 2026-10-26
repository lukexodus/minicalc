"""Independent reference semantics for MiniCalc (INT-002).

This module is a second, spec-only implementation of MiniCalc evaluation. It
was written from ``docs/context/language-spec.md`` (sections 2-7) and the
decision-log rulings in [D-05], [D-06], [D-07], [D-08], and [D-15] before any
``minicalc`` implementation module was opened. The only import from the
``minicalc`` package is ``INT_MIN`` and ``INT_MAX`` from ``limits.py``.

Evaluation is over a small private expression tree (:class:`Const`,
:class:`Var`, :class:`UnaryOp`, :class:`BinaryOp`, :class:`CallOp`, and
:class:`AssignStmt`). :func:`evaluate` returns an ``int`` or raises
:class:`OracleError` carrying the spec's error class name. :func:`execute`
adds the statement layer (assignment, ``ans``, reserved names, atomicity).

Phase 2 rulings encoded here ([D-15], spec sections 2, 5, and 6):

- ``ans`` changes only on a successful expression, never on an assignment.
- ``INT_MIN % -1`` is ``0``.
- A negative exponent is ``DomainError`` for every base, including ``0``,
  ``1``, and ``-1``; that check precedes the ``**`` special cases.
- ``gcd(INT_MIN, 0)`` and ``gcd(INT_MIN, INT_MIN)`` are
  ``IntegerRangeError`` (the true result is 2147483648, out of range).
- The reserved-name check on an assignment target runs before the right side
  is evaluated, so ``ans = 1 / 0`` is ``AssignmentError``.
- ``12é`` is a ``LexError`` at column 3 (recorded in
  :data:`PHASE2_LEX_CASES` for the lexical-ruling check).

Reference renderers are provided for the differential test. Both render the
same tree; :func:`render_full` parenthesizes every operation, while
:func:`render_minimal` uses the spec precedence/associativity table.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Union

from minicalc.limits import INT_MAX, INT_MIN

#: Names that cannot be assigned ([D-08] and spec section 6).
RESERVED_NAMES = frozenset({"ans", "abs", "min", "max", "gcd"})

#: Names of the built-in functions (the only callables in v1.0).
BUILTIN_NAMES = frozenset({"abs", "min", "max", "gcd"})

#: Comparison operators. They are non-associative and yield 1 or 0.
COMPARISON_OPS = frozenset({"==", "!=", "<", "<=", ">", ">="})

#: Arithmetic operators handled by :func:`_apply_binary`.
BINARY_OPS = frozenset({"+", "-", "*", "/", "//", "%", "**"}) | COMPARISON_OPS

#: Source text for the smallest 32-bit value, which cannot be a literal.
INT_MIN_SOURCE = "-2147483647 - 1"


class OracleError(Exception):
    """A spec error class reported by the reference evaluator.

    Attributes:
        kind: The spec's error class name, for example ``"DomainError"``.
    """

    def __init__(self, kind: str) -> None:
        """Initialize the error with a spec class name.

        Args:
            kind: The error class name from spec section 7.
        """
        super().__init__(kind)
        self.kind = kind

    def __repr__(self) -> str:
        """Return a diagnostic representation naming the error class."""
        return f"OracleError({self.kind!r})"


@dataclass(frozen=True)
class Const:
    """An integer value used as a leaf of the reference tree.

    Attributes:
        value: The semantic integer value, already within the signed 32-bit
            range. Negative values are rendered by the printers as unary
            minus expressions, because MiniCalc has no negative literals.
    """

    value: int


@dataclass(frozen=True)
class Var:
    """A name reference (a variable, ``ans``, or a bare built-in name).

    Attributes:
        name: The identifier text as written in source.
    """

    name: str


@dataclass(frozen=True)
class UnaryOp:
    """A prefix unary operation.

    Attributes:
        op: ``"-"`` or ``"+"``.
        operand: The child expression tree.
    """

    op: str
    operand: "Node"


@dataclass(frozen=True)
class BinaryOp:
    """A binary operation.

    Attributes:
        op: One of the arithmetic or comparison operators in
            :data:`BINARY_OPS`.
        left: The left operand tree.
        right: The right operand tree.
    """

    op: str
    left: "Node"
    right: "Node"


@dataclass(frozen=True)
class CallOp:
    """A function call written as ``func(arg, ...)``.

    Attributes:
        func: The function name as written (a built-in or an unknown name).
        args: The argument trees, in source order.
    """

    func: str
    args: tuple["Node", ...]


@dataclass(frozen=True)
class AssignStmt:
    """An assignment statement ``target = value``.

    Attributes:
        target: The identifier being bound.
        value: The right-hand expression tree.
    """

    target: str
    value: "Node"


#: The reference expression tree union.
Node = Union[Const, Var, UnaryOp, BinaryOp, CallOp]


@dataclass
class OracleState:
    """Reference environment state for one interpreter session.

    Attributes:
        variables: Bound user variables, name to signed 32-bit value.
        ans: The value of the most recent successful expression, or ``None``
            when no expression has succeeded yet.
    """

    variables: dict[str, int] = field(default_factory=dict)
    ans: int | None = None


def _check_range(value: int) -> int:
    """Return ``value`` if it is a signed 32-bit integer, else raise.

    Args:
        value: A value produced by an operation.

    Returns:
        The same value, unchanged.

    Raises:
        OracleError: ``"IntegerRangeError"`` when the value is outside
            ``INT_MIN..INT_MAX``.
    """
    if not INT_MIN <= value <= INT_MAX:
        raise OracleError("IntegerRangeError")
    return value


def _apply_binary(op: str, left: int, right: int) -> int:
    """Apply a binary operator with the spec's exact integer semantics.

    Args:
        op: The operator text.
        left: The already-evaluated left operand.
        right: The already-evaluated right operand.

    Returns:
        The signed 32-bit result.

    Raises:
        OracleError: ``"DivisionByZeroError"`` for a zero divisor,
            ``"DomainError"`` for a negative exponent, or
            ``"IntegerRangeError"`` when a result leaves the range.
    """
    if op == "+":
        return _check_range(left + right)
    if op == "-":
        return _check_range(left - right)
    if op == "*":
        return _check_range(left * right)
    if op in ("/", "//", "%"):
        if right == 0:
            raise OracleError("DivisionByZeroError")
        if op == "/":
            # Truncate toward zero without using float arithmetic.
            quotient = abs(left) // abs(right)
            if (left < 0) != (right < 0):
                quotient = -quotient
            return _check_range(quotient)
        if op == "//":
            # Python's // is floor division, as the spec requires.
            return _check_range(left // right)
        # Python's % is floored modulo; INT_MIN % -1 is 0, in range.
        return _check_range(left % right)
    if op == "**":
        if right < 0:
            # This check precedes every base special case ([D-15] ruling 4).
            raise OracleError("DomainError")
        if right == 0:
            return 1
        if left == 0:
            return 0
        if left == 1:
            return 1
        if left == -1:
            return 1 if right % 2 == 0 else -1
        if abs(left) >= 2 and right > 31:
            # Short-circuit before computing: 2 ** 1000000000 must not hang.
            raise OracleError("IntegerRangeError")
        return _check_range(left**right)
    if op == "==":
        return 1 if left == right else 0
    if op == "!=":
        return 1 if left != right else 0
    if op == "<":
        return 1 if left < right else 0
    if op == "<=":
        return 1 if left <= right else 0
    if op == ">":
        return 1 if left > right else 0
    if op == ">=":
        return 1 if left >= right else 0
    raise ValueError(f"unknown binary operator: {op!r}")


#: Arity table for the built-ins: name -> (minimum, maximum); ``None`` means
#: unbounded maximum.
_BUILTIN_ARITY: dict[str, tuple[int, int | None]] = {
    "abs": (1, 1),
    "min": (1, None),
    "max": (1, None),
    "gcd": (2, 2),
}


def _apply_call(func: str, args: tuple["Node", ...], state: OracleState) -> int:
    """Evaluate a call: arity first, then arguments left to right.

    Args:
        func: The function name as written.
        args: The argument trees.
        state: The environment used to evaluate arguments.

    Returns:
        The signed 32-bit call result.

    Raises:
        OracleError: ``"CallError"`` for an unknown function or wrong arity,
            plus any error raised while evaluating an argument or computing
            the result.
    """
    if func not in _BUILTIN_ARITY:
        # Unknown function, or a name that is not callable (spec section 6).
        raise OracleError("CallError")
    minimum, maximum = _BUILTIN_ARITY[func]
    if len(args) < minimum or (maximum is not None and len(args) > maximum):
        raise OracleError("CallError")
    values = [evaluate(arg, state) for arg in args]
    if func == "abs":
        if values[0] == INT_MIN:
            raise OracleError("IntegerRangeError")
        return _check_range(abs(values[0]))
    if func == "min":
        return _check_range(min(values))
    if func == "max":
        return _check_range(max(values))
    # gcd: math.gcd is always non-negative; the result is range-checked, so
    # gcd(INT_MIN, 0) and gcd(INT_MIN, INT_MIN) raise IntegerRangeError.
    return _check_range(math.gcd(values[0], values[1]))


def evaluate(node: "Node", state: OracleState) -> int:
    """Evaluate a reference expression tree.

    Binary operands and call arguments are evaluated left to right; that is
    the natural source order and the order the spec fixes explicitly for call
    arguments.

    Args:
        node: The expression tree to evaluate.
        state: The reference environment used for name lookup.

    Returns:
        The signed 32-bit integer result.

    Raises:
        OracleError: A spec evaluation error class name.
    """
    if isinstance(node, Const):
        return _check_range(node.value)
    if isinstance(node, Var):
        if node.name == "ans":
            if state.ans is None:
                raise OracleError("UndefinedNameError")
            return state.ans
        if node.name in state.variables:
            return state.variables[node.name]
        # Unset variables and bare built-in names are both undefined values.
        raise OracleError("UndefinedNameError")
    if isinstance(node, UnaryOp):
        value = evaluate(node.operand, state)
        if node.op == "+":
            return value
        return _check_range(-value)
    if isinstance(node, BinaryOp):
        left = evaluate(node.left, state)
        right = evaluate(node.right, state)
        return _apply_binary(node.op, left, right)
    if isinstance(node, CallOp):
        return _apply_call(node.func, node.args, state)
    raise TypeError(f"unknown node: {node!r}")


def execute(stmt: Union["Node", AssignStmt], state: OracleState) -> tuple[str, int | None, str | None]:
    """Execute one statement against reference state, atomically.

    A successful expression updates ``ans``. A successful assignment binds
    its target and leaves ``ans`` unchanged. A failing statement changes
    neither variables nor ``ans``.

    Args:
        stmt: An :class:`AssignStmt` or an expression tree.
        state: The reference environment, mutated only on success.

    Returns:
        A ``(kind, value, name)`` tuple where ``kind`` is ``"value"`` or
        ``"assign"``; ``name`` is the assignment target or ``None``.

    Raises:
        OracleError: ``"AssignmentError"`` when the target is reserved (the
            check precedes right-side evaluation), or any expression error.
    """
    if isinstance(stmt, AssignStmt):
        if stmt.target in RESERVED_NAMES:
            raise OracleError("AssignmentError")
        value = evaluate(stmt.value, state)
        state.variables[stmt.target] = value
        return ("assign", value, stmt.target)
    value = evaluate(stmt, state)
    state.ans = value
    return ("value", value, None)


#: Precedence strength used by the minimal renderer. Larger binds tighter:
#: comparison 1, additive 2, multiplicative 3, unary 4, power 5, primary 6.
_PRECEDENCE: dict[str, int] = {
    "==": 1,
    "!=": 1,
    "<": 1,
    "<=": 1,
    ">": 1,
    ">=": 1,
    "+": 2,
    "-": 2,
    "*": 3,
    "/": 3,
    "//": 3,
    "%": 3,
    "**": 5,
}

_PRIMARY_PRECEDENCE = 6
_UNARY_PRECEDENCE = 4


def _literal_text(value: int) -> str:
    """Render an integer value as valid MiniCalc source.

    Negative constants are rendered as unary minus expressions. ``INT_MIN``
    is rendered as ``((-2147483647) - 1)`` because ``2147483648`` is not a
    valid literal.

    Args:
        value: An in-range integer value.

    Returns:
        Source text for a primary expression evaluating to ``value``.
    """
    if value == INT_MIN:
        return "((-2147483647) - 1)"
    if value < 0:
        return f"(-{-value})"
    return str(value)


def _node_precedence(node: "Node") -> int:
    """Return the binding strength of a reference tree node.

    Args:
        node: The tree node.

    Returns:
        The precedence strength used by :func:`_render_minimal`.
    """
    if isinstance(node, (Const, Var, CallOp)):
        return _PRIMARY_PRECEDENCE
    if isinstance(node, UnaryOp):
        return _UNARY_PRECEDENCE
    if isinstance(node, BinaryOp):
        return _PRECEDENCE[node.op]
    raise TypeError(f"unknown node: {node!r}")


def _render_full(node: "Node") -> str:
    """Render a tree with every operation parenthesized.

    Args:
        node: The tree node.

    Returns:
        Fully parenthesized MiniCalc source.
    """
    if isinstance(node, Const):
        return _literal_text(node.value)
    if isinstance(node, Var):
        return node.name
    if isinstance(node, UnaryOp):
        return f"({node.op}{_render_full(node.operand)})"
    if isinstance(node, BinaryOp):
        return f"({_render_full(node.left)} {node.op} {_render_full(node.right)})"
    if isinstance(node, CallOp):
        args = ", ".join(_render_full(arg) for arg in node.args)
        return f"{node.func}({args})"
    raise TypeError(f"unknown node: {node!r}")


def _render_operand(node: "Node", required: int) -> str:
    """Render an operand, parenthesizing it when its precedence is too low.

    Args:
        node: The operand tree.
        required: The minimum unparenthesized precedence strength.

    Returns:
        MiniCalc source for the operand.
    """
    text = _render_minimal(node)
    if _node_precedence(node) < required:
        return f"({text})"
    return text


def _render_minimal(node: "Node") -> str:
    """Render a tree using the spec precedence and associativity table.

    Args:
        node: The tree node.

    Returns:
        Minimally parenthesized MiniCalc source.
    """
    if isinstance(node, Const):
        return _literal_text(node.value)
    if isinstance(node, Var):
        return node.name
    if isinstance(node, UnaryOp):
        # Grammar: unary = (MINUS | PLUS) unary | power.
        return f"{node.op}{_render_operand(node.operand, _UNARY_PRECEDENCE)}"
    if isinstance(node, BinaryOp):
        op = node.op
        if op in COMPARISON_OPS:
            # Grammar: additive [compare_op additive].
            left = _render_operand(node.left, 2)
            right = _render_operand(node.right, 2)
        elif op in ("+", "-"):
            # Left associative: the left child may share the level.
            left = _render_operand(node.left, 2)
            right = _render_operand(node.right, 3)
        elif op in ("*", "/", "//", "%"):
            # Left associative: the left child may share the level.
            left = _render_operand(node.left, 3)
            right = _render_operand(node.right, 4)
        elif op == "**":
            # Right associative; the left side is a primary, the right side
            # is a unary (which includes another power).
            left = _render_operand(node.left, _PRIMARY_PRECEDENCE)
            right = _render_operand(node.right, _UNARY_PRECEDENCE)
        else:
            raise ValueError(f"unknown binary operator: {op!r}")
        return f"{left} {op} {right}"
    if isinstance(node, CallOp):
        args = ", ".join(_render_minimal(arg) for arg in node.args)
        return f"{node.func}({args})"
    raise TypeError(f"unknown node: {node!r}")


def render_full(node: "Node") -> str:
    """Render a reference tree with every operation parenthesized.

    Args:
        node: The expression tree.

    Returns:
        A fully parenthesized MiniCalc expression.
    """
    return _render_full(node)


def render_minimal(node: "Node") -> str:
    """Render a reference tree with minimal parentheses.

    Args:
        node: The expression tree.

    Returns:
        A MiniCalc expression using the spec precedence table.
    """
    return _render_minimal(node)


#: Fixed spec rulings from [D-15] and spec sections 2, 5, and 6. An integer
#: expectation is a successful value; a string is the expected error class.
PHASE2_RULING_CASES: tuple[tuple[str, object], ...] = (
    (f"({INT_MIN_SOURCE}) % -1", 0),
    ("0 ** -1", "DomainError"),
    ("1 ** -1", "DomainError"),
    ("(-1) ** -1", "DomainError"),
    (f"gcd({INT_MIN_SOURCE}, 0)", "IntegerRangeError"),
    (f"gcd({INT_MIN_SOURCE}, {INT_MIN_SOURCE})", "IntegerRangeError"),
    ("ans = 1 / 0", "AssignmentError"),
    ("abs = 1 / 0", "AssignmentError"),
)

#: Lexical ruling from [D-15] ruling 2: (source, error class, 1-based column).
PHASE2_LEX_CASES: tuple[tuple[str, str, int], ...] = (
    ("12é", "LexError", 3),
)

#: Worked examples from spec sections 3 and 5, used as a fixed sanity check
#: for truncation, floor division, floored modulo, power associativity, and
#: range/domain errors. An integer is a value; a string is an error class.
SPEC_WORKED_CASES: tuple[tuple[str, object], ...] = (
    ("2 + 3 * 4", 14),
    ("(2 + 3) * 4", 20),
    ("10 - 3 - 2", 5),
    ("-2 ** 2", -4),
    ("2 ** 3 ** 2", 512),
    ("2 ** 30", 1073741824),
    ("7 / 2", 3),
    ("-7 / 2", -3),
    ("7 // 2", 3),
    ("-7 // 2", -4),
    ("-7 % 2", 1),
    ("7 % -2", -1),
    ("-7 % -2", -1),
    ("5 > 3", 1),
    ("5 == 4", 0),
    ("2 + 3 == 5", 1),
    (INT_MIN_SOURCE, INT_MIN),
    ("5 / 0", "DivisionByZeroError"),
    ("2 ** 31", "IntegerRangeError"),
    ("2 ** -1", "DomainError"),
    ("2147483647 + 1", "IntegerRangeError"),
)
