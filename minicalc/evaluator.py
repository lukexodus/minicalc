"""Walking-skeleton evaluator: number literals only (CORE-003).

# STUB (CORE-003): replaced wholesale by FEAT-003

FEAT-003 replaces this module with full operator, variable, and built-in
evaluation. Until then, a ``Number`` node evaluates to its literal value.
"""

from __future__ import annotations

from .ast_nodes import Node, Number
from .environment import Environment
from .errors import EvalError, IntegerRangeError
from .limits import in_range


class Evaluator:
    """Evaluate the walking-skeleton subset of the AST.

    Attributes:
        env: The environment used for variables and ``ans`` (not yet read by
            the stub, but part of the locked constructor).
    """

    def __init__(self, env: Environment) -> None:
        """Store the environment.

        Args:
            env: The interpreter's environment.
        """
        self.env = env

    def evaluate(self, node: Node) -> int:
        """Evaluate one node.

        Args:
            node: The AST node to evaluate.

        Returns:
            The integer value of a ``Number`` node.

        Raises:
            IntegerRangeError: If the literal is outside the 32-bit range.
            EvalError: For every node type the walking skeleton does not yet
                implement.
        """
        if isinstance(node, Number):
            if not in_range(node.value):
                raise IntegerRangeError("integer out of range", node.pos)
            return node.value
        raise EvalError("not implemented yet", node.pos)
