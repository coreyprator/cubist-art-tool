from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

# Robust import for the trace helpers
try:
    from ._trace import TRACE, t, dump, try_stats, file_info  # type: ignore
except Exception:  # pragma: no cover
    from geometry_plugins._trace import TRACE, t, dump, try_stats, file_info  # type: ignore

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None  # type: ignore

Point = Tuple[float, float]
Sample = Tuple[float, float, float]

# ---------------------------------------------------------------------------------
# Bridson Poisson‑disk sampler in rectangle


def _poisson_samples(
    width: int, height: int, r: float, k: int, seed: int
) -> List[Point]:
    random.seed(int(seed))
    cell = r / math.sqrt(2)
    grid_w = int(math.ceil(width / cell))
    grid_h = int(math.ceil(height / cell))
    grid: List[List[int | None]] = [[None] * grid_h for _ in range(grid_w)]

    def in_bounds(p: Point) -> bool:
        x, y = p
        return 0 <= x < width and 0 <= y < height

    def grid_coords(p: Point) -> Tuple[int, int]:
        x, y = p
        return int(x / cell), int(y / cell)

    def far_enough(p: Point) -> bool:
        gx, gy = grid_coords(p)
        for ix in range(max(gx - 2, 0), min(gx + 3, grid_w)):
            for iy in range(max(gy - 2, 0), min(gy + 3, grid_h)):
                j = grid[ix][iy]
                if j is None:
                    continue
                px, py = samples[j]
                if (p[0] - px) ** 2 + (p[1] - py) ** 2 < r**2:
                    return False
        return True

    # initial point
    p0 = (random.random() * width, random.random() * height)
    samples: List[Point] = [p0]
    active: List[int] = [0]
    gx, gy = grid_coords(p0)
    grid[gx][gy] = 0

    while active:
        idx = random.choice(active)
        base = samples[idx]
        found = False
        for _ in range(k):
            ang = random.random() * 2 * math.pi
            rad = r * (1 + random.random())
            cand = (base[0] + math.cos(ang) * rad, base[1] + math.sin(ang) * rad)
            if in_bounds(cand) and far_enough(cand):
                samples.append(cand)
                active.append(len(samples) - 1)
                gx, gy = grid_coords(cand)
                grid[gx][gy] = len(samples) - 1
                found = True
        if not found:
            active.remove(idx)

    return samples


# ---------------------------------------------------------------------------------


def _auto_radius(w: int, h: int, points: int) -> float:
    area = float(w * h)
    # Invert the disk packing density roughly to hit target points
    return max(1.5, math.sqrt((area / max(points, 1)) / math.pi) * 0.85)


def _sample_color(img, x: float, y: float) -> str:
    if img is None:
        return "#000"
    xi = min(max(int(x), 0), img.width - 1)
    yi = min(max(int(y), 0), img.height - 1)
    r, g, b = img.getpixel((xi, yi))[:3]
    return f"#{r:02x}{g:02x}{b:02x}"


# Public API expected by cubist_cli


def generate(
    *,
    input: str | None = None,
    output: str | None = None,
    points: int = 1000,
    seed: int = 0,
    w: int | None = None,
    h: int | None = None,
    params: dict | None = None,
) -> int:
    """Poisson‑disk circles with optional color sampling from the input image."""
    if output is None:
        raise ValueError("poisson_disk.generate requires an output path")

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)

    img = None
    if w is not None and h is not None and w > 0 and h > 0:
        W, H = int(w), int(h)
    elif input and Image is not None:
        p = Path(input)
        if p.exists():
            img = Image.open(p).convert("RGB")  # type: ignore
            W, H = img.width, img.height
        else:
            W, H = 100, 100
    else:
        W, H = 100, 100

    random.seed(int(seed) if seed is not None else 0)

    r = _auto_radius(W, H, int(points))
    k = int((params or {}).get("k", 30))

    if TRACE:
        t(f"canvas={W}x{H} total_points~={points} seed={seed} radius={r} k={k}")

    pts = _poisson_samples(W, H, r, k, int(seed))
    samples: list[Sample] = [(x, y, r) for (x, y) in pts]
    if TRACE:
        dump("samples", try_stats(samples))

    if img is None and input and Image is not None:
        p = Path(input)
        if p.exists():
            try:
                img = Image.open(p).convert("RGB")  # type: ignore
            except Exception:
                img = None

    svg_path = out if out.suffix.lower() == ".svg" else out.with_suffix(".svg")
    with svg_path.open("w", encoding="utf-8") as f:
        f.write(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
        )
        for x, y, rr in samples:
            fill = _sample_color(img, x, y) if img is not None else "#000"
            f.write(
                f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="{rr:.2f}" fill="{fill}" stroke="none"/>\n'
            )
        f.write("</svg>\n")

    if TRACE:
        t(f"wrote svg {file_info(svg_path)}")

    return 0
