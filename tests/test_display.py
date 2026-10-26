"""Tests for ``minicalc.display``: plain and ANSI-styled rendering."""

import re

import pytest

from minicalc.display import (
    banner,
    format_outcome,
    format_result,
    help_text,
    use_color,
)
from minicalc.errors import LexError, SourcePos
from minicalc.interpreter import LineOutcome, Result

ANSI = re.compile(r"\x1b\[[0-9;]*m")
RULE = "-" * 44


class _Stream:
    """A minimal text stream stand-in.

    Attributes:
        tty: The value returned by ``isatty``.
    """

    def __init__(self, tty: bool) -> None:
        """Store the fake terminal status.

        Args:
            tty: Whether the stream claims to be a terminal.
        """
        self.tty = tty

    def isatty(self) -> bool:
        """Report the configured terminal status."""
        return self.tty


class _BrokenStream:
    """A stream whose ``isatty`` always raises.

    Attributes:
        None.
    """

    def isatty(self) -> bool:
        """Raise, as an unusual stream might."""
        raise OSError("no tty here")


def _plain(text: str) -> str:
    """Strip ANSI escape sequences from ``text``."""
    return ANSI.sub("", text)


def test_use_color_requires_a_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    """A TTY without NO_COLOR enables color."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert use_color(_Stream(True)) is True


def test_use_color_is_false_off_a_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-TTY never enables color."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert use_color(_Stream(False)) is False


def test_use_color_respects_no_color(monkeypatch: pytest.MonkeyPatch) -> None:
    """NO_COLOR disables color even on a TTY, including when empty."""
    monkeypatch.setenv("NO_COLOR", "1")
    assert use_color(_Stream(True)) is False
    monkeypatch.setenv("NO_COLOR", "")
    assert use_color(_Stream(True)) is False


def test_use_color_tolerates_streams_without_isatty() -> None:
    """Objects without ``isatty`` are treated as plain streams."""
    assert use_color(object()) is False  # type: ignore[arg-type]


def test_use_color_tolerates_a_raising_isatty() -> None:
    """A raising ``isatty`` is treated as a non-TTY."""
    assert use_color(_BrokenStream()) is False  # type: ignore[arg-type]


def test_format_result_value_assignment_and_empty() -> None:
    """Plain results use the exact contract forms."""
    assert format_result(Result("value", 42)) == "= 42"
    assert format_result(Result("assign", 7, "x")) == "x = 7"
    assert format_result(Result("empty")) == ""


def test_format_result_colors_only_the_value() -> None:
    """Color mode wraps the value in bold green and leaves the name plain."""
    assert format_result(Result("value", 42), color=True) == (
        "= \x1b[1;32m42\x1b[0m"
    )
    assert format_result(Result("assign", 7, "x"), color=True) == (
        "x = \x1b[1;32m7\x1b[0m"
    )


def test_format_outcome_value_and_assignment() -> None:
    """Script outcomes prefix results with their 1-based line number."""
    assert format_outcome(LineOutcome(3, "42", Result("value", 42), None)) == (
        "line 3: = 42"
    )
    assert format_outcome(
        LineOutcome(4, "x = 7", Result("assign", 7, "x"), None)
    ) == "line 4: x = 7"


def test_format_outcome_empty_is_blank() -> None:
    """Empty lines and blank comments produce no script output."""
    assert format_outcome(LineOutcome(2, "", Result("empty"), None)) == ""
    assert format_outcome(LineOutcome(2, "# note", Result("empty"), None)) == ""


def test_format_outcome_error_uses_render() -> None:
    """Errors delegate to ``render`` so the caret and position are kept."""
    error = LexError("illegal character '@'", SourcePos(3, 5)).with_source("2 + @")
    outcome = LineOutcome(3, "2 + @", None, error)
    assert format_outcome(outcome) == error.render(False)
    assert format_outcome(outcome, color=True) == error.render(True)


def test_banner_exact_plain_text() -> None:
    """The banner is exactly two 44-character rules and two text lines."""
    expected = "\n".join(
        (
            RULE,
            "MiniCalc 1.0  integer arithmetic language",
            "Type :help for help, :quit to exit.",
            RULE,
        )
    )
    assert banner() == expected
    lines = banner().splitlines()
    assert lines[0] == RULE and lines[-1] == RULE
    assert "\x1b" not in banner()


def test_banner_color_strips_to_plain() -> None:
    """Coloring the banner changes only escape codes, not the text."""
    assert "\x1b[" in banner(color=True)
    assert _plain(banner(color=True)) == banner()


def test_help_text_has_all_sections_and_examples() -> None:
    """Help covers operators, functions, names, commands, and three examples."""
    text = help_text()
    assert "\x1b" not in text
    headings = re.findall(r"^(Operators.*|Functions|Names|Commands|Examples)$",
                          text, re.MULTILINE)
    assert headings == [
        "Operators (highest to lowest)",
        "Functions",
        "Names",
        "Commands",
        "Examples",
    ]
    assert len(text.split("\n\n")) == 5
    assert "abs(x)" in text and "gcd(a, b)" in text
    assert ":help" in text and ":vars" in text
    assert "2 + 3 * 4" in text and "gcd(12, 18)" in text


def test_help_text_precedence_is_high_to_low() -> None:
    """The operator rows appear from level 1 down to level 6."""
    text = help_text()
    positions = [text.index(f"  {level}  ") for level in range(1, 7)]
    assert positions == sorted(positions)


def test_help_text_columns_are_aligned() -> None:
    """Every help row puts its description in the same column."""
    rows = [
        line
        for line in help_text().splitlines()
        if line.startswith("  ") and len(line) > 24
    ]
    assert rows
    for line in rows:
        assert line[23] == " "
        assert line[24] != " "


def test_help_text_color_strips_to_plain() -> None:
    """Colored help has the same text as plain help."""
    assert "\x1b[" in help_text(color=True)
    assert _plain(help_text(color=True)) == help_text()
