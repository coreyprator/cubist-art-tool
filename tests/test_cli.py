# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tests/test_cli.py
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:47+02:00
# === CUBIST STAMP END ===

# ======================================================================
# File: test_cli.py
# Stamp: 2025-08-22T17:31:37Z
# (Auto-added header for paste verification)
# ======================================================================
"""
CLI smoke tests.

We keep these tests light:
- Verify the CLI module imports and exposes main().
- Verify argparse can be invoked indirectly without executing a full run.
- Optionally exercise `--help` in a subprocess to ensure the script entry
  prints usage and exits cleanly (return code 0).
"""

from __future__ import annotations

import subprocess
import sys
import importlib
from pathlib import Path


def test_cli_import_and_main_callable():
    cli = importlib.import_module("cubist_cli")
    assert hasattr(cli, "main") and callable(cli.main)


def test_cli_help_subprocess(tmp_path: Path):
    """
    Running the module with --help should succeed and not run the algorithm.
    We use `-m` so it works whether or not there is an entry point installed.
    """
    # On Windows/posix this works the same: python -m cubist_cli --help
    cmd = [sys.executable, "-m", "cubist_cli", "--help"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    # --help should print usage and exit 0
    assert proc.returncode == 0
    assert "usage:" in proc.stdout.lower() or "usage:" in proc.stderr.lower()
# ======================================================================
# End of File: test_cli.py  (2025-08-22T17:31:37Z)
# ======================================================================




# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:47+02:00
# === CUBIST FOOTER STAMP END ===
