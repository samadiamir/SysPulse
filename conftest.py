"""
conftest.py

Shared pytest fixtures for the SysPulse test suite.

Ensures tests run headless on every platform by forcing the
``offscreen`` Qt platform plugin *before* any QApplication exists,
and guarantees a single QApplication instance per session.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make the project root importable.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Force headless rendering — must be set before QApplication is created.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

# Create the QApplication eagerly at import time so that pytest-qt's
# ``qapp`` fixture finds an existing instance and reuses it, avoiding
# the known hang when creating one mid-session with the offscreen
# platform on Windows + PySide6 6.11.
from PySide6.QtWidgets import QApplication  # noqa: E402
_APP = QApplication.instance() or QApplication(sys.argv)


@pytest.fixture(scope="session")
def qapp():
    """Return the pre-created QApplication."""
    yield _APP
