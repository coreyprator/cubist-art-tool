# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tools/file_audit.py
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:24:02+02:00
# === CUBIST STAMP END ===

# ======================================================================
# File: tools/file_audit.py
# Stamp: 2025-08-24T20:45:00Z
# ======================================================================

from __future__ import annotations

from pathlib import Path
from typing import List


def list_written_files(dir_path: Path) -> List[str]:
    """Return 'filename (NNN bytes)' lines for all files in dir_path, sorted by mtime then name."""
    if not dir_path.exists():
        return []
    files = [p for p in dir_path.iterdir() if p.is_file()]
    files.sort(key=lambda p: (p.stat().st_mtime, p.name))
    return [f"{p.name} ({p.stat().st_size} bytes)" for p in files]


# ======================================================================
# End of File: tools/file_audit.py
# ======================================================================


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:24:02+02:00
# === CUBIST FOOTER STAMP END ===
