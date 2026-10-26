"""Variable storage and the special ``ans`` binding (CORE-003).

The environment is the only mutable state in the interpreter. ``ans`` is a
separate read-only binding updated after each successful expression; it is not
part of ``variables``.
"""

from __future__ import annotations

from .errors import SourcePos, UndefinedNameError


class Environment:
    """Hold user variables and the current ``ans`` value.

    Attributes:
        variables: User-defined name-to-value bindings.
        ans: Value of the last successful expression, or ``None`` before the
            first success.
    """

    def __init__(self) -> None:
        """Create an empty environment with no ``ans`` value."""
        self.variables: dict[str, int] = {}
        self.ans: int | None = None

    def get(self, name: str, pos: SourcePos) -> int:
        """Read a variable or ``ans``.

        Args:
            name: The identifier to look up.
            pos: Position used for the error if the name has no value.

        Returns:
            The stored integer.

        Raises:
            UndefinedNameError: For an unset variable or an unset ``ans``.
        """
        if name == "ans":
            if self.ans is None:
                raise UndefinedNameError(
                    "ans has no value yet; evaluate an expression first", pos
                )
            return self.ans
        if name in self.variables:
            return self.variables[name]
        raise UndefinedNameError(f"name '{name}' is not defined", pos)

    def set(self, name: str, value: int) -> None:
        """Bind a variable.

        Args:
            name: The identifier to bind.
            value: The integer value.
        """
        self.variables[name] = value

    def record_result(self, value: int) -> None:
        """Record the value of a successful expression as ``ans``.

        Args:
            value: The expression's value.
        """
        self.ans = value

    def clear(self) -> None:
        """Remove every variable and the ``ans`` value."""
        self.variables.clear()
        self.ans = None

    def items(self) -> list[tuple[str, int]]:
        """List user variables in sorted name order.

        Returns:
            Sorted ``(name, value)`` pairs; ``ans`` is never included.
        """
        return sorted(self.variables.items())
