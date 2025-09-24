from __future__ import annotations
import argparse
import os
import sys
import subprocess
from pathlib import Path

GEOMS = ["delaunay", "voronoi", "rectangles"]

GALLERY_HTML = """<!doctype html>
<meta charset="utf-8">
<title>Cubist Output Gallery</title>
<style>
  body{font-family:system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:20px}
  h1{margin:0 0 12px 0}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
  figure{margin:0;padding:12px;border:1px solid #ddd;border-radius:12px;background:#fafafa}
  figcaption{font-size:12px;color:#555;margin-top:8px;word-break:break-word}
  iframe{width:100%;height:360px;border:0;background:white}
</style>
<h1>Cubist — Generated SVGs</h1>
<div class="grid">
{cards}
</div>
"""


def run(cmd: list[str]) -> int:
    print(">", " ".join(cmd))
    r = subprocess.run(cmd)
    return r.returncode


def write_gallery(out_dir: Path, svgs: list[Path]) -> Path:
    cards = []
    for p in svgs:
        rel = p.relative_to(out_dir).as_posix()
        cards.append(
            f'<figure><iframe src="{rel}"></iframe><figcaption>{rel}</figcaption></figure>'
        )
    html = GALLERY_HTML.replace("{cards}", "\n".join(cards))
    html_path = out_dir / "gallery.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"[gallery] Wrote: {html_path}")
    return html_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="path to raster image input")
    ap.add_argument("--points_cascade", type=int, default=1200)
    ap.add_argument("--points_poisson", type=int, default=800)
    ap.add_argument("--seed", type=int, default=123)
    ap.add_argument("--poisson_min_px", type=int, default=22)
    ap.add_argument("--open", action="store_true", help="open gallery.html when done")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    cli = str(root / "cubist_cli.py")
    out_dir = root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    made: list[Path] = []

    # 1) Cascades
    for g in GEOMS:
        out = out_dir / f"prod_{g}_cascade.svg"
        cmd = [
            sys.executable,
            cli,
            "--pipeline",
            "--input",
            args.input,
            "--output",
            str(out),
            "--geometry",
            g,
            "--points",
            str(args.points_cascade),
            "--seed",
            str(args.seed),
            "--cascade-stages",
            "3",
            "--cascade-fill",
            "image",
            "--export-svg",
        ]
        if run(cmd) != 0:
            print(f"[warn] failed: {out}")
        else:
            made.append(out)

    # 2) Poisson
    for g in GEOMS:
        out = out_dir / f"prod_{g}_poisson.svg"
        cmd = [
            sys.executable,
            cli,
            "--pipeline",
            "--input",
            args.input,
            "--output",
            str(out),
            "--geometry",
            g,
            "--points",
            str(args.points_poisson),
            "--seed",
            str(args.seed),
            "--param",
            "seed_mode=poisson",
            "--param",
            f"poisson_min_px={args.poisson_min_px}",
            "--export-svg",
        ]
        if run(cmd) != 0:
            print(f"[warn] failed: {out}")
        else:
            made.append(out)

    # 3) Gallery
    html = write_gallery(out_dir, made)
    if args.open:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(html))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(html)], check=False)
            else:
                subprocess.run(["xdg-open", str(html)], check=False)
        except Exception as e:
            print(f"[warn] could not auto-open gallery: {e}")


if __name__ == "__main__":
    main()
