"""Unit tests for the canonical golden-line formatter (CORE-002)."""

from types import SimpleNamespace

import pytest

from golden_format import canonical_line
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


def _result(kind: str, value: int | None = None, name: str | None = None) -> object:
    """Build a duck-typed ``Result`` stand-in."""
    return SimpleNamespace(kind=kind, value=value, name=name)


def _outcome(result: object | None = None, error: BaseException | None = None) -> object:
    """Build a duck-typed ``LineOutcome`` stand-in."""
    return SimpleNamespace(result=result, error=error)


def test_value_result() -> None:
    """Expression results print as ``OK <value>``."""
    assert canonical_line(_outcome(result=_result("value", 42))) == "OK 42"


def test_assign_result() -> None:
    """Assignments print as ``OK <name>=<value>``."""
    assert canonical_line(_outcome(result=_result("assign", 7, "x"))) == "OK x=7"


def test_empty_result() -> None:
    """Blank and comment-only lines produce no golden line."""
    assert canonical_line(_outcome(result=_result("empty"))) is None


def test_missing_result_and_error_is_empty() -> None:
    """A degenerate outcome with neither field is treated as no output."""
    assert canonical_line(_outcome()) is None


@pytest.mark.parametrize(
    "error_cls",
    [
        MiniCalcError,
        LexError,
        ParseError,
        EvalError,
        DivisionByZeroError,
        IntegerRangeError,
        DomainError,
        UndefinedNameError,
        CallError,
        AssignmentError,
    ],
)
def test_errors_use_canonical_form(error_cls: type[MiniCalcError]) -> None:
    """Every error class is formatted through ``canonical()``.

    Args:
        error_cls: The error class under test.
    """
    err = error_cls("message text is ignored", SourcePos(3, 5))
    assert canonical_line(_outcome(error=err)) == f"ERR {error_cls.__name__} 3:5"


def test_error_without_position_uses_fallback() -> None:
    """The ``?:?`` canonical fallback is preserved."""
    err = ParseError("no position")
    assert canonical_line(_outcome(error=err)) == "ERR ParseError ?:?"


def test_error_takes_precedence_over_result() -> None:
    """If both fields are set, the error is reported."""
    err = LexError("bad", SourcePos(1, 1))
    assert canonical_line(_outcome(result=_result("value", 1), error=err)) == "ERR LexError 1:1"


def test_unknown_kind_is_rejected() -> None:
    """An out-of-contract result kind is a programming error, not silence."""
    with pytest.raises(ValueError, match="unknown result kind"):
        canonical_line(_outcome(result=_result("mystery")))
