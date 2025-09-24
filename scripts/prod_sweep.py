# === CUBIST STAMP BEGIN ===
# Project : Cubist Art
# File    : scripts/prod_sweep.py
# Version : (stamped by add_headers.py)
# Usage   : python scripts/prod_sweep.py
# === CUBIST STAMP END ===
"""Usage:
  python scripts/prod_sweep.py

Notes:
  - This docstring is injected/updated by add_headers.py
  - Safe to keep above 'from __future__ import ...'
"""

from __future__ import annotations
# Usage:
#   python prod_sweep.py --help
#   (Most scripts also support: -h / --help for options.)
#
# RFF: scripts/prod_sweep.py


import argparse

import subprocess

from pathlib import Path

import shlex

import sys

import time


RUNS = [
    # cascade (image-driven fill + edge seeding)
    (
        "prod_delaunay_cascade.svg",
        "delaunay",
        1200,
        {"cascade_stages": 3, "cascade_fill": "image", "seed_mode": "edge"},
    ),
    (
        "prod_voronoi_cascade.svg",
        "voronoi",
        1200,
        {"cascade_stages": 3, "cascade_fill": "image", "seed_mode": "edge"},
    ),
    (
        "prod_rectangles_cascade.svg",
        "rectangles",
        1200,
        {"cascade_stages": 3, "cascade_fill": "image", "seed_mode": "edge"},
    ),
    # poisson (placement driven by Poisson disk)
    (
        "prod_delaunay_poisson.svg",
        "delaunay",
        800,
        {"seed_mode": "poisson", "poisson_min_px": 22},
    ),
    (
        "prod_voronoi_poisson.svg",
        "voronoi",
        800,
        {"seed_mode": "poisson", "poisson_min_px": 22},
    ),
    (
        "prod_rectangles_poisson.svg",
        "rectangles",
        800,
        {"seed_mode": "poisson", "poisson_min_px": 22},
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser()

    ap.add_argument("--input", required=True)

    ap.add_argument("--outdir", default="output")

    ap.add_argument("--seed", type=int, default=123)

    ap.add_argument("--open", action="store_true")

    ap.add_argument("--quiet", action="store_true")

    args = ap.parse_args()

    outdir = Path(args.outdir)

    outdir.mkdir(parents=True, exist_ok=True)

    exe = [sys.executable, "cubist_cli.py"]

    generated = []

    failed = []

    t0 = time.time()

    for name, geom, pts, extras in RUNS:
        out = outdir / name

        cmd = [
            *exe,
            "--pipeline",
            "--input",
            args.input,
            "--output",
            str(out),
            "--geometry",
            geom,
            "--points",
            str(pts),
            "--seed",
            str(args.seed),
            "--export-svg",
        ]

        # cascade flags if provided

        if extras.get("cascade_stages"):
            cmd += ["--cascade-stages", str(extras["cascade_stages"])]

        if extras.get("cascade_fill"):
            cmd += ["--cascade-fill", extras["cascade_fill"]]

        # generic params

        for k, v in extras.items():
            if k in {"cascade_stages", "cascade_fill"}:
                continue

            cmd += ["--param", f"{k}={v}"]

        if args.quiet:
            cmd += ["--quiet"]

        print(f"▶ {' '.join(shlex.quote(c) for c in cmd)}")

        try:
            subprocess.run(cmd, check=True)

            generated.append(name)

        except subprocess.CalledProcessError:
            failed.append(name)

    # write gallery for this outdir

    try:
        subprocess.run(
            [sys.executable, "scripts/make_gallery.py", str(outdir)], check=True
        )

    except subprocess.CalledProcessError:
        print("[gallery] failed to create gallery", file=sys.stderr)

    sec = round(time.time() - t0, 2)

    print("\n=== SUMMARY ===")

    print(
        {
            "generated": [n for n, _ in jobs if n not in fails],
            "failed": fails,
            "seconds": round(secs, 2),
        }
    )

    if not fails:
        print("✅ All 6 renders succeeded")

    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# === CUBIST FOOTER STAMP BEGIN ===
# End of file - stamped 2025-09-03T10:37:27+02:00
# === CUBIST FOOTER STAMP END ===


# === CUBIST FOOTER BEGIN ===
# File  : scripts/prod_sweep.py
# Lines : 216
# === CUBIST FOOTER END ===
