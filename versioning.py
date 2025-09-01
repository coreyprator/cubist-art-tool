# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: versioning.py
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:45+02:00
# === CUBIST STAMP END ===

from __future__ import annotations

import os
import sys
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


# ---- single source of truth -------------------------------------------------
VERSION: str = "v2.3.6"
# BUILD_TS is the moment this file was prepared; update when you cut a build:
BUILD_TS: str = "2025-09-01T09:20:00"


def _git_short_commit() -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        commit = out.decode("utf-8", errors="ignore").strip()
        return commit or None
    except Exception:
        return None


@dataclass(frozen=True)
class BuildInfo:
    program: str
    version: str
    build_ts: str
    python: str
    commit: Optional[str]
    runtime_ts: str
    cwd: str


def build_info(program: str) -> BuildInfo:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    return BuildInfo(
        program=program,
        version=VERSION,
        build_ts=BUILD_TS,
        python=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        commit=_git_short_commit(),
        runtime_ts=now,
        cwd=os.getcwd(),
    )


def print_banner(program: str) -> None:
    """Print a one-line and a multi-line banner to stdout."""
    info = build_info(program)
    one = f"[{program}] {info.version} | build={info.build_ts} | run={info.runtime_ts}"
    print(one, flush=True)
    details = [
        f"[{program}] python={info.python}",
        f"[{program}] commit={info.commit or 'n/a'}",
        f"[{program}] cwd={info.cwd}",
    ]
    for line in details:
        print(line, flush=True)


if __name__ == "__main__":
    prog = os.path.basename(sys.argv[0]).split(".")[0]
    print_banner(prog)


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:45+02:00
# === CUBIST FOOTER STAMP END ===
