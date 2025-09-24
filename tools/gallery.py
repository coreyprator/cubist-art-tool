from __future__ import annotations

from pathlib import Path
from typing import Iterable

try:
    from svg_checks import count_svg_shapes  # type: ignore
except Exception:  # pragma: no cover

    def count_svg_shapes(_p: Path) -> int:
        return 0


def iter_svgs(batch_dir: Path) -> Iterable[Path]:
    for p in sorted(batch_dir.rglob("*.svg")):
        # show only leaf files (skip duplicate trace.json etc.)
        if p.is_file():
            yield p


def write_gallery(batch_dir: Path) -> Path:
    batch_dir = Path(batch_dir)
    out = batch_dir / "gallery.html"

    cards = []
    for svg in iter_svgs(batch_dir):
        rel = svg.relative_to(batch_dir)
        shapes = count_svg_shapes(svg)
        cards.append(
            """
            <figure class='card'>
              <object type="image/svg+xml" data="{escape(str(rel)).replace('\\\\','/')}#svgView(viewBox(0,0,100,100))"></object>
              <figcaption>{escape(str(rel))} — shapes: {shapes}</figcaption>
            </figure>
            """
        )

    body = "<p>No SVGs present.</p>" if not cards else "\n".join(cards)

    html = """
<!doctype html>
<meta charset="utf-8"/>
<title>Gallery — {escape(str(batch_dir))}</title>
<style>
  body{{font-family:system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:1rem;}}
  h1{{font-size:clamp(1.2rem,2vw,1.8rem);}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:1rem;}}
  .card{{background:#fafafa;border:1px solid #eee;border-radius:10px;padding:.5rem;}}
  .card object{{width:100%;height:60vh;}}
  figcaption{{font-size:.8rem;color:#555;margin-top:.25rem;}}
</style>
<h1>Gallery — {escape(str(batch_dir))}</h1>
<div class="grid">{body}</div>
"""

    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":  # pragma: no cover
    import sys

    print(write_gallery(Path(sys.argv[1])))
