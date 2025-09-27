from __future__ import annotations
import re
from typing import List, Tuple, Optional
import math


# Simple CSS color parser (hex, rgb(), rgba(), hsl())
def parse_css_color(s: str) -> Optional[Tuple[int, int, int]]:
    try:
        s = s.strip()
        if s.startswith("#"):
            h = s[1:]
            if len(h) == 3:
                h = "".join(ch * 2 for ch in h)
            if len(h) == 6:
                return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
            return None
        m = re.match(
            r"rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)", s, flags=re.I
        )
        if m:
            r, g, b = m.groups()
            return (int(float(r)), int(float(g)), int(float(b)))
        m = re.match(
            r"hsla?\(\s*([0-9.]+)\s*,\s*([0-9.]+)%\s*,\s*([0-9.]+)%", s, flags=re.I
        )
        if m:
            h, sp, lp = map(float, m.groups())
            h = h % 360 / 360.0
            s_v = sp / 100.0
            l = lp / 100.0

            def hue2rgb(p, q, t):
                if t < 0:
                    t += 1
                if t > 1:
                    t -= 1
                if t < 1 / 6:
                    return p + (q - p) * 6 * t
                if t < 1 / 2:
                    return q
                if t < 2 / 3:
                    return p + (q - p) * (2 / 3 - t) * 6
                return p

            if s_v == 0:
                r = g = b = l
            else:
                q = l * (1 + s_v) if l < 0.5 else l + s_v - l * s_v
                p = 2 * l - q
                r = hue2rgb(p, q, h + 1 / 3)
                g = hue2rgb(p, q, h)
                b = hue2rgb(p, q, h - 1 / 3)
            return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))
        n = s.lower()
        name_map = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "red": (255, 0, 0),
            "green": (0, 128, 0),
            "blue": (0, 0, 255),
        }
        if n in name_map:
            return name_map[n]
    except Exception:
        pass
    return None


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


# CIE Lab helpers for perceptual distance
def _srgb_chan_to_linear(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgb_to_xyz(rgb: Tuple[int, int, int]):
    r_lin = _srgb_chan_to_linear(rgb[0])
    g_lin = _srgb_chan_to_linear(rgb[1])
    b_lin = _srgb_chan_to_linear(rgb[2])
    x = r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375
    y = r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750
    z = r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041
    return (x, y, z)


def _xyz_to_lab(xyz):
    x, y, z = xyz
    xn, yn, zn = 0.95047, 1.00000, 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t) + (16.0 / 116.0)

    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return (L, a, b)


def rgb_to_lab(rgb: Tuple[int, int, int]):
    return _xyz_to_lab(_rgb_to_xyz(rgb))


def color_distance(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    try:
        la = rgb_to_lab(a)
        lb = rgb_to_lab(b)
        return math.sqrt(
            (la[0] - lb[0]) ** 2 + (la[1] - lb[1]) ** 2 + (la[2] - lb[2]) ** 2
        )
    except Exception:
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def map_to_palette(
    color: Tuple[int, int, int], palette: List[Tuple[int, int, int]]
) -> Tuple[Tuple[int, int, int], float]:
    """Return nearest palette color and distance."""
    best = min(palette, key=lambda p: color_distance(color, p))
    return best, color_distance(color, best)
