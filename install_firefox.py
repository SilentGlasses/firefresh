#!/usr/bin/env python3
"""Compatibility wrapper for legacy script usage."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from firefox_installer_app.cli import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
