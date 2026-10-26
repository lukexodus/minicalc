"""Command-line entry point: REPL, script file, and ``-e`` modes ([D-09]).

Exit codes are 0 for success, 1 when a MiniCalc error occurred (or an
unexpected internal error was reported), and 2 for usage or file-read errors.
Foreign exceptions are reported as ``Internal error:`` lines so no traceback
is shown to the user.
"""

from __future__ import annotations

import argparse
import sys

from .display import format_outcome, format_result, use_color
from .errors import MiniCalcError
from .interpreter import Interpreter
from .repl import Repl


def _build_parser() -> argparse.ArgumentParser:
    """Build the ``minicalc`` argument parser.

    Returns:
        A parser accepting an optional file, ``-e/--expr``, ``--no-color``,
        and ``--version``.
    """
    parser = argparse.ArgumentParser(
        prog="minicalc",
        description="MiniCalc 1.0: a small integer-arithmetic language.",
    )
    parser.add_argument("file", nargs="?", help="run a MiniCalc script file")
    parser.add_argument(
        "-e",
        "--expr",
        metavar="EXPR",
        help="evaluate one expression and exit",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable ANSI colors",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="MiniCalc 1.0.0",
        help="show the version and exit",
    )
    return parser


def _write_stderr(line: str) -> None:
    """Write one error line to stderr without reordering merged streams.

    Pending stdout is flushed first so that, when stdout and stderr share a
    pipe or file (``2>&1``), results produced earlier still appear before this
    error. Stderr is flushed immediately so the error keeps its place.

    Args:
        line: The complete line to write, without a trailing newline.
    """
    sys.stdout.flush()
    print(line, file=sys.stderr, flush=True)


def _internal_error(exc: BaseException) -> str:
    """Describe an unexpected exception on one line.

    Args:
        exc: The exception that escaped.

    Returns:
        A line beginning ``Internal error:`` with the exception type and
        message, or just the type when the message is empty.
    """
    detail = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
    return f"Internal error: {detail}"


def _run_expression(interpreter: Interpreter, expr: str, color: bool) -> int:
    """Evaluate one expression and print its result.

    Args:
        interpreter: The facade to use.
        expr: The expression source.
        color: Whether to style the output.

    Returns:
        0 on success, 1 for a MiniCalc error or an internal error.
    """
    try:
        result = interpreter.run_line(expr)
        formatted = format_result(result, color)
        if formatted:
            print(formatted)
        return 0
    except MiniCalcError as error:
        _write_stderr(error.render(color))
        return 1
    except Exception as exc:
        _write_stderr(_internal_error(exc))
        return 1


def _run_file(interpreter: Interpreter, path: str, color: bool) -> int:
    """Run a UTF-8 script file and report each non-empty outcome.

    Args:
        interpreter: The facade to use.
        path: The script path.
        color: Whether to style values and errors.

    Returns:
        0 when every line succeeded, 1 when any line failed or an internal
        error occurred, or 2 when the file cannot be read as UTF-8 text.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeError) as exc:
        _write_stderr(f"minicalc: cannot read '{path}': {exc}")
        return 2

    try:
        outcomes = interpreter.run_source(text)
    except Exception as exc:
        _write_stderr(_internal_error(exc))
        return 1

    exit_code = 0
    for outcome in outcomes:
        try:
            formatted = format_outcome(outcome, color)
            if not formatted:
                continue
            if outcome.error is not None:
                _write_stderr(formatted)
                exit_code = 1
            else:
                print(formatted)
        except Exception as exc:
            _write_stderr(_internal_error(exc))
            exit_code = 1
    return exit_code


def main(argv: list[str] | None = None) -> int:
    """Run MiniCalc according to the command-line arguments.

    Args:
        argv: Argument list to parse; ``None`` means ``sys.argv[1:]``.

    Returns:
        0 for success, 1 when a MiniCalc or internal error occurred, and 2 for
        usage errors and unreadable or undecodable script files.
    """
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 0

    if args.file is not None and args.expr is not None:
        sys.stdout.flush()
        parser.print_usage(sys.stderr)
        _write_stderr(
            "minicalc: error: a file and -e/--expr cannot be used together"
        )
        return 2

    color = not args.no_color and use_color(sys.stdout)
    interpreter = Interpreter()

    if args.expr is not None:
        return _run_expression(interpreter, args.expr, color)
    if args.file is not None:
        return _run_file(interpreter, args.file, color)
    try:
        return Repl(interpreter, color=color).run()
    except Exception as exc:
        _write_stderr(_internal_error(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
