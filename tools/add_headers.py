# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tools/add_headers.py
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:34+02:00
# === CUBIST STAMP END ===

# ======================================================================
# File: tools/add_headers.py
# Stamp: 2025-08-22T00:00:00Z
#
# Purpose:
#   Add a header and trailer comment to files for copy/paste verification.
#   Skips files that already contain the marker phrase.
# Usage:
#   python tools/add_headers.py <file1> [file2 ...]
# ======================================================================

from __future__ import annotations

import pathlib
import sys
import time


HEADER_TMPL = """# ======================================================================
# File: {fname}
# Stamp: {stamp}
# (Auto-added header for paste verification)
# ======================================================================

"""

FOOTER_TMPL = """
# ======================================================================
# End of File: {fname}  ({stamp})
# ======================================================================
"""


def stamp(path: pathlib.Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "Auto-added header for paste verification" in text:
        return

    fname = str(path).replace("\\", "/")
    stamp_text = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    new_text = (
        HEADER_TMPL.format(fname=fname, stamp=stamp_text)
        + text.rstrip()
        + "\n"
        + FOOTER_TMPL.format(fname=fname, stamp=stamp_text)
    )
    path.write_text(new_text, encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python tools/add_headers.py <file1> [file2 ...]")
        return 2
    for p in argv[1:]:
        path = pathlib.Path(p)
        if path.is_file():
            stamp(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:34+02:00
# === CUBIST FOOTER STAMP END ===
