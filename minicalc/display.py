"""User-facing formatting for MiniCalc results, banners, and help text.

All rendering is ASCII-safe. Styling uses plain ANSI escape codes ([D-02])
and is applied only when the caller asks for color; plain output never
contains escape sequences.
"""

from __future__ import annotations

import os
from typing import TextIO

from .interpreter import LineOutcome, Result

#: Bold green, used for produced values.
_BOLD_GREEN = "\x1b[1;32m"
#: Bold cyan, used for banner titles and help section headings.
_BOLD_CYAN = "\x1b[1;36m"
#: Dim, used for the banner's hint line.
_DIM = "\x1b[2m"
#: Reset all ANSI attributes.
_RESET = "\x1b[0m"
#: Width of the banner rules.
_RULE_WIDTH = 44
#: Column width for the left side of aligned help rows.
_HELP_COLUMN = 20


def use_color(stream: TextIO) -> bool:
    """Decide whether ANSI styling may be written to ``stream``.

    Args:
        stream: The output stream to inspect. Streams without an ``isatty``
            attribute, or whose ``isatty`` raises, are treated as non-TTYs.

    Returns:
        True only when ``stream.isatty()`` is true and the ``NO_COLOR``
        environment variable is absent ([D-09]).
    """
    try:
        isatty = getattr(stream, "isatty", None)
        if not callable(isatty) or not isatty():
            return False
    except Exception:
        return False
    return "NO_COLOR" not in os.environ


def _paint(text: str, code: str, color: bool) -> str:
    """Wrap ``text`` in an ANSI code when ``color`` is true.

    Args:
        text: The plain text to style.
        code: The ANSI sequence that starts the style.
        color: Whether styling is enabled.

    Returns:
        The styled text, or ``text`` unchanged.
    """
    if not color:
        return text
    return f"{code}{text}{_RESET}"


def format_result(result: Result, color: bool = False) -> str:
    """Format one successful result for interactive or one-shot output.

    Args:
        result: The result returned by ``Interpreter.run_line``.
        color: Whether to render the value in bold green.

    Returns:
        ``"= 42"`` for a value, ``"x = 7"`` for an assignment, or ``""``
        for an empty line.
    """
    if result.kind == "empty":
        return ""
    value = _paint(str(result.value), _BOLD_GREEN, color)
    if result.kind == "assign":
        return f"{result.name} = {value}"
    return f"= {value}"


def format_outcome(outcome: LineOutcome, color: bool = False) -> str:
    """Format one script-mode line outcome, prefixed with its line number.

    Args:
        outcome: One item from ``Interpreter.run_source``.
        color: Whether to style values and error carets.

    Returns:
        ``"line 3: = 42"`` or ``"line 4: x = 7"`` for results, ``""`` for an
        empty line, and ``outcome.error.render(color)`` for an error.
    """
    if outcome.error is not None:
        return outcome.error.render(color)
    if outcome.result is None:
        return ""
    formatted = format_result(outcome.result, color)
    if not formatted:
        return ""
    return f"line {outcome.line_no}: {formatted}"


def banner(color: bool = False) -> str:
    """Build the REPL welcome banner.

    The plain form is four lines: a 44-character rule, the title, the hint,
    and another rule. Only the title and hint are styled in color mode.

    Args:
        color: Whether to style the title and hint.

    Returns:
        The banner text without a trailing newline.
    """
    rule = "-" * _RULE_WIDTH
    title = _paint("MiniCalc 1.0  integer arithmetic language", _BOLD_CYAN, color)
    hint = _paint("Type :help for help, :quit to exit.", _DIM, color)
    return "\n".join((rule, title, hint, rule))


def _section(title: str, rows: list[tuple[str, str]], color: bool) -> str:
    """Render one help section with aligned left and right columns.

    Args:
        title: The section heading (styled bold cyan in color mode).
        rows: ``(left, right)`` pairs; the left column is padded.
        color: Whether to style the heading.

    Returns:
        The heading and its indented rows, without a trailing newline.
    """
    heading = _paint(title, _BOLD_CYAN, color)
    body = "\n".join(
        f"  {left:<{_HELP_COLUMN}}  {right}" for left, right in rows
    )
    return f"{heading}\n{body}"


def help_text(color: bool = False) -> str:
    """Build the ``:help`` reference.

    Args:
        color: Whether to style section headings.

    Returns:
        Five sections separated by blank lines: operator precedence (highest
        to lowest), functions, names, commands, and three examples.
    """
    operators = [
        ("1  ( )", "grouping, function calls"),
        ("2  **", "exponentiation (right-associative)"),
        ("3  - +", "unary sign (prefix)"),
        ("4  * / // %", "multiplication, division, modulo (left)"),
        ("5  + -", "addition, subtraction (left)"),
        ("6  == != < <= > >=", "comparison (cannot chain)"),
    ]
    functions = [
        ("abs(x)", "absolute value"),
        ("min(a, b, ...)", "smallest argument"),
        ("max(a, b, ...)", "largest argument"),
        ("gcd(a, b)", "greatest common divisor"),
    ]
    names = [
        ("x = 7", "assign the value to a name"),
        ("ans", "value of the last successful statement"),
    ]
    commands = [
        (":help", "show this help"),
        (":vars", "list ans and variables"),
        (":clear", "remove all variables and ans"),
        (":quit, :q", "exit the REPL"),
    ]
    examples = [
        ("2 + 3 * 4", "= 14"),
        ("x = 7", "x = 7"),
        ("gcd(12, 18)", "= 6"),
    ]
    return "\n\n".join(
        (
            _section("Operators (highest to lowest)", operators, color),
            _section("Functions", functions, color),
            _section("Names", names, color),
            _section("Commands", commands, color),
            _section("Examples", examples, color),
        )
    )
