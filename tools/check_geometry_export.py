from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
RUN = TOOLS / "run_cli.py"

GEOMS = [
    "poisson_disk",
    "scatter_circles",
    "rectangles",
    "voronoi",
    "delaunay",
    "concentric_circles",
]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Proxy to run_cli with strict Wrote/JSON output"
    )
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--geometry", required=True, choices=GEOMS)
    ap.add_argument("--points", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--cascade-stages", type=int, default=3)
    ap.add_argument("--export-svg", action="store_true")
    ap.add_argument("--enable-plugin-exec", action="store_true")
    args = ap.parse_args()

    # forward into run_cli
    argv = [
        str(RUN),
        "--input",
        args.input,
        "--output",
        args.output,
        "--geometry",
        args.geometry,
        "--points",
        str(args.points),
        "--seed",
        str(args.seed),
        "--cascade-stages",
        str(args.cascade_stages),
        "--verbose",
    ]
    if args.export_svg:
        argv.append("--export-svg")
    if args.enable_plugin_exec:
        argv.append("--enable-plugin-exec")

    # Hand off to run_cli within this interpreter for simplicity
    from run_cli import main as run_main  # type: ignore

    sys.argv = ["run_cli.py", *argv[1:]]
    return run_main()


if __name__ == "__main__":
    raise SystemExit(main())
