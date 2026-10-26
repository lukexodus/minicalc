"""Canonical golden-test formatting (CORE-002).

The format is design-locked in ``docs/context/interface-contract.md`` section
12: one expected line per non-empty statement line, in source order. Errors
compare only the class name and ``line:col`` via ``MiniCalcError.canonical()``,
never message text.
"""

from __future__ import annotations


def canonical_line(outcome: object) -> str | None:
    """Convert one interpreter outcome to its canonical golden line.

    Duck-typed on ``outcome.result`` and ``outcome.error`` so the harness does
    not depend on the concrete ``LineOutcome`` class from CORE-003.

    Args:
        outcome: Any object with ``result`` and ``error`` attributes.

    Returns:
        ``OK <value>`` for a value result, ``OK <name>=<value>`` for an
        assignment, an error's ``canonical()`` string, or ``None`` when the
        line produced no output.

    Raises:
        ValueError: If a result carries a kind outside the contract.
    """
    error = getattr(outcome, "error", None)
    if error is not None:
        return error.canonical()

    result = getattr(outcome, "result", None)
    if result is None:
        return None

    kind = result.kind
    if kind == "value":
        return f"OK {result.value}"
    if kind == "assign":
        return f"OK {result.name}={result.value}"
    if kind == "empty":
        return None
    raise ValueError(f"unknown result kind: {kind!r}")
