"""Package-level smoke tests for the MiniCalc bootstrap (ARCH-002)."""

import minicalc


def test_version() -> None:
    """The package exposes the design-locked version string."""
    assert minicalc.__version__ == "1.0.0"
