# tools/prod_ui.py - Side-by-Side Fill Methods + Fixed SVG Thumbnails
from __future__ import annotations

import json
import logging
import queue
import re
import shutil
import subprocess
import threading
import time
import webbrowser
import io
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from flask import Flask, jsonify, render_template_string, request, send_file, Response

# Add missing imports
try:
    from PIL import Image
    try:
        from PIL import ImageCms
    except Exception:
        ImageCms = None
except Exception:
    Image = None
    ImageCms = None

# ---------------- Paths & constants ----------------
ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
OUT_ROOT = ROOT / "output" / "production"
PREFS_PATH = TOOLS / ".prod_ui_prefs.json"

# Geometry list
GEOMS = [
    "rectangles",
    "delaunay",
    "voronoi",
    "poisson_disk",
    "scatter_circles",
]

# Fill methods
FILL_METHODS = [
    {"id": "default", "name": "Default Fill", "description": "Base shapes only"},
    {"id": "cascade", "name": "Cascade Fill", "description": "Base shapes + gap filling"},
]

# ---------------- App state ----------------
app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

_LOGQ: "queue.Queue[str]" = queue.Queue()
BUSY = False
RUN_THREAD: threading.Thread | None = None


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _log(line: str, level: str = "info") -> None:
    """Enhanced logging with color coding"""
    timestamp = f"[{_now()}]"

    if level == "success":
        _LOGQ.put(
            f'<span style="color: #28a745; font-weight: bold;">{timestamp} {line}</span>'
        )
    elif level == "error":
        _LOGQ.put(
            f'<span style="color: #dc3545; font-weight: bold;">{timestamp} {line}</span>'
        )
    elif level == "warning":
        _LOGQ.put(
            f'<span style="color: #ffc107; font-weight: bold;">{timestamp} {line}</span>'
        )
    elif level == "complete":
        _LOGQ.put(
            f'<span style="color: #28a745; font-size: 1.1em; font-weight: bold; background-color: #d4edda; padding: 2px 6px; border-radius: 3px;">{timestamp} {line}</span>'
        )
    else:
        _LOGQ.put(f"{timestamp} {line}")


def _load_prefs() -> Dict[str, Any]:
    if PREFS_PATH.exists():
        try:
            return json.loads(PREFS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Try to find a reasonable default input image
    default_input = None
    for candidate in [
        "x_your_input_image.jpg",
        "your_input_image.jpg",
        "test_image.jpg",
        "sample.jpg",
    ]:
        test_path = ROOT / "input" / candidate
        if test_path.exists():
            default_input = str(test_path.resolve())
            break

    if not default_input:
        default_input = str((ROOT / "input" / "your_input_image.jpg").resolve())

    return {
        "input_image": default_input,
        "points": 500,
        "seed": 42,
        "export_svg": True,
        "enable_plugin_exec": True,
        "verbose_probe": True,
        "auto_open_gallery": True,
        "geoms": GEOMS[:3],
        "fill_methods": ["default"],  # Changed to array
    }


def _save_prefs(prefs: Dict[str, Any]) -> None:
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFS_PATH.write_text(json.dumps(prefs, indent=2), encoding="utf-8")


def _run_single_geometry(
    geom: str,
    input_image: str,
    output_dir: Path,
    points: int,
    seed: int,
    fill_method: str = "default",
    verbose: bool = False,
) -> Tuple[bool, str]:
    """Run a single geometry with fill method support"""

    # Use different output paths for different fill methods
    method_suffix = "_cascade" if fill_method == "cascade" else "_default"
    geom_output = output_dir / f"{geom}{method_suffix}" / f"frame_{geom}.svg"
    geom_output.parent.mkdir(parents=True, exist_ok=True)

    # Resolve input path
    try:
        in_p = Path(input_image)
        if not in_p.is_absolute():
            in_p = (ROOT / "input" / input_image).resolve()
        else:
            in_p = in_p.resolve()
    except Exception:
        in_p = Path(input_image)

    cmd = [
        "python",
        "cubist_cli.py",
        "--input", str(in_p),
        "--output", str(output_dir / f"{geom}{method_suffix}" / f"frame_{geom}"),
        "--geometry", geom,
        "--points", str(points),
        "--seed", str(seed),
        "--export-svg",
    ]

    # Add fill method parameters
    if fill_method == "cascade":
        cmd.extend(["--param", "cascade_fill_enabled=true"])
        cmd.extend(["--param", "cascade_intensity=0.8"])
    else:
        cmd.extend(["--param", "cascade_fill_enabled=false"])

    if verbose:
        cmd.append("--verbose")

    _log(f"Running: {geom} ({fill_method} fill)", "info")
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=300
        )
        elapsed = time.time() - start_time

        # Forward verbose output
        if result.stdout and verbose:
            for ln in result.stdout.strip().splitlines():
                _log(ln)
        if result.stderr and (verbose or result.returncode != 0):
            for ln in result.stderr.strip().splitlines():
                _log(ln, "error")

        if result.returncode == 0:
            svg_size = (
                geom_output.with_suffix(".svg").stat().st_size
                if geom_output.with_suffix(".svg").exists()
                else 0
            )
            shapes = "unknown"
            try:
                lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
                json_line = None
                for l in reversed(lines):
                    s = l.strip()
                    if s.startswith("{") and s.endswith("}"):
                        json_line = s
                        break
                if json_line:
                    data = json.loads(json_line)
                    shapes = data.get("svg_shapes", "unknown")
            except Exception:
                pass

            _log(
                f"✓ {geom} ({fill_method}): {shapes} shapes, {svg_size} bytes ({elapsed:.2f}s)",
                "success",
            )
            return True, f"✓ {geom} ({fill_method}): {shapes} shapes, {svg_size} bytes ({elapsed:.2f}s)"
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            _log(
                f"✗ {geom} ({fill_method}): failed with rc={result.returncode} ({elapsed:.2f}s)",
                "error",
            )
            _log(f"  Error: {error_msg}", "error")
            return False, f"✗ {geom} ({fill_method}): failed - {error_msg}"

    except subprocess.TimeoutExpired:
        _log(f"✗ {geom} ({fill_method}): timed out after 5 minutes", "error")
        return False, f"✗ {geom} ({fill_method}): timed out"
    except Exception as e:
        _log(f"✗ {geom} ({fill_method}): exception - {e}", "error")
        return False, f"✗ {geom} ({fill_method}): {e}"


def _run_batch(
    geoms: List[str],
    input_image: str,
    points: int,
    seed: int,
    fill_methods: List[str],
    auto_open: bool,
    verbose: bool = False,
) -> None:
    """Enhanced batch runner with multiple fill methods"""
    global BUSY
    try:
        BUSY = True
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir = OUT_ROOT / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        # Resolve input image
        try:
            p = Path(input_image)
            if not p.is_absolute():
                resolved_input = (ROOT / "input" / input_image).resolve()
            else:
                resolved_input = p.resolve()
        except Exception:
            resolved_input = Path(input_image)

        _log(f"Starting batch with {len(geoms)} geometries × {len(fill_methods)} fill methods")
        _log(f"Fill methods: {', '.join(fill_methods)}")
        _log(f"Input image: {resolved_input}")

        results = []
        successful = 0
        total_combinations = len(geoms) * len(fill_methods)

        for geom in geoms:
            for fill_method in fill_methods:
                success, msg = _run_single_geometry(
                    geom, str(resolved_input), output_dir, points, seed, fill_method, verbose
                )
                results.append((geom, success, msg, fill_method))
                if success:
                    successful += 1

        # Generate comparison gallery
        _generate_comparison_gallery(output_dir, results, resolved_input, fill_methods)

        failed = total_combinations - successful
        if failed == 0:
            _log(f"🎉 All {total_combinations} combinations completed successfully!", "complete")
        elif successful > 0:
            _log(
                f"⚠ Batch complete: {successful}/{total_combinations} successful, {failed} failed",
                "warning",
            )
        else:
            _log(f"⚠ Batch failed: 0/{total_combinations} successful", "error")

        _log(f"Wrote comparison gallery -> {output_dir}/index.html")

        if auto_open:
            gallery_path = output_dir / "index.html"
            _log("Opening gallery in browser...", "success")
            webbrowser.open(f"file:///{gallery_path}")
            _log("Gallery opened. Look for new browser tab!", "success")

        _log("🎯 Batch complete", "complete")
    except Exception as e:
        _log(f"⚠ Batch failed with exception: {e}", "error")
    finally:
        BUSY = False


def _generate_comparison_gallery(
    output_dir: Path,
    results: List[Tuple[str, bool, str, str]],
    input_image: str | Path,
    fill_methods: List[str]
) -> None:
    """Generate comparison gallery with side-by-side fill methods"""

    # Copy input image for preview
    preview_rel = None
    try:
        src = Path(input_image)
        if not src.is_absolute():
            src = (ROOT / "input" / str(input_image)).resolve()
        if src.exists() and src.is_file():
            assets = output_dir / "assets"
            assets.mkdir(parents=True, exist_ok=True)
            dest = assets / src.name
            if not dest.exists():
                shutil.copy2(src, dest)
            preview_rel = f"assets/{src.name}"
    except Exception:
        pass

    # Enhanced wrapper template for proper image fitting
    def create_wrapper_template(geom_name: str, method: str) -> str:
        method_suffix = "_cascade" if method == "cascade" else "_default"
        return f"""<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{geom_name} ({method} fill) - Cubist Art</title>
    <style>
        html, body {{
            height: 100vh;
            margin: 0;
            padding: 0;
            background: #111;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .header {{
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            color: white;
            font-family: Arial, sans-serif;
            font-size: 14px;
            background: rgba(0,0,0,0.7);
            padding: 5px 15px;
            border-radius: 5px;
            z-index: 100;
        }}
        .svg-container {{
            width: 100vw;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            box-sizing: border-box;
        }}
        img {{
            max-width: 100%;
            max-height: 100%;
            width: auto;
            height: auto;
            object-fit: contain;
            border: 1px solid #333;
            background: white;
        }}
    </style>
</head>
<body>
    <div class="header">{geom_name} ({method} fill)</div>
    <div class="svg-container">
        <img src="frame_{geom_name}.svg" alt="{geom_name} {method} fill">
    </div>
</body>
</html>"""

    # Group results by geometry for side-by-side comparison
    results_by_geom = {}
    for geom, success, msg, method in results:
        if geom not in results_by_geom:
            results_by_geom[geom] = {}
        results_by_geom[geom][method] = (success, msg)

    gallery_items = []

    for geom in results_by_geom:
        # Create comparison row for this geometry
        method_columns = []

        for method in fill_methods:
            method_suffix = "_cascade" if method == "cascade" else "_default"
            svg_path = output_dir / f"{geom}{method_suffix}" / f"frame_{geom}.svg"
            wrapper_path = output_dir / f"{geom}{method_suffix}" / f"frame_{geom}.html"

            if method in results_by_geom[geom]:
                success, msg = results_by_geom[geom][method]

                if success and svg_path.exists():
                    # Create enhanced wrapper with img tag instead of object
                    wrapper_html = create_wrapper_template(geom, method)
                    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
                    wrapper_path.write_text(wrapper_html, encoding="utf-8")

                    rel_wrapper = f"{geom}{method_suffix}/frame_{geom}.html"
                    rel_svg = f"{geom}{method_suffix}/frame_{geom}.svg"
                    file_size = svg_path.stat().st_size
                    size_str = (
                        f"{file_size / 1024:.1f} KB"
                        if file_size > 1024
                        else f"{file_size} bytes"
                    )

                    # Count shapes in SVG
                    shapes = "unknown"
                    try:
                        svg_content = svg_path.read_text(encoding="utf-8")
                        shapes = (
                            svg_content.count("<circle")
                            + svg_content.count("<polygon")
                            + svg_content.count("<path")
                            + svg_content.count("<rect")
                        )
                    except Exception:
                        pass

                    method_columns.append(f"""
                        <div class="method-column">
                            <h4>✅ {method.title()} Fill</h4>
                            <p><strong>{shapes} shapes</strong> • {size_str}</p>
                            <p><a href="{rel_wrapper}" target="_blank">view fullscreen</a> | <a href="{rel_svg}" target="_blank">raw SVG</a></p>
                            <div class="thumbnail-container" onclick="window.open('{rel_wrapper}', '_blank')">
                                <img src="{rel_svg}" alt="{geom} {method} fill">
                            </div>
                        </div>
                    """)
                else:
                    method_columns.append(f"""
                        <div class="method-column">
                            <h4>⚠ {method.title()} Fill</h4>
                            <p>Failed to generate</p>
                            <div class="thumbnail-container error">
                                <p>No SVG generated</p>
                            </div>
                        </div>
                    """)
            else:
                method_columns.append(f"""
                    <div class="method-column">
                        <h4>{method.title()} Fill</h4>
                        <p>Not selected</p>
                        <div class="thumbnail-container">
                            <p>-</p>
                        </div>
                    </div>
                """)

        # Create geometry comparison row
        gallery_items.append(f"""
            <div class="geometry-comparison">
                <h3>{geom}</h3>
                <div class="methods-row">
                    {''.join(method_columns)}
                </div>
            </div>
        """)

    # Build preview section
    preview_html = ""
    if preview_rel:
        preview_html = f'<div style="margin-bottom:16px"><h3>Input preview</h3><a href="{preview_rel}" target="_blank"><img src="{preview_rel}" style="max-width:420px;max-height:300px;border:1px solid #ccc;object-fit:contain"></a></div>'

    # Enhanced gallery template with comparison layout
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Cubist Art Gallery - Fill Method Comparison</title>
        <style>
            body {{
                font-family: system-ui, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 20px;
                background-color: #f8f9fa;
            }}
            .header {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
            .geometry-comparison {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
            .methods-row {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-top: 15px;
            }}
            .method-column {{
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                background: #f8f9fa;
            }}
            .thumbnail-container {{
                width: 100%;
                height: 250px;
                border: 1px solid #ddd;
                background: white;
                cursor: pointer;
                border-radius: 4px;
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.2s ease;
                position: relative;
            }}
            .thumbnail-container:hover {{
                transform: scale(1.02);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }}
            .thumbnail-container img {{
                max-width: 100%;
                max-height: 100%;
                width: auto;
                height: auto;
                object-fit: contain;
                display: block;
            }}
            .thumbnail-container.error {{
                background: #f8d7da;
                color: #721c24;
            }}
            a {{
                color: #007bff;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            h3 {{
                margin-top: 0;
                color: #495057;
                border-bottom: 2px solid #007bff;
                padding-bottom: 8px;
            }}
            h4 {{
                margin-top: 0;
                color: #495057;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎨 Cubist Art Gallery - Fill Method Comparison</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Methods: {', '.join(fill_methods)}</p>
        </div>
        {preview_html}
        <div class="gallery">
            {''.join(gallery_items)}
        </div>
    </body>
    </html>
    """
    (output_dir / "index.html").write_text(html_content, encoding="utf-8")


# ----------------- Flask routes -----------------
@app.route("/")
def index():
    return Response(render_template_string("""
<!doctype html><html><head><meta charset="utf-8"><title>Cubist Production UI v2.5</title>
<style>
body{font-family:system-ui,Arial;margin:18px;background-color:#f8f9fa}
.card{background:white;padding:20px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);margin-bottom:20px}
.row{margin-bottom:15px}
input[type=text]{width:520px;padding:8px;border:1px solid #ddd;border-radius:4px}
select{padding:8px;border:1px solid #ddd;border-radius:4px}
.button{padding:10px 16px;border-radius:6px;border:none;background:#007bff;color:#fff;cursor:pointer;font-weight:bold}
.button:hover{background:#0056b3}
.button.secondary{background:#6c757d}
.button.secondary:hover{background:#545b62}
.log{background:#111;color:#eee;padding:15px;height:300px;overflow:auto;font-family:'Courier New',monospace;border-radius:4px}
.preview{max-width:360px;max-height:200px;border:1px solid #444;border-radius:6px}
.points-input{width:100px;padding:8px;margin-right:8px;border:1px solid #ddd;border-radius:4px}
.error{color:#dc3545;font-size:12px;margin-top:4px}
.fill-method-section{background:#f8f9fa;padding:15px;border-radius:6px;border:1px solid #dee2e6}
.fill-method-option{margin-bottom:10px;padding:8px;border:1px solid #ddd;border-radius:4px;background:white}
.fill-method-option input[type=checkbox]{margin-right:8px}
.fill-method-description{font-size:12px;color:#666;margin-left:24px}
.status{margin:10px 0;font-weight:bold;padding:8px;border-radius:4px}
.status.idle{background:#d4edda;color:#155724}
.status.running{background:#cce7ff;color:#004085}
</style>
</head><body>
<h1>🎨 Cubist Art — Production UI v2.5.0</h1>

<div class="card">
  <h3>Input Configuration</h3>
  <div class="row">
    <label><strong>Input image</strong></label><br/>
    <input id="input_image" type="text" placeholder="filename or absolute path"/>
    <div style="margin-top:6px">
      <select id="input_files_select" style="max-width:420px"></select>
      <button class="button" onclick="useSelected()">Use selected</button>
      <input id="file_input" type="file" style="margin-left:8px"/>
      <button class="button" onclick="uploadFile()">Upload</button>
    </div>
    <div style="margin-top:8px">
      <img id="input_preview" class="preview" src="" style="display:none"/>
      <div><a id="open_input_link" href="#" target="_blank" style="display:none">open image in new tab</a></div>
    </div>
  </div>

  <div class="row">
    <label><strong>Points</strong></label><br/>
    <input id="points" type="text" class="points-input" placeholder="e.g. 500" min="1" max="50000"/>
    <span style="color:#666;font-size:12px">Enter number of shapes (1-50000)</span>
    <div id="points-error" class="error" style="display:none"></div>
  </div>
</div>

<div class="card">
  <h3>Fill Methods (Select Multiple for Side-by-Side Comparison)</h3>
  <div class="fill-method-section">
    <div class="fill-method-option">
      <label>
        <input type="checkbox" name="fill_method" value="default" checked/>
        <strong>Default Fill</strong>
      </label>
      <div class="fill-method-description">Base shapes only - traditional algorithm</div>
    </div>
    <div class="fill-method-option">
      <label>
        <input type="checkbox" name="fill_method" value="cascade"/>
        <strong>Cascade Fill</strong>
      </label>
      <div class="fill-method-description">Base shapes + gap filling - higher density, better coverage</div>
    </div>
  </div>
</div>

<div class="card">
  <h3>Geometries</h3>
  <div class="row">
    {% for g in geoms %}
      <label style="margin-right:15px;display:inline-block">
        <input type="checkbox" id="geom_{{g}}" {% if loop.index <= 3 %}checked{% endif %}/>
        <strong>{{g}}</strong>
      </label>
    {% endfor %}
  </div>
</div>

<div class="card">
  <h3>Execution</h3>
  <div class="row">
    <label><input id="auto_open" type="checkbox" checked/> <strong>Auto-open gallery</strong></label>
    <label style="margin-left:20px"><input id="verbose" type="checkbox"/> <strong>Verbose logging</strong></label>
  </div>

  <div class="row">
    <button class="button" id="run_btn" onclick="runBatch()">🚀 Run Batch</button>
    <button class="button secondary" onclick="clearLog()">Clear Log</button>
    <button class="button secondary" onclick="copyLog()">Copy Log</button>
  </div>

  <div id="status" class="status idle">Status: Idle</div>
</div>

<div class="card">
  <h3>Execution Log</h3>
  <div id="log" class="log"></div>
</div>

<script>
const geoms = {{ geoms_json|safe }};

function validatePoints(value) {
  const num = parseInt(value);
  if (isNaN(num)) return { valid: false, error: 'Must be a number' };
  if (num < 1) return { valid: false, error: 'Must be at least 1' };
  if (num > 50000) return { valid: false, error: 'Must be 50000 or less' };
  return { valid: true, value: num };
}

function updatePointsValidation() {
  const input = document.getElementById('points');
  const errorDiv = document.getElementById('points-error');
  const runBtn = document.getElementById('run_btn');

  const validation = validatePoints(input.value);

  if (validation.valid) {
    input.style.borderColor = '';
    errorDiv.style.display = 'none';
    runBtn.disabled = false;
    savePrefs();
  } else {
    input.style.borderColor = '#dc3545';
    errorDiv.textContent = validation.error;
    errorDiv.style.display = 'block';
    runBtn.disabled = true;
  }
}

async function loadInputFiles(){
  try{
    const res = await fetch('/input_files');
    const files = await res.json();
    const sel = document.getElementById('input_files_select');
    sel.innerHTML = '';
    files.forEach(f=>{
      const o = document.createElement('option'); o.value = f; o.text = f; sel.appendChild(o);
    });
  }catch(e){ console.warn(e); }
}

function setInputPreview(path){
  const img = document.getElementById('input_preview');
  const link = document.getElementById('open_input_link');
  if(!path){ img.style.display='none'; img.src=''; link.style.display='none'; return; }
  const url = '/preview?file=' + encodeURIComponent(path);
  img.src = url; img.style.display = 'inline-block'; link.href = url; link.style.display='inline';
}

function useSelected(){
  const sel = document.getElementById('input_files_select');
  if(!sel.value) return;
  document.getElementById('input_image').value = sel.value;
  setInputPreview(sel.value);
  savePrefs();
}

async function uploadFile(){
  const inp = document.getElementById('file_input');
  if(!inp.files || inp.files.length===0){ alert('Select file'); return; }
  const fd = new FormData(); fd.append('file', inp.files[0]);
  const r = await fetch('/upload',{method:'POST', body:fd});
  const j = await r.json();
  if(r.ok && j.filename){
    await loadInputFiles();
    document.getElementById('input_files_select').value = j.filename;
    useSelected();
  } else {
    alert('Upload failed: ' + (j.error || 'unknown'));
  }
}

function clearLog(){ document.getElementById('log').innerHTML = ''; }
function copyLog(){
  navigator.clipboard.writeText(document.getElementById('log').innerText).then(
    ()=>{ alert('Log copied') },
    ()=> alert('Copy failed')
  );
}

function getSelectedFillMethods() {
  const checkboxes = document.querySelectorAll('input[name="fill_method"]:checked');
  return Array.from(checkboxes).map(cb => cb.value);
}

async function savePrefs(obj){
  try{
    const pointsValidation = validatePoints(document.getElementById('points').value);
    const base = {
      input_image: document.getElementById('input_image').value,
      points: pointsValidation.valid ? pointsValidation.value : 500,
      geoms: Array.from(geoms).filter(g=>document.getElementById('geom_'+g).checked),
      auto_open_gallery: document.getElementById('auto_open').checked,
      verbose_probe: document.getElementById('verbose').checked,
      fill_methods: getSelectedFillMethods()
    };
    const payload = Object.assign(base, obj||{});
    await fetch('/save_prefs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  }catch(e){ console.warn('savePrefs', e); }
}

document.addEventListener('DOMContentLoaded', async ()=>{
  document.getElementById('points').addEventListener('input', updatePointsValidation);
  document.getElementById('points').addEventListener('blur', updatePointsValidation);

  await loadInputFiles();

  document.getElementById('auto_open').addEventListener('change', ()=> savePrefs());
  document.getElementById('verbose').addEventListener('change', ()=> savePrefs());

  geoms.forEach(g=>{
    const el = document.getElementById('geom_'+g);
    if(el) el.addEventListener('change', ()=> savePrefs());
  });

  document.querySelectorAll('input[name="fill_method"]').forEach(checkbox => {
    checkbox.addEventListener('change', () => savePrefs());
  });

  // Load prefs
  try{
    const p = await (await fetch('/prefs')).json();
    if(p.input_image) document.getElementById('input_image').value = p.input_image;
    if(p.points) document.getElementById('points').value = p.points;
    if(Array.isArray(p.geoms)){
      geoms.forEach(g=>{ const el=document.getElementById('geom_'+g); if(el) el.checked = p.geoms.includes(g); });
    }
    document.getElementById('auto_open').checked = p.auto_open_gallery !== false;
    document.getElementById('verbose').checked = !!(p.verbose_probe || p.verbose);

    if(Array.isArray(p.fill_methods)){
      p.fill_methods.forEach(method => {
        const checkbox = document.querySelector(`input[name="fill_method"][value="${method}"]`);
        if(checkbox) checkbox.checked = true;
      });
    }

    setInputPreview(p.input_image || '');
    updatePointsValidation();
  }catch(e){ console.warn('prefs load', e); }
});

async function runBatch(){
  const inputImage = document.getElementById('input_image').value.trim();
  if(!inputImage){ alert('Specify input'); return; }

  const pointsValidation = validatePoints(document.getElementById('points').value);
  if(!pointsValidation.valid){
    alert('Invalid points value: ' + pointsValidation.error);
    return;
  }

  const selected = geoms.filter(g=>document.getElementById('geom_'+g).checked);
  if(selected.length===0){ alert('Select at least one geometry'); return; }

  const fillMethods = getSelectedFillMethods();
  if(fillMethods.length===0){ alert('Select at least one fill method'); return; }

  const payload = {
    input_image: inputImage,
    points: pointsValidation.value,
    seed: 42,
    geoms: selected,
    fill_methods: fillMethods,
    auto_open: document.getElementById('auto_open').checked,
    verbose: document.getElementById('verbose').checked
  };

  await fetch('/run_batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
}

// Polling logs/status
setInterval(async ()=>{
  try{
    const st = await (await fetch('/status')).json();
    const statusEl = document.getElementById('status');
    if(st.busy) {
      statusEl.textContent = 'Status: Running...';
      statusEl.className = 'status running';
    } else {
      statusEl.textContent = 'Status: Idle';
      statusEl.className = 'status idle';
    }

    const logs = await (await fetch('/logs')).json();
    if(Array.isArray(logs) && logs.length){
      const container = document.getElementById('log');
      logs.forEach(h=>{ const d=document.createElement('div'); d.innerHTML = h; container.appendChild(d); });
      container.scrollTop = container.scrollHeight;
    }
  }catch(e){ /* ignore */ }
}, 1000);
</script>
</body></html>
    """, geoms_json=json.dumps(GEOMS), geoms=GEOMS), content_type='text/html; charset=utf-8')


@app.route("/input_files")
def input_files():
    input_dir = ROOT / "input"
    files: List[str] = []
    try:
        if input_dir.exists():
            for p in sorted(input_dir.iterdir()):
                if p.is_file() and p.suffix.lower() in (
                    ".jpg", ".jpeg", ".png", ".gif", ".webp",
                ):
                    files.append(p.name)
    except Exception:
        pass
    return jsonify(files)


@app.route("/preview")
def preview():
    fname = request.args.get("file", "")
    if not fname:
        return "Not found", 404
    try:
        p = Path(fname)
        if p.is_absolute():
            p_res = p.resolve()
        else:
            p_res = (ROOT / "input" / fname).resolve()
        if p_res.exists() and p_res.is_file():
            return send_file(p_res)
    except Exception:
        pass
    return "Not found", 404


@app.route("/upload", methods=["POST"])
def upload():
    try:
        f = request.files.get("file")
        if not f or f.filename == "":
            return jsonify({"error": "no file"}), 400
        dest = ROOT / "input"
        dest.mkdir(parents=True, exist_ok=True)
        filename = Path(f.filename).name
        out = dest / filename
        f.save(str(out))
        _log(f"Uploaded input file: {out}", "success")
        return jsonify({"ok": True, "filename": filename})
    except Exception as e:
        _log(f"Upload failed: {e}", "error")
        return jsonify({"error": str(e)}), 500


@app.route("/save_prefs", methods=["POST"])
def save_prefs():
    try:
        data = request.get_json() or {}
        prefs = _load_prefs()
        prefs.update(data)
        _save_prefs(prefs)
        return jsonify({"ok": True})
    except Exception as e:
        _log(f"Failed saving prefs: {e}", "error")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/run_batch", methods=["POST"])
def run_batch():
    global RUN_THREAD
    if BUSY:
        return jsonify({"error": "Already running"}), 400

    data = request.get_json() or {}

    prefs = _load_prefs()
    prefs.update(data)
    _save_prefs(prefs)

    RUN_THREAD = threading.Thread(
        target=_run_batch,
        args=(
            data.get("geoms", GEOMS[:3]),
            data.get("input_image", ""),
            int(data.get("points", 500)),
            int(data.get("seed", 42)),
            data.get("fill_methods", ["default"]),
            bool(data.get("auto_open", True)),
            bool(data.get("verbose", False)),
        ),
        daemon=True,
    )
    RUN_THREAD.start()
    return jsonify({"status": "started"})


@app.route("/status")
def status():
    return jsonify({"busy": BUSY})


@app.route("/logs")
def logs():
    out: List[str] = []
    try:
        while True:
            out.append(_LOGQ.get_nowait())
    except Exception:
        pass
    return jsonify(out)


@app.route("/prefs")
def prefs():
    return jsonify(_load_prefs())


if __name__ == "__main__":
    print("🎨 Cubist Production UI v2.5.0 - Side-by-Side Fill Comparison")
    print("🚀 Server running at http://127.0.0.1:5123")
    try:
        app.run(host="127.0.0.1", port=5123, debug=False)
    except Exception as e:
        print(f"❌ Server failed to start: {e}")