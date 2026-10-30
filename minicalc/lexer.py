"""Full lexer for MiniCalc (FEAT-001).

Turn one source line into a flat list of :class:`~minicalc.tokens.Token`
objects in a single left-to-right pass. Longest-match operator handling,
explicit ASCII-only character classes, and positioned :class:`LexError`
messages follow ``docs/context/language-spec.md`` section 2.

Whitespace is exactly space, tab, and carriage return. A ``#`` ends
tokenization; the rest of the line is a comment. Every line is capped at
``MAX_LINE_LENGTH`` characters before scanning begins.
"""

from __future__ import annotations

from .errors import LexError, SourcePos
from .limits import INT_MAX, MAX_LINE_LENGTH
from .tokens import Token, TokenType

#: Characters that may start an identifier: ASCII letters and underscore.
_IDENT_START = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
)

#: Characters that may continue an identifier: ASCII letters, digits, underscore.
_IDENT_CONTINUE = _IDENT_START | frozenset("0123456789")

#: Characters ignored between tokens.
_WHITESPACE = frozenset(" \t\r")

#: Two-character operators, checked before their one-character prefixes.
_TWO_CHAR_TOKENS = {
    "**": TokenType.POW,
    "//": TokenType.DSLASH,
    "==": TokenType.EQ,
    "!=": TokenType.NE,
    "<=": TokenType.LE,
    ">=": TokenType.GE,
}

#: One-character tokens with no longer form to consider.
_SINGLE_CHAR_TOKENS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "%": TokenType.PERCENT,
    "=": TokenType.ASSIGN,
    "<": TokenType.LT,
    ">": TokenType.GT,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    ",": TokenType.COMMA,
}


def _is_ascii_digit(char: str) -> bool:
    """Return whether ``char`` is an ASCII decimal digit ``0``-``9``.

    Args:
        char: A single character.

    Returns:
        True only for the ten ASCII digit characters.
    """
    return "0" <= char <= "9"


def _is_ident_start(char: str) -> bool:
    """Return whether ``char`` can start an identifier.

    Args:
        char: A single character.

    Returns:
        True for ASCII letters and underscore only.
    """
    return char in _IDENT_START


def _is_ident_continue(char: str) -> bool:
    """Return whether ``char`` can continue an identifier.

    Args:
        char: A single character.

    Returns:
        True for ASCII letters, digits, and underscore only.
    """
    return char in _IDENT_CONTINUE


class Lexer:
    """Turn one source line into tokens.

    Attributes:
        source: The single source line, without its newline. Held rather than
            passed around so ``tokenize`` scans it once, left to right, with no
            backtracking and no copy of the text.
        line_no: 1-based line number stamped on every ``SourcePos``. A script
            runs each line through a fresh lexer, so this is what makes an
            error report the line inside the file rather than always 1.
    """

    def __init__(self, source: str, line_no: int = 1) -> None:
        """Store the line to tokenize.

        Args:
            source: One source line with no trailing newline.
            line_no: 1-based line number for every token position.
        """
        self.source = source
        self.line_no = line_no

    def _pos(self, index: int) -> SourcePos:
        """Build the 1-based position for a 0-based scan index.

        Args:
            index: 0-based index into ``self.source``.

        Returns:
            The corresponding 1-based ``SourcePos``.
        """
        return SourcePos(self.line_no, index + 1)

    def tokenize(self) -> list[Token]:
        """Tokenize the stored line, always ending with one ``EOF`` token.

        Returns:
            Tokens in source order; the last is always ``EOF`` with an empty
            lexeme at column ``len(source) + 1``.

        Raises:
            LexError: For a line over ``MAX_LINE_LENGTH``, a decimal point, a
                letter directly after digits, an out-of-range literal, a lone
                ``!``, or any other illegal character.
        """
        source = self.source
        if len(source) > MAX_LINE_LENGTH:
            raise LexError(
                f"line is too long ({len(source)} characters); "
                f"the limit is {MAX_LINE_LENGTH}",
                SourcePos(self.line_no, MAX_LINE_LENGTH + 1),
            )

        tokens: list[Token] = []
        index = 0
        length = len(source)

        while index < length:
            char = source[index]

            if char in _WHITESPACE:
                index += 1
                continue

            if char == "#":
                break

            if _is_ascii_digit(char):
                index = self._scan_number(source, index, tokens)
                continue

            if _is_ident_start(char):
                start = index
                while index < length and _is_ident_continue(source[index]):
                    index += 1
                tokens.append(
                    Token(TokenType.IDENT, source[start:index], self._pos(start))
                )
                continue

            pair = source[index : index + 2]
            if pair in _TWO_CHAR_TOKENS:
                tokens.append(Token(_TWO_CHAR_TOKENS[pair], pair, self._pos(index)))
                index += 2
                continue

            if char in _SINGLE_CHAR_TOKENS:
                tokens.append(
                    Token(_SINGLE_CHAR_TOKENS[char], char, self._pos(index))
                )
                index += 1
                continue

            if char == ".":
                if self._follows_number(tokens, index):
                    raise LexError(
                        "decimals are not supported; "
                        "MiniCalc works with integers only",
                        self._pos(index),
                    )
                raise LexError("illegal character '.'", self._pos(index))

            if char == "!":
                raise LexError(
                    "illegal character '!'; use '!=' for not-equal",
                    self._pos(index),
                )

            raise LexError(f"illegal character {char!r}", self._pos(index))

        tokens.append(Token(TokenType.EOF, "", SourcePos(self.line_no, length + 1)))
        return tokens

    def _scan_number(self, source: str, index: int, tokens: list[Token]) -> int:
        """Scan a digit run, append its token, and return the next index.

        Args:
            source: The source line being scanned.
            index: 0-based index of the first digit.
            tokens: Token list to append the ``NUMBER`` token to.

        Returns:
            The index of the first character after the number.

        Raises:
            LexError: If a letter or underscore directly follows the digits
                (reported at the start of the number), or the literal exceeds
                ``INT_MAX`` (also at the start of the number).
        """
        start = index
        length = len(source)
        while index < length and _is_ascii_digit(source[index]):
            index += 1

        if index < length and _is_ident_start(source[index]):
            raise LexError(
                f"unexpected {source[index]!r} after a number; "
                "identifiers cannot start with a digit",
                self._pos(start),
            )

        lexeme = source[start:index]
        value = int(lexeme)
        if value > INT_MAX:
            raise LexError(
                f"integer literal {lexeme} is larger than the maximum "
                f"supported value {INT_MAX}",
                self._pos(start),
            )
        tokens.append(Token(TokenType.NUMBER, lexeme, self._pos(start), value))
        return index

    @staticmethod
    def _follows_number(tokens: list[Token], index: int) -> bool:
        """Return whether the character at ``index`` directly follows a number.

        Args:
            tokens: Tokens produced so far.
            index: 0-based index of the current character.

        Returns:
            True when the last token is a ``NUMBER`` ending immediately before
            ``index`` (so a ``.`` there is a decimal point, not a stray dot).
        """
        if not tokens or tokens[-1].type is not TokenType.NUMBER:
            return False
        token = tokens[-1]
        end = token.pos.col - 1 + len(token.lexeme)  # 0-based index after token
        return end == index
