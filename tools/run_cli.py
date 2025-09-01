# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tools/run_cli.py
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:34+02:00
# === CUBIST STAMP END ===


from __future__ import annotations

import sys
import subprocess
from pathlib import Path
import versioning


def main() -> int:
    versioning.print_banner("run_cli")
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "cubist_cli.py"
    if not cli.exists():
        print(f"[run_cli] ERROR: cubist_cli.py not found at {cli}", flush=True)
        return 2
    cmd = [sys.executable, str(cli), *sys.argv[1:]]
    proc = subprocess.run(cmd)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:34+02:00
# === CUBIST FOOTER STAMP END ===
