# tools/diagnostics/plugin_env_probe.py
from __future__ import annotations
import json
import os
import sys
from pathlib import Path


def main():
    tools = Path(__file__).resolve().parent
    root = tools.parents[2]  # .../cubist_art
    src = root / "src"

    # Try to make 'geometries' importable regardless of env
    paths = [str(root)]
    if src.exists():
        paths.insert(0, str(src))
    sys.path[:0] = paths

    ok = True
    err = ""
    where = list(sys.path[:2])
    try:
        import geometries  # noqa: F401
    except Exception as e:
        ok = False
        err = repr(e)

    print(
        json.dumps(
            {
                "ok": ok,
                "root": str(root),
                "sys_path_0": sys.path[0] if sys.path else "",
                "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
                "added": paths,
                "error": err,
            }
        )
    )


if __name__ == "__main__":
    main()
