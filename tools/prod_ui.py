# tools/prod_ui.py
from __future__ import annotations

import json
import logging
import os
import queue
import subprocess
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from flask import Flask, Response, jsonify, render_template_string, request, send_file

# ---------------- Paths & constants ----------------
ROOT = Path(__file__).resolve().parents[1]  # .../cubist_art
TOOLS = ROOT / "tools"
OUT_ROOT = ROOT / "output" / "production"
PREFS_PATH = TOOLS / ".prod_ui_prefs.json"
GEOMS = [
    "delaunay",
    "voronoi",
    "rectangles",
    "poisson_disk",
    "scatter_circles",
    "concentric_circles",
]

# ---------------- App state ----------------
app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.ERROR)  # suppress heartbeat GET noise

_LOGQ: "queue.Queue[str]" = queue.Queue()
BUSY = False
RUN_THREAD: threading.Thread | None = None


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _log(line: str) -> None:
    _LOGQ.put(f"[{_now()}] {line}")


def _load_prefs() -> Dict[str, Any]:
    if PREFS_PATH.exists():
        try:
            return json.loads(PREFS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Try to find a reasonable default input image
    default_input = None
    for candidate in ["your_input_image.jpg", "test_image.jpg", "sample.jpg"]:
        test_path = ROOT / "input" / candidate
        if test_path.exists():
            default_input = str(test_path.resolve())
            break

    if not default_input:
        default_input = str((ROOT / "input" / "your_input_image.jpg").resolve())

    return {
        "input_image": default_input,
        "points": 4000,
        "seed": 42,
        "cascade": 3,
        "export_svg": True,
        "enable_plugin_exec": True,
        "verbose_probe": True,
        "auto_open_gallery": True,
        "geoms": GEOMS[:3],  # Start with working geometries only
    }


def _save_prefs(p: Dict[str, Any]) -> None:
    try:
        PREFS_PATH.write_text(json.dumps(p, indent=2), encoding="utf-8")
    except Exception as e:
        _log(f"[ui] WARNING: failed saving prefs: {e!r}")


def _cmd_for_geom(geom: str, prefs: Dict[str, Any], out_dir: Path) -> List[str]:
    """Build command for our working cubist_cli.py (not the old wrapper)"""
    dest = out_dir / geom / f"frame_{geom}"
    cmd = [
        os.sys.executable,
        str(ROOT / "cubist_cli.py"),  # Use our working CLI directly
        "--input",
        prefs["input_image"],
        "--output",
        str(dest),
        "--geometry",
        geom,
        "--points",
        str(prefs.get("points", 4000)),
        "--seed",
        str(prefs.get("seed", 42)),
        "--cascade-stages",
        str(prefs.get("cascade", 3)),
    ]

    # Add export-svg flag if enabled
    if prefs.get("export_svg", True):
        cmd.append("--export-svg")

    # Add quiet flag for cleaner output
    cmd.append("--quiet")

    return cmd


def _env_with_paths() -> Dict[str, str]:
    """Add ROOT and ROOT/src to PYTHONPATH for subprocesses and probes."""
    env = os.environ.copy()
    sep = ";" if os.name == "nt" else ":"
    extras = [str(ROOT)]
    if (ROOT / "src").exists():
        extras.append(str(ROOT / "src"))
    extra = sep.join(extras)
    env["PYTHONPATH"] = extra + (
        sep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    return env


def _completed_tail(
    proc: subprocess.CompletedProcess, n: int = 12
) -> Tuple[List[str], List[str]]:
    out = (proc.stdout or "").splitlines()[-n:]
    err = (proc.stderr or "").splitlines()[-n:]
    return out, err


def _parse_cli_json_output(stdout: str) -> Dict[str, Any]:
    """Parse JSON output from our updated cubist_cli.py"""
    if not stdout.strip():
        return {}

    try:
        # The CLI now outputs clean JSON
        return json.loads(stdout.strip())
    except json.JSONDecodeError:
        # Fallback: try to find JSON in the output
        lines = stdout.strip().splitlines()
        for line in reversed(lines):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        return {}


def _write_gallery(out_dir: Path, results: List[Dict[str, Any]]) -> Path:
    """Write gallery HTML with both local file:// URLs and web server URLs"""
    out_dir.mkdir(parents=True, exist_ok=True)
    html = [
        "<!doctype html><meta charset='utf-8'><title>Cubist — Run Summary</title>",
        "<style>body{font:14px system-ui,Segoe UI,Tahoma,Arial;margin:22px} "
        ".ok{color:#080}.err{color:#b00} a{color:#06c;text-decoration:none} a:hover{text-decoration:underline} "
        ".preview{max-width:200px;max-height:150px;border:1px solid #ccc;margin:5px 0;background:#f9f9f9} "
        ".gallery-info{background:#e3f2fd;padding:15px;border-radius:8px;margin-bottom:20px} "
        ".switch-btn{padding:6px 12px;background:#2196f3;color:white;border:none;border-radius:4px;cursor:pointer;margin:0 5px}</style>",
        "<div class='gallery-info'>",
        f"<h2>🎨 {out_dir.name}</h2>",
        "<p><strong>View Mode:</strong> <button class='switch-btn' onclick='switchToServer()'>Web Server View</button> ",
        "<button class='switch-btn' onclick='location.reload()'>Refresh</button></p>",
        f"<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        "</div>",
        "<ul>",
    ]

    success_count = 0
    for r in results:
        geom = r.get("geometry") or r.get("_geom") or "?"
        outputs = r.get("outputs", {})
        svg_exists = outputs.get("svg_exists", False)

        if svg_exists:
            svg_size = outputs.get("svg_size", 0)
            svg_shapes = outputs.get("svg_shapes", 0)
            svg_path = outputs.get("svg_path", "")
            size_k = f"{svg_size/1024:.1f} KB"

            # Create both file:// URL for local viewing and web server URL
            try:
                file_path = Path(svg_path).resolve()
                file_url = file_path.as_uri()  # file:///path/to/file.svg

                rel_path = file_path.relative_to(ROOT)
                web_path = str(rel_path).replace("\\", "/")
                web_url = f"http://127.0.0.1:5123/file?p={web_path}"

            except (ValueError, OSError):
                # Fallback if path operations fail
                file_url = f"file:///{svg_path.replace(chr(92), '/')}"
                web_url = (
                    f"http://127.0.0.1:5123/file?p={svg_path.replace(chr(92), '/')}"
                )

            html.append(
                f"<li class='ok'><b>{geom}</b> — {svg_shapes} shapes • {size_k} • "
                f"<a target='_blank' href='{file_url}'>open SVG</a><br>"
                f"<embed src='{file_url}' type='image/svg+xml' class='preview' "
                f"onerror='this.src=\"{web_url}\"'></li>"
            )
            success_count += 1
        else:
            expected = outputs.get(
                "expected_svg", f"Expected: {out_dir / geom / f'frame_{geom}.svg'}"
            )
            rc = r.get("rc", "unknown")
            html.append(
                f"<li class='err'>⚠ No SVG for <b>{geom}</b> (rc={rc}) — {expected}</li>"
            )

    # Add summary and controls
    html.extend(
        [
            "</ul>",
            "<div style='margin-top:30px;padding:15px;background:#f0f8ff;border-radius:8px'>",
            f"<p><strong>Batch Results:</strong> {success_count} successful, {len(results) - success_count} failed</p>",
            "<button onclick='location.reload()' style='padding:8px 16px;background:#007bff;color:white;border:none;border-radius:4px;cursor:pointer;margin-right:10px'>Refresh Gallery</button>",
            "<button onclick='switchToServer()' style='padding:8px 16px;background:#28a745;color:white;border:none;border-radius:4px;cursor:pointer'>View in Web Server</button>",
            "</div>",
            "<script>",
            "function switchToServer() {",
            f"  window.open('http://127.0.0.1:5123/gallery/{out_dir.name}', '_blank');",
            "}",
            "</script>",
        ]
    )

    path = out_dir / "index.html"
    path.write_text("\n".join(html), encoding="utf-8")
    _log(f"[ui] Wrote gallery -> {path}")
    return path


def _run_worker(prefs: Dict[str, Any]) -> None:
    global BUSY
    BUSY = True
    try:
        run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_dir = OUT_ROOT / run_id
        geoms = list(prefs.get("geoms", GEOMS))
        _log(f"[ui] Running {len(geoms)} geometries into {out_dir}…")
        _log(f"[ui] Input image: {prefs.get('input_image', 'NOT SET')}")

        # Quick environment check
        cli_path = ROOT / "cubist_cli.py"
        if not cli_path.exists():
            _log(f"[ui] ERROR: CLI not found at {cli_path}")
            return

        # Check input image
        input_path = Path(prefs.get("input_image", ""))
        if not input_path.exists():
            _log(f"[ui] ERROR: Input image not found at {input_path}")
            return

        results: List[Dict[str, Any]] = []
        for g in geoms:
            cmd = _cmd_for_geom(g, prefs, out_dir)
            _log(f"[cmd] Running: {g}")

            t0 = time.time()
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    env=_env_with_paths(),
                    cwd=ROOT,  # Ensure we're in the right directory
                )
            except Exception as e:
                _log(f"[cli] spawn ERROR for {g}: {e!r}")
                results.append(
                    {
                        "_geom": g,
                        "geometry": g,
                        "rc": 998,
                        "outputs": {"svg_exists": False},
                    }
                )
                continue

            # Parse the JSON output from our CLI
            output_data = _parse_cli_json_output(proc.stdout)
            if not output_data:
                output_data = {"_geom": g, "geometry": g, "rc": proc.returncode or 1}

            # Ensure geometry field is set
            output_data["geometry"] = g
            output_data["_geom"] = g

            rc = output_data.get("rc", proc.returncode or 1)
            elapsed = f"{time.time()-t0:.2f}s"
            results.append(output_data)

            outputs = output_data.get("outputs", {})
            if rc == 0 and outputs.get("svg_exists"):
                svg_path = outputs.get("svg_path", "")
                svg_shapes = outputs.get("svg_shapes", 0)
                svg_size = outputs.get("svg_size", 0)
                _log(f"[cli] ✓ {g}: {svg_shapes} shapes, {svg_size} bytes ({elapsed})")
            else:
                _log(f"[cli] ✗ {g}: failed with rc={rc} ({elapsed})")
                # Log more details for debugging
                if proc.stderr:
                    err_lines = proc.stderr.strip().splitlines()
                    for err_line in err_lines[:2]:  # First 2 lines of stderr
                        if err_line.strip():
                            _log(f"[cli] stderr: {err_line.strip()}")

        # Generate gallery
        try:
            gallery_path = _write_gallery(out_dir, results)
            success_count = len(
                [r for r in results if r.get("outputs", {}).get("svg_exists")]
            )
            _log(
                f"[ui] Generated gallery with {success_count}/{len(results)} successful SVGs"
            )

            # Auto-open with better messaging
            if prefs.get("auto_open_gallery", True):
                try:
                    _log("[ui] Opening gallery in browser...")
                    _log(f"[ui] Gallery URL: {gallery_path.as_uri()}")

                    if os.name == "nt":
                        os.startfile(gallery_path)  # type: ignore[attr-defined]
                    else:
                        webbrowser.open(str(gallery_path))

                    _log("[ui] Gallery opened. Look for new browser tab!")
                    _log(
                        f"[ui] Web server gallery: http://127.0.0.1:5123/gallery/{out_dir.name}"
                    )

                except Exception as e:
                    _log(f"[ui] Could not auto-open gallery: {e}")
                    _log(f"[ui] Manual gallery URL: {gallery_path.as_uri()}")
            else:
                _log(f"[ui] Gallery ready: {gallery_path.as_uri()}")

        except Exception as e:
            _log(f"[ui] Gallery generation ERROR: {e!r}")

    except Exception as e:
        _log(f"[ui] Worker ERROR: {e!r}")
    finally:
        BUSY = False
        _log("[ui] Batch complete")


# ---------------- Flask UI ----------------

TPL = r"""
<!doctype html><meta charset="utf-8">
<title>Cubist — Batch Runner</title>
<style>
 body{font:16px system-ui,Segoe UI,Tahoma,Arial;margin:16px}
 .row{margin:8px 0}
 input[type=text]{width:560px;font-family:monospace;font-size:14px}
 .log{background:#111;color:#ddd;min-height:340px;padding:10px;white-space:pre-wrap;font-family:monospace;font-size:13px;border-radius:4px}
 .btn{padding:8px 14px;border:1px solid #888;border-radius:6px;background:#f5f5f5;cursor:pointer;margin:2px}
 .btn[disabled]{opacity:.5;cursor:not-allowed}
 .btn.primary{background:#007bff;color:white;border-color:#0056b3}
 img#preview{max-height:80px;vertical-align:middle;margin-left:10px;border:1px solid #ccc;border-radius:3px}
 .note{font-size:12px;color:#666;margin-top:4px}
 .status{padding:8px;margin:8px 0;border-radius:4px}
 .status.success{background:#d4edda;color:#155724}
 .status.error{background:#f8d7da;color:#721c24}
 .status.warning{background:#fff3cd;color:#856404}
 .geom-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:8px 0}
 .input-status{font-size:12px;margin-top:4px;padding:4px 8px;border-radius:3px}
 .input-status.ok{background:#d4edda;color:#155724}
 .input-status.error{background:#f8d7da;color:#721c24}
</style>

<h1>🎨 Cubist Art — Production Batch Runner</h1>

<div class="status success">
  <strong>Status:</strong> Production UI v2.3.7 ready. Server running at <code>http://127.0.0.1:5123</code>
</div>

<div class="row">
  <label><strong>Input image:</strong><br>
    <input id="input_image" type="text" placeholder="Path to input image (or upload below)">
  </label><br>
  <div id="input_status" class="input-status" style="display:none"></div>
  <input id="filepick" type="file" accept="image/*">
  <img id="preview" alt="preview" style="display:none">
  <div class="note">Upload a file or specify path to existing image. Preview shows what will be processed.</div>
</div>

<div class="row">
  <label>Points: <input id="points" type="number" value="4000" style="width:100px" min="50" max="10000"></label>
  <label>Seed: <input id="seed" type="number" value="42" style="width:80px" min="1" max="9999"></label>
  <label>Cascade: <input id="cascade" type="number" value="3" style="width:60px" min="1" max="5"></label>
</div>

<div class="row">
  <strong>Geometries:</strong> (Start with working ones: delaunay, voronoi, rectangles)<br>
  <div class="geom-grid">
    <label><input type="checkbox" class="g" value="delaunay" checked> delaunay (triangles)</label>
    <label><input type="checkbox" class="g" value="voronoi" checked> voronoi (cells)</label>
    <label><input type="checkbox" class="g" value="rectangles" checked> rectangles</label>
    <label><input type="checkbox" class="g" value="poisson_disk"> poisson_disk</label>
    <label><input type="checkbox" class="g" value="scatter_circles"> scatter_circles</label>
    <label><input type="checkbox" class="g" value="concentric_circles"> concentric_circles</label>
  </div>
  <div class="note">Note: Some geometries may have compatibility issues. Start with the checked ones for best results.</div>
</div>

<div class="row">
  <strong>Options:</strong><br>
  <label><input id="export_svg" type="checkbox" checked> Export SVG files</label>
  <label><input id="auto_open_gallery" type="checkbox" checked> Auto-open gallery when complete</label>
</div>

<div class="row">
  <button id="run" class="btn primary">🚀 Run Batch</button>
  <button id="idle" class="btn">💤 Status Check</button>
  <button id="copy" class="btn">📋 Copy Log</button>
  <button id="export" class="btn">💾 Export Log</button>
  <button id="clear" class="btn">🗑️ Clear Log</button>
</div>

<h3>Batch Execution Log</h3>
<div id="log" class="log">Production UI ready - v2.3.7 compatible
🎨 Server running at http://127.0.0.1:5123
Auto-open enabled: Gallery will open in new browser tab when batch completes
Select input image, choose geometries, and click 'Run Batch' to start.
</div>

<script>
const qs = id => document.getElementById(id);
const logEl = qs('log');
let seq = 0;

function addLog(lines){
  if(!lines || !lines.length) return;
  logEl.textContent += lines.join("\n") + "\n";
  logEl.scrollTop = logEl.scrollHeight;
}

function gather(){
  const geoms = Array.from(document.querySelectorAll('input.g:checked')).map(x => x.value);
  return {
    input_image: qs('input_image').value.trim(),
    points: Number(qs('points').value),
    seed: Number(qs('seed').value),
    cascade: Number(qs('cascade').value),
    export_svg: qs('export_svg').checked,
    auto_open_gallery: qs('auto_open_gallery').checked,
    geoms
  };
}

async function savePrefs(){
  try {
    const r = await fetch('/save_prefs', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(gather())});
    const j = await r.json(); addLog(j.log || []);
  } catch(e) {
    addLog(['[ui] Error saving preferences: ' + e.message]);
  }
}

async function loadPrefs(){
  try {
    const r = await fetch('/load_prefs'); const p = await r.json();
    qs('input_image').value = p.input_image || '';
    qs('points').value = p.points ?? 4000;
    qs('seed').value = p.seed ?? 42;
    qs('cascade').value = p.cascade ?? 3;
    qs('export_svg').checked = !!p.export_svg;
    qs('auto_open_gallery').checked = !!p.auto_open_gallery;
    // Uncheck all first
    document.querySelectorAll('input.g').forEach(box => box.checked = false);
    (p.geoms||[]).forEach(g => { const box = document.querySelector('input.g[value="'+g+'"]'); if(box) box.checked = true; });
    refreshPreview();
  } catch(e) {
    addLog(['[ui] Error loading preferences: ' + e.message]);
  }
}

function refreshPreview(){
  const p = qs('input_image').value.trim();
  const preview = qs('preview');
  const status = qs('input_status');

  if(p) {
    preview.src = '/file?p='+encodeURIComponent(p)+'&t='+Date.now();
    preview.style.display = 'inline';
    preview.onload = () => {
      status.textContent = '✓ Image preview loaded: ' + p.split(/[/\\]/).pop();
      status.className = 'input-status ok';
      status.style.display = 'block';
    };
    preview.onerror = () => {
      preview.style.display = 'none';
      status.textContent = '⚠ Could not preview image: ' + p.split(/[/\\]/).pop();
      status.className = 'input-status error';
      status.style.display = 'block';
    };
  } else {
    preview.style.display = 'none';
    status.style.display = 'none';
  }
}

qs('filepick').addEventListener('change', async ()=>{
  const f = qs('filepick').files[0]; if(!f) return;
  const form = new FormData(); form.append('file', f);
  addLog(['[ui] Uploading ' + f.name + '...']);
  try {
    const r = await fetch('/upload', {method:'POST', body:form});
    const j = await r.json();
    if(j.ok && j.path){
      qs('input_image').value = j.path;
      addLog(['[ui] ✓ Uploaded -> '+j.path]);
      refreshPreview();
      await savePrefs();
    } else {
      addLog(['[ui] ✗ Upload failed: '+(j.error||'unknown error')]);
    }
  } catch(e) {
    addLog(['[ui] ✗ Upload error: '+e.message]);
  }
});

qs('input_image').addEventListener('change', refreshPreview);
qs('input_image').addEventListener('blur', savePrefs);

qs('run').addEventListener('click', async ()=>{
  const prefs = gather();
  if(!prefs.input_image) {
    addLog(['[ui] ✗ Please specify an input image']);
    return;
  }
  if(prefs.geoms.length === 0) {
    addLog(['[ui] ✗ Please select at least one geometry']);
    return;
  }
  await savePrefs();
  addLog([`[ui] Starting batch: ${prefs.geoms.join(', ')}, ${prefs.points} points, seed ${prefs.seed}`]);
  if(prefs.auto_open_gallery) {
    addLog(['[ui] Auto-open enabled: Gallery will open in new tab when complete']);
  }
  await fetch('/run', {method:'POST'});
});

qs('idle').addEventListener('click', ()=>addLog(['[ui] Status: ' + (document.getElementById('run').disabled ? 'BUSY - batch running' : 'IDLE - ready for commands')]));
qs('copy').addEventListener('click', ()=>{
  navigator.clipboard.writeText(logEl.textContent||'').then(()=>addLog(['[ui] Log copied to clipboard']));
});
qs('export').addEventListener('click', ()=>{
  const blob = new Blob([logEl.textContent||''], {type:'text/plain;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'cubist_batch_log_'+new Date().toISOString().slice(0,19).replace(/[:-]/g,'_')+'.txt';
  a.click();
  URL.revokeObjectURL(a.href);
  addLog(['[ui] Log exported']);
});
qs('clear').addEventListener('click', ()=>{
  logEl.textContent = 'Log cleared.\nProduction UI ready for next batch.\n';
});

async function poll(){
  try{
    const r = await fetch('/status?since='+seq);
    const j = await r.json();
    if(j.seq !== undefined) seq = j.seq;
    addLog(j.lines || []);
    if(j.busy){
      qs('run').setAttribute('disabled', 'true');
      qs('run').textContent = '🔄 Running...';
    } else {
      qs('run').removeAttribute('disabled');
      qs('run').textContent = '🚀 Run Batch';
    }
  }catch(e){
    // Silently handle polling errors
  }
  setTimeout(poll, 1200);
}

// Initialize
loadPrefs().then(()=>{
  poll();
  addLog(['[ui] Production UI initialized']);
  addLog(['[ui] Tip: Gallery auto-opens when batch completes (look for new browser tab)']);
});
</script>
"""


@app.route("/")
def home() -> Response:
    return render_template_string(TPL)


@app.route("/file")
def get_file():
    p_param = request.args.get("p", "")

    # Handle both absolute and relative paths
    if Path(p_param).is_absolute():
        p = Path(p_param)
    else:
        p = ROOT / p_param

    if not p.exists():
        return Response("File not found", status=404)

    # Security check - ensure file is within project
    try:
        p.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return Response("Access denied", status=403)

    return send_file(p, conditional=True)


@app.route("/gallery/<run_id>")
def web_gallery(run_id):
    """Serve gallery via web server instead of static file"""
    gallery_dir = OUT_ROOT / run_id
    if not gallery_dir.exists():
        return Response("Gallery not found", status=404)

    # Read results from the static HTML or reconstruct
    html_file = gallery_dir / "index.html"
    if html_file.exists():
        content = html_file.read_text(encoding="utf-8")
        # Replace file:// URLs with web server URLs
        content = content.replace("file:///", "/file?p=")
        return Response(content, mimetype="text/html")
    else:
        return Response("Gallery not ready", status=404)


@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"ok": False, "error": "no file"}), 400

    if not f.filename:
        return jsonify({"ok": False, "error": "no filename"}), 400

    dest_dir = ROOT / "input" / "uploads"
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Clean filename
    safe_name = "".join(c for c in f.filename if c.isalnum() or c in "._-")
    if not safe_name:
        safe_name = "uploaded_image"

    dest = dest_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_{safe_name}"

    try:
        f.save(dest)
        return jsonify({"ok": True, "path": str(dest.resolve())})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/save_prefs", methods=["POST"])
def save_prefs_route():
    try:
        p = request.get_json(force=True)
        _save_prefs(p)
        return jsonify({"ok": True, "log": ["[ui] Preferences saved"]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/load_prefs")
def load_prefs_route():
    return jsonify(_load_prefs())


_SEQ = 0


@app.route("/status")
def status():
    global _SEQ
    since = int(request.args.get("since", 0))
    lines: List[str] = []
    while not _LOGQ.empty():
        lines.append(_LOGQ.get())
    if lines:
        _SEQ += 1
    return jsonify({"busy": BUSY, "lines": lines if _SEQ > since else [], "seq": _SEQ})


@app.route("/run", methods=["POST"])
def run_batch():
    global RUN_THREAD, BUSY
    if BUSY:
        _log("[ui] Batch already running - please wait")
        return jsonify({"ok": False, "busy": True})

    prefs = _load_prefs()
    _log(f"[ui] Starting batch with {len(prefs.get('geoms', []))} geometries")

    RUN_THREAD = threading.Thread(target=_run_worker, args=(prefs,), daemon=True)
    RUN_THREAD.start()
    return jsonify({"ok": True, "busy": True})


if __name__ == "__main__":
    print("🎨 Cubist Art Production UI v2.3.7")
    print("=" * 50)
    print("Starting Flask server...")
    print()
    print("🌐 Web UI: http://127.0.0.1:5123")
    print("📁 Project: " + str(ROOT))
    print()
    print("Features:")
    print("• Advanced batch runner with real-time logging")
    print("• File upload and preview system")
    print("• Auto-generated galleries with SVG previews")
    print("• Multi-geometry selection and parameter tuning")
    print()
    print("ℹ️  Starting up...")
    print("   Server will be ready in a few seconds")
    print("   Browser will auto-open when ready")
    print("   Look for new browser tab!")
    print()
    print("Press Ctrl+C to stop server")
    print("=" * 50)

    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    # Auto-open browser after short delay to let server start
    def delayed_open():
        time.sleep(2)  # Wait for server to be ready
        try:
            webbrowser.open("http://127.0.0.1:5123")
            print("🌐 Browser opened: http://127.0.0.1:5123")
        except Exception as e:
            print(f"Could not auto-open browser: {e}")
            print("Manual URL: http://127.0.0.1:5123")

    threading.Thread(target=delayed_open, daemon=True).start()

    app.run(port=5123, debug=False, host="127.0.0.1")
