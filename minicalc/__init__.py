"""MiniCalc: a small integer-arithmetic programming language.

The package is organized as a one-way pipeline: source lines flow through the
lexer, parser, and evaluator, and are coordinated by the ``Interpreter`` facade
in ``minicalc.interpreter``. See ``docs/context/interface-contract.md`` for the
authoritative module map and ``docs/context/language-spec.md`` for behavior.
"""

__version__ = "1.0.0"
