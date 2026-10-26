"""Tests for tokens and AST nodes (CORE-001)."""

from dataclasses import FrozenInstanceError, fields

import pytest

from minicalc.ast_nodes import Assign, Binary, Call, Name, Number, Unary
from minicalc.errors import SourcePos
from minicalc.tokens import Token, TokenType

POS = SourcePos(1, 1)


def test_token_types_are_complete() -> None:
    """The contract's token set is present and nothing extra is required."""
    assert {member.name for member in TokenType} == {
        "NUMBER",
        "IDENT",
        "PLUS",
        "MINUS",
        "STAR",
        "SLASH",
        "DSLASH",
        "PERCENT",
        "POW",
        "EQ",
        "NE",
        "LT",
        "LE",
        "GT",
        "GE",
        "ASSIGN",
        "LPAREN",
        "RPAREN",
        "COMMA",
        "EOF",
    }


def test_token_fields_and_default() -> None:
    """``value`` defaults to None and is only meaningful for NUMBER."""
    token = Token(TokenType.IDENT, "x", POS)
    assert token.value is None
    assert token.type is TokenType.IDENT
    assert token.lexeme == "x"
    assert token.pos == POS


def test_token_is_frozen_and_hashable() -> None:
    """Tokens are immutable value objects."""
    token = Token(TokenType.NUMBER, "42", POS, 42)
    with pytest.raises(FrozenInstanceError):
        token.value = 7  # type: ignore[misc]
    assert token == Token(TokenType.NUMBER, "42", POS, 42)
    assert hash(token) == hash(Token(TokenType.NUMBER, "42", POS, 42))


def _node_samples() -> list[object]:
    """Build one instance of every AST node type."""
    number = Number(2, POS)
    name = Name("x", POS)
    unary = Unary("-", number, SourcePos(1, 2))
    binary = Binary("+", number, name, SourcePos(1, 4))
    call = Call("max", (number, name), POS)
    assign = Assign("x", binary, POS)
    return [number, name, unary, binary, call, assign]


@pytest.mark.parametrize("node", _node_samples())
def test_nodes_have_pos_last(node: object) -> None:
    """Every node declares ``pos`` as its final dataclass field."""
    assert fields(node)[-1].name == "pos"  # type: ignore[arg-type]
    assert node.pos == getattr(node, "pos")  # type: ignore[attr-defined]


@pytest.mark.parametrize("node", _node_samples())
def test_nodes_are_frozen_hashable_and_value_equal(node: object) -> None:
    """Nodes cannot be mutated and compare structurally."""
    with pytest.raises(FrozenInstanceError):
        node.pos = SourcePos(9, 9)  # type: ignore[misc,attr-defined]
    clone = _node_samples()[_node_samples().index(node)]
    assert node == clone
    assert hash(node) == hash(clone)


def test_call_args_are_a_tuple() -> None:
    """``Call.args`` is immutable and keeps source order."""
    call = Call("min", (Number(3, POS), Number(1, POS)), POS)
    assert isinstance(call.args, tuple)
    assert [arg.value for arg in call.args] == [3, 1]  # type: ignore[attr-defined]


def test_structural_equality_distinguishes_fields() -> None:
    """Different values or operators are not equal."""
    assert Number(1, POS) != Number(2, POS)
    assert Binary("+", Number(1, POS), Number(2, POS), POS) != Binary(
        "-", Number(1, POS), Number(2, POS), POS
    )
