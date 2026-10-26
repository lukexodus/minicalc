"""Numeric limits for the MiniCalc integer model ([D-05]).

Values are signed 32-bit integers with checked arithmetic: a result outside
this range raises ``IntegerRangeError`` instead of wrapping. The line-length
cap keeps one source line small enough that the recursive-descent parser stays
well below Python's recursion limit.
"""

INT_MIN: int = -2_147_483_648
INT_MAX: int = 2_147_483_647
MAX_LINE_LENGTH: int = 1000


def in_range(value: int) -> bool:
    """Return whether ``value`` fits the signed 32-bit range.

    Args:
        value: An integer produced by the lexer or evaluator.

    Returns:
        True when ``INT_MIN <= value <= INT_MAX``, otherwise False.
    """
    return INT_MIN <= value <= INT_MAX
