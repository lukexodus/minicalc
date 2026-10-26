"""The MiniCalc error hierarchy ([D-07]).

Every error carries an optional :class:`SourcePos`, and may carry the offending
source line so :meth:`MiniCalcError.render` can draw a caret under the column.
Golden tests compare :meth:`MiniCalcError.canonical` output only, never message
text, so message wording stays free to improve.
"""

from dataclasses import dataclass as _dataclass
from typing import ClassVar as _ClassVar

#: Prefix used by ``render(color=True)`` for the ``Error:`` label.
_BOLD_RED = "\x1b[1;31m"
#: Prefix used by ``render(color=True)`` for the caret.
_RED = "\x1b[31m"
#: ANSI reset sequence.
_RESET = "\x1b[0m"


@_dataclass(frozen=True)
class SourcePos:
    """A 1-based position in the original source text.

    Attributes:
        line: 1-based line number.
        col: 1-based column number; tabs count as one column.
    """

    line: int
    col: int


class MiniCalcError(Exception):
    """Base class for every error MiniCalc reports to the user.

    Attributes:
        kind (ClassVar[str]): Human-readable category shown by ``render()``.
        message: The specific message for this error instance.
        pos: Position of the offending token, or ``None`` when unknown.
        source_line: The offending line without its newline, used to draw a
            caret; ``None`` when unavailable.
    """

    kind: _ClassVar[str] = "Error"

    message: str
    pos: SourcePos | None
    source_line: str | None

    def __init__(
        self,
        message: str,
        pos: SourcePos | None = None,
        source_line: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: The specific message for this error instance.
            pos: Position of the offending token, or ``None``.
            source_line: The offending source line, or ``None``.
        """
        super().__init__(message)
        self.message = message
        self.pos = pos
        self.source_line = source_line

    def __str__(self) -> str:
        """Return the bare message, matching ``err.message``."""
        return self.message

    def __reduce__(self) -> tuple[object, tuple[object, ...]]:
        """Preserve the full error state across ``pickle`` round-trips."""
        return (type(self), (self.message, self.pos, self.source_line))

    def with_source(self, source_line: str) -> "MiniCalcError":
        """Attach the offending source line and return this same error.

        Args:
            source_line: The offending line without its newline.

        Returns:
            This error instance, to allow chaining.
        """
        self.source_line = source_line
        return self

    def render(self, color: bool = False) -> str:
        """Render a user-facing, optionally colored, multi-line message.

        Args:
            color: When True, style ``Error:`` in bold red and the caret in
                red with ANSI escape codes.

        Returns:
            The error heading, plus the source line and caret when both
            ``pos`` and ``source_line`` are available.
        """
        if self.pos is None:
            heading = f"Error: {self.kind}: {self.message}"
        else:
            heading = (
                f"Error: {self.kind} at line {self.pos.line}, "
                f"column {self.pos.col}: {self.message}"
            )

        if color:
            heading = heading.replace("Error:", f"{_BOLD_RED}Error:{_RESET}", 1)

        lines = [heading]
        if self.pos is not None and self.source_line is not None:
            source = self.source_line.replace("\t", " ")
            padding = "  " + " " * (self.pos.col - 1)
            caret = "^"
            if color:
                caret = f"{_RED}^{_RESET}"
            lines.append("  " + source)
            lines.append(padding + caret)
        return "\n".join(lines)

    def canonical(self) -> str:
        """Return the stable golden-test form of this error.

        Returns:
            ``ERR <ClassName> <line>:<col>``, or ``ERR <ClassName> ?:?`` when
            the error has no position.
        """
        name = type(self).__name__
        if self.pos is None:
            return f"ERR {name} ?:?"
        return f"ERR {name} {self.pos.line}:{self.pos.col}"


class LexError(MiniCalcError):
    """Raised by the lexer for malformed characters or literals.

    Attributes:
        kind (ClassVar[str]): ``"Lexical error"``.
    """

    kind: _ClassVar[str] = "Lexical error"


class ParseError(MiniCalcError):
    """Raised by the parser for malformed syntax.

    Attributes:
        kind (ClassVar[str]): ``"Syntax error"``.
    """

    kind: _ClassVar[str] = "Syntax error"


class EvalError(MiniCalcError):
    """Base class for every runtime (evaluation) error.

    Attributes:
        kind (ClassVar[str]): ``"Runtime error"``.
    """

    kind: _ClassVar[str] = "Runtime error"


class DivisionByZeroError(EvalError):
    """Raised when ``/``, ``//``, or ``%`` receives a zero divisor.

    Attributes:
        kind (ClassVar[str]): Inherited ``"Runtime error"``.
    """


class IntegerRangeError(EvalError):
    """Raised when a produced value leaves the signed 32-bit range.

    Attributes:
        kind (ClassVar[str]): Inherited ``"Runtime error"``.
    """


class DomainError(EvalError):
    """Raised for a mathematically invalid operation, such as a negative exponent.

    Attributes:
        kind (ClassVar[str]): Inherited ``"Runtime error"``.
    """


class UndefinedNameError(EvalError):
    """Raised when a variable is not set, including an unset ``ans``.

    Attributes:
        kind (ClassVar[str]): Inherited ``"Runtime error"``.
    """


class CallError(EvalError):
    """Raised for an unknown function, non-function call, or wrong arity.

    Attributes:
        kind (ClassVar[str]): Inherited ``"Runtime error"``.
    """


class AssignmentError(EvalError):
    """Raised when assigning to ``ans`` or to a built-in name.

    Attributes:
        kind (ClassVar[str]): Inherited ``"Runtime error"``.
    """
