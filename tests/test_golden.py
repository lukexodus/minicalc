"""Run every ``tests/golden/<stem>.mc`` file against its ``<stem>.out`` (CORE-002).

Skipped until CORE-003 provides ``minicalc.interpreter``. Each case runs the
whole file through one fresh ``Interpreter`` so state carries across lines.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from golden_format import canonical_line

if importlib.util.find_spec("minicalc.interpreter") is None:
    pytest.skip("minicalc.interpreter arrives in CORE-003", allow_module_level=True)

from minicalc.interpreter import Interpreter  # noqa: E402  (after the skip guard)

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
MC_FILES = sorted(GOLDEN_DIR.glob("*.mc"))


def _read_expected(path: Path) -> list[str]:
    """Read a ``.out`` file and drop trailing blank lines.

    Args:
        path: The expected-output file.

    Returns:
        Expected lines in order, without a trailing blank block.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _format_mismatch(mc_path: Path, expected: list[str], actual: list[str],
                     outcomes: list[object]) -> str:
    """Build a readable report for a golden mismatch.

    Args:
        mc_path: The golden input file.
        expected: Lines read from the ``.out`` file.
        actual: Canonical lines produced by the interpreter.
        outcomes: The interpreter outcomes that produced ``actual``.

    Returns:
        A multi-line failure message naming each differing index.
    """
    report = [f"Golden mismatch: {mc_path}"]
    total = max(len(expected), len(actual))
    for index in range(total):
        want = expected[index] if index < len(expected) else "<missing expected line>"
        got = actual[index] if index < len(actual) else "<missing actual line>"
        if want == got:
            continue
        if index < len(outcomes):
            outcome = outcomes[index]
            line_no = getattr(outcome, "line_no", "?")
            source = getattr(outcome, "source", "")
            location = f"file line {line_no}"
        else:
            source = ""
            location = "past end of source"
        report.append(f"  index {index} ({location}): source {source!r}")
        report.append(f"    expected: {want}")
        report.append(f"    actual:   {got}")
    report.append(f"Expected {len(expected)} line(s), got {len(actual)}.")
    return "\n".join(report)


@pytest.mark.parametrize("mc_path", MC_FILES, ids=[path.stem for path in MC_FILES])
def test_golden_file(mc_path: Path) -> None:
    """One golden input must reproduce its expected canonical output.

    Args:
        mc_path: The ``.mc`` file selected by the parametrization.
    """
    out_path = mc_path.with_suffix(".out")
    if not out_path.is_file():
        pytest.fail(f"Missing golden expected file: {out_path}", pytrace=False)

    text = mc_path.read_text(encoding="utf-8")
    outcomes = Interpreter().run_source(text)
    actual = [line for line in (canonical_line(item) for item in outcomes) if line is not None]
    kept_outcomes = [
        outcome for outcome in outcomes if canonical_line(outcome) is not None
    ]
    expected = _read_expected(out_path)

    if actual != expected:
        pytest.fail(
            _format_mismatch(mc_path, expected, actual, kept_outcomes),
            pytrace=False,
        )
