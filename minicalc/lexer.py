"""Walking-skeleton lexer: whitespace, comments, numbers, EOF (CORE-003).

# STUB (CORE-003): replaced wholesale by FEAT-001

FEAT-001 replaces this module with the full token set. Until then, only what
the walking skeleton needs is recognized; every other character is an illegal
character at its own column.
"""

from __future__ import annotations

from .errors import LexError, SourcePos
from .limits import INT_MAX, MAX_LINE_LENGTH
from .tokens import Token, TokenType

_ASCII_LETTER_OR_UNDERSCORE = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")


def _is_ascii_digit(char: str) -> bool:
    """Return whether ``char`` is an ASCII decimal digit."""
    return "0" <= char <= "9"


def _is_ascii_letter_or_underscore(char: str) -> bool:
    """Return whether ``char`` can start an identifier."""
    return char in _ASCII_LETTER_OR_UNDERSCORE


class Lexer:
    """Turn one source line into tokens.

    Attributes:
        source: The single source line, without its newline.
        line_no: 1-based line number stamped on every ``SourcePos``.
    """

    def __init__(self, source: str, line_no: int = 1) -> None:
        """Store the line to tokenize.

        Args:
            source: One source line with no trailing newline.
            line_no: 1-based line number for every token position.
        """
        self.source = source
        self.line_no = line_no

    def tokenize(self) -> list[Token]:
        """Tokenize the stored line, always ending with one ``EOF`` token.

        Returns:
            Tokens in source order.

        Raises:
            LexError: For a line over ``MAX_LINE_LENGTH``, an out-of-range
                literal, letters directly after digits, or an illegal
                character.
        """
        source = self.source
        if len(source) > MAX_LINE_LENGTH:
            raise LexError(
                "line too long",
                SourcePos(self.line_no, MAX_LINE_LENGTH + 1),
            )

        tokens: list[Token] = []
        index = 0
        length = len(source)

        while index < length:
            char = source[index]

            if char in " \t\r":
                index += 1
                continue

            if char == "#":
                break

            if _is_ascii_digit(char):
                start = index
                while index < length and _is_ascii_digit(source[index]):
                    index += 1
                if index < length and _is_ascii_letter_or_underscore(source[index]):
                    raise LexError(
                        "letters cannot follow a number",
                        SourcePos(self.line_no, start + 1),
                    )
                lexeme = source[start:index]
                value = int(lexeme)
                if value > INT_MAX:
                    raise LexError(
                        "integer literal out of range",
                        SourcePos(self.line_no, start + 1),
                    )
                tokens.append(
                    Token(TokenType.NUMBER, lexeme, SourcePos(self.line_no, start + 1), value)
                )
                continue

            raise LexError(
                f"illegal character {char!r}",
                SourcePos(self.line_no, index + 1),
            )

        tokens.append(Token(TokenType.EOF, "", SourcePos(self.line_no, length + 1)))
        return tokens
