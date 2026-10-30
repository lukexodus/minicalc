"""Token vocabulary shared by the lexer and parser.

The lexer emits a flat list of :class:`Token` objects that always ends with one
``TokenType.EOF`` token. The parser consumes that list without re-reading the
source text, so every token keeps its exact ``lexeme`` and its 1-based
:class:`~minicalc.errors.SourcePos`.
"""

from dataclasses import dataclass as _dataclass
from enum import Enum as _Enum

from .errors import SourcePos


class TokenType(_Enum):
    """Every token kind the MiniCalc lexer can produce.

    Attributes:
        NUMBER: Decimal integer literal; ``Token.value`` holds the integer.
        IDENT: Identifier (``[A-Za-z_][A-Za-z0-9_]*``), case-sensitive.
        PLUS: ``+`` operator.
        MINUS: ``-`` operator.
        STAR: ``*`` operator.
        SLASH: ``/`` operator (truncating division).
        DSLASH: ``//`` operator (floor division).
        PERCENT: ``%`` operator (floored modulo).
        POW: ``**`` operator (right-associative exponentiation).
        EQ: ``==`` comparison operator.
        NE: ``!=`` comparison operator.
        LT: ``<`` comparison operator.
        LE: ``<=`` comparison operator.
        GT: ``>`` comparison operator.
        GE: ``>=`` comparison operator.
        ASSIGN: Single ``=`` assignment operator.
        LPAREN: ``(``.
        RPAREN: ``)``.
        COMMA: ``,``.
        EOF: End of the source line; always the last token.
    """

    NUMBER = "NUMBER"
    IDENT = "IDENT"
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    DSLASH = "DSLASH"
    PERCENT = "PERCENT"
    POW = "POW"
    EQ = "EQ"
    NE = "NE"
    LT = "LT"
    LE = "LE"
    GT = "GT"
    GE = "GE"
    ASSIGN = "ASSIGN"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    EOF = "EOF"


@_dataclass(frozen=True)
class Token:
    """One lexical token and its position in the source line.

    Attributes:
        type: The token kind; the parser switches on this, never on text.
        lexeme: Exact source text of the token (``""`` for ``EOF``). It is kept
            verbatim so parser errors can echo the offending punctuation (for
            example ``expected ')', found '*'``) instead of re-slicing source.
        pos: 1-based line and column where the token starts. Error positions
            and the caret line under a bad token both come from this field, so
            a wrong ``pos`` shows up as a caret pointing at the wrong column.
        value: Parsed integer for ``NUMBER`` tokens; ``None`` for all others.
            The lexer parses once, so the evaluator never touches text.
    """

    type: TokenType
    lexeme: str
    pos: SourcePos
    value: int | None = None
