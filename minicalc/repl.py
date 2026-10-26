"""The interactive MiniCalc REPL and its meta-commands ([D-09]).

``Repl`` talks only to the ``Interpreter`` facade and to injected input and
output callables, which keeps it testable without a terminal. Foreign
exceptions from the facade or from a meta-command are reported as
``Internal error:`` lines and never terminate the session.
"""

from __future__ import annotations

from typing import Callable, ClassVar

from .display import banner, format_result, help_text
from .errors import MiniCalcError
from .interpreter import Interpreter


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


class Repl:
    """Read, evaluate, print, and loop until ``:quit``, EOF, or Ctrl-C.

    Attributes:
        PROMPT (ClassVar[str]): The input prompt, ``"minicalc> "``.
        interpreter: The facade used for every non-meta-command line.
        input_fn: Callable taking the prompt and returning one line; its
            defaults match the built-in ``input``.
        output_fn: Callable receiving one string per output line; its defaults
            match the built-in ``print``.
        color: Whether error rendering and display styling use ANSI codes.
    """

    PROMPT: ClassVar[str] = "minicalc> "

    def __init__(
        self,
        interpreter: Interpreter,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
        color: bool = False,
    ) -> None:
        """Store the interpreter and the injected I/O callables.

        Args:
            interpreter: The interpreter facade shared by every line.
            input_fn: Reads one line, given the prompt.
            output_fn: Writes one output line.
            color: Whether to use ANSI styling in rendered output.
        """
        self.interpreter = interpreter
        self.input_fn = input_fn
        self.output_fn = output_fn
        self.color = color

    def run(self) -> int:
        """Print the banner and process lines until the session ends.

        Returns:
            Always 0: EOF, Ctrl-C, and ``:quit`` are all clean exits.
        """
        self.output_fn(banner(self.color))
        while True:
            try:
                line = self.input_fn(self.PROMPT)
            except (EOFError, StopIteration):
                self.output_fn("")
                break
            except KeyboardInterrupt:
                self.output_fn("")
                break
            except Exception as exc:
                self.output_fn(_internal_error(exc))
                continue

            try:
                if not self._handle_line(line):
                    break
            except Exception as exc:
                self.output_fn(_internal_error(exc))
        return 0

    def _handle_line(self, line: str) -> bool:
        """Handle one input line.

        Args:
            line: The line returned by ``input_fn``, without a newline.

        Returns:
            False when the line was ``:quit`` or ``:q``; True otherwise.
        """
        stripped = line.strip()
        if not stripped:
            return True
        if stripped.startswith(":"):
            return self._meta_command(stripped)

        try:
            result = self.interpreter.run_line(line)
        except MiniCalcError as error:
            self.output_fn(error.render(self.color))
            self.output_fn("")
            return True

        formatted = format_result(result, self.color)
        if formatted:
            self.output_fn(formatted)
        return True

    def _meta_command(self, command: str) -> bool:
        """Execute a ``:`` meta-command.

        Args:
            command: The stripped input line, beginning with ``:``.

        Returns:
            False for ``:quit`` and ``:q``; True for every other command.
        """
        if command in (":quit", ":q"):
            return False
        if command == ":help":
            self.output_fn(help_text(self.color))
        elif command == ":vars":
            self._print_vars()
        elif command == ":clear":
            count = len(self.interpreter.env.items())
            self.interpreter.env.clear()
            self.output_fn(f"Cleared {count} variable(s).")
        else:
            self.output_fn(
                f"Unknown command '{command}'. Type :help for a list."
            )
        return True

    def _print_vars(self) -> None:
        """Print ``ans`` first (when set), then variables in sorted order."""
        env = self.interpreter.env
        rows: list[tuple[str, int]] = []
        if env.ans is not None:
            rows.append(("ans", env.ans))
        rows.extend(env.items())
        if not rows:
            self.output_fn("(no variables)")
            return
        width = max(len(name) for name, _ in rows)
        for name, value in rows:
            self.output_fn(f"{name:<{width}} = {value}")
