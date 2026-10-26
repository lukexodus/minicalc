"""Walking-skeleton parser: empty lines and bare number literals (CORE-003).

# STUB (CORE-003): replaced wholesale by FEAT-002

FEAT-002 replaces this module with the full precedence-aware grammar. Until
then, ``NUMBER EOF`` is the only accepted statement.
"""

from __future__ import annotations

from .ast_nodes import Node, Number
from .errors import ParseError
from .tokens import Token, TokenType


class Parser:
    """Parse the walking-skeleton subset of the MiniCalc grammar.

    Attributes:
        tokens: The token list to consume; the last token is ``EOF``.
    """

    def __init__(self, tokens: list[Token]) -> None:
        """Store the token list produced by the lexer.

        Args:
            tokens: Tokens in source order, ending with exactly one ``EOF``.
        """
        self.tokens = tokens

    def parse_statement(self) -> Node | None:
        """Parse one statement from the token list.

        Returns:
            ``None`` for an empty line (only ``EOF``), or a ``Number`` node
            for a single number literal.

        Raises:
            ParseError: For any input outside the walking-skeleton subset.
        """
        first = self.tokens[0]
        if first.type is TokenType.EOF:
            return None

        if (
            len(self.tokens) == 2
            and first.type is TokenType.NUMBER
            and self.tokens[1].type is TokenType.EOF
        ):
            return Number(first.value, first.pos)  # type: ignore[arg-type]

        offending = self.tokens[1] if len(self.tokens) > 1 else first
        found = offending.lexeme if offending.type is not TokenType.EOF else "end of line"
        raise ParseError(f"expected a number, found {found!r}", offending.pos)
