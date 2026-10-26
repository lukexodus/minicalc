"""Tests for limits and the MiniCalc error hierarchy (CORE-001)."""

import pickle
from dataclasses import FrozenInstanceError

import pytest

from minicalc.errors import (
    AssignmentError,
    CallError,
    DivisionByZeroError,
    DomainError,
    EvalError,
    IntegerRangeError,
    LexError,
    MiniCalcError,
    ParseError,
    SourcePos,
    UndefinedNameError,
)
from minicalc.limits import INT_MAX, INT_MIN, MAX_LINE_LENGTH, in_range

EVAL_ERRORS = [
    DivisionByZeroError,
    IntegerRangeError,
    DomainError,
    UndefinedNameError,
    CallError,
    AssignmentError,
]


def test_limits_values() -> None:
    """The design-locked constants are exact."""
    assert INT_MIN == -2_147_483_648
    assert INT_MAX == 2_147_483_647
    assert MAX_LINE_LENGTH == 1000


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (INT_MIN - 1, False),
        (INT_MIN, True),
        (INT_MAX, True),
        (INT_MAX + 1, False),
    ],
)
def test_in_range(value: int, expected: bool) -> None:
    """Boundaries are inclusive."""
    assert in_range(value) is expected


def test_render_matches_contract_example() -> None:
    """The contract section 3 layout is reproduced byte for byte."""
    err = ParseError("expected an expression, found '*'", SourcePos(1, 5), "2 + * 3")
    assert err.render() == (
        "Error: Syntax error at line 1, column 5: expected an expression, found '*'\n"
        "  2 + * 3\n"
        "      ^"
    )


def test_render_without_source_line() -> None:
    """No source line means no caret block."""
    err = LexError("illegal character '@'", SourcePos(3, 2))
    assert err.render() == "Error: Lexical error at line 3, column 2: illegal character '@'"


def test_render_without_position() -> None:
    """No position means the kind-only heading."""
    err = MiniCalcError("something went wrong")
    assert err.render() == "Error: Error: something went wrong"


def test_render_tab_alignment() -> None:
    """Each tab becomes one space so the caret stays aligned."""
    err = ParseError("bad token", SourcePos(1, 2), "\t7 + 1")
    assert err.render() == "Error: Syntax error at line 1, column 2: bad token\n   7 + 1\n   ^"


def test_render_color_styles_only_label_and_caret() -> None:
    """Color mode wraps exactly two spans."""
    err = ParseError("expected an expression, found '*'", SourcePos(1, 5), "2 + * 3")
    assert err.render(color=True) == (
        "\x1b[1;31mError:\x1b[0m Syntax error at line 1, column 5: "
        "expected an expression, found '*'\n"
        "  2 + * 3\n"
        "      \x1b[31m^\x1b[0m"
    )


def test_with_source_is_chainable() -> None:
    """``with_source`` sets the line and returns the same object."""
    err = ParseError("bad")
    assert err.with_source("1 +") is err
    assert err.source_line == "1 +"


def test_str_is_message() -> None:
    """``str(err)`` never includes the kind or position."""
    err = DomainError("negative exponent", SourcePos(2, 4))
    assert str(err) == "negative exponent"
    assert err.message == "negative exponent"


def test_canonical_formats() -> None:
    """Canonical output names the concrete subclass and position."""
    assert ParseError("x", SourcePos(1, 5)).canonical() == "ERR ParseError 1:5"
    assert LexError("x", SourcePos(2, 1)).canonical() == "ERR LexError 2:1"
    assert DivisionByZeroError("x", SourcePos(3, 9)).canonical() == (
        "ERR DivisionByZeroError 3:9"
    )
    assert MiniCalcError("x").canonical() == "ERR MiniCalcError ?:?"


@pytest.mark.parametrize(
    "cls",
    [LexError, ParseError, EvalError, *EVAL_ERRORS],
)
def test_hierarchy_and_kinds(cls: type[MiniCalcError]) -> None:
    """Every class subclasses MiniCalcError with the right ``kind``."""
    assert issubclass(cls, MiniCalcError)
    expected_kind = {
        LexError: "Lexical error",
        ParseError: "Syntax error",
    }.get(cls, "Runtime error")
    assert cls.kind == expected_kind
    if cls is not EvalError and cls not in (LexError, ParseError):
        assert issubclass(cls, EvalError)


def test_source_pos_is_frozen() -> None:
    """``SourcePos`` cannot be mutated."""
    pos = SourcePos(1, 2)
    with pytest.raises(FrozenInstanceError):
        pos.line = 3  # type: ignore[misc]


def test_errors_are_picklable() -> None:
    """Errors survive a pickle round-trip with position and source line."""
    err = UndefinedNameError("x is not set", SourcePos(4, 7), "x + 1")
    clone = pickle.loads(pickle.dumps(err))
    assert type(clone) is UndefinedNameError
    assert clone.message == err.message
    assert clone.pos == err.pos
    assert clone.source_line == err.source_line
