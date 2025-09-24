from __future__ import annotations
import json
import zipfile
from pathlib import Path
from datetime import datetime


def write_gallery(root: Path):
    root = Path(root)

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    traces = sorted(root.rglob("trace.json"))
    py = np = sc = None
    if traces:
        j = json.loads(traces[0].read_text(encoding="utf-8"))
        env = j.get("env", {})
        py, np, sc = env.get("python"), env.get("numpy"), env.get("scipy")
    html = [
        """<!doctype html><meta charset="utf-8"><title>{esc(root.name)}</title>
    <style>body{{font-family:system-ui,sans-serif;margin:22px}} code{{font-family:ui-monospace}} .geom{{margin:14px 0}} .warn{{color:#b00}}</style>
    <h1>{esc(root.name)}</h1>
    <h3>Diagnostics</h3>
    <div><b>Python</b><br><code>{esc(py or '')}</code></div>
    <div><b>NumPy</b><br><code>{esc(np or '')}</code></div>
    <div><b>SciPy</b><br><code>{esc(sc or '')}</code></div>
    """
    ]
    for gdir in sorted([p for p in root.iterdir() if p.is_dir()]):
        t = gdir / "trace.json"
        if not t.exists():
            continue
        js = json.loads(t.read_text(encoding="utf-8"))
        geom = js.get("meta", {}).get("geometry", gdir.name)
        out_svg = js.get("outputs", {}).get("svg_path")
        size = js.get("outputs", {}).get("svg_size", 0)
        shapes = js.get("outputs", {}).get("svg_shapes", 0)
        if out_svg:
            html.append(
                f'<div class="geom"><b>{geom}</b> — {shapes} shapes • {size/1024:.1f} KB</div>'
            )
        else:
            html.append(f'<div class="geom warn">⚠ No SVG for {geom}</div>')
    html.append("</body>")
    (root / "index.html").write_text("\n".join(html), encoding="utf-8")


def make_support_bundle_zip(root: Path) -> str:
    root = Path(root)
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    zpath = root / f"support_{ts}.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for t in sorted(root.rglob("trace.json")):
            gdir = t.parent
            for name in ["trace.json", "stdout.txt", "stderr.txt"]:
                p = gdir / name
                if p.exists():
                    zf.write(p, p.relative_to(root).as_posix())
        # env.txt (simple)
        env_txt = []
        try:
            import sys

            env_txt.append("Python: " + sys.version.replace("\\n", " "))
        except Exception:
            env_txt.append("Python: <unknown>")
        try:
            import numpy

            env_txt.append(
                "NumPy : " + getattr(numpy, "__version__", "<not installed>")
            )
        except Exception:
            env_txt.append("NumPy : <not installed>")
        try:
            import importlib

            env_txt.append(
                "SciPy : "
                + getattr(
                    importlib.import_module("scipy"), "__version__", "<not installed>"
                )
            )
        except Exception:
            env_txt.append("SciPy : <not installed>")
        zf.writestr("env.txt", "\n".join(env_txt))
    return str(zpath)
