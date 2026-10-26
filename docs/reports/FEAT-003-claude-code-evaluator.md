# Task Report: FEAT-003 — Evaluator and built-ins

**Date:** 2026-10-26
**Agent:** claude-code
**Task ID:** FEAT-003
**Status:** needs-review
**Commit:** `feat(FEAT-003): implement evaluator and built-ins` (single task commit on `task/FEAT-003`)
**Worktree:** `../minicalc-FEAT-003` (branch `task/FEAT-003`)
**Patch File:** `patch/FEAT-003-claude-code-evaluator.patch`

---

## 1. Executive Summary

Implemented the complete MiniCalc runtime: checked signed-32-bit arithmetic,
all operators from the language spec (`+ - * / // % **`, comparisons, unary
`+ -`), variables and `ans`, the four built-ins (`abs`, `min`, `max`, `gcd`),
reserved-name enforcement, atomic assignments, and the documented evaluation
errors. `minicalc/evaluator.py` is no longer a stub and the new
`minicalc/builtins.py` holds the frozen `Builtin` registry.

`pytest -q` reports **256 passed, 0 failed, 0 skipped** (77 pre-existing tests
plus 179 new evaluator/built-in tests). All AST nodes in the new tests are
built by hand, so they do not depend on FEAT-001/FEAT-002. The environment was
reviewed and left unchanged because no defect was found.

---

## 2. Implementation Details

### 2.1 Changes Made

- `minicalc/builtins.py` (new): frozen `Builtin` dataclass, the `BUILTINS`
  registry (`abs` 1 arg, `min`/`max` 1+, `gcd` exactly 2), iterative Euclid
  `gcd` on absolute values, and `is_reserved()` for `ans` plus every built-in.
  Functions take plain ints and return ints; range checking stays in the
  evaluator.
- `minicalc/evaluator.py` (rewritten): dispatch for every AST node, with a
  single `_checked()` helper applied to every produced value. `/` truncates
  toward zero with `abs(a) // abs(b)` (no floats), `//` and `%` use Python
  floor semantics, zero divisors fail before range checks, and `**`
  short-circuits oversized powers. Calls check arity before evaluating
  arguments; arguments evaluate left to right. Assignments check reserved
  names first and bind only after the right side succeeds.
- `tests/test_evaluator.py` (new): 136 cases covering every worked-example
  row, every spec evaluation-error row, the truncation/floor/modulo grid,
  exponent edge cases (including a timed `2 ** 1000000000`), range edges,
  built-in arity/argument-order behavior, name/reserved errors, and
  assignment atomicity.
- `tests/test_builtins.py` (new): 43 cases covering registry shape, arity
  metadata, frozen dataclass, each built-in's values/signs/zeros, and exact
  case-sensitive reserved-name matching.
- `minicalc/environment.py`: unchanged (reviewed; CORE-003 implementation
  already matches the contract).

### 2.2 Conformance to Specifications & Decisions

- `docs/context/language-spec.md` sections 4-7: signed 32-bit model with no
  wrapping, all operator semantics, `ans`/variables/built-ins, and the error
  class/position table.
- [D-05]: every result range-checked; `**` short-circuits when
  `abs(base) >= 2` and `exp > 31`.
- [D-06]: `/` truncates, `//` floors, `%` is floored modulo, `**` is
  right-associative in the parser and negative exponents are `DomainError`.
- [D-07]: atomic statements; assignment binds only after success.
- [D-08]: `ans` and built-in names are reserved; built-ins used as values
  raise `UndefinedNameError` with a call hint.
- [D-11]: module and public function docstrings; `Builtin` and `Evaluator`
  have `Attributes:` sections covering every attribute.
- No decision IDs were reserved for FEAT-003 and none were added.

---

## 3. Verification & Test Evidence

### 3.1 Test Execution

Command executed:

```bash
python -m pytest -q
```

**Results:**
- Tests passed: 256
- Tests failed: 0
- Tests skipped: 0

Real output:

```text
........................................................................ [ 28%]
........................................................................ [ 56%]
........................................................................ [ 84%]
........................................                                 [100%]
256 passed in 9.57s
```

The new test modules alone report `179 passed`. The pre-existing suite
(77 tests, including the CORE-003 facade tests and the golden smoke case)
still passes unchanged.

### 3.2 Edge Cases & Negative Testing

- Truncation vs floor vs modulo over the 8 x 6 sign grid, asserting
  `a == (a // b) * b + a % b` and the sign rule for `%`.
- `**`: `0**0`, `0**5`, `1**1000000`, `(-1)**3`, `(-1)**4`, `2**30`,
  `(-2)**31 == INT_MIN`; errors for `2**31`, `(-2)**32`, `2**-1`, `3**-1`;
  `2**1000000000` raises in under 0.5 s (timed with `time.perf_counter`).
- `INT_MIN / -1` and `INT_MIN // -1` are range errors; `-INT_MIN` fails at
  the unary operator; `5 / 0`, `5 // 0`, `5 % 0` fail at the operator.
- Arity errors are raised before argument evaluation; a two-failing-argument
  call always reports the leftmost failure.
- Assignment atomicity: a failed right side binds nothing (new or existing
  names); `ans`/built-in targets fail before a failing right side runs.
- `abs(INT_MIN)`, unset `ans`, unset variables, built-in-name shadowing, and
  calling a variable/`ans` produce the documented classes and columns.

`grep -nE "float|math\.pow|int\(.* / " minicalc/evaluator.py` returns no
matches.

---

## 4. Decisions Recorded

None. No decision ID was reserved for FEAT-003.

---

## 5. Unified Git Diff

Verbatim `git diff HEAD~1 -- minicalc tests`:

```diff
diff --git c/minicalc/builtins.py w/minicalc/builtins.py
new file mode 100644
index 0000000..776d432
--- /dev/null
+++ w/minicalc/builtins.py
@@ -0,0 +1,109 @@
+"""Built-in MiniCalc functions and reserved-name rules ([D-08]).
+
+Built-ins are the only functions in v1.0. Each implementation accepts plain
+Python integers and returns a plain integer; 32-bit range checking of a call's
+result belongs to the evaluator, not to these functions. ``abs(INT_MIN)``
+therefore returns ``2147483648`` here and the evaluator reports the range
+error at the call site.
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from typing import Callable
+
+
+@dataclass(frozen=True)
+class Builtin:
+    """Description of one built-in function.
+
+    Attributes:
+        name: The function name as written in source (for example ``"abs"``).
+        min_args: Minimum number of arguments the function accepts.
+        max_args: Maximum number of arguments, or ``None`` for unbounded.
+        fn: The implementation; it takes plain ints and returns an int.
+        doc: One-line human-readable description used by documentation.
+    """
+
+    name: str
+    min_args: int
+    max_args: int | None
+    fn: Callable[..., int]
+    doc: str
+
+
+def _abs(value: int) -> int:
+    """Return the absolute value of ``value``.
+
+    Args:
+        value: Any integer.
+
+    Returns:
+        ``value`` when it is non-negative, otherwise ``-value``.
+    """
+    return -value if value < 0 else value
+
+
+def _min(*values: int) -> int:
+    """Return the smallest of ``values``.
+
+    Args:
+        values: One or more integers, guaranteed non-empty by the arity check.
+
+    Returns:
+        The smallest argument.
+    """
+    return min(values)
+
+
+def _max(*values: int) -> int:
+    """Return the largest of ``values``.
+
+    Args:
+        values: One or more integers, guaranteed non-empty by the arity check.
+
+    Returns:
+        The largest argument.
+    """
+    return max(values)
+
+
+def _gcd(a: int, b: int) -> int:
+    """Return the non-negative greatest common divisor of ``a`` and ``b``.
+
+    Uses the iterative Euclid algorithm on absolute values, so it cannot
+    overflow the Python recursion limit and ``_gcd(0, 0)`` is ``0``.
+
+    Args:
+        a: Any integer.
+        b: Any integer.
+
+    Returns:
+        The greatest common divisor, always ``>= 0``.
+    """
+    a = _abs(a)
+    b = _abs(b)
+    while b:
+        a, b = b, a % b
+    return a
+
+
+#: Every built-in function, keyed by its source name ([D-08]).
+BUILTINS: dict[str, Builtin] = {
+    "abs": Builtin("abs", 1, 1, _abs, "Absolute value."),
+    "min": Builtin("min", 1, None, _min, "Smallest argument."),
+    "max": Builtin("max", 1, None, _max, "Largest argument."),
+    "gcd": Builtin("gcd", 2, 2, _gcd, "Greatest common divisor (non-negative)."),
+}
+
+
+def is_reserved(name: str) -> bool:
+    """Return whether ``name`` cannot be used as a variable.
+
+    Args:
+        name: An identifier text, case-sensitive.
+
+    Returns:
+        True for ``"ans"`` and every built-in function name.
+    """
+    return name == "ans" or name in BUILTINS
diff --git c/minicalc/evaluator.py w/minicalc/evaluator.py
index e190ea8..a8ee9bf 100644
--- c/minicalc/evaluator.py
+++ w/minicalc/evaluator.py
@@ -1,51 +1,300 @@
-"""Walking-skeleton evaluator: number literals only (CORE-003).
+"""AST evaluator: checked 32-bit integer semantics for MiniCalc ([D-05]).
 
-# STUB (CORE-003): replaced wholesale by FEAT-003
-
-FEAT-003 replaces this module with full operator, variable, and built-in
-evaluation. Until then, a ``Number`` node evaluates to its literal value.
+The evaluator implements language-spec sections 4 to 7. Every value it
+produces passes through :meth:`Evaluator._checked`, so arithmetic never wraps
+or silently leaves the signed 32-bit range. Statements are atomic: in
+particular :class:`~minicalc.ast_nodes.Assign` binds its target only after the
+right-hand side has evaluated successfully.
 """
 
 from __future__ import annotations
 
-from .ast_nodes import Node, Number
+from .ast_nodes import Assign, Binary, Call, Name, Node, Number, Unary
+from .builtins import BUILTINS, is_reserved
 from .environment import Environment
-from .errors import EvalError, IntegerRangeError
+from .errors import (
+    AssignmentError,
+    CallError,
+    DivisionByZeroError,
+    DomainError,
+    IntegerRangeError,
+    SourcePos,
+    UndefinedNameError,
+)
 from .limits import in_range
 
 
 class Evaluator:
-    """Evaluate the walking-skeleton subset of the AST.
+    """Evaluate MiniCalc AST nodes against one environment.
 
     Attributes:
-        env: The environment used for variables and ``ans`` (not yet read by
-            the stub, but part of the locked constructor).
+        env: The environment holding variables and the read-only ``ans``
+            binding; assignments mutate it only after a successful right side.
     """
 
     def __init__(self, env: Environment) -> None:
-        """Store the environment.
+        """Store the environment used for name lookups and assignment.
 
         Args:
-            env: The interpreter's environment.
+            env: The interpreter's persistent environment.
         """
         self.env = env
 
     def evaluate(self, node: Node) -> int:
-        """Evaluate one node.
+        """Evaluate one node and return its checked integer value.
 
         Args:
             node: The AST node to evaluate.
 
         Returns:
-            The integer value of a ``Number`` node.
+            The value of the expression, always within the signed 32-bit range.
 
         Raises:
-            IntegerRangeError: If the literal is outside the 32-bit range.
-            EvalError: For every node type the walking skeleton does not yet
-                implement.
+            AssignmentError: Assigning to ``ans`` or a built-in name.
+            CallError: Unknown function, non-function call, or wrong arity.
+            DivisionByZeroError: ``/``, ``//``, or ``%`` by zero.
+            DomainError: A negative exponent.
+            IntegerRangeError: A produced value outside the 32-bit range.
+            UndefinedNameError: An unset variable, unset ``ans``, or a
+                built-in name used as a value.
+            TypeError: For an unknown AST node type (a programming error).
         """
         if isinstance(node, Number):
-            if not in_range(node.value):
-                raise IntegerRangeError("integer out of range", node.pos)
-            return node.value
-        raise EvalError("not implemented yet", node.pos)
+            return self._checked(node.value, node.pos)
+        if isinstance(node, Binary):
+            return self._binary(node)
+        if isinstance(node, Unary):
+            return self._unary(node)
+        if isinstance(node, Name):
+            return self._name(node)
+        if isinstance(node, Call):
+            return self._call(node)
+        if isinstance(node, Assign):
+            return self._assign(node)
+        raise TypeError(f"unknown AST node type: {type(node).__name__}")
+
+    def _checked(self, value: int, pos: SourcePos) -> int:
+        """Return ``value`` if it fits the 32-bit range, else raise.
+
+        Args:
+            value: A produced integer.
+            pos: The ``SourcePos`` of the operator or call that produced it.
+
+        Returns:
+            ``value`` unchanged.
+
+        Raises:
+            IntegerRangeError: When ``value`` is outside the signed 32-bit
+                range.
+        """
+        if not in_range(value):
+            raise IntegerRangeError("integer result out of 32-bit range", pos)
+        return value
+
+    def _binary(self, node: Binary) -> int:
+        """Evaluate a binary operation, left operand first.
+
+        Args:
+            node: The ``Binary`` node.
+
+        Returns:
+            The checked result.
+
+        Raises:
+            DivisionByZeroError: For a zero divisor in ``/``, ``//``, ``%``.
+            DomainError: For a negative exponent.
+            IntegerRangeError: When the result is outside the 32-bit range.
+            TypeError: For an operator outside :data:`~minicalc.ast_nodes.Op`.
+        """
+        left = self.evaluate(node.left)
+        right = self.evaluate(node.right)
+        op = node.op
+
+        if op == "+":
+            return self._checked(left + right, node.pos)
+        if op == "-":
+            return self._checked(left - right, node.pos)
+        if op == "*":
+            return self._checked(left * right, node.pos)
+        if op == "/":
+            if right == 0:
+                raise DivisionByZeroError("division by zero", node.pos)
+            quotient = abs(left) // abs(right)
+            if (left < 0) != (right < 0):
+                quotient = -quotient
+            return self._checked(quotient, node.pos)
+        if op == "//":
+            if right == 0:
+                raise DivisionByZeroError("division by zero", node.pos)
+            return self._checked(left // right, node.pos)
+        if op == "%":
+            if right == 0:
+                raise DivisionByZeroError("division by zero", node.pos)
+            return self._checked(left % right, node.pos)
+        if op == "**":
+            return self._power(left, right, node.pos)
+        if op == "==":
+            return self._checked(int(left == right), node.pos)
+        if op == "!=":
+            return self._checked(int(left != right), node.pos)
+        if op == "<":
+            return self._checked(int(left < right), node.pos)
+        if op == "<=":
+            return self._checked(int(left <= right), node.pos)
+        if op == ">":
+            return self._checked(int(left > right), node.pos)
+        if op == ">=":
+            return self._checked(int(left >= right), node.pos)
+        raise TypeError(f"unknown binary operator: {op!r}")
+
+    def _power(self, base: int, exponent: int, pos: SourcePos) -> int:
+        """Evaluate ``base ** exponent`` under the spec's short-circuit rules.
+
+        Args:
+            base: The already-evaluated base.
+            exponent: The already-evaluated exponent.
+            pos: Position of the ``**`` operator for error reporting.
+
+        Returns:
+            The checked result.
+
+        Raises:
+            DomainError: When ``exponent`` is negative.
+            IntegerRangeError: When the result is outside the 32-bit range;
+                for ``abs(base) >= 2`` and ``exponent > 31`` this is raised
+                immediately without computing the power.
+        """
+        if exponent < 0:
+            raise DomainError("negative exponent", pos)
+        if exponent == 0:
+            return self._checked(1, pos)
+        if base == 0:
+            return self._checked(0, pos)
+        if base == 1:
+            return self._checked(1, pos)
+        if base == -1:
+            return self._checked(1 if exponent % 2 == 0 else -1, pos)
+        if exponent > 31:
+            raise IntegerRangeError("integer result out of 32-bit range", pos)
+        return self._checked(base**exponent, pos)
+
+    def _unary(self, node: Unary) -> int:
+        """Evaluate a prefix unary operation.
+
+        Args:
+            node: The ``Unary`` node.
+
+        Returns:
+            The checked result.
+
+        Raises:
+            IntegerRangeError: When negating ``INT_MIN``.
+            TypeError: For an operator other than ``-`` or ``+``.
+        """
+        value = self.evaluate(node.operand)
+        if node.op == "-":
+            return self._checked(-value, node.pos)
+        if node.op == "+":
+            return self._checked(value, node.pos)
+        raise TypeError(f"unknown unary operator: {node.op!r}")
+
+    def _name(self, node: Name) -> int:
+        """Evaluate a variable reference or ``ans``.
+
+        Args:
+            node: The ``Name`` node.
+
+        Returns:
+            The name's stored value.
+
+        Raises:
+            UndefinedNameError: For an unset variable, unset ``ans``, or a
+                built-in name used as a value (with a call hint).
+        """
+        if node.ident in BUILTINS:
+            raise UndefinedNameError(
+                f"'{node.ident}' is a function; call it like "
+                f"{node.ident}(...)",
+                node.pos,
+            )
+        return self.env.get(node.ident, node.pos)
+
+    def _call(self, node: Call) -> int:
+        """Evaluate a built-in call.
+
+        Arity is checked before any argument is evaluated. Arguments then
+        evaluate left to right, so the first failing argument determines the
+        error.
+
+        Args:
+            node: The ``Call`` node.
+
+        Returns:
+            The checked result of the built-in.
+
+        Raises:
+            CallError: Unknown function, non-function call, or wrong arity.
+            IntegerRangeError: When the built-in's result is outside the
+                32-bit range (for example ``abs(INT_MIN)``).
+        """
+        builtin = BUILTINS.get(node.func)
+        if builtin is None:
+            if node.func == "ans" or node.func in self.env.variables:
+                raise CallError(
+                    f"'{node.func}' is a variable, not a function", node.pos
+                )
+            raise CallError(f"unknown function '{node.func}'", node.pos)
+
+        count = len(node.args)
+        if count < builtin.min_args or (
+            builtin.max_args is not None and count > builtin.max_args
+        ):
+            raise CallError(
+                self._arity_message(builtin.name, builtin.min_args, builtin.max_args, count),
+                node.pos,
+            )
+
+        values = [self.evaluate(arg) for arg in node.args]
+        return self._checked(builtin.fn(*values), node.pos)
+
+    @staticmethod
+    def _arity_message(
+        name: str, min_args: int, max_args: int | None, count: int
+    ) -> str:
+        """Build the ``CallError`` message for a wrong argument count.
+
+        Args:
+            name: The built-in's name.
+            min_args: Its minimum arity.
+            max_args: Its maximum arity, or ``None`` when unbounded.
+            count: The number of arguments supplied.
+
+        Returns:
+            A human-readable arity error message.
+        """
+        if max_args == min_args:
+            return f"{name}() takes exactly {min_args} argument(s) ({count} given)"
+        return f"{name}() takes at least {min_args} argument(s) ({count} given)"
+
+    def _assign(self, node: Assign) -> int:
+        """Evaluate an assignment atomically.
+
+        The reserved-target check happens first; the right side is evaluated
+        next; the environment is mutated only after both succeed.
+
+        Args:
+            node: The ``Assign`` node.
+
+        Returns:
+            The assigned value.
+
+        Raises:
+            AssignmentError: When the target is ``ans`` or a built-in name.
+        """
+        if is_reserved(node.target):
+            raise AssignmentError(
+                f"cannot assign to reserved name '{node.target}'", node.pos
+            )
+        value = self.evaluate(node.value)
+        self.env.set(node.target, value)
+        return self._checked(value, node.pos)
diff --git c/tests/test_builtins.py w/tests/test_builtins.py
new file mode 100644
index 0000000..f3e8a94
--- /dev/null
+++ w/tests/test_builtins.py
@@ -0,0 +1,132 @@
+"""Unit tests for MiniCalc built-ins and reserved names (FEAT-003).
+
+The functions operate on plain Python integers: range checking is the
+evaluator's responsibility, so ``abs(INT_MIN)`` is expected to return
+``2147483648`` here.
+"""
+
+from dataclasses import FrozenInstanceError
+
+import pytest
+
+from minicalc.builtins import BUILTINS, Builtin, is_reserved
+from minicalc.limits import INT_MAX, INT_MIN
+
+
+def test_registry_contents_and_arities() -> None:
+    """The registry holds exactly the four spec built-ins with their arities."""
+    assert set(BUILTINS) == {"abs", "min", "max", "gcd"}
+    assert (BUILTINS["abs"].min_args, BUILTINS["abs"].max_args) == (1, 1)
+    assert (BUILTINS["min"].min_args, BUILTINS["min"].max_args) == (1, None)
+    assert (BUILTINS["max"].min_args, BUILTINS["max"].max_args) == (1, None)
+    assert (BUILTINS["gcd"].min_args, BUILTINS["gcd"].max_args) == (2, 2)
+    for name, builtin in BUILTINS.items():
+        assert builtin.name == name
+        assert isinstance(builtin.doc, str) and builtin.doc
+
+
+def test_builtin_is_frozen() -> None:
+    """``Builtin`` instances are immutable."""
+    with pytest.raises(FrozenInstanceError):
+        BUILTINS["abs"].name = "other"  # type: ignore[misc]
+
+
+@pytest.mark.parametrize(
+    ("value", "expected"),
+    [
+        (0, 0),
+        (5, 5),
+        (-5, 5),
+        (INT_MAX, INT_MAX),
+        (INT_MIN, 2_147_483_648),
+    ],
+)
+def test_abs(value: int, expected: int) -> None:
+    """``abs`` returns a plain non-negative integer, even for ``INT_MIN``."""
+    result = BUILTINS["abs"].fn(value)
+    assert result == expected
+    assert isinstance(result, int)
+
+
+def test_abs_int_min_is_out_of_range_but_plain_int() -> None:
+    """Range checking is deliberately left to the evaluator."""
+    result = BUILTINS["abs"].fn(INT_MIN)
+    assert result == 2_147_483_648
+    assert result > INT_MAX
+
+
+@pytest.mark.parametrize("name", ["min", "max"])
+def test_min_max_require_at_least_one_argument(name: str) -> None:
+    """The registry advertises an unbounded maximum and a minimum of one."""
+    assert BUILTINS[name].min_args == 1
+    assert BUILTINS[name].max_args is None
+
+
+@pytest.mark.parametrize(
+    ("values", "expected"),
+    [
+        ((4,), 4),
+        ((3, 1, 2), 1),
+        ((-3, -1, -4), -4),
+        ((INT_MAX, INT_MIN, 0), INT_MIN),
+    ],
+)
+def test_min(values: tuple[int, ...], expected: int) -> None:
+    """``min`` returns the smallest argument for any arity >= 1."""
+    assert BUILTINS["min"].fn(*values) == expected
+
+
+@pytest.mark.parametrize(
+    ("values", "expected"),
+    [
+        ((4,), 4),
+        ((3, 1, 2), 3),
+        ((-3, -1, -4), -1),
+        ((INT_MAX, INT_MIN, 0), INT_MAX),
+    ],
+)
+def test_max(values: tuple[int, ...], expected: int) -> None:
+    """``max`` returns the largest argument for any arity >= 1."""
+    assert BUILTINS["max"].fn(*values) == expected
+
+
+@pytest.mark.parametrize(
+    ("a", "b", "expected"),
+    [
+        (0, 0, 0),
+        (0, 5, 5),
+        (5, 0, 5),
+        (12, 18, 6),
+        (-4, 6, 2),
+        (4, -6, 2),
+        (-4, -6, 2),
+        (-1, 1, 1),
+        (7, 13, 1),
+        (INT_MIN, 2, 2),
+    ],
+)
+def test_gcd_signs_and_zeros(a: int, b: int, expected: int) -> None:
+    """``gcd`` uses absolute values and always returns a non-negative int."""
+    result = BUILTINS["gcd"].fn(a, b)
+    assert result == expected
+    assert result >= 0
+    assert isinstance(result, int)
+
+
+def test_gcd_is_symmetric() -> None:
+    """``gcd(a, b) == gcd(b, a)`` across sign combinations."""
+    fn = BUILTINS["gcd"].fn
+    for a, b in [(12, 18), (-12, 18), (12, -18), (-12, -18), (0, 9), (9, 0)]:
+        assert fn(a, b) == fn(b, a)
+
+
+@pytest.mark.parametrize("name", ["ans", "abs", "min", "max", "gcd"])
+def test_reserved_names(name: str) -> None:
+    """``ans`` and every built-in name are reserved."""
+    assert is_reserved(name)
+
+
+@pytest.mark.parametrize("name", ["x", "Ans", "ABS", "answer", "_abs", "minimum"])
+def test_non_reserved_names(name: str) -> None:
+    """Reserved-name matching is case-sensitive and exact."""
+    assert not is_reserved(name)
diff --git c/tests/test_evaluator.py w/tests/test_evaluator.py
new file mode 100644
index 0000000..fed5392
--- /dev/null
+++ w/tests/test_evaluator.py
@@ -0,0 +1,487 @@
+"""Unit tests for the MiniCalc evaluator (FEAT-003).
+
+Every AST node is built by hand through the small helpers below, so these
+tests do not depend on the lexer or parser. Positions are chosen to match the
+source text used in the language spec wherever the error column matters.
+"""
+
+import time
+
+import pytest
+
+from minicalc.ast_nodes import Assign, Binary, Call, Name, Node, Number, Unary
+from minicalc.environment import Environment
+from minicalc.errors import (
+    AssignmentError,
+    CallError,
+    DivisionByZeroError,
+    DomainError,
+    IntegerRangeError,
+    SourcePos,
+    UndefinedNameError,
+)
+from minicalc.evaluator import Evaluator
+from minicalc.limits import INT_MAX, INT_MIN
+
+
+def p(col: int) -> SourcePos:
+    """Return a position on line 1 at ``col``."""
+    return SourcePos(1, col)
+
+
+def n(value: int, col: int = 1) -> Number:
+    """Build a number literal node."""
+    return Number(value, p(col))
+
+
+def nm(ident: str, col: int = 1) -> Name:
+    """Build a name node."""
+    return Name(ident, p(col))
+
+
+def u(op: str, operand: Node, col: int = 1) -> Unary:
+    """Build a unary node."""
+    return Unary(op, operand, p(col))  # type: ignore[arg-type]
+
+
+def b(op: str, left: Node, right: Node, col: int = 3) -> Binary:
+    """Build a binary node; the default operator column is 3."""
+    return Binary(op, left, right, p(col))  # type: ignore[arg-type]
+
+
+def call(func: str, *args: Node, col: int = 1) -> Call:
+    """Build a call node whose position is the function name."""
+    return Call(func, tuple(args), p(col))
+
+
+def assign(target: str, value: Node, col: int = 1) -> Assign:
+    """Build an assignment node whose position is the target name."""
+    return Assign(target, value, p(col))
+
+
+def neg(value: int, col: int = 1) -> Unary:
+    """Build ``-value`` as unary minus over a non-negative literal."""
+    return u("-", n(value, col + 1), col)
+
+
+def int_min() -> Binary:
+    """Build ``-2147483647 - 1``, the only way to spell ``INT_MIN``."""
+    return b("-", u("-", n(2147483647, 2), 1), n(1, 14), 12)
+
+
+def evaluate(node: Node, env: Environment | None = None) -> int:
+    """Evaluate ``node`` in a fresh environment unless one is supplied."""
+    return Evaluator(env if env is not None else Environment()).evaluate(node)
+
+
+# --- Worked examples from language-spec section 5 -------------------------
+
+WORKED_EXAMPLES = [
+    pytest.param(b("+", n(2), b("*", n(3), n(4))), 14, id="2+3*4"),
+    pytest.param(b("*", b("+", n(2), n(3)), n(4)), 20, id="(2+3)*4"),
+    pytest.param(b("-", b("-", n(10), n(3)), n(2)), 5, id="10-3-2"),
+    pytest.param(u("-", b("**", n(2), n(2)), 1), -4, id="-2**2"),
+    pytest.param(b("**", n(2), b("**", n(3), n(2))), 512, id="2**3**2"),
+    pytest.param(b("**", n(2), n(30)), 1073741824, id="2**30"),
+    pytest.param(b("/", n(7), n(2)), 3, id="7/2"),
+    pytest.param(b("/", u("-", n(7)), n(2)), -3, id="-7/2"),
+    pytest.param(b("//", n(7), n(2)), 3, id="7//2"),
+    pytest.param(b("//", u("-", n(7)), n(2)), -4, id="-7//2"),
+    pytest.param(b("%", u("-", n(7)), n(2)), 1, id="-7%2"),
+    pytest.param(b("%", n(7), u("-", n(2))), -1, id="7%-2"),
+    pytest.param(b("%", u("-", n(7)), u("-", n(2))), -1, id="-7%-2"),
+    pytest.param(b(">", n(5), n(3)), 1, id="5>3"),
+    pytest.param(b("==", n(5), n(4)), 0, id="5==4"),
+    pytest.param(b("==", b("+", n(2), n(3)), n(5)), 1, id="2+3==5"),
+    pytest.param(int_min(), INT_MIN, id="INT_MIN"),
+]
+
+
+@pytest.mark.parametrize(("node", "expected"), WORKED_EXAMPLES)
+def test_worked_examples(node: Node, expected: int) -> None:
+    """Every row of the language-spec worked-examples table evaluates."""
+    assert evaluate(node) == expected
+
+
+# --- Evaluation-error examples from the spec ------------------------------
+
+EVALUATION_ERRORS = [
+    pytest.param(b("/", n(5, 1), n(0, 5), 3), DivisionByZeroError, 3, id="5/0"),
+    pytest.param(b("//", n(5, 1), n(0, 6), 3), DivisionByZeroError, 3, id="5//0"),
+    pytest.param(b("%", n(5, 1), n(0, 5), 3), DivisionByZeroError, 3, id="5%0"),
+    pytest.param(b("**", n(2, 1), n(31, 6), 3), IntegerRangeError, 3, id="2**31"),
+    pytest.param(b("**", n(2, 1), neg(1, 6), 3), DomainError, 3, id="2**-1"),
+    pytest.param(b("+", n(INT_MAX, 1), n(1, 14), 12), IntegerRangeError, 12, id="max+1"),
+    pytest.param(b("*", n(INT_MAX, 1), n(2, 14), 12), IntegerRangeError, 12, id="max*2"),
+    pytest.param(b("-", n(INT_MIN, 1), n(1, 14), 13), IntegerRangeError, 13, id="min-1"),
+]
+
+
+@pytest.mark.parametrize(("node", "error_type", "col"), EVALUATION_ERRORS)
+def test_evaluation_errors_class_and_column(
+    node: Node, error_type: type[Exception], col: int
+) -> None:
+    """Every evaluation-error example reports the documented class and column."""
+    with pytest.raises(error_type) as info:
+        evaluate(node)
+    assert info.value.pos == p(col)
+
+
+def test_zero_divisor_checked_before_range_for_division() -> None:
+    """``INT_MIN / 0`` is a division error, not a range error."""
+    with pytest.raises(DivisionByZeroError):
+        evaluate(b("/", int_min(), n(0)))
+
+
+def test_int_min_divided_by_minus_one_is_range_error() -> None:
+    """``INT_MIN / -1`` overflows the 32-bit range."""
+    with pytest.raises(IntegerRangeError) as info:
+        evaluate(b("/", int_min(), neg(1), 12))
+    assert info.value.pos == p(12)
+
+
+def test_int_min_floor_divided_by_minus_one_is_range_error() -> None:
+    """``INT_MIN // -1`` overflows the 32-bit range."""
+    with pytest.raises(IntegerRangeError) as info:
+        evaluate(b("//", int_min(), neg(1), 12))
+    assert info.value.pos == p(12)
+
+
+def test_int_min_modulo_minus_one_is_zero() -> None:
+    """Floored modulo of ``INT_MIN`` by ``-1`` is in range and zero."""
+    assert evaluate(b("%", int_min(), neg(1), 12)) == 0
+
+
+def test_negating_int_min_is_range_error() -> None:
+    """``-INT_MIN`` fails at the unary operator position."""
+    with pytest.raises(IntegerRangeError) as info:
+        evaluate(u("-", int_min(), 1))
+    assert info.value.pos == p(1)
+
+
+# --- Truncation, floor, and floored modulo --------------------------------
+
+
+@pytest.mark.parametrize(
+    ("left", "right", "expected"),
+    [
+        (7, 2, 3),
+        (-7, 2, -3),
+        (7, -2, -3),
+        (-7, -2, 3),
+        (6, 2, 3),
+        (-6, 2, -3),
+    ],
+)
+def test_slash_truncates_toward_zero(left: int, right: int, expected: int) -> None:
+    """``/`` truncates toward zero for every sign combination."""
+    assert evaluate(b("/", n(left), n(right))) == expected
+
+
+@pytest.mark.parametrize("left", [-7, -3, -2, -1, 1, 2, 3, 7])
+@pytest.mark.parametrize("right", [-3, -2, -1, 1, 2, 3])
+def test_division_modulo_identity_grid(left: int, right: int) -> None:
+    """``a == (a // b) * b + a % b`` and ``%`` takes the divisor's sign."""
+    env = Environment()
+    quotient = evaluate(b("//", n(left), n(right)), env)
+    remainder = evaluate(b("%", n(left), n(right)), env)
+    truncated = evaluate(b("/", n(left), n(right)), env)
+
+    assert quotient == left // right
+    assert remainder == left % right
+    if remainder != 0:
+        assert (remainder < 0) == (right < 0)
+    assert left == quotient * right + remainder
+
+    expected_truncated = abs(left) // abs(right)
+    if (left < 0) != (right < 0):
+        expected_truncated = -expected_truncated
+    assert truncated == expected_truncated
+
+
+# --- Exponentiation edge cases --------------------------------------------
+
+
+@pytest.mark.parametrize(
+    ("base", "exponent", "expected"),
+    [
+        (0, 0, 1),
+        (0, 5, 0),
+        (1, 1_000_000, 1),
+        (-1, 3, -1),
+        (-1, 4, 1),
+        (2, 30, 1_073_741_824),
+        (-2, 31, INT_MIN),
+        (-1, 0, 1),
+    ],
+)
+def test_power_edge_cases(base: int, exponent: int, expected: int) -> None:
+    """``**`` follows the spec's exact zero/one/minus-one rules."""
+    base_node: Node = neg(-base, 2) if base < 0 else n(base)
+    if exponent < 0:
+        exponent_node: Node = neg(-exponent, 6)
+    else:
+        exponent_node = n(exponent, 6)
+    assert evaluate(b("**", base_node, exponent_node)) == expected
+
+
+@pytest.mark.parametrize(
+    ("base", "exponent"),
+    [
+        (2, 31),
+        (-2, 32),
+        (2, -1),
+        (3, -1),
+        (7, 32),
+    ],
+)
+def test_power_errors(base: int, exponent: int) -> None:
+    """Oversized and negative exponents raise the documented errors."""
+    base_node: Node = neg(-base, 2) if base < 0 else n(base)
+    if exponent < 0:
+        exponent_node: Node = neg(-exponent, 6)
+        error_type: type[Exception] = DomainError
+    else:
+        exponent_node = n(exponent, 6)
+        error_type = IntegerRangeError
+    with pytest.raises(error_type) as info:
+        evaluate(b("**", base_node, exponent_node, 3))
+    assert info.value.pos == p(3)
+
+
+def test_huge_power_fails_quickly() -> None:
+    """``2 ** 1000000000`` short-circuits well under 0.5 seconds."""
+    start = time.perf_counter()
+    with pytest.raises(IntegerRangeError) as info:
+        evaluate(b("**", n(2), n(1_000_000_000), 3))
+    elapsed = time.perf_counter() - start
+    assert info.value.pos == p(3)
+    assert elapsed < 0.5
+
+
+# --- Unary ----------------------------------------------------------------
+
+
+def test_unary_plus_is_identity() -> None:
+    """``+x`` returns ``x`` including ``INT_MIN``."""
+    assert evaluate(u("+", n(5))) == 5
+    assert evaluate(u("+", int_min())) == INT_MIN
+
+
+def test_double_unary_minus() -> None:
+    """Nested unary minus composes."""
+    assert evaluate(u("-", u("-", n(5)))) == 5
+
+
+# --- Names, variables, and ans --------------------------------------------
+
+
+def test_variable_lookup() -> None:
+    """A set variable evaluates to its value."""
+    env = Environment()
+    env.set("x", 7)
+    assert evaluate(nm("x"), env) == 7
+
+
+def test_unset_variable_error_at_name() -> None:
+    """An unset variable raises at the identifier's position."""
+    with pytest.raises(UndefinedNameError) as info:
+        evaluate(nm("x", 4))
+    assert info.value.pos == p(4)
+
+
+def test_unset_ans_error() -> None:
+    """``ans`` is undefined before the first successful statement."""
+    with pytest.raises(UndefinedNameError) as info:
+        evaluate(nm("ans", 2))
+    assert info.value.pos == p(2)
+
+
+def test_ans_reads_recorded_value() -> None:
+    """``ans`` reads the value recorded by the facade."""
+    env = Environment()
+    env.record_result(42)
+    assert evaluate(nm("ans"), env) == 42
+
+
+@pytest.mark.parametrize("builtin_name", ["abs", "min", "max", "gcd"])
+def test_builtin_name_as_value_has_call_hint(builtin_name: str) -> None:
+    """Using a built-in without parentheses raises with a call hint."""
+    with pytest.raises(UndefinedNameError) as info:
+        evaluate(nm(builtin_name, 5))
+    assert info.value.pos == p(5)
+    assert str(info.value) == (
+        f"'{builtin_name}' is a function; call it like {builtin_name}(...)"
+    )
+
+
+# --- Calls and built-ins --------------------------------------------------
+
+
+@pytest.mark.parametrize(
+    ("func", "args"),
+    [
+        ("abs", ()),
+        ("abs", (n(1), n(2))),
+        ("gcd", ()),
+        ("gcd", (n(1),)),
+        ("gcd", (n(1), n(2), n(3))),
+        ("min", ()),
+        ("max", ()),
+    ],
+)
+def test_wrong_arity_is_call_error(func: str, args: tuple[Node, ...]) -> None:
+    """Every arity violation raises ``CallError`` at the function name."""
+    with pytest.raises(CallError) as info:
+        evaluate(call(func, *args, col=7))
+    assert info.value.pos == p(7)
+
+
+def test_arity_checked_before_arguments() -> None:
+    """A wrong arity wins over an already-failing argument."""
+    with pytest.raises(CallError) as info:
+        evaluate(call("abs", b("/", n(1), n(0)), n(2), col=1))
+    assert info.value.pos == p(1)
+
+
+@pytest.mark.parametrize(
+    ("node", "expected"),
+    [
+        pytest.param(call("abs", neg(5)), 5, id="abs"),
+        pytest.param(call("min", n(3), n(1), n(2)), 1, id="min"),
+        pytest.param(call("max", neg(3), neg(1), neg(4)), -1, id="max"),
+        pytest.param(call("max", n(9)), 9, id="max-one-arg"),
+        pytest.param(call("gcd", n(12), n(18)), 6, id="gcd"),
+    ],
+)
+def test_builtin_calls_succeed(node: Node, expected: int) -> None:
+    """Calls evaluate their arguments and return the built-in result."""
+    assert evaluate(node) == expected
+
+
+def test_abs_int_min_is_range_error_at_call() -> None:
+    """``abs(INT_MIN)`` fails the range check at the call position."""
+    with pytest.raises(IntegerRangeError) as info:
+        evaluate(call("abs", int_min(), col=4))
+    assert info.value.pos == p(4)
+
+
+def test_gcd_int_min_zero_is_range_error() -> None:
+    """The true ``gcd(INT_MIN, 0)`` is out of range and fails the call check."""
+    with pytest.raises(IntegerRangeError):
+        evaluate(call("gcd", int_min(), n(0)))
+
+
+def test_arguments_evaluated_left_to_right_first_failure_wins() -> None:
+    """The leftmost failing argument determines the call's error."""
+    with pytest.raises(DivisionByZeroError) as info:
+        evaluate(
+            call(
+                "max",
+                b("/", n(1), n(0), 10),
+                b("+", n(INT_MAX), n(1), 20),
+            )
+        )
+    assert info.value.pos == p(10)
+
+    with pytest.raises(IntegerRangeError) as info:
+        evaluate(
+            call(
+                "max",
+                b("+", n(INT_MAX), n(1), 10),
+                b("/", n(1), n(0), 20),
+            )
+        )
+    assert info.value.pos == p(10)
+
+
+def test_call_unknown_function() -> None:
+    """An unknown name raises ``CallError`` at the name."""
+    with pytest.raises(CallError) as info:
+        evaluate(call("foo", n(1), col=3))
+    assert info.value.pos == p(3)
+    assert str(info.value) == "unknown function 'foo'"
+
+
+def test_call_variable_is_not_a_function() -> None:
+    """Calling a variable raises a specific ``CallError``."""
+    env = Environment()
+    env.set("x", 5)
+    with pytest.raises(CallError) as info:
+        evaluate(call("x", n(1), col=2), env)
+    assert info.value.pos == p(2)
+    assert str(info.value) == "'x' is a variable, not a function"
+
+
+def test_call_ans_is_not_a_function() -> None:
+    """Calling ``ans`` raises ``CallError`` at the name."""
+    env = Environment()
+    env.record_result(5)
+    with pytest.raises(CallError) as info:
+        evaluate(call("ans", col=6), env)
+    assert info.value.pos == p(6)
+
+
+# --- Assignment -----------------------------------------------------------
+
+
+def test_assignment_binds_after_success() -> None:
+    """A successful assignment binds the target and returns the value."""
+    env = Environment()
+    assert evaluate(assign("x", b("+", n(1), n(2)), 1), env) == 3
+    assert env.variables == {"x": 3}
+    assert env.ans is None
+
+
+def test_failed_right_side_does_not_bind_new_name() -> None:
+    """A failing right side never creates the target binding."""
+    env = Environment()
+    with pytest.raises(IntegerRangeError):
+        evaluate(assign("y", b("+", n(INT_MAX), n(1))), env)
+    assert env.variables == {}
+
+
+def test_failed_assignment_preserves_existing_value() -> None:
+    """A failing reassignment leaves the old value untouched."""
+    env = Environment()
+    env.set("x", 11)
+    with pytest.raises(DivisionByZeroError):
+        evaluate(assign("x", b("/", n(1), n(0))), env)
+    assert env.variables == {"x": 11}
+
+
+@pytest.mark.parametrize("target", ["ans", "abs", "min", "max", "gcd"])
+def test_assignment_to_reserved_name_fails(target: str) -> None:
+    """Assigning to a reserved name raises ``AssignmentError`` at the target."""
+    env = Environment()
+    with pytest.raises(AssignmentError) as info:
+        evaluate(assign(target, n(1), col=9), env)
+    assert info.value.pos == p(9)
+    assert env.variables == {}
+
+
+def test_reserved_check_precedes_right_side() -> None:
+    """A reserved target fails before a failing right side is evaluated."""
+    with pytest.raises(AssignmentError):
+        evaluate(assign("ans", b("/", n(1), n(0), 5), 1))
+
+
+# --- Programming errors ---------------------------------------------------
+
+
+def test_unknown_node_type_raises_type_error() -> None:
+    """An unsupported AST object is a programming error, not a MiniCalcError."""
+    with pytest.raises(TypeError):
+        Evaluator(Environment()).evaluate(object())  # type: ignore[arg-type]
+
+
+def test_unknown_binary_operator_raises_type_error() -> None:
+    """An operator outside the locked ``Op`` set is a programming error."""
+    with pytest.raises(TypeError):
+        evaluate(Binary("^", n(1), n(2), p(3)))  # type: ignore[arg-type]
+
+
+def test_unknown_unary_operator_raises_type_error() -> None:
+    """An unsupported unary operator is a programming error."""
+    with pytest.raises(TypeError):
+        evaluate(Unary("~", n(1), p(1)))  # type: ignore[arg-type]
```

---

## 6. Flagged for APC / Operator Attention

- [ ] **`gcd` result range edge:** `gcd(INT_MIN, 0)` (and
  `gcd(INT_MIN, INT_MIN)`) is mathematically `2147483648`, which is outside
  the signed 32-bit range. The spec says every produced value is
  range-checked, so the evaluator reports `IntegerRangeError` at the call.
  This is the conservative reading; the spec does not call the case out
  explicitly. Same reasoning applies to `abs(INT_MIN)`, which the spec does
  call out.
- [ ] **Built-in call messages:** `ans(...)` is reported as
  `'ans' is a variable, not a function`. Message text is not compared by
  golden tests; class and column follow the spec.
- [ ] No other discrepancies were found between the prompt, the spec, the
  interface contract, and the code on disk.
