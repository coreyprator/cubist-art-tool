from __future__ import annotations

import argparse
import json
import subprocess
import sys
import hashlib
from pathlib import Path
from xml.etree import ElementTree as ET
from datetime import datetime, timezone

# ------------------------------ utils ----------------------------------------


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def count_svg_shapes(svg_path: Path) -> int:
    try:
        root = ET.parse(svg_path).getroot()
    except Exception:
        return 0
    SHAPE_TAGS = {"rect", "circle", "ellipse", "line", "polyline", "polygon", "path"}
    n = 0
    for el in root.iter():
        tag = el.tag.split("}", 1)[-1] if el.tag.startswith("{") else el.tag
        if tag in SHAPE_TAGS:
            n += 1
    return n


def looks_like_svg(p: Path) -> bool:
    if not p.exists() or p.is_dir():
        return False
    try:
        head = p.read_bytes()[:256].lstrip()
    except Exception:
        return False
    return head.startswith(b"<svg") or b"<svg" in head


# ------------------------------ main -----------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--geometry", required=False)
    ap.add_argument("--points", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cascade-stages", type=int, default=0)
    ap.add_argument("--export-svg", action="store_true")
    ap.add_argument("--enable-plugin-exec", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument(
        "--force-append-svg",
        action="store_true",
        help="If output has no extension, write/rename to .svg and overwrite if present",
    )
    args = ap.parse_args(argv)

    started = datetime.now(timezone.utc).isoformat()

    inp = Path(args.input)
    out = Path(args.output)

    print(
        f"[trace] src_input path={inp} exists={inp.exists()} size={inp.stat().st_size if inp.exists() else 0} sha256={sha256_file(inp)[:64] if inp.exists() else 'NA'}"
    )

    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "cubist_cli.py"),
        "--input",
        str(inp),
        "--output",
        str(out),
    ]
    if args.geometry:
        cmd += ["--geometry", args.geometry]
    if args.export_svg:
        cmd += ["--export-svg"]
    if args.enable_plugin_exec:
        cmd += ["--enable-plugin-exec"]
    if args.cascade_stages:
        cmd += ["--cascade-stages", str(args.cascade_stages)]
    cmd += ["--points", str(args.points), "--seed", str(args.seed)]

    print(f"[run_cli] CMD: {' '.join(map(repr, cmd)).replace('\\', '\\')}")

    # Run the CLI and capture both out/err so plugin traces show up
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        for line in proc.stdout.splitlines():
            if line.strip():
                print(f"[cli] {line}")
    if proc.stderr:
        for line in proc.stderr.splitlines():
            if line.strip():
                print(f"[cli-err] {line}")

    rc = proc.returncode

    # Post-process: prefer an explicit .svg if it exists; otherwise, attach one.
    base = out
    target = out if out.suffix.lower() == ".svg" else out.with_suffix(".svg")

    base_exists = base.exists()
    target_exists = target.exists()
    print(
        f"[trace] post: base_exists={base_exists} target_exists={target_exists} base={base} target={target}"
    )

    svg_path = target if target_exists else base

    if not target_exists and base_exists:
        # We have a file with no extension. If it looks like SVG, normalize the name.
        if looks_like_svg(base):
            try:
                if args.force_append_svg and target.exists():
                    try:
                        target.unlink()
                    except FileNotFoundError:
                        pass
                if not target.exists():
                    base.rename(target)
                    print(f"[fix] appended .svg -> {target}")
                svg_path = target
            except Exception as e:  # noqa: BLE001
                print(f"[warn] could not append .svg: {e}")
        else:
            # leave as-is (could be binary or temp)
            svg_path = base
    elif target_exists:
        svg_path = target

    shapes = 0
    size = 0
    if svg_path.exists():
        size = svg_path.stat().st_size
        shapes = count_svg_shapes(svg_path)

    print(f"[trace] outputs={int(svg_path.exists())} svg_shapes={shapes} size={size}")

    # Write a tiny audit trace for the UI to consume
    audit = {
        "started": started,
        "input": str(inp),
        "output": str(svg_path),
        "geometry": args.geometry,
        "rc": rc,
        "svg_exists": svg_path.exists(),
        "svg_shapes": shapes,
        "svg_size": size,
    }
    try:
        (svg_path.parent / "trace.json").write_text(
            json.dumps(audit, indent=2), encoding="utf-8"
        )
        print(f"[trace] wrote audit {svg_path.parent / 'trace.json'}")
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
