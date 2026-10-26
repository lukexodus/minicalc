"""The stable MiniCalc facade: one line or a whole source through the pipeline.

This module is final from CORE-003 onward. FEAT-001, FEAT-002, and FEAT-003
replace the lexer, parser, and evaluator behind it without changing ``Result``,
``LineOutcome``, or ``Interpreter``.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Literal

from .ast_nodes import Assign
from .environment import Environment
from .errors import EvalError, MiniCalcError, ParseError, SourcePos
from .evaluator import Evaluator
from .lexer import Lexer
from .parser import Parser

_MIN_RECURSION_LIMIT = 4000


@dataclass(frozen=True)
class Result:
    """The outcome of one successfully processed line.

    Attributes:
        kind: ``"value"`` for an expression, ``"assign"`` for an assignment,
            or ``"empty"`` for a blank/comment-only line.
        value: The produced integer for value and assign results.
        name: The bound identifier when ``kind == "assign"``.
    """

    kind: Literal["value", "assign", "empty"]
    value: int | None = None
    name: str | None = None


@dataclass(frozen=True)
class LineOutcome:
    """One line's result or error, in source order.

    Attributes:
        line_no: 1-based line number in the original text.
        source: The original line, without its newline.
        result: The successful result, or ``None`` when ``error`` is set.
        error: The error, or ``None`` when ``result`` is set.
    """

    line_no: int
    source: str
    result: Result | None
    error: MiniCalcError | None


class Interpreter:
    """Coordinate the lexer, parser, evaluator, and environment.

    Attributes:
        env: The persistent environment shared by every processed line.
    """

    def __init__(self, env: Environment | None = None) -> None:
        """Create the facade, raising the recursion limit if needed.

        Args:
            env: Optional environment to reuse; a fresh one otherwise.
        """
        self.env = env if env is not None else Environment()
        if sys.getrecursionlimit() < _MIN_RECURSION_LIMIT:
            sys.setrecursionlimit(_MIN_RECURSION_LIMIT)

    def run_line(self, source: str, line_no: int = 1) -> Result:
        """Run one source line and return its result.

        Args:
            source: One line with no trailing newline.
            line_no: 1-based line number used for positions.

        Returns:
            The line's ``Result``.

        Raises:
            MiniCalcError: Any lexical, syntax, or runtime error, with the
                offending ``source`` attached for caret rendering.
        """
        try:
            tokens = Lexer(source, line_no).tokenize()
            try:
                node = Parser(tokens).parse_statement()
            except RecursionError as exc:
                raise ParseError(
                    "expression is too deeply nested",
                    SourcePos(line_no, 1),
                ) from exc

            if node is None:
                return Result("empty")

            try:
                value = Evaluator(self.env).evaluate(node)
            except RecursionError as exc:
                raise EvalError(
                    "expression is too deeply nested",
                    SourcePos(line_no, 1),
                ) from exc

            if isinstance(node, Assign):
                return Result("assign", value, node.target)
            self.env.record_result(value)
            return Result("value", value)
        except MiniCalcError as error:
            raise error.with_source(source) from None

    def run_source(self, text: str) -> list[LineOutcome]:
        """Run every line of ``text``, continuing after errors.

        Args:
            text: A whole source file or script.

        Returns:
            One ``LineOutcome`` per line, numbered from 1. Never raises
            ``MiniCalcError``.
        """
        lines = text.split("\n")
        if lines and lines[-1] == "":
            lines.pop()  # a trailing newline starts no new line

        outcomes: list[LineOutcome] = []
        for line_no, raw in enumerate(lines, start=1):
            line = raw[:-1] if raw.endswith("\r") else raw
            try:
                result = self.run_line(line, line_no)
                error = None
            except MiniCalcError as exc:
                result = None
                error = exc.with_source(line)
            outcomes.append(LineOutcome(line_no, line, result, error))
        return outcomes
