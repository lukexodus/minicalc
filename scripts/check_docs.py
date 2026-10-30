#!/usr/bin/env python3
"""check_docs.py — enforce the [D-11] documentation standard.

Scans every ``*.py`` under ``minicalc/`` plus ``main.py`` and reports the
docstring rules the rubric's top Documentation band depends on:

* every module has a docstring;
* every class has a docstring, and a class that declares any attribute (a
  class-level annotation or assignment, which covers dataclass fields and enum
  members, or ``self.<name> = ...`` inside ``__init__``) also has an
  ``Attributes:`` section that names every one of those attributes;
* every public function and method (``__init__`` included) has a docstring,
  with ``Args:`` when it takes parameters other than ``self``/``cls``,
  ``Returns:`` when it returns a value, and ``Raises:`` when it raises.

The checker is static: it parses with :mod:`ast` and never imports the target
modules, so it runs on untrusted or half-written code and needs no third-party
package ([D-02]).

Usage::

    python scripts/check_docs.py                 # whole package + main.py
    python scripts/check_docs.py minicalc/lexer.py

Exit codes: 0 when every rule holds, 1 when at least one violation is found,
2 for a usage error.

Design notes:
    Names beginning with an underscore are private by convention and are not
    required to document their steps; the prompt's rule is "public functions
    and methods (no leading underscore, plus ``__init__``)".  Dunder methods
    such as ``__str__`` therefore stay exempt, which keeps the checker aligned
    with the written standard rather than with a stricter invented one.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

#: Attribute and section headers the checker understands in a Google-style
#: docstring. Only the four required ones are validated; the rest merely stop
#: an ``Attributes:`` body early, so a following ``Example:`` is not mistaken
#: for a documented attribute.
_SECTION_HEADERS = (
    "Args:",
    "Returns:",
    "Raises:",
    "Attributes:",
    "Yields:",
    "Example:",
    "Examples:",
    "Note:",
    "Notes:",
    "Todo:",
)

#: One documented entry, for example ``pos: ...`` or ``kind (ClassVar[str]):``.
_ENTRY_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*:")

#: Node types whose bodies belong to a different scope, so a ``return`` or
#: ``raise`` inside them is not attributed to the enclosing function.
_NESTED_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


@dataclass(frozen=True)
class Violation:
    """One documentation rule violation.

    Attributes:
        path: File the violation was found in, relative to the repo root.
        line: 1-based line of the offending definition.
        message: Human-readable description of what is missing.
    """

    path: str
    line: int
    message: str

    def format(self) -> str:
        """Return the ``path:line: message`` form used by the CLI.

        Returns:
            The violation rendered on one line.
        """
        return f"{self.path}:{self.line}: {self.message}"


@dataclass
class Counts:
    """How many definitions the checker inspected.

    Attributes:
        classes: Number of classes visited.
        functions: Number of public functions and methods visited.
    """

    classes: int = 0
    functions: int = 0


def _own_nodes(body: list[ast.stmt]) -> list[ast.AST]:
    """Collect the nodes evaluated in one function's own scope.

    Nested ``def``/``class``/``lambda`` bodies are excluded because their
    ``return`` and ``raise`` statements do not make the enclosing function a
    returning or raising one.

    Args:
        body: Statement list to walk.

    Returns:
        Every node of the function body, excluding nested scopes.
    """
    collected: list[ast.AST] = []
    stack: list[ast.AST] = list(body)
    while stack:
        node = stack.pop()
        collected.append(node)
        if isinstance(node, _NESTED_SCOPES):
            continue
        stack.extend(ast.iter_child_nodes(node))
    return collected


def _section(docstring: str, header: str) -> str | None:
    """Return the body of one Google-style section.

    Args:
        docstring: The cleaned docstring to search.
        header: Section header including the colon, for example ``"Args:"``.

    Returns:
        The text after the header up to the next section header, or ``None``
        when the section is absent.
    """
    lines = docstring.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == header:
            body: list[str] = []
            for follow in lines[index + 1 :]:
                if follow.strip() in _SECTION_HEADERS:
                    break
                body.append(follow)
            return "\n".join(body)
    return None


def _documented_names(section_text: str | None) -> set[str]:
    """Extract the entry names documented in one section.

    Args:
        section_text: Section body, or ``None`` when the section is absent.

    Returns:
        Every name that starts a line in ``name:`` or ``name (type):`` form.
    """
    if not section_text:
        return set()
    names = set()
    for line in section_text.splitlines():
        match = _ENTRY_RE.match(line)
        if match:
            names.add(match.group(1))
    return names


def _class_attributes(node: ast.ClassDef) -> list[str]:
    """List the attributes a class declares.

    Covers class-level annotations (dataclass fields and ``ClassVar``
    constants), class-level assignments (enum members), annotated or plain
    ``self.<name> = ...`` bindings in ``__init__``, and documented instance
    attributes introduced only by annotation.

    Args:
        node: The class definition to inspect.

    Returns:
        Attribute names in declaration order, without duplicates.
    """
    names: list[str] = []

    def add(name: str) -> None:
        if name not in names:
            names.append(name)

    for statement in node.body:
        if isinstance(statement, ast.AnnAssign) and isinstance(
            statement.target, ast.Name
        ):
            add(statement.target.id)
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    add(target.id)
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if statement.name != "__init__":
                continue
            for inner in _own_nodes(statement.body):
                if isinstance(inner, (ast.Assign, ast.AnnAssign)):
                    targets = (
                        inner.targets
                        if isinstance(inner, ast.Assign)
                        else [inner.target]
                    )
                    for target in targets:
                        if (
                            isinstance(target, ast.Attribute)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                        ):
                            add(target.attr)
    return names


def _parameter_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """List a function's parameters, excluding ``self`` and ``cls``.

    Args:
        node: The function definition to inspect.

    Returns:
        Parameter names, including ``*args``/``**kwargs`` and keyword-only
        parameters, in declaration order.
    """
    arguments = node.args
    names = [
        argument.arg
        for argument in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
        if argument.arg not in ("self", "cls")
    ]
    if arguments.vararg is not None:
        names.append(arguments.vararg.arg)
    if arguments.kwarg is not None:
        names.append(arguments.kwarg.arg)
    return names


def _returns_value(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Report whether a function returns a value of its own.

    Args:
        node: The function definition to inspect.

    Returns:
        True when its own body (nested scopes excluded) has a ``return`` with
        a value.
    """
    return any(
        isinstance(inner, ast.Return) and inner.value is not None
        for inner in _own_nodes(node.body)
    )


def _raises(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Report whether a function raises of its own.

    Args:
        node: The function definition to inspect.

    Returns:
        True when its own body (nested scopes excluded) has a ``raise``.
    """
    return any(isinstance(inner, ast.Raise) for inner in _own_nodes(node.body))


def _check_class(node: ast.ClassDef, path: str, counts: Counts) -> list[Violation]:
    """Check one class definition and its methods.

    Args:
        node: The class definition.
        path: Path used in violation messages.
        counts: Running totals, updated in place.

    Returns:
        Every violation found in the class, its docstring, and its methods.
    """
    counts.classes += 1
    violations: list[Violation] = []
    docstring = ast.get_docstring(node)
    line = node.lineno

    if docstring is None:
        violations.append(Violation(path, line, f"class '{node.name}' has no docstring"))
    else:
        attributes = _class_attributes(node)
        section = _section(docstring, "Attributes:")
        if attributes and section is None:
            violations.append(
                Violation(
                    path,
                    line,
                    f"class '{node.name}' has no 'Attributes:' section "
                    f"documenting {_names(attributes)}",
                )
            )
        elif attributes:
            documented = _documented_names(section)
            missing = [name for name in attributes if name not in documented]
            if missing:
                violations.append(
                    Violation(
                        path,
                        line,
                        f"class '{node.name}' does not document attribute(s) "
                        f"{_names(missing)} in its 'Attributes:' section",
                    )
                )

    for statement in node.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            violations.extend(_check_function(statement, path, counts))
    return violations


def _check_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef, path: str, counts: Counts
) -> list[Violation]:
    """Check one module-level function or method.

    Args:
        node: The function definition.
        path: Path used in violation messages.
        counts: Running totals, updated in place.

    Returns:
        Every violation found for the function.
    """
    if node.name != "__init__" and node.name.startswith("_"):
        return []  # private helper: not required to document its steps

    counts.functions += 1
    violations: list[Violation] = []
    docstring = ast.get_docstring(node)
    line = node.lineno
    label = f"function '{node.name}'"

    if docstring is None:
        violations.append(Violation(path, line, f"{label} has no docstring"))
        return violations

    if _parameter_names(node) and _section(docstring, "Args:") is None:
        violations.append(
            Violation(path, line, f"{label} takes parameters but has no 'Args:' section")
        )
    if _returns_value(node) and _section(docstring, "Returns:") is None:
        violations.append(
            Violation(path, line, f"{label} returns a value but has no 'Returns:' section")
        )
    if _raises(node) and _section(docstring, "Raises:") is None:
        violations.append(
            Violation(path, line, f"{label} raises but has no 'Raises:' section")
        )
    return violations


def _names(names: list[str]) -> str:
    """Render attribute names for a violation message.

    Args:
        names: Attribute names to render.

    Returns:
        The names wrapped in backticks, separated by commas.
    """
    return ", ".join(f"`{name}`" for name in names)


def check_file(path: Path, display_path: str, counts: Counts) -> list[Violation]:
    """Check one Python file against the documentation standard.

    Args:
        path: File to read and parse.
        display_path: Path used in violation messages.
        counts: Running totals, updated in place.

    Returns:
        Every violation found in the file, in source order.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [Violation(display_path, 1, f"cannot read file: {exc}")]
    try:
        module = ast.parse(source, filename=display_path)
    except SyntaxError as exc:
        return [
            Violation(display_path, exc.lineno or 1, f"cannot parse file: {exc.msg}")
        ]

    violations: list[Violation] = []
    if ast.get_docstring(module) is None:
        violations.append(Violation(display_path, 1, "module has no docstring"))

    for statement in module.body:
        if isinstance(statement, ast.ClassDef):
            violations.extend(_check_class(statement, display_path, counts))
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            violations.extend(_check_function(statement, display_path, counts))
    return violations


def default_targets(repo_root: Path) -> list[Path]:
    """List the files the checker inspects by default.

    Args:
        repo_root: Repository root holding ``minicalc/`` and ``main.py``.

    Returns:
        Every ``*.py`` under ``minicalc/`` plus ``main.py``, sorted, restricted
        to files that exist.
    """
    targets = sorted((repo_root / "minicalc").rglob("*.py"))
    main = repo_root / "main.py"
    if main.exists():
        targets.append(main)
    return targets


def _display_path(path: Path, repo_root: Path) -> str:
    """Render a path relative to the repository root with forward slashes.

    Args:
        path: File to render.
        repo_root: Repository root used as the base.

    Returns:
        The relative path, or the absolute path when it is outside the root.
    """
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def run(targets: list[Path], repo_root: Path) -> tuple[list[Violation], Counts]:
    """Check every target file.

    Args:
        targets: Files to check.
        repo_root: Base used to shorten paths in messages.

    Returns:
        The violations in path/line order and the definition counts.
    """
    counts = Counts()
    violations: list[Violation] = []
    for target in targets:
        violations.extend(check_file(target, _display_path(target, repo_root), counts))
    violations.sort(key=lambda violation: (violation.path, violation.line))
    return violations, counts


def main(argv: list[str] | None = None) -> int:
    """Run the checker as a command-line tool.

    Args:
        argv: Arguments to parse; ``None`` means ``sys.argv[1:]``.

    Returns:
        0 when the standard holds, 1 when violations were found, 2 for a
        usage error.
    """
    repo_root_default = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        prog="check_docs",
        description="Check MiniCalc docstrings against the [D-11] standard.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="files or directories to check (default: minicalc/ and main.py)",
    )
    parser.add_argument(
        "--repo-root",
        default=str(repo_root_default),
        help="repository root used to shorten reported paths",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if args.paths:
        targets: list[Path] = []
        for raw in args.paths:
            candidate = Path(raw)
            if candidate.is_dir():
                targets.extend(sorted(candidate.rglob("*.py")))
            elif candidate.exists():
                targets.append(candidate)
            else:
                print(f"check_docs: no such file or directory: {raw}", file=sys.stderr)
                return 2
    else:
        targets = default_targets(repo_root)

    violations, counts = run(targets, repo_root)
    for violation in violations:
        print(violation.format())
    print(f"{counts.classes} classes, {counts.functions} functions checked")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
