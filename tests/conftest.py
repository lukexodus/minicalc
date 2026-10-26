"""Shared paths for the golden-test harness (CORE-002)."""

from pathlib import Path

#: Directory holding ``<stem>.mc`` inputs and ``<stem>.out`` expected outputs.
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
