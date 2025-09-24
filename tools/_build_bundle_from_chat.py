# tools/_build_bundle_from_chat.py
from __future__ import annotations
import json
import hashlib
import zipfile
import datetime
import argparse


def build_zip(zpath: str):
    files = {}

    # -------- tools/prod_ui.py (UI fix + integrated verbose/probe + Export bundle) --------
    files["tools/prod_ui.py"] = r'''from __future__ import annotations
import sys
import os
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, request, send_file, Response
from werkzeug.utils import secure_filename
import subprocess

app = Flask(__name__)

_state = {
    "running": False,
    "log": [],
    "last_output_root": None,
    "thread": None,
}

GEOMS = ["poisson_disk","scatter_circles","rectangles","voronoi","delaunay","concentric_circles"]

def _log(msg: str):
    stamp = time.strftime("[%H:%M:%S] ")
    line = f"{stamp}{msg}"
    _state["log"].append(line)
    # soft cap
    if len(_state["log"]) > 5000:
        _state["log"] = _state["log"][-3000:]

@app.get("/")
def index():
    # Simple HTML page (no template file needed)
    return Response(f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Cubist — Batch Runner</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 22px; }}
    .row {{ margin: 6px 0; }}
    input[type=text] {{ width: 520px; }}
    textarea {{ width: 100%; height: 420px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .pill {{ display:inline-block; padding:6px 10px; border:1px solid #ddd; border-radius:18px; margin-right:8px; }}
    .btn {{ padding:6px 10px; margin-right:6px; }}
    .minor {{ color:#666; }}
  </style>
</head>
<body>
  <h1>Cubist — Batch Runner</h1>

  <div class="row">
    <label>Input image:</label>
    <input id="input" type="text" value="" />
    <button class="btn" onclick="upload()">Upload…</button>
  </div>
  <div class="row">
    <label>Points:</label> <input id="points" type="text" value="4000" size="6" />
    &nbsp; Seed: <input id="seed" type="text" value="42" size="6" />
    &nbsp; Cascade stages: <input id="stages" type="text" value="3" size="6" />
  </div>
  <div class="row">
    <label><input id="export_svg" type="checkbox" checked /> export SVG</label>
    <label style="margin-left:18px;"><input id="plugin" type="checkbox" checked /> enable plugin exec</label>
    <label style="margin-left:18px;"><input id="verbose" type="checkbox" /> Verbose + Probe</label>
  </div>
  <div class="row">
    {"".join(f'<label class="pill"><input type="checkbox" checked id="g_{g}"/> {g}</label>' for g in GEOMS)}
  </div>
  <div class="row">
    <button class="btn" onclick="run()">Run</button>
    <button class="btn" onclick="idle()">Idle</button>
    <button class="btn" onclick="copyAll()">Copy All</button>
    <button class="btn" onclick="saveLog()">Save Log</button>
    <button class="btn" onclick="exportBundle()">Export Support Bundle</button>
    <span class="minor" id="hint"></span>
  </div>

  <h3>Log</h3>
  <textarea id="log" readonly></textarea>

<script>
async function poll(){
  const r = await fetch('/status');
  const js = await r.json();
  document.getElementById('log').value = js.log.join('\\n');
  setTimeout(poll, 1000);
}
poll();

function gather(){
  const geoms = %s.filter(g => document.getElementById('g_'+g).checked);
  return {
    input: document.getElementById('input').value,
    points: document.getElementById('points').value,
    seed: document.getElementById('seed').value,
    stages: document.getElementById('stages').value,
    export_svg: document.getElementById('export_svg').checked,
    plugin: document.getElementById('plugin').checked,
    verbose: document.getElementById('verbose').checked,
    geoms: geoms,
  };
}

async function run(){
  const body = JSON.stringify(gather());
  const r = await fetch('/run', {method:'POST', headers:{'Content-Type':'application/json'}, body});
  const js = await r.json();
  document.getElementById('hint').textContent = js.msg || '';
}

async function idle(){
  const r = await fetch('/idle', {method:'POST'});
  const js = await r.json();
  document.getElementById('hint').textContent = js.msg || '';
}

async function upload(){
  const f = prompt('Enter absolute path to image (or cancel):');
  if(!f) return;
  document.getElementById('input').value = f;
}

function copyAll(){
  const ta = document.getElementById('log');
  ta.select(); document.execCommand('copy'); ta.selectionStart = ta.selectionEnd;
}

async function saveLog(){
  const r = await fetch('/save_log'); const js = await r.json();
  document.getElementById('hint').textContent = 'Saved -> ' + js.path;
}

async function exportBundle(){
  const r = await fetch('/export_bundle');
  if (r.status === 200){
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'support_bundle.zip'; a.click();
    URL.revokeObjectURL(url);
  } else {
    alert('No bundle yet (run first).');
  }
}
</script>
</body></html>
        """ % json.dumps(GEOMS)), mimetype="text/html")

@app.get("/status")
def status():
    return {"running": _state["running"], "log": _state["log"], "last_output_root": _state["last_output_root"]}

@app.post("/save_log")
def save_log():
    p = Path("output") / "production" / "_debug"
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    out = p / f"log_{ts}.txt"
    out.write_text("\n".join(_state["log"]), encoding="utf-8")
    return {"ok": True, "path": str(out)}

@app.post("/idle")
def idle():
    _state["running"] = False
    return {"ok": True, "msg": "Set idle."}

def _run_worker(args):
    _state["running"] = True
    try:
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        out_root = Path("output/production") / ts
        _state["last_output_root"] = str(out_root)
        _log(f"[ui] Running {len(args['geoms'])} geometries into {out_root}…")

        for g in args["geoms"]:
            out_dir = out_root / g
            out_prefix = out_dir / f"frame_{g}"
            out_dir.mkdir(parents=True, exist_ok=True)

            cmd = [
                sys.executable, "tools/run_cli.py",
                "--input", args["input"],
                "--output", str(out_prefix),
                "--geometry", g,
                "--points", str(args["points"]),
                "--seed", str(args["seed"]),
                "--cascade-stages", str(args["stages"]),
            ]
            if args.get("export_svg"): cmd.append("--export-svg")
            if args.get("plugin"): cmd.append("--enable-plugin-exec")
            cmd += ["--force-append-svg", "--verbose"]

            _log(f"[cmd] CMD: {json.dumps(cmd)}")
            # stream run_cli's stdout line-by-line
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(Path('.').resolve()))
            for line in proc.stdout:
                _log("[cli] " + line.rstrip("\n"))
            rc = proc.wait()
            if rc != 0:
                _log(f"[ui] WARN: run_cli.py exited rc={rc} for {g}")
    except Exception as e:  # noqa: BLE001
        _log(f"[ui] ERROR: {e}")
    finally:
        _state["running"] = False
        # attempt to build a tiny gallery
        try:
            from tools.support_bundle import write_gallery
            write_gallery(Path(_state["last_output_root"]))
            _log(f"[ui] Wrote gallery -> {Path(_state['last_output_root'])/'index.html'}")
            _log("[ui] Opening gallery (if present)…")
        except Exception as e:  # noqa: BLE001
            _log(f"[ui] gallery error: {e}")

@app.post("/run")
def run():
    if _state["running"]:
        return {"ok": False, "msg": "Already running"}
    args = request.get_json(force=True)
    _state["thread"] = threading.Thread(target=_run_worker, args=(args,), daemon=True)
    _state["thread"].start()
    return {"ok": True, "msg": "Started."}

@app.get("/export_bundle")
def export_bundle():
    root = _state.get("last_output_root")
    if not root or not Path(root).exists():
        return Response("No bundle", status=404)
    try:
        from tools.support_bundle import make_support_bundle_zip
        zpath = make_support_bundle_zip(Path(root))
        return send_file(zpath, as_attachment=True, download_name="support_bundle.zip")
    except Exception as e:  # noqa: BLE001
        return Response(str(e), status=500)

if __name__ == "__main__":
    app.run("127.0.0.1", 5123, debug=False)
'''

    # -------- tools/run_cli.py (strict write verification + trace.json) --------
    files["tools/run_cli.py"] = r"""from __future__ import annotations
import argparse, json, os, sys, subprocess, time, hashlib
from pathlib import Path
from datetime import datetime

# local SVG audit (counts shapes; tolerant parse)
try:
    from tools.svg_audit import count_shapes
except Exception:
    def count_shapes(_): return 0

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True, help="output prefix (without extension)")
    ap.add_argument("--geometry", required=True)
    ap.add_argument("--points", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--param", action="append", default=[])
    ap.add_argument("--export-svg", action="store_true")
    ap.add_argument("--cascade-stages", type=int, default=3)
    ap.add_argument("--enable-plugin-exec", action="store_true")
    ap.add_argument("--pipeline")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--force-append-svg", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    out_prefix = Path(args.output)
    geom_dir = out_prefix.parent
    geom_dir.mkdir(parents=True, exist_ok=True)
    expected_svg = out_prefix.with_suffix(".svg")

    # run cubist_cli.py
    cmd = [sys.executable, "cubist_cli.py",
           "--input", args.input,
           "--output", str(out_prefix),
           "--geometry", args.geometry,
           "--points", str(args.points),
           "--seed", str(args.seed),
           "--cascade-stages", str(args.cascade_stages)]
    if args.export_svg: cmd.append("--export-svg")
    if args.enable_plugin_exec: cmd.append("--enable-plugin-exec")
    if args.force_append_svg: cmd.append("--force-append-svg")
    if args.pipeline: cmd += ["--pipeline", args.pipeline]
    if args.quiet: cmd.append("--quiet")

    stdout_path = geom_dir / "stdout.txt"
    stderr_path = geom_dir / "stderr.txt"
    with open(stdout_path, "w", encoding="utf-8", newline="") as so, \
         open(stderr_path, "w", encoding="utf-8", newline="") as se:
        proc = subprocess.Popen(cmd, cwd=str(Path(".").resolve()), stdout=so, stderr=se, text=True)
        rc = proc.wait()

    # env probe
    pyver = sys.version.replace("\n"," ")
    try:
        import numpy as _np; npver = _np.__version__
    except Exception: npver = "<not installed>"
    try:
        import importlib as _il; sciver = getattr(_il.import_module("scipy"), "__version__", "<not installed>")
    except Exception: sciver = "<not installed>"

    # verify write (retry: slow FS / sync lag)
    svg_exists = False
    svg_size = 0
    svg_sha = None
    svg_shapes = 0
    for _ in range(20):  # ~2s
        if expected_svg.exists():
            svg_size = expected_svg.stat().st_size
            if svg_size > 0:
                svg_exists = True
                break
        time.sleep(0.1)

    if svg_exists:
        try: svg_sha = sha256_of(expected_svg)
        except Exception: svg_sha = None
        try: svg_shapes = count_shapes(expected_svg)
        except Exception: svg_shapes = 0

    nearby = sorted([str(p) for p in geom_dir.glob("*.svg")])
    run_scan = sorted([str(p) for p in Path(".").rglob(out_prefix.name + "*.svg")])[:20]

    trace = {
        "meta": {
            "geometry": args.geometry,
            "rc": rc,
        },
        "cmd": cmd,
        "cwd": str(Path(".").resolve()),
        "sys_path_head": sys.path[:12],
        "env": {
            "python": pyver,
            "numpy": npver,
            "scipy": sciver,
            "PATH_head": os.environ.get("PATH","").split(os.pathsep)[:10],
        },
        "outputs": {
            "expected_svg": str(expected_svg),
            "svg_exists": svg_exists,
            "svg_path": str(expected_svg) if svg_exists else None,
            "svg_size": svg_size,
            "svg_sha256": svg_sha,
            "svg_shapes": svg_shapes,
            "geom_dir_listing": [
                {"name": p.name, "is_dir": p.is_dir(), "size": (p.stat().st_size if p.is_file() else None),
                 "mtime": int(p.stat().st_mtime)} for p in sorted(geom_dir.iterdir())
            ] if geom_dir.exists() else [],
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
        },
        "fallback": {
            "nearby_scan": nearby,
            "run_scan": run_scan,
        },
        "hints": []
    }
    (geom_dir / "trace.json").write_text(json.dumps(trace, indent=2), encoding="utf-8")

    print(json.dumps({
        "ts": None,
        "input": args.input,
        "output": str(out_prefix),
        "geometry": args.geometry,
        "rc": rc,
        "svg_exists": svg_exists,
        "svg_path": str(expected_svg) if svg_exists else None,
        "svg_shapes": svg_shapes,
        "svg_size": svg_size
    }))

    if svg_exists:
        print(f"Wrote: {out_prefix}")
    else:
        if args.export_svg and rc == 0:
            return 3
    return 0 if (rc == 0 and (not args.export_svg or svg_exists)) else (rc or 1)

if __name__ == "__main__":
    sys.exit(main())
"""

    # -------- tools/svg_audit.py (used by run_cli verification) --------
    files["tools/svg_audit.py"] = r"""from __future__ import annotations
from pathlib import Path
from xml.etree import ElementTree as ET
from collections import Counter

SVG_NS = "{http://www.w3.org/2000/svg}"
SHAPE_TAGS = {"rect","circle","ellipse","line","polyline","polygon","path"}

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
    except Exception as e:  # noqa: BLE001
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
        "exists": True, "ok": True,
        "width": root.get("width"),
        "height": root.get("height"),
        "viewBox": root.get("viewBox"),
        "shapes": sum(counts.get(t,0) for t in SHAPE_TAGS),
        "tag_counts": dict(counts),
        "fills_unique": len(fills),
        "fills_top": fills.most_common(8),
    }
"""

    # -------- tools/support_bundle.py (gallery + bundle writer) --------
    files["tools/support_bundle.py"] = r'''from __future__ import annotations
import os, json, io, zipfile
from pathlib import Path
from datetime import datetime

def write_gallery(root: Path):
    root = Path(root)
    def esc(s): return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    traces = sorted(root.rglob("trace.json"))
    py = np = sc = None
    if traces:
        j = json.loads(traces[0].read_text(encoding="utf-8"))
        env = j.get("env", {})
        py, np, sc = env.get("python"), env.get("numpy"), env.get("scipy")
    html = [f"""<!doctype html><meta charset="utf-8"><title>{esc(root.name)}</title>
    <style>body{{font-family:system-ui,sans-serif;margin:22px}} code{{font-family:ui-monospace}} .geom{{margin:14px 0}} .warn{{color:#b00}}</style>
    <h1>{esc(root.name)}</h1>
    <h3>Diagnostics</h3>
    <div><b>Python</b><br><code>{esc(py or '')}</code></div>
    <div><b>NumPy</b><br><code>{esc(np or '')}</code></div>
    <div><b>SciPy</b><br><code>{esc(sc or '')}</code></div>
    """ ]
    for gdir in sorted([p for p in root.iterdir() if p.is_dir()]):
        t = gdir / "trace.json"
        if not t.exists():
            continue
        js = json.loads(t.read_text(encoding="utf-8"))
        geom = js.get("meta",{}).get("geometry", gdir.name)
        out_svg = js.get("outputs",{}).get("svg_path")
        size = js.get("outputs",{}).get("svg_size",0)
        shapes = js.get("outputs",{}).get("svg_shapes",0)
        if out_svg:
            html.append(f'<div class="geom"><b>{geom}</b> — {shapes} shapes • {size/1024:.1f} KB</div>')
        else:
            html.append(f'<div class="geom warn">⚠ No SVG for {geom}</div>')
    html.append("</body>")
    (root/"index.html").write_text("\n".join(html), encoding="utf-8")

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
            env_txt.append("Python: " + sys.version.replace("\\n"," "))
        except Exception:
            env_txt.append("Python: <unknown>")
        try:
            import numpy
            env_txt.append("NumPy : " + getattr(numpy,"__version__","<not installed>"))
        except Exception:
            env_txt.append("NumPy : <not installed>")
        try:
            import importlib
            env_txt.append("SciPy : " + getattr(importlib.import_module("scipy"),"__version__","<not installed>"))
        except Exception:
            env_txt.append("SciPy : <not installed>")
        zf.writestr("env.txt", "\n".join(env_txt))
    return str(zpath)
'''

    # -------- tools/diagnostics/cli_proxy.py (optional helper) --------
    files["tools/diagnostics/cli_proxy.py"] = r"""from __future__ import annotations
import sys, subprocess

# Usage: python tools/cli_proxy.py -- --input ... --output ... --geometry ...
def main():
    if "--" not in sys.argv:
        print("USAGE: python tools/cli_proxy.py -- --input ... --output ... --geometry ...")
        return 2
    idx = sys.argv.index("--")
    forwarded = sys.argv[idx+1:]
    cmd = [sys.executable, "cubist_cli.py"] + forwarded
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="")
    if "Wrote:" not in (proc.stdout or ""):
        print("VERIFY: no 'Wrote:' line emitted by CLI")
    return proc.returncode

if __name__ == "__main__":
    sys.exit(main())
"""

    # -------- tools/diagnostics/check_geometry_export.py (optional matrix probe) --------
    files[
        "tools/diagnostics/check_geometry_export.py"
    ] = r"""from __future__ import annotations
import sys, subprocess
from pathlib import Path

GEOMS = ["poisson_disk","scatter_circles","rectangles","voronoi","delaunay","concentric_circles"]

def run_one(inp: str, root: Path, geom: str) -> tuple[int,str]:
    out_dir = root / geom
    out_prefix = out_dir / f"frame_{geom}"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "tools/run_cli.py",
           "--input", inp,
           "--output", str(out_prefix),
           "--geometry", geom,
           "--points", "4000",
           "--seed", "42",
           "--cascade-stages", "3",
           "--export-svg",
           "--enable-plugin-exec",
           "--force-append-svg",
           "--verbose"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr)

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    print(f"Input: {Path(args.input).resolve()}")
    print(f"Output root: {root.resolve()}\n")
    for g in GEOMS:
        rc, out = run_one(args.input, root, g)
        print(f"[{g:18}] {'OK' if rc==0 else f'FAIL(rc={rc})'}")
        low = out.lower()
        if "error:" in low or "usage:" in low:
            for l in out.splitlines()[:6]:
                print(" " * 21 + l)
    print("\nDone.")

if __name__ == "__main__":
    sys.exit(main())
"""

    # build zip + manifest
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as z:
        manifest = {"files": []}
        for path, content in files.items():
            data = content.encode("utf-8")
            z.writestr(path, data)
            sha = hashlib.sha256(data).hexdigest()
            lines = content.count("\n") + (0 if content.endswith("\n") else 1)
            manifest["files"].append({"path": path, "sha256": sha, "lines": lines})
        z.writestr("manifest.json", json.dumps(manifest, indent=2).encode("utf-8"))
    return zpath, manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        default=f"cubist_bundle_{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.zip",
    )
    args = ap.parse_args()
    path, manifest = build_zip(args.out)
    print("WROTE", path)
    print(json.dumps(manifest, indent=2))
