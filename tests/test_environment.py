# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tests/test_environment.py
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:24:00+02:00
# === CUBIST STAMP END ===

# ======================================================================
# File: test_environment.py
# Stamp: 2025-08-22T17:31:37Z
# (Auto-added header for paste verification)
# ======================================================================
"""
Basic environment sanity checks for the Cubist Art project.

These tests are intentionally light and dependency-tolerant:
- They verify Python can import the core CLI and logic modules.
- They surface optional deps (cv2, Pillow) without failing the suite.
"""

from __future__ import annotations

import importlib
import sys


def test_python_version():
    # Require a reasonably modern Python (adjust if your project supports older)
    major, minor = sys.version_info[:2]
    assert (major, minor) >= (3, 10)


def test_import_cubist_cli_module():
    # Importing the module should NOT exit; main() only runs under __main__
    mod = importlib.import_module("cubist_cli")
    assert hasattr(mod, "main") and callable(mod.main)


def test_import_core_logic():
    # Core algorithm module should import and expose run_cubist
    mod = importlib.import_module("cubist_core_logic")
    assert hasattr(mod, "run_cubist") and callable(mod.run_cubist)


def test_optional_deps_are_tolerated():
    """
    Optional dependencies should not hard-crash the environment.
    These imports are best-effort: absence is OK.
    """
    for name in ("cv2", "PIL", "numpy"):
        try:
            importlib.import_module(name)  # noqa: F401
        except Exception:
            # Optional or environment-specific; do not fail the build.
            pass
# ======================================================================
# End of File: test_environment.py  (2025-08-22T17:31:37Z)
# ======================================================================



# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:24:00+02:00
# === CUBIST FOOTER STAMP END ===
