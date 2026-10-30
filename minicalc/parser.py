"""Hand-written recursive-descent parser for MiniCalc (FEAT-002).

The parser consumes the flat token list produced by the lexer and builds the
frozen AST nodes from :mod:`minicalc.ast_nodes`. It never re-reads source text:
every node position comes from the token that produced it. The grammar itself
is documented in the :class:`Parser` class docstring.
"""

from __future__ import annotations

from .ast_nodes import Assign, Binary, Call, Name, Node, Number, Op, Unary
from .errors import ParseError
from .tokens import Token, TokenType

#: Maximum number of simultaneously active ``_expression`` calls. Deeper input
#: raises ``ParseError`` instead of exhausting the Python stack.
MAX_DEPTH: int = 200

#: Binary-text spelling of every comparison operator token.
_COMPARE_OPS: dict[TokenType, Op] = {
    TokenType.EQ: "==",
    TokenType.NE: "!=",
    TokenType.LT: "<",
    TokenType.LE: "<=",
    TokenType.GT: ">",
    TokenType.GE: ">=",
}

#: Binary-text spelling of every additive operator token.
_ADDITIVE_OPS: dict[TokenType, Op] = {
    TokenType.PLUS: "+",
    TokenType.MINUS: "-",
}

#: Binary-text spelling of every multiplicative operator token.
_TERM_OPS: dict[TokenType, Op] = {
    TokenType.STAR: "*",
    TokenType.SLASH: "/",
    TokenType.DSLASH: "//",
    TokenType.PERCENT: "%",
}


class Parser:
    """Turn one line's token list into a MiniCalc statement AST.

    Grammar (lowest precedence first; authoritative copy in
    ``docs/context/language-spec.md`` section 3)::

        line        = [ statement ] EOF ;
        statement   = assignment | expression ;
        assignment  = IDENT ASSIGN expression ;
        expression  = additive [ compare_op additive ] ;  (* non-associative *)
        compare_op  = EQ | NE | LT | LE | GT | GE ;
        additive    = term { ( PLUS | MINUS ) term } ;
        term        = unary { ( STAR | SLASH | DSLASH | PERCENT ) unary } ;
        unary       = ( MINUS | PLUS ) unary | power ;
        power       = primary [ POW unary ] ;             (* right-associative *)
        primary     = NUMBER | IDENT | call | LPAREN expression RPAREN ;
        call        = IDENT LPAREN [ expression { COMMA expression } ] RPAREN ;

    Left-associative levels (``additive`` and ``term``) are parsed with loops,
    so long chains such as ``1 + 1 + ...`` use constant stack space. Recursion
    is used only for genuinely nested constructs: parentheses, calls, prefix
    unary operators, and the right-associative ``**``.

    Attributes:
        tokens: The token list to consume; the last token is ``EOF``. Holding
            the list (rather than re-lexing) is what lets every node carry the
            exact position of the token that produced it.
        index: Zero-based index of the next token to consume. One cursor is
            enough because the grammar is LL(1): every decision needs at most
            the next token, so no token list is ever copied.
        _depth: Number of ``_expression`` calls currently on the stack, compared
            against ``MAX_DEPTH`` so pathological nesting becomes a
            ``ParseError`` instead of an escaping ``RecursionError``.
    """

    def __init__(self, tokens: list[Token]) -> None:
        """Store the token list produced by the lexer.

        Args:
            tokens: Tokens in source order, ending with exactly one ``EOF``.
        """
        self.tokens = tokens
        self.index = 0
        self._depth = 0

    # ------------------------------------------------------------------
    # Token cursor helpers
    # ------------------------------------------------------------------
    def _peek(self, offset: int = 0) -> Token:
        """Return a token without consuming it.

        Args:
            offset: How many tokens ahead of the cursor to inspect.

        Returns:
            The requested token, clamped to the final ``EOF`` token.
        """
        index = self.index + offset
        if index >= len(self.tokens):
            index = len(self.tokens) - 1
        return self.tokens[index]

    def _advance(self) -> Token:
        """Consume and return the token at the cursor."""
        token = self._peek()
        if token.type is not TokenType.EOF:
            self.index += 1
        return token

    @staticmethod
    def _describe(token: Token) -> str:
        """Return the user-facing description of a found token.

        Args:
            token: The token to describe.

        Returns:
            ``end of line`` for ``EOF``, otherwise the token's lexeme in
            quotes so punctuation is visible in the message.
        """
        if token.type is TokenType.EOF:
            return "end of line"
        return repr(token.lexeme)

    # ------------------------------------------------------------------
    # Statement and grammar rules
    # ------------------------------------------------------------------
    def parse_statement(self) -> Node | None:
        """Parse one statement from the token list.

        Returns:
            ``None`` when the line holds only ``EOF``, an ``Assign`` for an
            assignment, or the root expression node otherwise.

        Raises:
            ParseError: For malformed syntax, leftover tokens, chained
                comparisons, chained assignments, a non-name assignment
                target, or nesting beyond ``MAX_DEPTH``.
        """
        try:
            return self._statement()
        except RecursionError as exc:
            raise ParseError(
                "expression is nested too deeply", self._peek().pos
            ) from exc

    def _statement(self) -> Node | None:
        """Parse ``line = [ statement ] EOF``.

        Returns:
            ``None`` for an empty line, otherwise the statement node.

        Raises:
            ParseError: For malformed syntax or tokens left after the
                statement.
        """
        first = self._peek()
        if first.type is TokenType.EOF:
            return None

        if first.type is TokenType.IDENT and self._peek(1).type is TokenType.ASSIGN:
            target_token = self._advance()
            self._advance()  # ASSIGN
            value = self._expression()
            if self._peek().type is TokenType.ASSIGN:
                raise ParseError(
                    "chained assignment is not supported", self._peek().pos
                )
            node: Node = Assign(target_token.lexeme, value, target_token.pos)
        else:
            node = self._expression()
            if self._peek().type is TokenType.ASSIGN:
                raise ParseError(
                    "left side of '=' must be a name", self._peek().pos
                )

        leftover = self._peek()
        if leftover.type is not TokenType.EOF:
            raise ParseError(
                f"expected end of line, found {self._describe(leftover)}",
                leftover.pos,
            )
        return node

    def _expression(self) -> Node:
        """Parse ``expression = additive [ compare_op additive ]``.

        Comparison is non-associative: a second comparison operator in the
        same expression is rejected.

        Returns:
            The expression node.

        Raises:
            ParseError: For a chained comparison or nesting beyond
                ``MAX_DEPTH``.
        """
        self._depth += 1
        try:
            if self._depth > MAX_DEPTH:
                raise ParseError(
                    "expression is nested too deeply", self._peek().pos
                )

            left = self._additive()
            operator = self._peek()
            op_text = _COMPARE_OPS.get(operator.type)
            if op_text is None:
                return left

            self._advance()
            right = self._additive()
            node = Binary(op_text, left, right, operator.pos)

            chained = self._peek()
            if chained.type in _COMPARE_OPS:
                raise ParseError(
                    "comparison operators cannot be chained; add parentheses",
                    chained.pos,
                )
            return node
        finally:
            self._depth -= 1

    def _additive(self) -> Node:
        """Parse ``additive = term { ( PLUS | MINUS ) term }`` left-associatively."""
        # Precedence climbing: each level loops over its own operators and calls
        # the next-tighter level for operands. Looping (rather than recursing per
        # operator) keeps `1 + 1 + ...` chains at constant stack depth.
        node = self._term()
        while self._peek().type in _ADDITIVE_OPS:
            operator = self._advance()
            right = self._term()
            node = Binary(_ADDITIVE_OPS[operator.type], node, right, operator.pos)
        return node

    def _term(self) -> Node:
        """Parse ``term = unary { ( STAR | SLASH | DSLASH | PERCENT ) unary }``."""
        # Same shape as _additive, one precedence level tighter, which is what
        # makes `2 + 3 * 4` mean `2 + (3 * 4)`.
        node = self._unary()
        while self._peek().type in _TERM_OPS:
            operator = self._advance()
            right = self._unary()
            node = Binary(_TERM_OPS[operator.type], node, right, operator.pos)
        return node

    def _unary(self) -> Node:
        """Parse ``unary = ( MINUS | PLUS ) unary | power``."""
        token = self._peek()
        if token.type in (TokenType.MINUS, TokenType.PLUS):
            self._advance()
            operand = self._unary()
            return Unary("-" if token.type is TokenType.MINUS else "+", operand, token.pos)
        return self._power()

    def _power(self) -> Node:
        """Parse ``power = primary [ POW unary ]``, right-associatively."""
        base = self._primary()
        token = self._peek()
        if token.type is TokenType.POW:
            self._advance()
            # The right side is _unary(), not _power(): that is what makes `**`
            # right-associative (`2 ** 3 ** 2` == `2 ** (3 ** 2)`), and because
            # `**` is reached from _unary only after a primary, it binds tighter
            # than unary minus (`-2 ** 2` == `-(2 ** 2)`, spec section 3).
            exponent = self._unary()
            return Binary("**", base, exponent, token.pos)
        return base

    def _primary(self) -> Node:
        """Parse ``primary = NUMBER | IDENT | call | LPAREN expression RPAREN``.

        Raises:
            ParseError: When the current token cannot start an expression or a
                closing parenthesis is missing.
        """
        token = self._peek()

        if token.type is TokenType.NUMBER:
            self._advance()
            assert token.value is not None
            return Number(token.value, token.pos)

        if token.type is TokenType.IDENT:
            self._advance()
            if self._peek().type is TokenType.LPAREN:
                args = self._call_args()
                return Call(token.lexeme, args, token.pos)
            return Name(token.lexeme, token.pos)

        if token.type is TokenType.LPAREN:
            self._advance()
            node = self._expression()
            closing = self._peek()
            if closing.type is not TokenType.RPAREN:
                raise ParseError(
                    f"expected ')', found {self._describe(closing)}", closing.pos
                )
            self._advance()
            return node

        raise ParseError(
            f"expected an expression, found {self._describe(token)}", token.pos
        )

    def _call_args(self) -> tuple[Node, ...]:
        """Parse ``LPAREN [ expression { COMMA expression } ] RPAREN``.

        Returns:
            The argument tuple, in source order.

        Raises:
            ParseError: When an argument is missing or the closing parenthesis
                or comma is missing.
        """
        self._advance()  # LPAREN

        if self._peek().type is TokenType.RPAREN:
            self._advance()
            return ()

        args: list[Node] = [self._expression()]
        while self._peek().type is TokenType.COMMA:
            self._advance()
            args.append(self._expression())

        closing = self._peek()
        if closing.type is not TokenType.RPAREN:
            raise ParseError(
                f"expected ',' or ')', found {self._describe(closing)}",
                closing.pos,
            )
        self._advance()
        return tuple(args)
