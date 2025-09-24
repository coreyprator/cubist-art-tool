from __future__ import annotations
import sys
import subprocess
from pathlib import Path

GEOMS = [
    "poisson_disk",
    "scatter_circles",
    "rectangles",
    "voronoi",
    "delaunay",
    "concentric_circles",
]


def run_one(inp: str, root: Path, geom: str) -> tuple[int, str]:
    out_dir = root / geom
    out_prefix = out_dir / f"frame_{geom}"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "tools/run_cli.py",
        "--input",
        inp,
        "--output",
        str(out_prefix),
        "--geometry",
        geom,
        "--points",
        "4000",
        "--seed",
        "42",
        "--cascade-stages",
        "3",
        "--export-svg",
        "--enable-plugin-exec",
        "--force-append-svg",
        "--verbose",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr)


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    print(f"Input: {Path(args.input).resolve()}")
    print(f"Output root: {root.resolve()}\n")
    for g in GEOMS:
        rc, out = run_one(args.input, root, g)
        print(f"[{g:18}] {'OK' if rc==0 else f'FAIL(rc={rc})'}")
        low = out.lower()
        if "error:" in low or "usage:" in low:
            for l in out.splitlines()[:6]:
                print(" " * 21 + l)
    print("\nDone.")


if __name__ == "__main__":
    sys.exit(main())
