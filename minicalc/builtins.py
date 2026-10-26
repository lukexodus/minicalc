"""Built-in MiniCalc functions and reserved-name rules ([D-08]).

Built-ins are the only functions in v1.0. Each implementation accepts plain
Python integers and returns a plain integer; 32-bit range checking of a call's
result belongs to the evaluator, not to these functions. ``abs(INT_MIN)``
therefore returns ``2147483648`` here and the evaluator reports the range
error at the call site.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Builtin:
    """Description of one built-in function.

    Attributes:
        name: The function name as written in source (for example ``"abs"``).
        min_args: Minimum number of arguments the function accepts.
        max_args: Maximum number of arguments, or ``None`` for unbounded.
        fn: The implementation; it takes plain ints and returns an int.
        doc: One-line human-readable description used by documentation.
    """

    name: str
    min_args: int
    max_args: int | None
    fn: Callable[..., int]
    doc: str


def _abs(value: int) -> int:
    """Return the absolute value of ``value``.

    Args:
        value: Any integer.

    Returns:
        ``value`` when it is non-negative, otherwise ``-value``.
    """
    return -value if value < 0 else value


def _min(*values: int) -> int:
    """Return the smallest of ``values``.

    Args:
        values: One or more integers, guaranteed non-empty by the arity check.

    Returns:
        The smallest argument.
    """
    return min(values)


def _max(*values: int) -> int:
    """Return the largest of ``values``.

    Args:
        values: One or more integers, guaranteed non-empty by the arity check.

    Returns:
        The largest argument.
    """
    return max(values)


def _gcd(a: int, b: int) -> int:
    """Return the non-negative greatest common divisor of ``a`` and ``b``.

    Uses the iterative Euclid algorithm on absolute values, so it cannot
    overflow the Python recursion limit and ``_gcd(0, 0)`` is ``0``.

    Args:
        a: Any integer.
        b: Any integer.

    Returns:
        The greatest common divisor, always ``>= 0``.
    """
    a = _abs(a)
    b = _abs(b)
    while b:
        a, b = b, a % b
    return a


#: Every built-in function, keyed by its source name ([D-08]).
BUILTINS: dict[str, Builtin] = {
    "abs": Builtin("abs", 1, 1, _abs, "Absolute value."),
    "min": Builtin("min", 1, None, _min, "Smallest argument."),
    "max": Builtin("max", 1, None, _max, "Largest argument."),
    "gcd": Builtin("gcd", 2, 2, _gcd, "Greatest common divisor (non-negative)."),
}


def is_reserved(name: str) -> bool:
    """Return whether ``name`` cannot be used as a variable.

    Args:
        name: An identifier text, case-sensitive.

    Returns:
        True for ``"ans"`` and every built-in function name.
    """
    return name == "ans" or name in BUILTINS
