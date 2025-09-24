# file=tools/diagnostics/cli_proxy.py
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "cubist_cli.py"


def main() -> int:
    # everything after the first '--' is forwarded verbatim
    argv = sys.argv[1:]
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]

    cmd = [sys.executable, str(CLI), *argv]
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)

    if "Wrote:" not in proc.stdout:
        print("VERIFY: no 'Wrote:' line emitted by CLI")

    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
