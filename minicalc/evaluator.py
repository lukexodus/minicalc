"""AST evaluator: checked 32-bit integer semantics for MiniCalc ([D-05]).

The evaluator implements language-spec sections 4 to 7. Every value it
produces passes through :meth:`Evaluator._checked`, so arithmetic never wraps
or silently leaves the signed 32-bit range. Statements are atomic: in
particular :class:`~minicalc.ast_nodes.Assign` binds its target only after the
right-hand side has evaluated successfully.
"""

from __future__ import annotations

from .ast_nodes import Assign, Binary, Call, Name, Node, Number, Unary
from .builtins import BUILTINS, is_reserved
from .environment import Environment
from .errors import (
    AssignmentError,
    CallError,
    DivisionByZeroError,
    DomainError,
    IntegerRangeError,
    SourcePos,
    UndefinedNameError,
)
from .limits import in_range


class Evaluator:
    """Evaluate MiniCalc AST nodes against one environment.

    Attributes:
        env: The environment holding variables and the read-only ``ans``
            binding; assignments mutate it only after a successful right side.
    """

    def __init__(self, env: Environment) -> None:
        """Store the environment used for name lookups and assignment.

        Args:
            env: The interpreter's persistent environment.
        """
        self.env = env

    def evaluate(self, node: Node) -> int:
        """Evaluate one node and return its checked integer value.

        Args:
            node: The AST node to evaluate.

        Returns:
            The value of the expression, always within the signed 32-bit range.

        Raises:
            AssignmentError: Assigning to ``ans`` or a built-in name.
            CallError: Unknown function, non-function call, or wrong arity.
            DivisionByZeroError: ``/``, ``//``, or ``%`` by zero.
            DomainError: A negative exponent.
            IntegerRangeError: A produced value outside the 32-bit range.
            UndefinedNameError: An unset variable, unset ``ans``, or a
                built-in name used as a value.
            TypeError: For an unknown AST node type (a programming error).
        """
        if isinstance(node, Number):
            return self._checked(node.value, node.pos)
        if isinstance(node, Binary):
            return self._binary(node)
        if isinstance(node, Unary):
            return self._unary(node)
        if isinstance(node, Name):
            return self._name(node)
        if isinstance(node, Call):
            return self._call(node)
        if isinstance(node, Assign):
            return self._assign(node)
        raise TypeError(f"unknown AST node type: {type(node).__name__}")

    def _checked(self, value: int, pos: SourcePos) -> int:
        """Return ``value`` if it fits the 32-bit range, else raise.

        Args:
            value: A produced integer.
            pos: The ``SourcePos`` of the operator or call that produced it.

        Returns:
            ``value`` unchanged.

        Raises:
            IntegerRangeError: When ``value`` is outside the signed 32-bit
                range.
        """
        if not in_range(value):
            raise IntegerRangeError("integer result out of 32-bit range", pos)
        return value

    def _binary(self, node: Binary) -> int:
        """Evaluate a binary operation, left operand first.

        Args:
            node: The ``Binary`` node.

        Returns:
            The checked result.

        Raises:
            DivisionByZeroError: For a zero divisor in ``/``, ``//``, ``%``.
            DomainError: For a negative exponent.
            IntegerRangeError: When the result is outside the 32-bit range.
            TypeError: For an operator outside :data:`~minicalc.ast_nodes.Op`.
        """
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        op = node.op

        if op == "+":
            return self._checked(left + right, node.pos)
        if op == "-":
            return self._checked(left - right, node.pos)
        if op == "*":
            return self._checked(left * right, node.pos)
        if op == "/":
            if right == 0:
                raise DivisionByZeroError("division by zero", node.pos)
            # Truncate toward zero, as the spec requires: Python's // floors, so
            # divide the magnitudes and restore the sign explicitly. This keeps
            # -7 / 2 at -3 while // below gives the floor, -4 ([D-06]).
            quotient = abs(left) // abs(right)
            if (left < 0) != (right < 0):
                quotient = -quotient
            return self._checked(quotient, node.pos)
        if op == "//":
            if right == 0:
                raise DivisionByZeroError("division by zero", node.pos)
            return self._checked(left // right, node.pos)
        if op == "%":
            if right == 0:
                raise DivisionByZeroError("division by zero", node.pos)
            # Python's % is already floored and takes the divisor's sign, which
            # is exactly the pairing the spec promises with // ([D-06]), so no
            # sign fix-up is needed here.
            return self._checked(left % right, node.pos)
        if op == "**":
            return self._power(left, right, node.pos)
        if op == "==":
            return self._checked(int(left == right), node.pos)
        if op == "!=":
            return self._checked(int(left != right), node.pos)
        if op == "<":
            return self._checked(int(left < right), node.pos)
        if op == "<=":
            return self._checked(int(left <= right), node.pos)
        if op == ">":
            return self._checked(int(left > right), node.pos)
        if op == ">=":
            return self._checked(int(left >= right), node.pos)
        raise TypeError(f"unknown binary operator: {op!r}")

    def _power(self, base: int, exponent: int, pos: SourcePos) -> int:
        """Evaluate ``base ** exponent`` under the spec's short-circuit rules.

        Args:
            base: The already-evaluated base.
            exponent: The already-evaluated exponent.
            pos: Position of the ``**`` operator for error reporting.

        Returns:
            The checked result.

        Raises:
            DomainError: When ``exponent`` is negative.
            IntegerRangeError: When the result is outside the 32-bit range;
                for ``abs(base) >= 2`` and ``exponent > 31`` this is raised
                immediately without computing the power.
        """
        if exponent < 0:
            raise DomainError("negative exponent", pos)
        if exponent == 0:
            return self._checked(1, pos)
        if base == 0:
            return self._checked(0, pos)
        if base == 1:
            return self._checked(1, pos)
        if base == -1:
            return self._checked(1 if exponent % 2 == 0 else -1, pos)
        if exponent > 31:
            # Short-circuit before computing: |base| >= 2 and exponent > 31 is
            # always out of 32-bit range, and `2 ** 1000000000` must fail
            # instantly rather than allocate a billion-digit integer (spec s.5).
            raise IntegerRangeError("integer result out of 32-bit range", pos)
        return self._checked(base**exponent, pos)

    def _unary(self, node: Unary) -> int:
        """Evaluate a prefix unary operation.

        Args:
            node: The ``Unary`` node.

        Returns:
            The checked result.

        Raises:
            IntegerRangeError: When negating ``INT_MIN``.
            TypeError: For an operator other than ``-`` or ``+``.
        """
        value = self.evaluate(node.operand)
        if node.op == "-":
            return self._checked(-value, node.pos)
        if node.op == "+":
            return self._checked(value, node.pos)
        raise TypeError(f"unknown unary operator: {node.op!r}")

    def _name(self, node: Name) -> int:
        """Evaluate a variable reference or ``ans``.

        Args:
            node: The ``Name`` node.

        Returns:
            The name's stored value.

        Raises:
            UndefinedNameError: For an unset variable, unset ``ans``, or a
                built-in name used as a value (with a call hint).
        """
        if node.ident in BUILTINS:
            raise UndefinedNameError(
                f"'{node.ident}' is a function; call it like "
                f"{node.ident}(...)",
                node.pos,
            )
        return self.env.get(node.ident, node.pos)

    def _call(self, node: Call) -> int:
        """Evaluate a built-in call.

        Arity is checked before any argument is evaluated. Arguments then
        evaluate left to right, so the first failing argument determines the
        error.

        Args:
            node: The ``Call`` node.

        Returns:
            The checked result of the built-in.

        Raises:
            CallError: Unknown function, non-function call, or wrong arity.
            IntegerRangeError: When the built-in's result is outside the
                32-bit range (for example ``abs(INT_MIN)``).
        """
        builtin = BUILTINS.get(node.func)
        if builtin is None:
            if node.func == "ans" or node.func in self.env.variables:
                raise CallError(
                    f"'{node.func}' is a variable, not a function", node.pos
                )
            raise CallError(f"unknown function '{node.func}'", node.pos)

        count = len(node.args)
        if count < builtin.min_args or (
            builtin.max_args is not None and count > builtin.max_args
        ):
            raise CallError(
                self._arity_message(builtin.name, builtin.min_args, builtin.max_args, count),
                node.pos,
            )

        values = [self.evaluate(arg) for arg in node.args]
        return self._checked(builtin.fn(*values), node.pos)

    @staticmethod
    def _arity_message(
        name: str, min_args: int, max_args: int | None, count: int
    ) -> str:
        """Build the ``CallError`` message for a wrong argument count.

        Args:
            name: The built-in's name.
            min_args: Its minimum arity.
            max_args: Its maximum arity, or ``None`` when unbounded.
            count: The number of arguments supplied.

        Returns:
            A human-readable arity error message.
        """
        if max_args == min_args:
            return f"{name}() takes exactly {min_args} argument(s) ({count} given)"
        return f"{name}() takes at least {min_args} argument(s) ({count} given)"

    def _assign(self, node: Assign) -> int:
        """Evaluate an assignment atomically.

        The reserved-target check happens first; the right side is evaluated
        next; the environment is mutated only after both succeed.

        Args:
            node: The ``Assign`` node.

        Returns:
            The assigned value.

        Raises:
            AssignmentError: When the target is ``ans`` or a built-in name.
        """
        if is_reserved(node.target):
            raise AssignmentError(
                f"cannot assign to reserved name '{node.target}'", node.pos
            )
        value = self.evaluate(node.value)
        self.env.set(node.target, value)
        return self._checked(value, node.pos)
