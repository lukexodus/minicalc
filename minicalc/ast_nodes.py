"""Immutable abstract-syntax-tree nodes for MiniCalc ([D-04]).

Every node is a frozen dataclass carrying ``pos`` as its last field, so nodes
are structurally comparable and hashable. ``Assign`` is produced only at the
top of a statement; expressions never contain one.
"""

from dataclasses import dataclass as _dataclass
from typing import Literal, Union

from .errors import SourcePos

#: Every binary operator that can appear in a ``Binary`` node.
Op = Literal["+", "-", "*", "/", "//", "%", "**", "==", "!=", "<", "<=", ">", ">="]


@_dataclass(frozen=True)
class Number:
    """An integer literal.

    Attributes:
        value: The literal value, already range-checked by the lexer.
        pos: 1-based position of the first digit.
    """

    value: int
    pos: SourcePos


@_dataclass(frozen=True)
class Name:
    """A variable reference.

    Attributes:
        ident: The identifier text, case-sensitive.
        pos: 1-based position of the first character of the name.
    """

    ident: str
    pos: SourcePos


@_dataclass(frozen=True)
class Unary:
    """A prefix unary operation.

    Attributes:
        op: Either ``"-"`` (negation) or ``"+"`` (identity).
        operand: The expression the operator applies to.
        pos: 1-based position of the operator character.
    """

    op: Literal["-", "+"]
    operand: "Node"
    pos: SourcePos


@_dataclass(frozen=True)
class Binary:
    """A binary operation.

    Attributes:
        op: One of the operators in :data:`Op`.
        left: The left operand.
        right: The right operand.
        pos: 1-based position of the operator character.
    """

    op: Op
    left: "Node"
    right: "Node"
    pos: SourcePos


@_dataclass(frozen=True)
class Call:
    """A call to a built-in function.

    Attributes:
        func: The built-in's name (``abs``, ``min``, ``max``, or ``gcd``).
        args: Immutable tuple of argument expressions, in source order.
        pos: 1-based position of the function name.
    """

    func: str
    args: tuple["Node", ...]
    pos: SourcePos


@_dataclass(frozen=True)
class Assign:
    """An assignment statement (``name = expression``).

    Attributes:
        target: The identifier being bound.
        value: The expression supplying the new value.
        pos: 1-based position of the target identifier.
    """

    target: str
    value: "Node"
    pos: SourcePos


#: Union of every concrete AST node type.
Node = Union[Number, Name, Unary, Binary, Call, Assign]
