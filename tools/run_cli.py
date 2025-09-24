# tools/run_cli.py
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent  # .../cubist_art/tools
ROOT = HERE.parent  # .../cubist_art


def _find_cli() -> Path | None:
    """Be robust to mislocated tools — search upwards for cubist_cli.py."""
    candidates = [
        ROOT / "cubist_cli.py",
        HERE.parent / "cubist_cli.py",
        ROOT.parent / "cubist_art" / "cubist_cli.py",
    ]
    # also scan a few parents just in case
    p = HERE
    for _ in range(5):
        candidates.append(p / "cubist_cli.py")
        p = p.parent
    for c in candidates:
        if c.exists():
            return c
    return None


def _augmented_env() -> dict:
    env = os.environ.copy()
    sep = ";" if os.name == "nt" else ":"
    extras = [str(ROOT)]
    if (ROOT / "src").exists():
        extras.append(str(ROOT / "src"))
    env["PYTHONPATH"] = sep.join(extras) + (
        sep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    return env


def _sha256(p: Path) -> tuple[int, str]:
    if not p.exists():
        return 0, ""
    h = hashlib.sha256()
    n = 0
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            n += len(chunk)
            h.update(chunk)
    return n, h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--geometry", required=True)
    ap.add_argument("--points", default="4000")
    ap.add_argument("--seed", default="42")
    ap.add_argument("--param", action="append")
    ap.add_argument("--export-svg", action="store_true")
    ap.add_argument("--cascade-stages", default="3")
    ap.add_argument("--enable-plugin-exec", action="store_true")
    ap.add_argument("--pipeline")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--verbose", action="store_true", help="wrapper verbosity")
    args = ap.parse_args()

    cli = _find_cli()
    out_svg = Path(args.output + ".svg")
    out_svg.parent.mkdir(parents=True, exist_ok=True)

    if not cli:
        summary = {
            "ts": None,
            "input": None,
            "output": args.output,
            "geometry": None,
            "rc": 2,
            "svg_exists": False,
            "expected_svg": str(out_svg),
            "stdout_tail": [],
            "stderr_tail": [f"cubist_cli.py not found near {HERE}"],
        }
        print(json.dumps(summary, ensure_ascii=False))
        return 2

    cmd = [
        sys.executable,
        str(cli),
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
    ]
    if args.export_svg:
        cmd.append("--export-svg")
    if args.enable_plugin_exec:
        cmd.append("--enable-plugin-exec")
    if args.param:
        for p in args.param:
            cmd.extend(["--param", p])
    if args.pipeline:
        cmd.extend(["--pipeline", args.pipeline])
    if args.quiet:
        cmd.append("--quiet")

    proc = subprocess.run(cmd, capture_output=True, text=True, env=_augmented_env())
    rc = proc.returncode

    exists = out_svg.exists()
    size, sha = _sha256(out_svg) if exists else (0, "")
    shapes = 0
    try:
        from svg_audit import count_shapes

        shapes = count_shapes(out_svg) if exists else 0
    except Exception:
        shapes = 0

    if args.verbose:
        if exists:
            print(f"Wrote: {out_svg}")
        else:
            print(f"NO-OUTPUT for {args.geometry}: expected {out_svg}", file=sys.stderr)

    summary = {
        "ts": None,
        "input": args.input if rc == 0 else None,
        "output": args.output,
        "geometry": args.geometry if rc == 0 else None,
        "rc": rc,
        "svg_exists": exists,
        "svg_path": str(out_svg) if exists else None,
        "svg_shapes": int(shapes),
        "svg_size": int(size),
        "expected_svg": str(out_svg),
    }
    if rc != 0 or not exists:
        summary["stdout_tail"] = (proc.stdout or "").splitlines()[-12:]
        summary["stderr_tail"] = (proc.stderr or "").splitlines()[-12:]

    print(json.dumps(summary, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
