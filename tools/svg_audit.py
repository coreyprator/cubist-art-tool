# tools/svg_audit.py
from __future__ import annotations

from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

SVG_NS = "{http://www.w3.org/2000/svg}"
SHAPE_TAGS = {"rect", "circle", "ellipse", "line", "polyline", "polygon", "path"}


def _strip(tag: str) -> str:
    return tag.split("}", 1)[-1] if tag.startswith("{") else tag


def count_shapes(svg_path: Path) -> int:
    try:
        root = ET.parse(svg_path).getroot()
    except Exception:
        return 0
    n = 0
    for el in root.iter():
        if _strip(el.tag) in SHAPE_TAGS:
            n += 1
    return n


def summarize(svg_path: Path) -> dict:
    svg_path = Path(svg_path)
    if not svg_path.exists():
        return {"exists": False}
    try:
        root = ET.parse(svg_path).getroot()
    except Exception as e:
        return {"exists": True, "ok": False, "error": str(e)}

    counts = Counter()
    fills = Counter()
    for el in root.iter():
        tag = _strip(el.tag)
        counts[tag] += 1
        if tag in SHAPE_TAGS:
            fill = el.get("fill")
            if fill:
                fills[fill] += 1

    return {
        "exists": True,
        "ok": True,
        "width": root.get("width"),
        "height": root.get("height"),
        "viewBox": root.get("viewBox"),
        "shapes": sum(counts.get(t, 0) for t in SHAPE_TAGS),
        "tag_counts": dict(counts),
        "fills_unique": len(fills),
        "fills_top": fills.most_common(8),
    }


if __name__ == "__main__":
    import json
    import sys

    for p in sys.argv[1:]:
        info = summarize(Path(p))
        print(Path(p).name, json.dumps(info, indent=2))
