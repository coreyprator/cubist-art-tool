from __future__ import annotations
import argparse
import re
from pathlib import Path
import sys
from typing import List, Tuple

try:
    from PIL import Image
except Exception:
    Image = None

from palette_mapper import parse_css_color, rgb_to_hex, map_to_palette


def top_image_colors(image_path: Path, n: int = 8) -> List[Tuple[int, int, int]]:
    if Image is None:
        return []
    try:
        with Image.open(str(image_path)) as im:
            im = im.convert("RGBA")
            im.thumbnail((300, 300))
            pixels = [px for px in im.getdata() if px[3] > 0]
            if not pixels:
                return []
            pal = Image.new("RGBA", im.size)
            pal.putdata(pixels)
            q = pal.convert("P", palette=Image.ADAPTIVE, colors=n)
            p = q.convert("RGB")
            colors = p.getcolors(p.size[0] * p.size[1]) or []
            colors.sort(reverse=True)
            out = []
            seen = set()
            for c in colors[:n]:
                rgb = c[1]
                if rgb not in seen:
                    seen.add(rgb)
                    out.append(rgb)
            return out
    except Exception:
        return []


_fill_re = re.compile(r'fill=["\']?([^"\' >]+)', re.I)


def find_svg_fills(svg_path: Path) -> List[str]:
    s = svg_path.read_text(encoding="utf-8", errors="ignore")
    fills = _fill_re.findall(s)
    return fills


def parse_fills_to_rgb(fills: List[str]) -> List[Tuple[int, int, int]]:
    rgbs = []
    for f in fills:
        c = parse_css_color(f)
        if c:
            rgbs.append(c)
    return rgbs


def analyze(
    input_image: Path, out_dir: Path, avg_thresh: float = 40.0, pct_thresh: float = 0.3
) -> int:
    palette = top_image_colors(input_image, 12)
    if not palette:
        print(
            "No input palette (Pillow missing or extraction failed) — skipping diff check"
        )
        return 0
    print("Input palette:", ", ".join(rgb_to_hex(c) for c in palette))
    # gather fills from svgs under out_dir
    svg_paths = list(out_dir.rglob("*.svg"))
    exported_colors = []
    for sp in svg_paths:
        fills = find_svg_fills(sp)
        exported_colors += parse_fills_to_rgb(fills)
    if not exported_colors:
        print("No fills found in SVGs — nothing to compare")
        return 0
    # compute nearest distances
    dists = []
    unmatched = 0
    for col in exported_colors:
        best, dist = map_to_palette(col, palette)
        dists.append(dist)
        if dist > avg_thresh:
            unmatched += 1
    avg = sum(dists) / len(dists)
    pct_unmatched = unmatched / len(dists)
    print(
        f"Exported fills: {len(dists)}  avg_dist={avg:.1f}  pct_unmatched={pct_unmatched:.2f}"
    )
    # fail conditions
    if avg > avg_thresh or pct_unmatched > pct_thresh:
        print("PALETTE DIFF FAILED: thresholds exceeded")
        return 2
    print("Palette diff OK")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--avg-threshold", type=float, default=40.0)
    p.add_argument("--pct-threshold", type=float, default=0.3)
    args = p.parse_args()
    code = analyze(
        Path(args.input), Path(args.out), args.avg_threshold, args.pct_threshold
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
