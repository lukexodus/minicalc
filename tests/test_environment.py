"""Tests for the MiniCalc Environment (CORE-003)."""

import pytest

from minicalc.environment import Environment
from minicalc.errors import SourcePos, UndefinedNameError

POS = SourcePos(1, 1)


def test_initial_state_is_empty() -> None:
    """A new environment has no variables and no ``ans``."""
    env = Environment()
    assert env.variables == {}
    assert env.ans is None
    assert env.items() == []


def test_unset_ans_message() -> None:
    """Reading ``ans`` before the first success is a positioned error."""
    env = Environment()
    with pytest.raises(UndefinedNameError) as info:
        env.get("ans", POS)
    assert str(info.value) == "ans has no value yet; evaluate a statement first"
    assert info.value.pos == POS


def test_unknown_name_message() -> None:
    """An unknown variable names itself in the error."""
    env = Environment()
    with pytest.raises(UndefinedNameError) as info:
        env.get("x", POS)
    assert str(info.value) == "name 'x' is not defined"
    assert info.value.pos == POS


def test_set_get_and_record_result() -> None:
    """``set`` binds and ``record_result`` updates only ``ans``."""
    env = Environment()
    env.set("x", 7)
    env.record_result(42)
    assert env.get("x", POS) == 7
    assert env.get("ans", POS) == 42
    assert env.ans == 42
    assert env.variables == {"x": 7}


def test_items_sorted_and_excludes_ans() -> None:
    """``items`` is sorted by name and never contains ``ans``."""
    env = Environment()
    env.set("b", 2)
    env.set("a", 1)
    env.record_result(9)
    assert env.items() == [("a", 1), ("b", 2)]


def test_clear_resets_everything() -> None:
    """``clear`` removes variables and the ``ans`` value."""
    env = Environment()
    env.set("x", 1)
    env.record_result(2)
    env.clear()
    assert env.variables == {}
    assert env.ans is None
