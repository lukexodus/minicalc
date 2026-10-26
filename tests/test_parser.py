"""Parser tests for the full MiniCalc grammar (FEAT-002).

Tokens are built directly from :class:`~minicalc.tokens.Token` and
:class:`~minicalc.tokens.TokenType`; the lexer is intentionally not imported so
parser behavior is tested in isolation from FEAT-001.
"""

from __future__ import annotations

import random
import re
import sys

import pytest

from minicalc.ast_nodes import Assign, Binary, Call, Name, Node, Number, Unary
from minicalc.errors import ParseError, SourcePos
from minicalc.parser import MAX_DEPTH, Parser
from minicalc.tokens import Token, TokenType

#: Lexeme-to-type lookup for hand-written token lists.
_TOKEN_TYPES: dict[str, TokenType] = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "//": TokenType.DSLASH,
    "%": TokenType.PERCENT,
    "**": TokenType.POW,
    "==": TokenType.EQ,
    "!=": TokenType.NE,
    "<": TokenType.LT,
    "<=": TokenType.LE,
    ">": TokenType.GT,
    ">=": TokenType.GE,
    "=": TokenType.ASSIGN,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    ",": TokenType.COMMA,
}

_NUMBER_RE = re.compile(r"[0-9]+")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
#: Longest operators first, so ``**`` wins over ``*`` and ``<=`` over ``<``.
_TEST_TOKEN_RE = re.compile(
    r"[0-9]+"
    r"|[A-Za-z_][A-Za-z0-9_]*"
    r"|//|\*\*|==|!=|<=|>="
    r"|[+\-*/%<>=(),]"
)


def toks(source: str) -> list[Token]:
    """Build a token list directly from test source text.

    This tiny self-contained scanner (independent of ``minicalc.lexer``)
    recognizes the vocabulary the parser needs and records each token's real
    1-based column, so adjacent tokens such as ``()`` are handled exactly.

    Args:
        source: Test source text; whitespace separates tokens and is ignored.

    Returns:
        The tokens in source order, ending with one ``EOF`` token.

    Raises:
        ValueError: If a non-whitespace character is not part of the test
            vocabulary.
    """
    tokens: list[Token] = []
    cursor = 0
    for match in _TEST_TOKEN_RE.finditer(source):
        if source[cursor:match.start()].strip():
            raise ValueError(f"unknown test token {source[cursor:match.start()]!r}")
        lexeme = match.group()
        pos = SourcePos(1, match.start() + 1)
        if _NUMBER_RE.fullmatch(lexeme):
            tokens.append(Token(TokenType.NUMBER, lexeme, pos, int(lexeme)))
        elif _IDENT_RE.fullmatch(lexeme):
            tokens.append(Token(TokenType.IDENT, lexeme, pos))
        elif lexeme in _TOKEN_TYPES:
            tokens.append(Token(_TOKEN_TYPES[lexeme], lexeme, pos))
        else:
            raise ValueError(f"unknown test token {lexeme!r}")
        cursor = match.end()
    if source[cursor:].strip():
        raise ValueError(f"unknown test token {source[cursor:]!r}")
    tokens.append(Token(TokenType.EOF, "", SourcePos(1, len(source) + 1)))
    return tokens


def parse(source: str) -> Node | None:
    """Parse a test source string with a fresh parser."""
    return Parser(toks(source)).parse_statement()


def parse_error(source: str) -> ParseError:
    """Parse ``source`` and return the ``ParseError`` it raises."""
    with pytest.raises(ParseError) as info:
        parse(source)
    return info.value


# ---------------------------------------------------------------------------
# Statement selection
# ---------------------------------------------------------------------------
def test_empty_line_returns_none() -> None:
    """Only ``EOF`` means an empty line."""
    assert parse("") is None


def test_expression_statement() -> None:
    """A bare expression returns its root node."""
    assert parse("x") == Name("x", SourcePos(1, 1))


def test_assignment_statement() -> None:
    """``IDENT ASSIGN expression`` becomes an ``Assign`` at the name."""
    assert parse("x = 5") == Assign("x", Number(5, SourcePos(1, 5)), SourcePos(1, 1))


def test_equality_is_not_assignment() -> None:
    """``x == 5`` is a comparison, not an assignment."""
    assert parse("x == 5") == Binary(
        "==",
        Name("x", SourcePos(1, 1)),
        Number(5, SourcePos(1, 6)),
        SourcePos(1, 3),
    )


def test_call_of_a_variable_parses() -> None:
    """``x(1)`` parses as a call; rejecting non-functions is the evaluator's job."""
    assert parse("x(1)") == Call("x", (Number(1, SourcePos(1, 3)),), SourcePos(1, 1))


# ---------------------------------------------------------------------------
# Precedence and associativity
# ---------------------------------------------------------------------------
def test_multiplication_binds_tighter_than_addition() -> None:
    """``2 + 3 * 4`` groups the multiplication first."""
    assert parse("2 + 3 * 4") == Binary(
        "+",
        Number(2, SourcePos(1, 1)),
        Binary(
            "*",
            Number(3, SourcePos(1, 5)),
            Number(4, SourcePos(1, 9)),
            SourcePos(1, 7),
        ),
        SourcePos(1, 3),
    )


def test_parentheses_override_precedence() -> None:
    """``(2 + 3) * 4`` makes the addition the left operand."""
    assert parse("(2 + 3) * 4") == Binary(
        "*",
        Binary(
            "+",
            Number(2, SourcePos(1, 2)),
            Number(3, SourcePos(1, 6)),
            SourcePos(1, 4),
        ),
        Number(4, SourcePos(1, 11)),
        SourcePos(1, 9),
    )


def test_additive_is_left_associative() -> None:
    """``10 - 3 - 2`` is ``(10 - 3) - 2``."""
    assert parse("10 - 3 - 2") == Binary(
        "-",
        Binary(
            "-",
            Number(10, SourcePos(1, 1)),
            Number(3, SourcePos(1, 6)),
            SourcePos(1, 4),
        ),
        Number(2, SourcePos(1, 10)),
        SourcePos(1, 8),
    )


def test_term_level_is_left_associative() -> None:
    """Every multiplicative operator shares one left-associative level."""
    assert parse("8 / 4 // 2 % 3 * 2") == Binary(
        "*",
        Binary(
            "%",
            Binary(
                "//",
                Binary(
                    "/",
                    Number(8, SourcePos(1, 1)),
                    Number(4, SourcePos(1, 5)),
                    SourcePos(1, 3),
                ),
                Number(2, SourcePos(1, 10)),
                SourcePos(1, 7),
            ),
            Number(3, SourcePos(1, 14)),
            SourcePos(1, 12),
        ),
        Number(2, SourcePos(1, 18)),
        SourcePos(1, 16),
    )


def test_additive_and_term_levels_combine() -> None:
    """``*`` binds tighter than ``+`` on both sides."""
    assert parse("2 * 3 + 4 * 5") == Binary(
        "+",
        Binary(
            "*",
            Number(2, SourcePos(1, 1)),
            Number(3, SourcePos(1, 5)),
            SourcePos(1, 3),
        ),
        Binary(
            "*",
            Number(4, SourcePos(1, 9)),
            Number(5, SourcePos(1, 13)),
            SourcePos(1, 11),
        ),
        SourcePos(1, 7),
    )


def test_power_is_right_associative() -> None:
    """``2 ** 3 ** 2`` is ``2 ** (3 ** 2)``."""
    assert parse("2 ** 3 ** 2") == Binary(
        "**",
        Number(2, SourcePos(1, 1)),
        Binary(
            "**",
            Number(3, SourcePos(1, 6)),
            Number(2, SourcePos(1, 11)),
            SourcePos(1, 8),
        ),
        SourcePos(1, 3),
    )


def test_power_binds_tighter_than_unary_minus() -> None:
    """``-2 ** 2`` is ``-(2 ** 2)``, per the spec."""
    assert parse("-2 ** 2") == Unary(
        "-",
        Binary(
            "**",
            Number(2, SourcePos(1, 2)),
            Number(2, SourcePos(1, 7)),
            SourcePos(1, 4),
        ),
        SourcePos(1, 1),
    )


def test_exponent_may_be_a_unary_expression() -> None:
    """``2 ** -1`` parses; the negative exponent fails only at evaluation."""
    assert parse("2 ** -1") == Binary(
        "**",
        Number(2, SourcePos(1, 1)),
        Unary("-", Number(1, SourcePos(1, 7)), SourcePos(1, 6)),
        SourcePos(1, 3),
    )


def test_prefix_operators_are_right_associative() -> None:
    """``--2`` and ``-+2`` stack as nested unary nodes."""
    assert parse("--2") == Unary(
        "-", Unary("-", Number(2, SourcePos(1, 3)), SourcePos(1, 2)), SourcePos(1, 1)
    )
    assert parse("-+2") == Unary(
        "-", Unary("+", Number(2, SourcePos(1, 3)), SourcePos(1, 2)), SourcePos(1, 1)
    )


def test_comparison_binds_loosest() -> None:
    """``2 + 3 == 5`` compares the arithmetic results."""
    assert parse("2 + 3 == 5") == Binary(
        "==",
        Binary(
            "+",
            Number(2, SourcePos(1, 1)),
            Number(3, SourcePos(1, 5)),
            SourcePos(1, 3),
        ),
        Number(5, SourcePos(1, 10)),
        SourcePos(1, 7),
    )


def test_parenthesized_comparison_inside_comparison() -> None:
    """``(1 < 2) < 3`` is legal because the inner comparison is parenthesized."""
    assert parse("(1 < 2) < 3") == Binary(
        "<",
        Binary(
            "<",
            Number(1, SourcePos(1, 2)),
            Number(2, SourcePos(1, 6)),
            SourcePos(1, 4),
        ),
        Number(3, SourcePos(1, 11)),
        SourcePos(1, 9),
    )


# ---------------------------------------------------------------------------
# Node positions
# ---------------------------------------------------------------------------
def test_positions_for_names_numbers_binary_unary_and_assign() -> None:
    """Every node position follows the contract's rule."""
    assert parse("  x = -1 + 2 * y") == Assign(
        "x",
        Binary(
            "+",
            Unary("-", Number(1, SourcePos(1, 8)), SourcePos(1, 7)),
            Binary(
                "*",
                Number(2, SourcePos(1, 12)),
                Name("y", SourcePos(1, 16)),
                SourcePos(1, 14),
            ),
            SourcePos(1, 10),
        ),
        SourcePos(1, 3),
    )


def test_positions_for_calls_and_arguments() -> None:
    """A call's position is its name; arguments keep their own positions."""
    assert parse("  max(abs(1), 2, gcd(4, 6))") == Call(
        "max",
        (
            Call("abs", (Number(1, SourcePos(1, 11)),), SourcePos(1, 7)),
            Number(2, SourcePos(1, 15)),
            Call(
                "gcd",
                (
                    Number(4, SourcePos(1, 22)),
                    Number(6, SourcePos(1, 25)),
                ),
                SourcePos(1, 18),
            ),
        ),
        SourcePos(1, 3),
    )


# ---------------------------------------------------------------------------
# Calls
# ---------------------------------------------------------------------------
def test_call_with_zero_arguments() -> None:
    """``abs()`` parses with an empty tuple; arity is checked later."""
    assert parse("abs()") == Call("abs", (), SourcePos(1, 1))


def test_call_with_one_argument() -> None:
    """A unary expression may be an argument."""
    assert parse("abs(-3)") == Call(
        "abs",
        (Unary("-", Number(3, SourcePos(1, 6)), SourcePos(1, 5)),),
        SourcePos(1, 1),
    )


def test_call_with_many_arguments() -> None:
    """Commas separate an arbitrary number of arguments."""
    assert parse("max(1, 2, 3, 4)") == Call(
        "max",
        (
            Number(1, SourcePos(1, 5)),
            Number(2, SourcePos(1, 8)),
            Number(3, SourcePos(1, 11)),
            Number(4, SourcePos(1, 14)),
        ),
        SourcePos(1, 1),
    )


def test_nested_calls_in_arguments() -> None:
    """Calls nest inside arguments and keep their own node positions."""
    assert parse("max(min(1, 2), abs(-3))") == Call(
        "max",
        (
            Call(
                "min",
                (
                    Number(1, SourcePos(1, 9)),
                    Number(2, SourcePos(1, 12)),
                ),
                SourcePos(1, 5),
            ),
            Call(
                "abs",
                (Unary("-", Number(3, SourcePos(1, 21)), SourcePos(1, 20)),),
                SourcePos(1, 16),
            ),
        ),
        SourcePos(1, 1),
    )


# ---------------------------------------------------------------------------
# Error table (spec section 3 plus the prompt's extension rows)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "source, column, fragment",
    [
        ("2 +", 4, "expected an expression, found end of line"),
        ("2 + * 3", 5, "expected an expression, found '*'"),
        ("(2 + 3", 7, "expected ')', found end of line"),
        ("2 3", 3, "expected end of line, found '3'"),
        ("1 < 2 < 3", 7, "comparison operators cannot be chained"),
        ("max(1,", 7, "expected an expression, found end of line"),
        ("max(1,)", 7, "expected an expression, found ')'"),
        (")", 1, "expected an expression, found ')'"),
        ("= 5", 1, "expected an expression, found '='"),
        ("x =", 4, "expected an expression, found end of line"),
        ("f(1 2)", 5, "expected ',' or ')', found '2'"),
        ("()", 2, "expected an expression, found ')'"),
        ("2 **", 5, "expected an expression, found end of line"),
    ],
)
def test_error_table_row(source: str, column: int, fragment: str) -> None:
    """Each documented syntax error is reported at its exact column."""
    error = parse_error(source)
    assert error.pos == SourcePos(1, column)
    assert fragment in error.message


def test_left_side_of_assignment_must_be_a_name() -> None:
    """A complete expression followed by ``=`` is not an assignment."""
    for source, column in (("5 = 3", 3), ("a + 1 = 2", 7)):
        error = parse_error(source)
        assert error.message == "left side of '=' must be a name"
        assert error.pos == SourcePos(1, column)


def test_chained_assignment_is_rejected() -> None:
    """``x = y = 3`` names the second ``=`` as the offending token."""
    error = parse_error("x = y = 3")
    assert error.message == "chained assignment is not supported"
    assert error.pos == SourcePos(1, 7)


def test_comparison_chain_tells_the_user_to_add_parentheses() -> None:
    """The chained-comparison message carries the required guidance."""
    error = parse_error("1 < 2 < 3")
    assert "add parentheses" in error.message


def test_leftover_token_after_assignment() -> None:
    """An assignment must also consume the whole line."""
    error = parse_error("x = 1 2")
    assert error.message == "expected end of line, found '2'"
    assert error.pos == SourcePos(1, 7)


# ---------------------------------------------------------------------------
# Nesting depth and long flat chains
# ---------------------------------------------------------------------------
def _nested_parens(depth: int) -> str:
    """Return ``depth`` nested parentheses around ``1``, space-separated."""
    return " ".join(["("] * depth + ["1"] + [")"] * depth)


def test_hundred_nested_parentheses_succeed() -> None:
    """100 levels are well inside ``MAX_DEPTH`` and parse normally."""
    node = parse(_nested_parens(100))
    assert isinstance(node, Number)
    assert node.value == 1


def test_three_hundred_nested_parentheses_fail_cleanly() -> None:
    """Pathological nesting raises ``ParseError``, never ``RecursionError``."""
    error = parse_error(_nested_parens(300))
    assert error.message == "expression is nested too deeply"


def test_depth_limit_counts_expression_entries() -> None:
    """``MAX_DEPTH`` itself (not just Python's stack) is enforced at 200."""
    assert MAX_DEPTH == 200
    previous_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(20000)
    try:
        error = parse_error(_nested_parens(MAX_DEPTH + 1))
    finally:
        sys.setrecursionlimit(previous_limit)
    assert error.message == "expression is nested too deeply"


def test_five_thousand_term_sum_does_not_recurse() -> None:
    """Left-associative chains are parsed with a loop, not recursion."""
    node = parse("1 + " * 4999 + "1")
    assert isinstance(node, Binary)
    assert node.op == "+"


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------
_RANDOM_TOKEN_TYPES: tuple[TokenType, ...] = (
    TokenType.NUMBER,
    TokenType.IDENT,
    TokenType.PLUS,
    TokenType.MINUS,
    TokenType.STAR,
    TokenType.SLASH,
    TokenType.DSLASH,
    TokenType.PERCENT,
    TokenType.POW,
    TokenType.EQ,
    TokenType.NE,
    TokenType.LT,
    TokenType.LE,
    TokenType.GT,
    TokenType.GE,
    TokenType.ASSIGN,
    TokenType.LPAREN,
    TokenType.RPAREN,
    TokenType.COMMA,
)

_RANDOM_LEXEMES: dict[TokenType, str] = {
    TokenType.PLUS: "+",
    TokenType.MINUS: "-",
    TokenType.STAR: "*",
    TokenType.SLASH: "/",
    TokenType.DSLASH: "//",
    TokenType.PERCENT: "%",
    TokenType.POW: "**",
    TokenType.EQ: "==",
    TokenType.NE: "!=",
    TokenType.LT: "<",
    TokenType.LE: "<=",
    TokenType.GT: ">",
    TokenType.GE: ">=",
    TokenType.ASSIGN: "=",
    TokenType.LPAREN: "(",
    TokenType.RPAREN: ")",
    TokenType.COMMA: ",",
}


def _random_tokens(rng: random.Random) -> list[Token]:
    """Build one random, syntactically arbitrary token list ending in ``EOF``."""
    tokens: list[Token] = []
    for index in range(rng.randint(0, 12)):
        token_type = rng.choice(_RANDOM_TOKEN_TYPES)
        pos = SourcePos(1, index + 1)
        if token_type is TokenType.NUMBER:
            value = rng.randint(0, 999)
            tokens.append(Token(token_type, str(value), pos, value))
        elif token_type is TokenType.IDENT:
            tokens.append(Token(token_type, rng.choice(("x", "y", "max", "ans")), pos))
        else:
            tokens.append(Token(token_type, _RANDOM_LEXEMES[token_type], pos))
    tokens.append(Token(TokenType.EOF, "", SourcePos(1, len(tokens) + 1)))
    return tokens


def test_random_token_sequences_only_raise_parse_error() -> None:
    """500 seeded random token lists return a node/``None`` or ``ParseError``."""
    rng = random.Random(20261026)
    node_types = (Number, Name, Unary, Binary, Call, Assign)
    for _ in range(500):
        tokens = _random_tokens(rng)
        try:
            node = Parser(tokens).parse_statement()
        except ParseError:
            continue
        except Exception as exc:  # noqa: BLE001 - this is the property under test
            pytest.fail(f"unexpected {type(exc).__name__} for {tokens!r}: {exc}")
        assert node is None or isinstance(node, node_types)
