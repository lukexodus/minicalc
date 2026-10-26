"""Unit tests for MiniCalc built-ins and reserved names (FEAT-003).

The functions operate on plain Python integers: range checking is the
evaluator's responsibility, so ``abs(INT_MIN)`` is expected to return
``2147483648`` here.
"""

from dataclasses import FrozenInstanceError

import pytest

from minicalc.builtins import BUILTINS, Builtin, is_reserved
from minicalc.limits import INT_MAX, INT_MIN


def test_registry_contents_and_arities() -> None:
    """The registry holds exactly the four spec built-ins with their arities."""
    assert set(BUILTINS) == {"abs", "min", "max", "gcd"}
    assert (BUILTINS["abs"].min_args, BUILTINS["abs"].max_args) == (1, 1)
    assert (BUILTINS["min"].min_args, BUILTINS["min"].max_args) == (1, None)
    assert (BUILTINS["max"].min_args, BUILTINS["max"].max_args) == (1, None)
    assert (BUILTINS["gcd"].min_args, BUILTINS["gcd"].max_args) == (2, 2)
    for name, builtin in BUILTINS.items():
        assert builtin.name == name
        assert isinstance(builtin.doc, str) and builtin.doc


def test_builtin_is_frozen() -> None:
    """``Builtin`` instances are immutable."""
    with pytest.raises(FrozenInstanceError):
        BUILTINS["abs"].name = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0),
        (5, 5),
        (-5, 5),
        (INT_MAX, INT_MAX),
        (INT_MIN, 2_147_483_648),
    ],
)
def test_abs(value: int, expected: int) -> None:
    """``abs`` returns a plain non-negative integer, even for ``INT_MIN``."""
    result = BUILTINS["abs"].fn(value)
    assert result == expected
    assert isinstance(result, int)


def test_abs_int_min_is_out_of_range_but_plain_int() -> None:
    """Range checking is deliberately left to the evaluator."""
    result = BUILTINS["abs"].fn(INT_MIN)
    assert result == 2_147_483_648
    assert result > INT_MAX


@pytest.mark.parametrize("name", ["min", "max"])
def test_min_max_require_at_least_one_argument(name: str) -> None:
    """The registry advertises an unbounded maximum and a minimum of one."""
    assert BUILTINS[name].min_args == 1
    assert BUILTINS[name].max_args is None


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ((4,), 4),
        ((3, 1, 2), 1),
        ((-3, -1, -4), -4),
        ((INT_MAX, INT_MIN, 0), INT_MIN),
    ],
)
def test_min(values: tuple[int, ...], expected: int) -> None:
    """``min`` returns the smallest argument for any arity >= 1."""
    assert BUILTINS["min"].fn(*values) == expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ((4,), 4),
        ((3, 1, 2), 3),
        ((-3, -1, -4), -1),
        ((INT_MAX, INT_MIN, 0), INT_MAX),
    ],
)
def test_max(values: tuple[int, ...], expected: int) -> None:
    """``max`` returns the largest argument for any arity >= 1."""
    assert BUILTINS["max"].fn(*values) == expected


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (0, 0, 0),
        (0, 5, 5),
        (5, 0, 5),
        (12, 18, 6),
        (-4, 6, 2),
        (4, -6, 2),
        (-4, -6, 2),
        (-1, 1, 1),
        (7, 13, 1),
        (INT_MIN, 2, 2),
    ],
)
def test_gcd_signs_and_zeros(a: int, b: int, expected: int) -> None:
    """``gcd`` uses absolute values and always returns a non-negative int."""
    result = BUILTINS["gcd"].fn(a, b)
    assert result == expected
    assert result >= 0
    assert isinstance(result, int)


def test_gcd_is_symmetric() -> None:
    """``gcd(a, b) == gcd(b, a)`` across sign combinations."""
    fn = BUILTINS["gcd"].fn
    for a, b in [(12, 18), (-12, 18), (12, -18), (-12, -18), (0, 9), (9, 0)]:
        assert fn(a, b) == fn(b, a)


@pytest.mark.parametrize("name", ["ans", "abs", "min", "max", "gcd"])
def test_reserved_names(name: str) -> None:
    """``ans`` and every built-in name are reserved."""
    assert is_reserved(name)


@pytest.mark.parametrize("name", ["x", "Ans", "ABS", "answer", "_abs", "minimum"])
def test_non_reserved_names(name: str) -> None:
    """Reserved-name matching is case-sensitive and exact."""
    assert not is_reserved(name)
