"""Differential test for MiniCalc (INT-002).

This test generates seeded random expression trees, renders each tree to
MiniCalc source in two ways (fully parenthesized and minimally parenthesized
per the spec table), and compares the real ``Interpreter`` against
:mod:`tests.oracle`, a reference evaluator written from the language spec
only.

The comparison is by value or error class, never by message text. Fixed spec
rulings ([D-15]) and the spec's worked examples are checked separately, and
seeded variable-state sequences verify assignment atomicity and ``ans``.
"""

from __future__ import annotations

import random
import time
from collections import Counter
from typing import Union

import pytest

from minicalc.errors import MiniCalcError
from minicalc.interpreter import Interpreter
from minicalc.limits import INT_MAX, INT_MIN

import oracle


#: Fixed seeds for the generated expression suite.
SEEDS: tuple[int, ...] = (20261026, 1729, 314159, 271828, 161803)

#: Expressions generated per category per seed, for each rendering.
PER_CATEGORY = 80

#: Top-level categories used for generation and reporting.
CATEGORIES: tuple[str, ...] = (
    "additive",
    "multiplicative",
    "division",
    "power",
    "comparison",
    "unary",
    "builtin_call",
)

#: The minimum number of generated expressions required per rendering.
MIN_EXPRESSIONS_PER_RENDERING = 2000

#: The required upper bound on total generated-suite runtime, in seconds.
MAX_RUNTIME_SECONDS = 15.0

#: At most this many mismatches are collected before the assertion fails.
MAX_MISMATCHES = 10

#: Fixed seeds for variable-state sequences.
STATE_SEEDS: tuple[int, ...] = (101, 202, 303, 404, 505, 606, 707, 808)

#: Lines per variable-state sequence.
SEQUENCE_LENGTH = 20

#: User variable names used by state sequences.
VAR_NAMES: tuple[str, ...] = ("v0", "v1", "v2", "v3", "v4")

#: A generated statement is either an expression tree or an assignment.
Statement = Union[oracle.Node, oracle.AssignStmt]

#: Bit patterns deliberately spread around the overflow boundaries.
_SMALL = tuple(range(0, 11))
_SQRT = (46339, 46340, 46341, 46342, -46340, -46341)
_NEAR = (
    INT_MAX,
    INT_MAX - 1,
    INT_MIN,
    INT_MIN + 1,
    2**30,
    -(2**30),
    2**31 - 2,
    -(2**31) + 2,
)
_POWERS = (
    0,
    1,
    2,
    4,
    8,
    16,
    32,
    64,
    128,
    256,
    512,
    1024,
    2**20,
    2**30,
    -1,
    -2,
    -4,
    -8,
    -16,
    -32,
    -64,
    -128,
    -256,
    -512,
    -1024,
)


def _random_constant(rng: random.Random) -> int:
    """Draw a constant from a mixture of magnitudes.

    The buckets are small values (zero-heavy), values around ``sqrt(2**31)``,
    values around the 32-bit boundary, and powers of two. This makes overflow,
    zero divisors, and special power bases all common.

    Args:
        rng: The seeded random source.

    Returns:
        An in-range signed 32-bit integer.
    """
    bucket = rng.random()
    if bucket < 0.30:
        return rng.choice(_SMALL)
    if bucket < 0.55:
        return rng.choice(_SQRT)
    if bucket < 0.80:
        return rng.choice(_NEAR)
    return rng.choice(_POWERS)


def _leaf(rng: random.Random, allow_vars: bool) -> oracle.Node:
    """Return a leaf node, optionally allowing names.

    Args:
        rng: The seeded random source.
        allow_vars: When true, emit variables, ``ans``, undefined names, and
            bare built-in names as well as constants.

    Returns:
        A :class:`oracle.Const` or :class:`oracle.Var` leaf.
    """
    if not allow_vars:
        return oracle.Const(_random_constant(rng))
    bucket = rng.random()
    if bucket < 0.30:
        return oracle.Const(_random_constant(rng))
    if bucket < 0.55:
        return oracle.Var(rng.choice(VAR_NAMES))
    if bucket < 0.70:
        return oracle.Var("ans")
    if bucket < 0.85:
        return oracle.Var(rng.choice(("never_set_a", "never_set_b")))
    if bucket < 0.93:
        # A bare built-in name is an undefined value (spec section 6).
        return oracle.Var("abs")
    return oracle.Const(_random_constant(rng))


def _random_exponent(rng: random.Random, depth: int, allow_vars: bool) -> oracle.Node:
    """Build an exponent tree, including negative and huge exponents.

    Args:
        rng: The seeded random source.
        depth: Remaining expression depth for a random exponent.
        allow_vars: Whether names are allowed in a random exponent.

    Returns:
        An expression tree used as a ``**`` right operand.
    """
    bucket = rng.random()
    if bucket < 0.55:
        return oracle.Const(rng.randint(0, 4))
    if bucket < 0.70:
        return oracle.Const(rng.choice((30, 31, 32, 33, 62, 100, 1000, INT_MAX)))
    if bucket < 0.85:
        return oracle.UnaryOp("-", oracle.Const(rng.randint(1, 5)))
    return random_expr(rng, max(0, depth - 1), allow_vars)


def _random_call(rng: random.Random, depth: int, allow_vars: bool) -> oracle.CallOp:
    """Build a built-in call, with a small share of invalid calls.

    Args:
        rng: The seeded random source.
        depth: Remaining expression depth for arguments.
        allow_vars: Whether names are allowed in arguments.

    Returns:
        A :class:`oracle.CallOp` node.
    """

    def argument() -> oracle.Node:
        return random_expr(rng, max(0, depth - 1), allow_vars)

    bucket = rng.random()
    if bucket < 0.32:
        return oracle.CallOp("abs", (argument(),))
    if bucket < 0.55:
        return oracle.CallOp("min", tuple(argument() for _ in range(rng.randint(1, 3))))
    if bucket < 0.78:
        return oracle.CallOp("max", tuple(argument() for _ in range(rng.randint(1, 3))))
    if bucket < 0.94:
        return oracle.CallOp("gcd", (argument(), argument()))
    if bucket < 0.97:
        return oracle.CallOp("foo", (argument(),))
    return oracle.CallOp("abs", (argument(), argument()))


def random_expr(rng: random.Random, depth: int, allow_vars: bool = False) -> oracle.Node:
    """Build a random expression tree of bounded depth.

    Args:
        rng: The seeded random source.
        depth: Maximum remaining depth; zero produces a leaf.
        allow_vars: Whether name leaves are allowed.

    Returns:
        An expression tree.
    """
    if depth <= 0:
        return _leaf(rng, allow_vars)
    bucket = rng.random()
    if bucket < 0.28:
        return oracle.BinaryOp(
            rng.choice(("+", "-", "*")),
            random_expr(rng, depth - 1, allow_vars),
            random_expr(rng, depth - 1, allow_vars),
        )
    if bucket < 0.48:
        op = rng.choice(("/", "//", "%"))
        right = random_expr(rng, depth - 1, allow_vars)
        if rng.random() < 0.20:
            right = oracle.Const(0)
        return oracle.BinaryOp(
            op, random_expr(rng, depth - 1, allow_vars), right
        )
    if bucket < 0.62:
        return oracle.BinaryOp(
            "**",
            random_expr(rng, depth - 1, allow_vars),
            _random_exponent(rng, depth, allow_vars),
        )
    if bucket < 0.74:
        return oracle.UnaryOp(
            rng.choice(("-", "+")), random_expr(rng, depth - 1, allow_vars)
        )
    if bucket < 0.88:
        return _random_call(rng, depth, allow_vars)
    if bucket < 0.96:
        return oracle.BinaryOp(
            rng.choice(sorted(oracle.COMPARISON_OPS)),
            random_expr(rng, depth - 1, allow_vars),
            random_expr(rng, depth - 1, allow_vars),
        )
    return _leaf(rng, allow_vars)


def generate_expression(rng: random.Random, category: str) -> oracle.Node:
    """Build an expression whose root belongs to ``category``.

    Args:
        rng: The seeded random source.
        category: One of :data:`CATEGORIES`.

    Returns:
        An expression tree.

    Raises:
        ValueError: If ``category`` is unknown.
    """
    if category == "additive":
        return oracle.BinaryOp(
            rng.choice(("+", "-")), random_expr(rng, 2), random_expr(rng, 2)
        )
    if category == "multiplicative":
        return oracle.BinaryOp("*", random_expr(rng, 2), random_expr(rng, 2))
    if category == "division":
        right = random_expr(rng, 2)
        if rng.random() < 0.30:
            right = oracle.Const(0)
        return oracle.BinaryOp(
            rng.choice(("/", "//", "%")), random_expr(rng, 2), right
        )
    if category == "power":
        if rng.random() < 0.30:
            # Guarantee right-nested powers, which distinguish left- and
            # right-associative parsing.
            exponent: oracle.Node = oracle.BinaryOp(
                "**", random_expr(rng, 1), oracle.Const(rng.randint(0, 4))
            )
        else:
            exponent = _random_exponent(rng, 2, False)
        return oracle.BinaryOp("**", random_expr(rng, 2), exponent)
    if category == "comparison":
        return oracle.BinaryOp(
            rng.choice(sorted(oracle.COMPARISON_OPS)),
            random_expr(rng, 2),
            random_expr(rng, 2),
        )
    if category == "unary":
        return oracle.UnaryOp(rng.choice(("-", "+")), random_expr(rng, 2))
    if category == "builtin_call":
        return _random_call(rng, 2, False)
    raise ValueError(f"unknown category: {category!r}")


def _oracle_value_outcome(tree: oracle.Node) -> tuple[object, ...]:
    """Evaluate a tree with the reference evaluator in a fresh state.

    Args:
        tree: The expression tree.

    Returns:
        ``("value", result)`` or ``("error", error_class)``.
    """
    state = oracle.OracleState()
    try:
        return ("value", oracle.evaluate(tree, state))
    except oracle.OracleError as exc:
        return ("error", exc.kind)


def _actual_value_outcome(interp: Interpreter, source: str) -> tuple[object, ...]:
    """Run one line through the real interpreter.

    Args:
        interp: The interpreter session.
        source: MiniCalc source text.

    Returns:
        ``("value", result)``, ``("assign", value, name)``, or
        ``("error", class_name, message)``.
    """
    try:
        result = interp.run_line(source)
    except MiniCalcError as exc:
        return ("error", type(exc).__name__, str(exc))
    except Exception as exc:  # pragma: no cover - defensive diagnostics only
        return ("error", f"{type(exc).__name__}", str(exc))
    if result.kind == "value":
        return ("value", result.value)
    if result.kind == "assign":
        return ("assign", result.value, result.name)
    return ("empty", None)


def _matches(expected: tuple[object, ...], actual: tuple[object, ...]) -> bool:
    """Compare outcomes by value or error class only.

    Args:
        expected: Oracle outcome.
        actual: Interpreter outcome.

    Returns:
        True when the outcomes agree.
    """
    if expected[0] == "error" and actual[0] == "error":
        return expected[1] == actual[1]
    return expected == actual


def _format_outcome(outcome: tuple[object, ...]) -> str:
    """Format an outcome for a mismatch message.

    Args:
        outcome: A value, assignment, or error tuple.

    Returns:
        A compact human-readable string.
    """
    if outcome[0] == "error":
        return f"{outcome[1]} ({outcome[2]})" if len(outcome) > 2 else str(outcome[1])
    return repr(outcome)


def _render(tree: oracle.Node, renderer) -> str:
    """Render a tree with the supplied reference renderer.

    Args:
        tree: The expression tree.
        renderer: ``oracle.render_full`` or ``oracle.render_minimal``.

    Returns:
        MiniCalc source text.
    """
    return renderer(tree)


def test_generated_expressions_match_oracle() -> None:
    """Compare thousands of generated expressions in both renderings.

    The oracle tree is rendered fully parenthesized and minimally
    parenthesized; both sources must produce the oracle value or error class.
    """
    started = time.perf_counter()
    interp = Interpreter()
    counts: dict[str, Counter[str]] = {
        "full": Counter(),
        "minimal": Counter(),
    }
    error_counts: dict[str, Counter[str]] = {
        "full": Counter(),
        "minimal": Counter(),
    }
    mismatches: list[str] = []

    for seed in SEEDS:
        for category_index, category in enumerate(CATEGORIES):
            rng = random.Random(seed * 1000 + category_index)
            for _ in range(PER_CATEGORY):
                tree = generate_expression(rng, category)
                expected = _oracle_value_outcome(tree)
                for rendering, renderer in (
                    ("full", oracle.render_full),
                    ("minimal", oracle.render_minimal),
                ):
                    source = _render(tree, renderer)
                    actual = _actual_value_outcome(interp, source)
                    counts[rendering][category] += 1
                    if expected[0] == "error":
                        error_counts[rendering][category] += 1
                    if not _matches(expected, actual):
                        mismatches.append(
                            f"seed={seed} category={category} rendering={rendering}\n"
                            f"  source:  {source}\n"
                            f"  oracle:  {_format_outcome(expected)}\n"
                            f"  actual:  {_format_outcome(actual)}"
                        )
                        if len(mismatches) >= MAX_MISMATCHES:
                            break
                if len(mismatches) >= MAX_MISMATCHES:
                    break
            if len(mismatches) >= MAX_MISMATCHES:
                break
        if len(mismatches) >= MAX_MISMATCHES:
            break

    elapsed = time.perf_counter() - started
    print("\ndifferential generated-expression summary:")
    print(
        f"  seeds={len(SEEDS)} categories={len(CATEGORIES)} "
        f"per_category={PER_CATEGORY}"
    )
    for rendering in ("full", "minimal"):
        total = counts[rendering].total()
        errors = error_counts[rendering].total()
        print(
            f"  {rendering}: {total} expressions, {errors} expected errors, "
            f"{total - errors} expected values"
        )
        print(f"    per category: {dict(sorted(counts[rendering].items()))}")
    print(f"  elapsed: {elapsed:.3f}s")

    assert not mismatches, "differential mismatches:\n" + "\n\n".join(mismatches)
    for rendering in ("full", "minimal"):
        assert counts[rendering].total() >= MIN_EXPRESSIONS_PER_RENDERING
    assert elapsed < MAX_RUNTIME_SECONDS, (
        f"generated suite took {elapsed:.3f}s, "
        f"limit is {MAX_RUNTIME_SECONDS:.1f}s"
    )


def _forced_failure(rng: random.Random) -> Statement:
    """Build a statement guaranteed to fail for a known spec reason.

    Args:
        rng: The seeded random source.

    Returns:
        A failing expression or assignment statement.
    """
    kind = rng.choice(
        (
            "div0",
            "domain",
            "range",
            "undefined",
            "reserved_ans",
            "reserved_abs",
            "undefined_operand",
        )
    )
    if kind == "div0":
        return oracle.BinaryOp("/", oracle.Const(_random_constant(rng)), oracle.Const(0))
    if kind == "domain":
        return oracle.BinaryOp(
            "**",
            oracle.Const(_random_constant(rng)),
            oracle.UnaryOp("-", oracle.Const(rng.randint(1, 3))),
        )
    if kind == "range":
        return oracle.BinaryOp(
            "+", oracle.Const(INT_MAX), oracle.Const(rng.randint(1, 5))
        )
    if kind == "undefined":
        return oracle.Var("never_set_a")
    if kind == "reserved_ans":
        # The reserved-name check precedes right-side evaluation.
        return oracle.AssignStmt(
            "ans", oracle.BinaryOp("/", oracle.Const(1), oracle.Const(0))
        )
    if kind == "reserved_abs":
        # Still AssignmentError even though the right side is undefined.
        return oracle.AssignStmt("abs", oracle.Var("never_set_b"))
    return oracle.BinaryOp("+", oracle.Var("never_set_b"), oracle.Const(1))


def generate_state_line(rng: random.Random, index: int) -> Statement:
    """Generate one line of a variable-state sequence.

    Every fifth line is a forced failure so each 20-line sequence exercises
    atomicity and ``ans`` on errors.

    Args:
        rng: The seeded random source.
        index: Zero-based line index inside the sequence.

    Returns:
        An expression tree or assignment statement.
    """
    if index % 5 == 3:
        return _forced_failure(rng)
    bucket = rng.random()
    if bucket < 0.40:
        return oracle.AssignStmt(rng.choice(VAR_NAMES), random_expr(rng, 2, True))
    if bucket < 0.50:
        return oracle.AssignStmt(
            rng.choice(("ans", "abs", "min", "gcd")), random_expr(rng, 2, True)
        )
    return random_expr(rng, 2, True)


def _render_statement(stmt: Statement) -> str:
    """Render a statement as MiniCalc source.

    Args:
        stmt: An expression tree or assignment statement.

    Returns:
        MiniCalc source text.
    """
    if isinstance(stmt, oracle.AssignStmt):
        return f"{stmt.target} = {oracle.render_minimal(stmt.value)}"
    return oracle.render_minimal(stmt)


def _oracle_statement_outcome(
    stmt: Statement, state: oracle.OracleState
) -> tuple[object, ...]:
    """Execute one statement on reference state.

    Args:
        stmt: The statement.
        state: The reference environment, mutated only on success.

    Returns:
        An outcome tuple matching :func:`_actual_value_outcome`.
    """
    try:
        kind, value, name = oracle.execute(stmt, state)
    except oracle.OracleError as exc:
        return ("error", exc.kind)
    if kind == "value":
        return ("value", value)
    return ("assign", value, name)


def test_variable_state_sequences_match_oracle() -> None:
    """Check seeded 20-line sequences, including failures and atomicity.

    After every line, both the variables and ``ans`` are compared with the
    oracle state. A failed line must change neither.
    """
    mismatches: list[str] = []
    lines_checked = 0

    for seed in STATE_SEEDS:
        rng = random.Random(seed)
        interp = Interpreter()
        state = oracle.OracleState()
        for index in range(SEQUENCE_LENGTH):
            stmt = generate_state_line(rng, index)
            source = _render_statement(stmt)
            expected = _oracle_statement_outcome(stmt, state)
            actual = _actual_value_outcome(interp, source)
            lines_checked += 1
            if not _matches(expected, actual):
                mismatches.append(
                    f"seed={seed} line={index + 1} sequence\n"
                    f"  source:  {source}\n"
                    f"  oracle:  {_format_outcome(expected)}\n"
                    f"  actual:  {_format_outcome(actual)}"
                )
            actual_variables = dict(interp.env.variables)
            actual_ans = interp.env.ans
            if actual_variables != state.variables or actual_ans != state.ans:
                mismatches.append(
                    f"seed={seed} line={index + 1} state mismatch\n"
                    f"  source:  {source}\n"
                    f"  oracle variables: {state.variables} ans={state.ans}\n"
                    f"  actual variables: {actual_variables} ans={actual_ans}"
                )
                # The sequence is meaningless once state diverges.
                break
            if len(mismatches) >= MAX_MISMATCHES:
                break
        if len(mismatches) >= MAX_MISMATCHES:
            break

    print(
        f"\nvariable-state summary: {len(STATE_SEEDS)} sequences x "
        f"{SEQUENCE_LENGTH} lines = {lines_checked} lines checked"
    )
    assert not mismatches, "variable-state mismatches:\n" + "\n\n".join(mismatches)


def _assert_fixed_source(source: str, expected: object) -> None:
    """Run one fixed source line on a fresh interpreter and compare.

    Args:
        source: MiniCalc source text.
        expected: An integer value, or an expected error class name.

    Raises:
        AssertionError: When the outcome differs.
    """
    interp = Interpreter()
    if isinstance(expected, int):
        result = interp.run_line(source)
        assert result.kind == "value", f"{source!r}: kind={result.kind!r}"
        assert result.value == expected, (
            f"{source!r}: expected {expected}, got {result.value}"
        )
        return
    with pytest.raises(MiniCalcError) as info:
        interp.run_line(source)
    actual = type(info.value).__name__
    assert actual == expected, f"{source!r}: expected {expected}, got {actual}"


def test_spec_worked_examples() -> None:
    """Check every fixed worked example recorded in the spec."""
    for source, expected in oracle.SPEC_WORKED_CASES:
        _assert_fixed_source(source, expected)


def test_phase2_rulings() -> None:
    """Check the Phase 2 rulings recorded in the spec ([D-15])."""
    for source, expected in oracle.PHASE2_RULING_CASES:
        _assert_fixed_source(source, expected)
    for source, expected_class, column in oracle.PHASE2_LEX_CASES:
        interp = Interpreter()
        with pytest.raises(MiniCalcError) as info:
            interp.run_line(source)
        assert type(info.value).__name__ == expected_class
        assert info.value.pos is not None
        assert info.value.pos.col == column


def test_ans_and_atomicity_ruling() -> None:
    """Check that only successful expressions update ``ans``."""
    interp = Interpreter()
    first = interp.run_line("2 + 3 * 4")
    assert first.kind == "value" and first.value == 14
    assert interp.env.ans == 14

    assigned = interp.run_line("x = 7")
    assert assigned.kind == "assign" and assigned.name == "x" and assigned.value == 7
    assert interp.env.ans == 14, "a successful assignment must not change ans"

    second = interp.run_line("ans * x")
    assert second.kind == "value" and second.value == 98
    assert interp.env.ans == 98

    with pytest.raises(MiniCalcError) as info:
        interp.run_line("1 / 0")
    assert type(info.value).__name__ == "DivisionByZeroError"
    assert interp.env.ans == 98, "a failing expression must not change ans"
    assert interp.env.variables == {"x": 7}, "a failing line must not change variables"
