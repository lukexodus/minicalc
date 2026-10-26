"""Shim so ``python main.py`` runs the MiniCalc command-line interface."""

from minicalc.__main__ import main

raise SystemExit(main())
