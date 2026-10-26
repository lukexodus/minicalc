"""Unit tests for the full MiniCalc lexer (FEAT-001).

The tests import only the lexer, tokens, errors, and limits modules; they never
touch the parser or evaluator (FEAT-002 / FEAT-003 are being built in parallel
against the same contract).
"""

import random

import pytest

from minicalc.errors import LexError, SourcePos
from minicalc.lexer import Lexer
from minicalc.limits import INT_MAX, MAX_LINE_LENGTH
from minicalc.tokens import Token, TokenType

T = TokenType
EOF = (T.EOF, "")
IDENT_X = (T.IDENT, "x")
IDENT_A = (T.IDENT, "a")
IDENT_B = (T.IDENT, "b")
NUMBER_2 = (T.NUMBER, "2")
NUMBER_3 = (T.NUMBER, "3")
NUMBER_7 = (T.NUMBER, "7")


def token_pairs(source: str, line_no: int = 1) -> list[tuple[TokenType, str]]:
    """Tokenize ``source`` and return ``(type, lexeme)`` pairs.

    Args:
        source: One source line, without a trailing newline.
        line_no: 1-based line number to stamp on positions.

    Returns:
        The token list reduced to ``(TokenType, lexeme)`` tuples.
    """
    return [(token.type, token.lexeme) for token in Lexer(source, line_no).tokenize()]


TOKEN_CASES = [
    # Empty and comment-only lines produce only EOF.
    ("", [EOF]),
    (" \t\r ", [EOF]),
    ("# a comment", [EOF]),
    ("   # indented comment", [EOF]),
    # Longest-match operator neighbors.
    ("2**3", [NUMBER_2, (T.POW, "**"), NUMBER_3, EOF]),
    ("2*3", [NUMBER_2, (T.STAR, "*"), NUMBER_3, EOF]),
    ("7//2", [NUMBER_7, (T.DSLASH, "//"), NUMBER_2, EOF]),
    ("7/2", [NUMBER_7, (T.SLASH, "/"), NUMBER_2, EOF]),
    ("a==b", [IDENT_A, (T.EQ, "=="), IDENT_B, EOF]),
    ("a=b", [IDENT_A, (T.ASSIGN, "="), IDENT_B, EOF]),
    ("a!=b", [IDENT_A, (T.NE, "!="), IDENT_B, EOF]),
    ("a<=b", [IDENT_A, (T.LE, "<="), IDENT_B, EOF]),
    ("a<b", [IDENT_A, (T.LT, "<"), IDENT_B, EOF]),
    ("a>=b", [IDENT_A, (T.GE, ">="), IDENT_B, EOF]),
    ("a>b", [IDENT_A, (T.GT, ">"), IDENT_B, EOF]),
    # Every remaining single-character operator.
    (
        "+ - * / % = ( ) ,",
        [
            (T.PLUS, "+"),
            (T.MINUS, "-"),
            (T.STAR, "*"),
            (T.SLASH, "/"),
            (T.PERCENT, "%"),
            (T.ASSIGN, "="),
            (T.LPAREN, "("),
            (T.RPAREN, ")"),
            (T.COMMA, ","),
            EOF,
        ],
    ),
    # Symbols laid out together, exercising longest match at each position.
    (
        "+ - * / // % ** == != < <= > >= = ( ) ,",
        [
            (T.PLUS, "+"),
            (T.MINUS, "-"),
            (T.STAR, "*"),
            (T.SLASH, "/"),
            (T.DSLASH, "//"),
            (T.PERCENT, "%"),
            (T.POW, "**"),
            (T.EQ, "=="),
            (T.NE, "!="),
            (T.LT, "<"),
            (T.LE, "<="),
            (T.GT, ">"),
            (T.GE, ">="),
            (T.ASSIGN, "="),
            (T.LPAREN, "("),
            (T.RPAREN, ")"),
            (T.COMMA, ","),
            EOF,
        ],
    ),
    # Identifiers accept ASCII letters, digits, and underscore after the first.
    ("_x", [(T.IDENT, "_x"), EOF]),
    ("x1", [(T.IDENT, "x1"), EOF]),
    ("abs", [(T.IDENT, "abs"), EOF]),
    ("A_b9", [(T.IDENT, "A_b9"), EOF]),
    # Calls and comma-separated arguments.
    (
        "min(1, 2)",
        [
            (T.IDENT, "min"),
            (T.LPAREN, "("),
            (T.NUMBER, "1"),
            (T.COMMA, ","),
            (T.NUMBER, "2"),
            (T.RPAREN, ")"),
            EOF,
        ],
    ),
    # Whitespace: space, tab, and carriage return all separate tokens.
    ("1 \t+\r 2", [(T.NUMBER, "1"), (T.PLUS, "+"), (T.NUMBER, "2"), EOF]),
    # Comments end tokenization wherever they appear.
    ("1 + 2 # trailing", [(T.NUMBER, "1"), (T.PLUS, "+"), (T.NUMBER, "2"), EOF]),
    ("1 # 2 + 3", [(T.NUMBER, "1"), EOF]),
    # Leading zeros are allowed; the lexeme preserves the source text.
    ("007", [(T.NUMBER, "007"), EOF]),
    # A multi-token assignment statement.
    (
        "x = 1 + 2",
        [
            IDENT_X,
            (T.ASSIGN, "="),
            (T.NUMBER, "1"),
            (T.PLUS, "+"),
            NUMBER_2,
            EOF,
        ],
    ),
]


@pytest.mark.parametrize("source,expected", TOKEN_CASES)
def test_tokenization(
    source: str, expected: list[tuple[TokenType, str]]
) -> None:
    """Each source line produces exactly the expected ``(type, lexeme)`` list."""
    assert token_pairs(source) == expected


def test_number_token_value_is_an_int() -> None:
    """``NUMBER`` tokens carry the parsed integer value, including leading zeros."""
    tokens = Lexer("007 2147483647 0").tokenize()
    assert [(token.lexeme, token.value) for token in tokens[:-1]] == [
        ("007", 7),
        ("2147483647", INT_MAX),
        ("0", 0),
    ]


def test_non_number_tokens_have_no_value() -> None:
    """Only ``NUMBER`` tokens set ``value``."""
    tokens = Lexer("x = 1 + 2").tokenize()
    assert all(
        token.value is None for token in tokens if token.type is not T.NUMBER
    )


def test_columns_for_multi_token_line() -> None:
    """Token positions are 1-based columns of each token's first character."""
    tokens = Lexer("x = 1 + 2").tokenize()
    assert [token.pos for token in tokens] == [
        SourcePos(1, 1),
        SourcePos(1, 3),
        SourcePos(1, 5),
        SourcePos(1, 7),
        SourcePos(1, 9),
        SourcePos(1, 10),
    ]


def test_eof_column_without_comment() -> None:
    """EOF sits one column past the end of the line."""
    tokens = Lexer("1 + 2").tokenize()
    assert tokens[-1] == Token(TokenType.EOF, "", SourcePos(1, 6))


def test_eof_column_with_trailing_comment() -> None:
    """A comment does not move EOF; it stays at ``len(source) + 1``."""
    source = "1 + 2 # note"
    tokens = Lexer(source).tokenize()
    assert tokens[-1].type is TokenType.EOF
    assert tokens[-1].pos == SourcePos(1, len(source) + 1)


def test_eof_column_on_empty_and_comment_only_lines() -> None:
    """Empty and comment-only lines still end with EOF at ``len + 1``."""
    assert Lexer("").tokenize()[-1].pos == SourcePos(1, 1)
    assert Lexer("# note").tokenize()[-1].pos == SourcePos(1, 7)


def test_tab_counts_as_one_column() -> None:
    """A tab advances the column by exactly one."""
    tokens = Lexer("\tx").tokenize()
    assert tokens[0].pos == SourcePos(1, 2)
    assert tokens[-1].pos == SourcePos(1, 3)


def test_carriage_return_is_whitespace() -> None:
    """A Windows-style trailing carriage return is harmless."""
    tokens = Lexer("1\r").tokenize()
    assert [(token.type, token.lexeme) for token in tokens] == [
        (T.NUMBER, "1"),
        EOF,
    ]
    assert Lexer("1\r+2").tokenize()[-1].pos == SourcePos(1, 5)


def test_line_number_is_stamped_on_every_position() -> None:
    """The ``line_no`` argument appears in every ``SourcePos``, including EOF."""
    tokens = Lexer("x = 1", line_no=7).tokenize()
    assert [token.pos.line for token in tokens] == [7, 7, 7, 7]
    assert tokens[-1].pos == SourcePos(7, 6)


ERROR_CASES = [
    # Decimals: the error points at the dot.
    ("3.14", 2, "decimals"),
    ("3.", 2, "decimals"),
    ("0.5", 2, "decimals"),
    # A dot that is not part of a decimal is an illegal character.
    (".5", 1, "illegal character"),
    ("x.", 2, "illegal character"),
    # Letters or underscore directly after digits: reported at number start.
    ("12abc", 1, "after a number"),
    ("9_", 1, "after a number"),
    ("7x", 1, "after a number"),
    # Out-of-range literals: reported at number start.
    ("99999999999", 1, "larger than"),
    ("2147483648", 1, "larger than"),
    ("0000002147483648", 1, "larger than"),
    # Illegal characters: reported at the offending column.
    ("2 @ 3", 3, "illegal character"),
    ("$x", 1, "illegal character"),
    (":", 1, "illegal character"),
    ("3 ! 4", 3, "illegal character"),
    ("!", 1, "illegal character"),
    ("3!", 2, "illegal character"),
    ("'\"[]{}~&|^`\\", 1, "illegal character"),
    # Non-ASCII input is always an illegal character at its own column.
    ("\u0663", 1, "illegal character"),  # Arabic-Indic digit three
    ("1\u00a02", 2, "illegal character"),  # non-breaking space
    ("1\u20282", 2, "illegal character"),  # line separator, not a newline
    ("1\x0c2", 2, "illegal character"),  # form feed is not whitespace
    ("12é", 3, "illegal character"),  # non-ASCII letter after digits
    # The line-length cap is checked before scanning, at column 1001.
    (" " * (MAX_LINE_LENGTH + 1), MAX_LINE_LENGTH + 1, "too long"),
]


@pytest.mark.parametrize("source,column,message_fragment", ERROR_CASES)
def test_lexical_errors(
    source: str, column: int, message_fragment: str
) -> None:
    """Every spec error row raises ``LexError`` at the required column."""
    with pytest.raises(LexError) as excinfo:
        Lexer(source).tokenize()
    assert excinfo.value.pos == SourcePos(1, column)
    assert message_fragment in excinfo.value.message.lower()


def test_error_position_uses_given_line_number() -> None:
    """Lexical errors are stamped with the ``line_no`` passed to the lexer."""
    with pytest.raises(LexError) as excinfo:
        Lexer("3.14", line_no=5).tokenize()
    assert excinfo.value.pos == SourcePos(5, 2)


def test_int_max_is_accepted() -> None:
    """``INT_MAX`` is a legal literal."""
    tokens = Lexer(str(INT_MAX)).tokenize()
    assert tokens[0].value == INT_MAX
    assert tokens[0].lexeme == str(INT_MAX)


def test_line_at_max_length_is_accepted() -> None:
    """A line of exactly ``MAX_LINE_LENGTH`` characters is still scanned."""
    tokens = Lexer(" " * MAX_LINE_LENGTH).tokenize()
    assert [(token.type, token.lexeme) for token in tokens] == [EOF]


def test_random_printable_ascii_only_raises_lex_error() -> None:
    """Fuzz: 500 seeded printable-ASCII lines end in EOF or raise ``LexError``."""
    rng = random.Random(0)
    alphabet = "".join(chr(code) for code in range(32, 127))
    for _ in range(500):
        source = "".join(
            rng.choice(alphabet) for _ in range(rng.randrange(MAX_LINE_LENGTH + 1))
        )
        try:
            tokens = Lexer(source).tokenize()
        except LexError:
            continue
        assert tokens, "tokenize() must never return an empty list"
        assert tokens[-1].type is TokenType.EOF
        assert tokens[-1].lexeme == ""
        assert tokens[-1].pos == SourcePos(1, len(source) + 1)
