"""Variable storage and the special ``ans`` binding (CORE-003).

The environment is the only mutable state in the interpreter. ``ans`` is a
separate read-only binding updated after each successful expression; it is not
part of ``variables``.
"""

from __future__ import annotations

from .errors import SourcePos, UndefinedNameError


class Environment:
    """Hold user variables and the current ``ans`` value.

    This is the only mutable state in the interpreter, so every statement sees
    exactly the bindings the previous statements left behind.

    Attributes:
        variables: User-defined name-to-value bindings. ``ans`` is deliberately
            kept out of this mapping so ``:vars`` and :meth:`items` list only
            names the user created, and so ``ans`` can never be overwritten by
            an assignment.
        ans: Value of the last successful expression, or ``None`` while none has
            succeeded yet. :meth:`record_result` sets it, and only
            ``Interpreter.run_line`` calls that method, after the statement is
            known to have succeeded and to be an expression rather than an
            assignment ([D-15] item 1). :meth:`clear` (the ``:clear`` command)
            resets it to ``None``, and no failed statement ever changes it,
            which is what keeps statements atomic ([D-07]).
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
