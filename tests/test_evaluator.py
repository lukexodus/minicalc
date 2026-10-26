"""Unit tests for the MiniCalc evaluator (FEAT-003).

Every AST node is built by hand through the small helpers below, so these
tests do not depend on the lexer or parser. Positions are chosen to match the
source text used in the language spec wherever the error column matters.
"""

import time

import pytest

from minicalc.ast_nodes import Assign, Binary, Call, Name, Node, Number, Unary
from minicalc.environment import Environment
from minicalc.errors import (
    AssignmentError,
    CallError,
    DivisionByZeroError,
    DomainError,
    IntegerRangeError,
    SourcePos,
    UndefinedNameError,
)
from minicalc.evaluator import Evaluator
from minicalc.limits import INT_MAX, INT_MIN


def p(col: int) -> SourcePos:
    """Return a position on line 1 at ``col``."""
    return SourcePos(1, col)


def n(value: int, col: int = 1) -> Number:
    """Build a number literal node."""
    return Number(value, p(col))


def nm(ident: str, col: int = 1) -> Name:
    """Build a name node."""
    return Name(ident, p(col))


def u(op: str, operand: Node, col: int = 1) -> Unary:
    """Build a unary node."""
    return Unary(op, operand, p(col))  # type: ignore[arg-type]


def b(op: str, left: Node, right: Node, col: int = 3) -> Binary:
    """Build a binary node; the default operator column is 3."""
    return Binary(op, left, right, p(col))  # type: ignore[arg-type]


def call(func: str, *args: Node, col: int = 1) -> Call:
    """Build a call node whose position is the function name."""
    return Call(func, tuple(args), p(col))


def assign(target: str, value: Node, col: int = 1) -> Assign:
    """Build an assignment node whose position is the target name."""
    return Assign(target, value, p(col))


def neg(value: int, col: int = 1) -> Unary:
    """Build ``-value`` as unary minus over a non-negative literal."""
    return u("-", n(value, col + 1), col)


def int_min() -> Binary:
    """Build ``-2147483647 - 1``, the only way to spell ``INT_MIN``."""
    return b("-", u("-", n(2147483647, 2), 1), n(1, 14), 12)


def evaluate(node: Node, env: Environment | None = None) -> int:
    """Evaluate ``node`` in a fresh environment unless one is supplied."""
    return Evaluator(env if env is not None else Environment()).evaluate(node)


# --- Worked examples from language-spec section 5 -------------------------

WORKED_EXAMPLES = [
    pytest.param(b("+", n(2), b("*", n(3), n(4))), 14, id="2+3*4"),
    pytest.param(b("*", b("+", n(2), n(3)), n(4)), 20, id="(2+3)*4"),
    pytest.param(b("-", b("-", n(10), n(3)), n(2)), 5, id="10-3-2"),
    pytest.param(u("-", b("**", n(2), n(2)), 1), -4, id="-2**2"),
    pytest.param(b("**", n(2), b("**", n(3), n(2))), 512, id="2**3**2"),
    pytest.param(b("**", n(2), n(30)), 1073741824, id="2**30"),
    pytest.param(b("/", n(7), n(2)), 3, id="7/2"),
    pytest.param(b("/", u("-", n(7)), n(2)), -3, id="-7/2"),
    pytest.param(b("//", n(7), n(2)), 3, id="7//2"),
    pytest.param(b("//", u("-", n(7)), n(2)), -4, id="-7//2"),
    pytest.param(b("%", u("-", n(7)), n(2)), 1, id="-7%2"),
    pytest.param(b("%", n(7), u("-", n(2))), -1, id="7%-2"),
    pytest.param(b("%", u("-", n(7)), u("-", n(2))), -1, id="-7%-2"),
    pytest.param(b(">", n(5), n(3)), 1, id="5>3"),
    pytest.param(b("==", n(5), n(4)), 0, id="5==4"),
    pytest.param(b("==", b("+", n(2), n(3)), n(5)), 1, id="2+3==5"),
    pytest.param(int_min(), INT_MIN, id="INT_MIN"),
]


@pytest.mark.parametrize(("node", "expected"), WORKED_EXAMPLES)
def test_worked_examples(node: Node, expected: int) -> None:
    """Every row of the language-spec worked-examples table evaluates."""
    assert evaluate(node) == expected


# --- Evaluation-error examples from the spec ------------------------------

EVALUATION_ERRORS = [
    pytest.param(b("/", n(5, 1), n(0, 5), 3), DivisionByZeroError, 3, id="5/0"),
    pytest.param(b("//", n(5, 1), n(0, 6), 3), DivisionByZeroError, 3, id="5//0"),
    pytest.param(b("%", n(5, 1), n(0, 5), 3), DivisionByZeroError, 3, id="5%0"),
    pytest.param(b("**", n(2, 1), n(31, 6), 3), IntegerRangeError, 3, id="2**31"),
    pytest.param(b("**", n(2, 1), neg(1, 6), 3), DomainError, 3, id="2**-1"),
    pytest.param(b("+", n(INT_MAX, 1), n(1, 14), 12), IntegerRangeError, 12, id="max+1"),
    pytest.param(b("*", n(INT_MAX, 1), n(2, 14), 12), IntegerRangeError, 12, id="max*2"),
    pytest.param(b("-", n(INT_MIN, 1), n(1, 14), 13), IntegerRangeError, 13, id="min-1"),
]


@pytest.mark.parametrize(("node", "error_type", "col"), EVALUATION_ERRORS)
def test_evaluation_errors_class_and_column(
    node: Node, error_type: type[Exception], col: int
) -> None:
    """Every evaluation-error example reports the documented class and column."""
    with pytest.raises(error_type) as info:
        evaluate(node)
    assert info.value.pos == p(col)


def test_zero_divisor_checked_before_range_for_division() -> None:
    """``INT_MIN / 0`` is a division error, not a range error."""
    with pytest.raises(DivisionByZeroError):
        evaluate(b("/", int_min(), n(0)))


def test_int_min_divided_by_minus_one_is_range_error() -> None:
    """``INT_MIN / -1`` overflows the 32-bit range."""
    with pytest.raises(IntegerRangeError) as info:
        evaluate(b("/", int_min(), neg(1), 12))
    assert info.value.pos == p(12)


def test_int_min_floor_divided_by_minus_one_is_range_error() -> None:
    """``INT_MIN // -1`` overflows the 32-bit range."""
    with pytest.raises(IntegerRangeError) as info:
        evaluate(b("//", int_min(), neg(1), 12))
    assert info.value.pos == p(12)


def test_int_min_modulo_minus_one_is_zero() -> None:
    """Floored modulo of ``INT_MIN`` by ``-1`` is in range and zero."""
    assert evaluate(b("%", int_min(), neg(1), 12)) == 0


def test_negating_int_min_is_range_error() -> None:
    """``-INT_MIN`` fails at the unary operator position."""
    with pytest.raises(IntegerRangeError) as info:
        evaluate(u("-", int_min(), 1))
    assert info.value.pos == p(1)


# --- Truncation, floor, and floored modulo --------------------------------


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (7, 2, 3),
        (-7, 2, -3),
        (7, -2, -3),
        (-7, -2, 3),
        (6, 2, 3),
        (-6, 2, -3),
    ],
)
def test_slash_truncates_toward_zero(left: int, right: int, expected: int) -> None:
    """``/`` truncates toward zero for every sign combination."""
    assert evaluate(b("/", n(left), n(right))) == expected


@pytest.mark.parametrize("left", [-7, -3, -2, -1, 1, 2, 3, 7])
@pytest.mark.parametrize("right", [-3, -2, -1, 1, 2, 3])
def test_division_modulo_identity_grid(left: int, right: int) -> None:
    """``a == (a // b) * b + a % b`` and ``%`` takes the divisor's sign."""
    env = Environment()
    quotient = evaluate(b("//", n(left), n(right)), env)
    remainder = evaluate(b("%", n(left), n(right)), env)
    truncated = evaluate(b("/", n(left), n(right)), env)

    assert quotient == left // right
    assert remainder == left % right
    if remainder != 0:
        assert (remainder < 0) == (right < 0)
    assert left == quotient * right + remainder

    expected_truncated = abs(left) // abs(right)
    if (left < 0) != (right < 0):
        expected_truncated = -expected_truncated
    assert truncated == expected_truncated


# --- Exponentiation edge cases --------------------------------------------


@pytest.mark.parametrize(
    ("base", "exponent", "expected"),
    [
        (0, 0, 1),
        (0, 5, 0),
        (1, 1_000_000, 1),
        (-1, 3, -1),
        (-1, 4, 1),
        (2, 30, 1_073_741_824),
        (-2, 31, INT_MIN),
        (-1, 0, 1),
    ],
)
def test_power_edge_cases(base: int, exponent: int, expected: int) -> None:
    """``**`` follows the spec's exact zero/one/minus-one rules."""
    base_node: Node = neg(-base, 2) if base < 0 else n(base)
    if exponent < 0:
        exponent_node: Node = neg(-exponent, 6)
    else:
        exponent_node = n(exponent, 6)
    assert evaluate(b("**", base_node, exponent_node)) == expected


@pytest.mark.parametrize(
    ("base", "exponent"),
    [
        (2, 31),
        (-2, 32),
        (2, -1),
        (3, -1),
        (7, 32),
    ],
)
def test_power_errors(base: int, exponent: int) -> None:
    """Oversized and negative exponents raise the documented errors."""
    base_node: Node = neg(-base, 2) if base < 0 else n(base)
    if exponent < 0:
        exponent_node: Node = neg(-exponent, 6)
        error_type: type[Exception] = DomainError
    else:
        exponent_node = n(exponent, 6)
        error_type = IntegerRangeError
    with pytest.raises(error_type) as info:
        evaluate(b("**", base_node, exponent_node, 3))
    assert info.value.pos == p(3)


def test_huge_power_fails_quickly() -> None:
    """``2 ** 1000000000`` short-circuits well under 0.5 seconds."""
    start = time.perf_counter()
    with pytest.raises(IntegerRangeError) as info:
        evaluate(b("**", n(2), n(1_000_000_000), 3))
    elapsed = time.perf_counter() - start
    assert info.value.pos == p(3)
    assert elapsed < 0.5


# --- Unary ----------------------------------------------------------------


def test_unary_plus_is_identity() -> None:
    """``+x`` returns ``x`` including ``INT_MIN``."""
    assert evaluate(u("+", n(5))) == 5
    assert evaluate(u("+", int_min())) == INT_MIN


def test_double_unary_minus() -> None:
    """Nested unary minus composes."""
    assert evaluate(u("-", u("-", n(5)))) == 5


# --- Names, variables, and ans --------------------------------------------


def test_variable_lookup() -> None:
    """A set variable evaluates to its value."""
    env = Environment()
    env.set("x", 7)
    assert evaluate(nm("x"), env) == 7


def test_unset_variable_error_at_name() -> None:
    """An unset variable raises at the identifier's position."""
    with pytest.raises(UndefinedNameError) as info:
        evaluate(nm("x", 4))
    assert info.value.pos == p(4)


def test_unset_ans_error() -> None:
    """``ans`` is undefined before the first successful statement."""
    with pytest.raises(UndefinedNameError) as info:
        evaluate(nm("ans", 2))
    assert info.value.pos == p(2)


def test_ans_reads_recorded_value() -> None:
    """``ans`` reads the value recorded by the facade."""
    env = Environment()
    env.record_result(42)
    assert evaluate(nm("ans"), env) == 42


@pytest.mark.parametrize("builtin_name", ["abs", "min", "max", "gcd"])
def test_builtin_name_as_value_has_call_hint(builtin_name: str) -> None:
    """Using a built-in without parentheses raises with a call hint."""
    with pytest.raises(UndefinedNameError) as info:
        evaluate(nm(builtin_name, 5))
    assert info.value.pos == p(5)
    assert str(info.value) == (
        f"'{builtin_name}' is a function; call it like {builtin_name}(...)"
    )


# --- Calls and built-ins --------------------------------------------------


@pytest.mark.parametrize(
    ("func", "args"),
    [
        ("abs", ()),
        ("abs", (n(1), n(2))),
        ("gcd", ()),
        ("gcd", (n(1),)),
        ("gcd", (n(1), n(2), n(3))),
        ("min", ()),
        ("max", ()),
    ],
)
def test_wrong_arity_is_call_error(func: str, args: tuple[Node, ...]) -> None:
    """Every arity violation raises ``CallError`` at the function name."""
    with pytest.raises(CallError) as info:
        evaluate(call(func, *args, col=7))
    assert info.value.pos == p(7)


def test_arity_checked_before_arguments() -> None:
    """A wrong arity wins over an already-failing argument."""
    with pytest.raises(CallError) as info:
        evaluate(call("abs", b("/", n(1), n(0)), n(2), col=1))
    assert info.value.pos == p(1)


@pytest.mark.parametrize(
    ("node", "expected"),
    [
        pytest.param(call("abs", neg(5)), 5, id="abs"),
        pytest.param(call("min", n(3), n(1), n(2)), 1, id="min"),
        pytest.param(call("max", neg(3), neg(1), neg(4)), -1, id="max"),
        pytest.param(call("max", n(9)), 9, id="max-one-arg"),
        pytest.param(call("gcd", n(12), n(18)), 6, id="gcd"),
    ],
)
def test_builtin_calls_succeed(node: Node, expected: int) -> None:
    """Calls evaluate their arguments and return the built-in result."""
    assert evaluate(node) == expected


def test_abs_int_min_is_range_error_at_call() -> None:
    """``abs(INT_MIN)`` fails the range check at the call position."""
    with pytest.raises(IntegerRangeError) as info:
        evaluate(call("abs", int_min(), col=4))
    assert info.value.pos == p(4)


def test_gcd_int_min_zero_is_range_error() -> None:
    """The true ``gcd(INT_MIN, 0)`` is out of range and fails the call check."""
    with pytest.raises(IntegerRangeError):
        evaluate(call("gcd", int_min(), n(0)))


def test_arguments_evaluated_left_to_right_first_failure_wins() -> None:
    """The leftmost failing argument determines the call's error."""
    with pytest.raises(DivisionByZeroError) as info:
        evaluate(
            call(
                "max",
                b("/", n(1), n(0), 10),
                b("+", n(INT_MAX), n(1), 20),
            )
        )
    assert info.value.pos == p(10)

    with pytest.raises(IntegerRangeError) as info:
        evaluate(
            call(
                "max",
                b("+", n(INT_MAX), n(1), 10),
                b("/", n(1), n(0), 20),
            )
        )
    assert info.value.pos == p(10)


def test_call_unknown_function() -> None:
    """An unknown name raises ``CallError`` at the name."""
    with pytest.raises(CallError) as info:
        evaluate(call("foo", n(1), col=3))
    assert info.value.pos == p(3)
    assert str(info.value) == "unknown function 'foo'"


def test_call_variable_is_not_a_function() -> None:
    """Calling a variable raises a specific ``CallError``."""
    env = Environment()
    env.set("x", 5)
    with pytest.raises(CallError) as info:
        evaluate(call("x", n(1), col=2), env)
    assert info.value.pos == p(2)
    assert str(info.value) == "'x' is a variable, not a function"


def test_call_ans_is_not_a_function() -> None:
    """Calling ``ans`` raises ``CallError`` at the name."""
    env = Environment()
    env.record_result(5)
    with pytest.raises(CallError) as info:
        evaluate(call("ans", col=6), env)
    assert info.value.pos == p(6)


# --- Assignment -----------------------------------------------------------


def test_assignment_binds_after_success() -> None:
    """A successful assignment binds the target and returns the value."""
    env = Environment()
    assert evaluate(assign("x", b("+", n(1), n(2)), 1), env) == 3
    assert env.variables == {"x": 3}
    assert env.ans is None


def test_failed_right_side_does_not_bind_new_name() -> None:
    """A failing right side never creates the target binding."""
    env = Environment()
    with pytest.raises(IntegerRangeError):
        evaluate(assign("y", b("+", n(INT_MAX), n(1))), env)
    assert env.variables == {}


def test_failed_assignment_preserves_existing_value() -> None:
    """A failing reassignment leaves the old value untouched."""
    env = Environment()
    env.set("x", 11)
    with pytest.raises(DivisionByZeroError):
        evaluate(assign("x", b("/", n(1), n(0))), env)
    assert env.variables == {"x": 11}


@pytest.mark.parametrize("target", ["ans", "abs", "min", "max", "gcd"])
def test_assignment_to_reserved_name_fails(target: str) -> None:
    """Assigning to a reserved name raises ``AssignmentError`` at the target."""
    env = Environment()
    with pytest.raises(AssignmentError) as info:
        evaluate(assign(target, n(1), col=9), env)
    assert info.value.pos == p(9)
    assert env.variables == {}


def test_reserved_check_precedes_right_side() -> None:
    """A reserved target fails before a failing right side is evaluated."""
    with pytest.raises(AssignmentError):
        evaluate(assign("ans", b("/", n(1), n(0), 5), 1))


# --- Programming errors ---------------------------------------------------


def test_unknown_node_type_raises_type_error() -> None:
    """An unsupported AST object is a programming error, not a MiniCalcError."""
    with pytest.raises(TypeError):
        Evaluator(Environment()).evaluate(object())  # type: ignore[arg-type]


def test_unknown_binary_operator_raises_type_error() -> None:
    """An operator outside the locked ``Op`` set is a programming error."""
    with pytest.raises(TypeError):
        evaluate(Binary("^", n(1), n(2), p(3)))  # type: ignore[arg-type]


def test_unknown_unary_operator_raises_type_error() -> None:
    """An unsupported unary operator is a programming error."""
    with pytest.raises(TypeError):
        evaluate(Unary("~", n(1), p(1)))  # type: ignore[arg-type]
