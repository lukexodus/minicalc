"""Tests for ``scripts/check_docs.py`` (DOC-001).

Each test writes a small module into ``tmp_path`` and checks one rule from the
[D-11] documentation standard, so a regression in the checker fails here
instead of silently passing a submission that the rubric would mark down.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECKER_PATH = REPO_ROOT / "scripts" / "check_docs.py"

#: A module that satisfies every rule: module docstring, a class with an
#: ``Attributes:`` section covering dataclass fields and a ``self`` binding, and
#: a public function with ``Args:``/``Returns:``/``Raises:``.
PASSING_MODULE = '''"""A module that documents everything."""


class Widget:
    """A widget with one field and one stored attribute.

    Attributes:
        size: The widget's size in millimetres.
        label (str): Human-readable name assigned in ``__init__``.
    """

    size: int

    def __init__(self, label: str) -> None:
        """Create the widget.

        Args:
            label: Human-readable name.
        """
        self.label = label


def measure(value: int) -> int:
    """Return the value unchanged.

    Args:
        value: Any integer.

    Returns:
        The same integer.

    Raises:
        ValueError: When ``value`` is negative.
    """
    if value < 0:
        raise ValueError("negative")
    return value
'''


def _load_checker() -> ModuleType:
    """Import ``scripts/check_docs.py`` as a module.

    Returns:
        The imported checker module.
    """
    spec = importlib.util.spec_from_file_location("check_docs_under_test", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before execution so dataclasses can resolve the module by name.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


check_docs = _load_checker()


def _check(tmp_path: Path, source: str) -> tuple[list[str], object]:
    """Run the checker over one temporary module.

    Args:
        tmp_path: Pytest temporary directory.
        source: Module source to write.

    Returns:
        The formatted violation messages and the definition counts.
    """
    path = tmp_path / "sample.py"
    path.write_text(source, encoding="utf-8")
    violations, counts = check_docs.run([path], tmp_path)
    return [violation.format() for violation in violations], counts


def test_passing_module_has_no_violations(tmp_path: Path) -> None:
    """A fully documented module reports nothing and still counts definitions."""
    messages, counts = _check(tmp_path, PASSING_MODULE)
    assert messages == []
    assert counts.classes == 1
    assert counts.functions == 2


def test_missing_module_docstring(tmp_path: Path) -> None:
    """The first rule: every module has a docstring."""
    messages, _ = _check(tmp_path, "x = 1\n")
    assert messages == ["sample.py:1: module has no docstring"]


def test_missing_class_docstring(tmp_path: Path) -> None:
    """A class without a docstring is a violation at the class line."""
    messages, _ = _check(tmp_path, '"""Mod."""\n\n\nclass A:\n    pass\n')
    assert messages == ["sample.py:4: class 'A' has no docstring"]


def test_class_attributes_without_attributes_section(tmp_path: Path) -> None:
    """A dataclass field requires an ``Attributes:`` section."""
    source = '"""Mod."""\n\n\nclass A:\n    """Just a class."""\n\n    size: int\n'
    messages, _ = _check(tmp_path, source)
    assert messages == [
        "sample.py:4: class 'A' has no 'Attributes:' section documenting `size`"
    ]


def test_undocumented_attribute_is_reported(tmp_path: Path) -> None:
    """Every attribute must be named, not just some of them."""
    source = (
        '"""Mod."""\n'
        "\n"
        "\n"
        "class A:\n"
        '    """A class.\n'
        "\n"
        "    Attributes:\n"
        "        size: Documented.\n"
        '    """\n'
        "\n"
        "    size: int\n"
        "\n"
        "    def __init__(self) -> None:\n"
        '        """Create it."""\n'
        "        self.secret = 1\n"
    )
    messages, _ = _check(tmp_path, source)
    assert messages == [
        "sample.py:4: class 'A' does not document attribute(s) `secret` "
        "in its 'Attributes:' section"
    ]


def test_enum_members_count_as_attributes(tmp_path: Path) -> None:
    """Enum members are class-level assignments and must be documented."""
    source = (
        '"""Mod."""\n'
        "\n"
        "from enum import Enum\n"
        "\n"
        "\n"
        "class Kind(Enum):\n"
        '    """Kinds.\n'
        "\n"
        "    Attributes:\n"
        "        A: The first kind.\n"
        '    """\n'
        "\n"
        '    A = "A"\n'
        '    B = "B"\n'
    )
    messages, _ = _check(tmp_path, source)
    assert messages == [
        "sample.py:6: class 'Kind' does not document attribute(s) `B` "
        "in its 'Attributes:' section"
    ]


def test_typed_attribute_form_is_accepted(tmp_path: Path) -> None:
    """``name (type):`` entries satisfy the rule as well as ``name:``."""
    source = (
        '"""Mod."""\n'
        "\n"
        "\n"
        "class A:\n"
        '    """A class.\n'
        "\n"
        "    Attributes:\n"
        "        flag (ClassVar[bool]): A documented constant.\n"
        '    """\n'
        "\n"
        "    flag: bool = True\n"
    )
    messages, _ = _check(tmp_path, source)
    assert messages == []


def test_public_function_without_docstring(tmp_path: Path) -> None:
    """Public functions need a docstring."""
    messages, _ = _check(tmp_path, '"""Mod."""\n\n\ndef f() -> None:\n    pass\n')
    assert messages == ["sample.py:4: function 'f' has no docstring"]


def test_missing_args_section(tmp_path: Path) -> None:
    """Parameters other than ``self`` require an ``Args:`` section."""
    source = (
        '"""Mod."""\n'
        "\n"
        "\n"
        "class A:\n"
        '    """A class."""\n'
        "\n"
        "    def run(self, times: int) -> None:\n"
        '        """Run it."""\n'
    )
    messages, _ = _check(tmp_path, source)
    assert messages == [
        "sample.py:7: function 'run' takes parameters but has no 'Args:' section"
    ]


def test_missing_returns_section(tmp_path: Path) -> None:
    """A ``return`` with a value requires a ``Returns:`` section."""
    source = (
        '"""Mod."""\n'
        "\n"
        "\n"
        "def f() -> int:\n"
        '    """Return one."""\n'
        "    return 1\n"
    )
    messages, _ = _check(tmp_path, source)
    assert messages == [
        "sample.py:4: function 'f' returns a value but has no 'Returns:' section"
    ]


def test_missing_raises_section(tmp_path: Path) -> None:
    """A ``raise`` requires a ``Raises:`` section."""
    source = (
        '"""Mod."""\n'
        "\n"
        "\n"
        "def f() -> None:\n"
        '    """Fail."""\n'
        '    raise ValueError("bad")\n'
    )
    messages, _ = _check(tmp_path, source)
    assert messages == [
        "sample.py:4: function 'f' raises but has no 'Raises:' section"
    ]


def test_private_helpers_and_dunders_are_exempt(tmp_path: Path) -> None:
    """Only public names and ``__init__`` are required to be documented."""
    source = (
        '"""Mod."""\n'
        "\n"
        "\n"
        "class A:\n"
        '    """A class."""\n'
        "\n"
        "    def __str__(self) -> str:\n"
        '        return "a"\n'
        "\n"
        "    def _helper(self, value: int) -> int:\n"
        "        return value\n"
    )
    messages, counts = _check(tmp_path, source)
    assert messages == []
    assert counts.functions == 0


def test_init_requires_docstring_and_args(tmp_path: Path) -> None:
    """``__init__`` is public for this rule even though it is a dunder."""
    source = (
        '"""Mod."""\n'
        "\n"
        "\n"
        "class A:\n"
        '    """A class.\n'
        "\n"
        "    Attributes:\n"
        "        size: The stored size.\n"
        '    """\n'
        "\n"
        "    def __init__(self, size: int) -> None:\n"
        "        self.size = size\n"
    )
    messages, _ = _check(tmp_path, source)
    assert messages == ["sample.py:11: function '__init__' has no docstring"]


def test_nested_function_return_does_not_leak(tmp_path: Path) -> None:
    """A nested ``return`` does not make the outer function a returning one."""
    source = (
        '"""Mod."""\n'
        "\n"
        "\n"
        "def outer() -> None:\n"
        '    """Do nothing visible."""\n'
        "\n"
        "    def inner() -> int:\n"
        "        return 1\n"
    )
    messages, _ = _check(tmp_path, source)
    assert messages == []


def test_syntax_error_is_reported_not_raised(tmp_path: Path) -> None:
    """An unparsable file becomes a violation instead of a crash."""
    messages, _ = _check(tmp_path, '"""Mod."""\n\ndef broken(:\n')
    assert len(messages) == 1
    assert messages[0].startswith("sample.py:3: cannot parse file:")


def test_cli_reports_summary_and_exit_codes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI prints ``N classes, M functions checked`` and sets the exit code."""
    clean = tmp_path / "clean.py"
    clean.write_text(PASSING_MODULE, encoding="utf-8")
    assert check_docs.main([str(clean)]) == 0
    assert "1 classes, 2 functions checked" in capsys.readouterr().out

    broken = tmp_path / "broken.py"
    broken.write_text("x = 1\n", encoding="utf-8")
    assert check_docs.main([str(broken)]) == 1
    output = capsys.readouterr().out
    assert "module has no docstring" in output
    assert "0 classes, 0 functions checked" in output


def test_cli_missing_path_is_a_usage_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A path that does not exist exits 2 with a message on stderr."""
    assert check_docs.main([str(tmp_path / "absent.py")]) == 2
    assert "no such file or directory" in capsys.readouterr().err


def test_repository_package_is_clean() -> None:
    """The real ``minicalc`` package satisfies the standard it is checked against."""
    violations, counts = check_docs.run(check_docs.default_targets(REPO_ROOT), REPO_ROOT)
    assert [violation.format() for violation in violations] == []
    assert counts.classes > 0
    assert counts.functions > 0
