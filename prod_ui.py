# tools/prod_ui.py - Phase 2: Hybrid Subdivision UI
from __future__ import annotations

import json
import logging
import queue
import shutil
import subprocess
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from flask import Flask, jsonify, render_template, request, send_file, Response

# Import version info
try:
    from version import VERSION, UI_TITLE
except ImportError:
    VERSION = "2.6.1"
    UI_TITLE = "Cubist Art — Production UI v2.6.1"

# Import parameter registry
GEOMETRY_PARAMETERS = {}
get_factory_defaults = None

try:
    import sys
    root_path = Path(__file__).resolve().parents[1]
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))
    from geometry_parameters import GEOMETRY_PARAMETERS, get_factory_defaults
    print(f"[prod_ui] Successfully loaded {len(GEOMETRY_PARAMETERS)} geometry parameter definitions")
except ImportError as e:
    print(f"[prod_ui] WARNING: Could not import geometry_parameters: {e}")
    print(f"[prod_ui] Using empty parameter definitions")
    def get_factory_defaults(geometry):
        return {}

# Import hybrid subdivision system
try:
    from hybrid_subdivision import MaskBasedSubdivision
    print(f"[prod_ui] Successfully loaded hybrid subdivision system")
except ImportError as e:
    print(f"[prod_ui] WARNING: Could not import hybrid_subdivision: {e}")
    MaskBasedSubdivision = None

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
ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
OUT_ROOT = ROOT / "output" / "production"
PREFS_PATH = ROOT  / ".prod_ui_prefs.json"

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

    # Initialize with factory defaults for all geometries
    geom_params = {}
    for geom in GEOMS:
        geom_params[geom] = get_factory_defaults(geom)

    return {
        "input_image": default_input,
        "mask_image": "",
        "background_image": "",
        "points": 500,
        "seed": 42,
        "export_svg": True,
        "enable_plugin_exec": True,
        "verbose_probe": True,
        "auto_open_gallery": True,
        "geoms": GEOMS[:3],
        "fill_methods": ["default"],
        "geometry_parameters": geom_params,
        "hybrid_mode": False,
        "region_assignments": {}
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
    geometry_params: Dict[str, float] = None,
    verbose: bool = False,
) -> Tuple[bool, str, Dict[str, float]]:
    """Run a single geometry with fill method and parameter support"""

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
    else:
        cmd.extend(["--param", "cascade_fill_enabled=false"])

    # Add geometry-specific parameters
    if geometry_params:
        for param_name, param_value in geometry_params.items():
            cmd.extend(["--param", f"{param_name}={param_value}"])
            if verbose:
                _log(f"  → {param_name}={param_value}")

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
            return True, f"✓ {geom} ({fill_method}): {shapes} shapes, {svg_size} bytes ({elapsed:.2f}s)", geometry_params or {}
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            _log(
                f"✗ {geom} ({fill_method}): failed with rc={result.returncode} ({elapsed:.2f}s)",
                "error",
            )
            _log(f"  Error: {error_msg}", "error")
            return False, f"✗ {geom} ({fill_method}): failed - {error_msg}", geometry_params or {}

    except subprocess.TimeoutExpired:
        _log(f"✗ {geom} ({fill_method}): timed out after 5 minutes", "error")
        return False, f"✗ {geom} ({fill_method}): timed out", geometry_params or {}
    except Exception as e:
        _log(f"✗ {geom} ({fill_method}): exception - {e}", "error")
        return False, f"✗ {geom} ({fill_method}): {e}", geometry_params or {}

def _run_batch(
    geoms: List[str],
    input_image: str,
    points: int,
    seed: int,
    fill_methods: List[str],
    geometry_parameters: Dict[str, Dict[str, float]],
    auto_open: bool,
    verbose: bool = False,
    hybrid_mode: bool = False,
    mask_image: str = "",
    background_image: str = "",
    region_assignments: Dict = None,
) -> None:
    """Enhanced batch runner with hybrid subdivision support"""
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

        _log(f"Starting batch generation")
        _log(f"Input image: {resolved_input}")
        
        if hybrid_mode:
            _log(f"HYBRID MODE ENABLED", "warning")
            if mask_image:
                _log(f"Mask image: {mask_image}")
            if background_image:
                _log(f"Background image: {background_image}")
            _log(f"Region assignments: {len(region_assignments) if region_assignments else 0} regions")
            
            # RUN HYBRID MODE GENERATION
            results = []
            successful = 0
            
            for fill_method in fill_methods:
                success, msg, params = _run_hybrid_generation(
                    input_image=str(resolved_input),
                    mask_image=mask_image,
                    background_image=background_image,
                    region_assignments=region_assignments,
                    output_dir=output_dir,
                    seed=seed,
                    fill_method=fill_method,
                    verbose=verbose
                )
                results.append(("hybrid_multi", success, msg, fill_method, params))
                if success:
                    successful += 1
            
            total_combinations = len(fill_methods)
        else:
            # ORIGINAL SINGLE GEOMETRY MODE
            _log(f"{len(geoms)} geometries × {len(fill_methods)} fill methods")
            _log(f"Fill methods: {', '.join(fill_methods)}")
            
            results = []
            successful = 0
            total_combinations = len(geoms) * len(fill_methods)

            for geom in geoms:
                geom_params = geometry_parameters.get(geom, {})
                if geom_params and verbose:
                    _log(f"Parameters for {geom}:")
                
                for fill_method in fill_methods:
                    success, msg, params = _run_single_geometry(
                        geom, str(resolved_input), output_dir, points, seed, 
                        fill_method, geom_params, verbose
                    )
                    results.append((geom, success, msg, fill_method, params))
                    if success:
                        successful += 1

        # Generate comparison gallery
        _generate_comparison_gallery(output_dir, results, resolved_input, fill_methods)

        failed = total_combinations - successful
        if failed == 0:
            _log(f"All {total_combinations} generations completed successfully!", "complete")
        elif successful > 0:
            _log(
                f"Batch complete: {successful}/{total_combinations} successful, {failed} failed",
                "warning",
            )
        else:
            _log(f"Batch failed: 0/{total_combinations} successful", "error")

        _log(f"Wrote comparison gallery -> {output_dir}/index.html")

        if auto_open:
            gallery_path = output_dir / "index.html"
            _log("Opening gallery in browser...", "success")
            webbrowser.open(f"file:///{gallery_path}")
            _log("Gallery opened. Look for new browser tab!", "success")

        _log("Batch complete", "complete")
    except Exception as e:
        _log(f"Batch failed with exception: {e}", "error")
    finally:
        BUSY = False


def _run_hybrid_generation(
    input_image: str,
    mask_image: str,
    background_image: str,
    region_assignments: Dict,
    output_dir: Path,
    seed: int,
    fill_method: str = "default",
    verbose: bool = False,
) -> Tuple[bool, str, Dict[str, float]]:
    """Run hybrid multi-geometry generation via CLI"""
    
    method_suffix = "_cascade" if fill_method == "cascade" else "_default"
    hybrid_output = output_dir / f"hybrid{method_suffix}" / "frame_hybrid"
    hybrid_output.parent.mkdir(parents=True, exist_ok=True)

    # Resolve paths
    try:
        input_p = Path(input_image).resolve()
        mask_p = (ROOT / "input" / mask_image).resolve() if mask_image else None
        bg_p = (ROOT / "input" / background_image).resolve() if background_image else None
    except Exception as e:
        return False, f"Path resolution failed: {e}", {}

    # Build CLI command
    cmd = [
        "python",
        "cubist_cli.py",
        "--input", str(input_p),
        "--mask", str(mask_p),
        "--output", str(hybrid_output),
        "--seed", str(seed),
        "--export-svg",
    ]
    
    if bg_p:
        cmd.extend(["--background", str(bg_p)])
    
    if fill_method == "cascade":
        cmd.append("--cascade")
    
    # Add region assignments
    for region_id, assignment in region_assignments.items():
        geometry = assignment.get('geometry', 'rectangles')
        target_count = assignment.get('target_count', 100)
        params = assignment.get('params', {})
        
        region_spec = f"{region_id}:{geometry}:{target_count}"
        
        # Add parameters to region spec
        for param_name, param_value in params.items():
            region_spec += f":{param_name}={param_value}"
        
        cmd.extend(["--region", region_spec])
    
    if verbose:
        cmd.append("--verbose")

    _log(f"Running: hybrid ({fill_method} fill)", "info")
    if verbose:
        _log(f"  Regions: {len(region_assignments)}")
    
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=600
        )
        elapsed = time.time() - start_time

        if result.stdout and verbose:
            for ln in result.stdout.strip().splitlines():
                _log(ln)
        if result.stderr and (verbose or result.returncode != 0):
            for ln in result.stderr.strip().splitlines():
                _log(ln, "error")

        if result.returncode == 0:
            svg_path = hybrid_output.with_suffix(".svg")
            svg_size = svg_path.stat().st_size if svg_path.exists() else 0
            
            shapes = "unknown"
            try:
                lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
                for l in reversed(lines):
                    s = l.strip()
                    if s.startswith("{") and s.endswith("}"):
                        data = json.loads(s)
                        shapes = data.get("outputs", {}).get("svg_shapes", "unknown")
                        break
            except Exception:
                pass

            # Build parameter summary for gallery display
            param_summary = {}
            for region_id, assignment in region_assignments.items():
                geometry = assignment.get('geometry', 'unknown')
                target_count = assignment.get('target_count', 0)
                # Format as readable string
                param_summary[f"region_{region_id}"] = f"{geometry} x{target_count}"
                
                # Add custom parameters if any
                params = assignment.get('params', {})
                for param_name, param_value in params.items():
                    if param_name not in ['cascade_fill_enabled', 'seed', 'verbose']:
                        param_summary[f"r{region_id}_{param_name}"] = param_value

            _log(
                f"✓ hybrid ({fill_method}): {shapes} shapes, {svg_size} bytes ({elapsed:.2f}s)",
                "success",
            )
            return True, f"✓ hybrid ({fill_method}): {shapes} shapes", param_summary
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            _log(
                f"✗ hybrid ({fill_method}): failed with rc={result.returncode} ({elapsed:.2f}s)",
                "error",
            )
            return False, f"✗ hybrid ({fill_method}): failed", {}

    except subprocess.TimeoutExpired:
        _log(f"✗ hybrid ({fill_method}): timed out after 10 minutes", "error")
        return False, f"✗ hybrid ({fill_method}): timed out", {}
    except Exception as e:
        _log(f"✗ hybrid ({fill_method}): exception - {e}", "error")
        return False, f"✗ hybrid ({fill_method}): {e}", {}

def _extract_svg_metadata(svg_path: Path) -> Dict[str, str]:
    """Extract XMP metadata from SVG file."""
    try:
        if not svg_path.exists():
            return {}
        
        content = svg_path.read_text(encoding='utf-8')
        metadata = {}
        
        # Simple regex extraction of key metadata fields
        import re
        
        patterns = {
            'generation_time': r'<cubist:generationTime>([\d.]+)</cubist:generationTime>',
            'actual_shapes': r'<cubist:actualShapes>(\d+)</cubist:actualShapes>',
            'space_utilization': r'<cubist:spaceUtilization>([\d.]+)</cubist:spaceUtilization>',
            'create_date': r'<xmp:CreateDate>([^<]+)</xmp:CreateDate>',
            'average_shape_area': r'<cubist:averageShapeArea>(\d+)</cubist:averageShapeArea>',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                metadata[key] = match.group(1)
        
        return metadata
    except Exception:
        return {}

def _generate_comparison_gallery(
    output_dir: Path,
    results: List[Tuple[str, bool, str, str, Dict[str, float]]],
    input_image: str | Path,
    fill_methods: List[str]
) -> None:
    """Generate comparison gallery with side-by-side fill methods and parameter values"""

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

    # Enhanced wrapper template with metadata from SVG
    def create_wrapper_template(geom_name: str, method: str, params: Dict[str, float], svg_metadata: Dict[str, str]) -> str:
        params_html = ""
        if params:
            param_items = [f"{k}={v}" for k, v in params.items()]
            params_html = f"<div style='font-size:11px; margin-top:3px'>{' | '.join(param_items)}</div>"
        
        # Add metadata display
        metadata_html = ""
        if svg_metadata:
            meta_items = []
            if 'actual_shapes' in svg_metadata:
                meta_items.append(f"Shapes: {svg_metadata['actual_shapes']}")
            if 'generation_time' in svg_metadata:
                gen_time = float(svg_metadata['generation_time'])
                meta_items.append(f"Time: {gen_time:.2f}s")
            if 'space_utilization' in svg_metadata:
                space_util = float(svg_metadata['space_utilization'])
                meta_items.append(f"Coverage: {space_util:.1f}%")
            if 'create_date' in svg_metadata:
                meta_items.append(f"Created: {svg_metadata['create_date']}")
            
            if meta_items:
                metadata_html = f"<div style='font-size:11px; margin-top:5px; padding:5px; background:rgba(0,123,255,0.15); border-radius:3px'>{' | '.join(meta_items)}</div>"
        
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
            background: rgba(0,0,0,0.85);
            padding: 8px 15px;
            border-radius: 5px;
            z-index: 100;
            max-width: 90%;
            text-align: center;
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
    <div class="header">
        <div style="font-size:14px; font-weight:bold">{geom_name} ({method} fill)</div>
        {params_html}
        {metadata_html}
    </div>
    <div class="svg-container">
        <img src="frame_{geom_name}.svg" alt="{geom_name} {method} fill">
    </div>
</body>
</html>"""

    # Group results by geometry for side-by-side comparison
    results_by_geom = {}
    for geom, success, msg, method, params in results:
        if geom not in results_by_geom:
            results_by_geom[geom] = {}
        results_by_geom[geom][method] = (success, msg, params)

    gallery_items = []

    for geom in results_by_geom:
        method_columns = []

        for method in fill_methods:
            method_suffix = "_cascade" if method == "cascade" else "_default"
            
            # Handle hybrid vs single geometry paths
            if geom == "hybrid_multi":
                svg_path = output_dir / f"hybrid{method_suffix}" / "frame_hybrid.svg"
                wrapper_path = output_dir / f"hybrid{method_suffix}" / "frame_hybrid.html"
                display_name = "hybrid"
            else:
                svg_path = output_dir / f"{geom}{method_suffix}" / f"frame_{geom}.svg"
                wrapper_path = output_dir / f"{geom}{method_suffix}" / f"frame_{geom}.html"
                display_name = geom

            if method in results_by_geom[geom]:
                success, msg, params = results_by_geom[geom][method]

                if success and svg_path.exists():
                    # Extract metadata from SVG
                    svg_metadata = _extract_svg_metadata(svg_path)
                    
                    # Create enhanced wrapper with metadata
                    wrapper_html = create_wrapper_template(display_name, method, params, svg_metadata)
                    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
                    wrapper_path.write_text(wrapper_html, encoding="utf-8")

                    # Build relative paths for gallery
                    if geom == "hybrid_multi":
                        rel_wrapper = f"hybrid{method_suffix}/frame_hybrid.html"
                        rel_svg = f"hybrid{method_suffix}/frame_hybrid.svg"
                    else:
                        rel_wrapper = f"{geom}{method_suffix}/frame_{geom}.html"
                        rel_svg = f"{geom}{method_suffix}/frame_{geom}.svg"
                    
                    file_size = svg_path.stat().st_size
                    size_str = (
                        f"{file_size / 1024:.1f} KB"
                        if file_size > 1024
                        else f"{file_size} bytes"
                    )

                    # Count shapes from metadata
                    shapes = svg_metadata.get('actual_shapes', 'unknown')

                    # Format metadata for display
                    metadata_display = ""
                    if svg_metadata:
                        meta_lines = []
                        if 'generation_time' in svg_metadata:
                            gen_time = float(svg_metadata['generation_time'])
                            meta_lines.append(f"<div style='font-size:11px; color:#28a745; font-weight:bold'>Generation: {gen_time:.2f}s</div>")
                        if 'space_utilization' in svg_metadata:
                            space_util = float(svg_metadata['space_utilization'])
                            meta_lines.append(f"<div style='font-size:11px; color:#007bff; font-weight:bold'>Coverage: {space_util:.1f}%</div>")
                        if 'create_date' in svg_metadata:
                            meta_lines.append(f"<div style='font-size:10px; color:#666'>{svg_metadata['create_date']}</div>")
                        metadata_display = "<div style='margin-top:8px; padding:8px; background:#f8f9fa; border-left:3px solid #007bff; border-radius:3px'>" + "".join(meta_lines) + "</div>"

                    # Format parameters for display
                    params_display = ""
                    if params:
                        param_lines = [f"<div style='font-size:11px'>{k}: {v}</div>" for k, v in params.items()]
                        params_display = "".join(param_lines)

                    method_columns.append(f"""
                        <div class="method-column">
                            <h4>✅ {method.title()} Fill</h4>
                            <p><strong>{shapes} shapes</strong> • {size_str}</p>
                            {params_display if params_display else '<div style="font-size:11px; color:#999">No custom parameters</div>'}
                            {metadata_display}
                            <p><a href="{rel_wrapper}" target="_blank">view fullscreen</a> | <a href="{rel_svg}" target="_blank">raw SVG</a></p>
                            <div class="thumbnail-container" onclick="window.open('{rel_wrapper}', '_blank')">
                                <img src="{rel_svg}" alt="{display_name} {method} fill">
                            </div>
                        </div>
                    """)
                else:
                    method_columns.append(f"""
                        <div class="method-column">
                            <h4>Failed</h4>
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

        gallery_items.append(f"""
            <div class="geometry-comparison">
                <h3>{geom}</h3>
                <div class="methods-row">
                    {''.join(method_columns)}
                </div>
            </div>
        """)

    preview_html = ""
    if preview_rel:
        preview_html = f'<div style="margin-bottom:16px"><h3>Input preview</h3><a href="{preview_rel}" target="_blank"><img src="{preview_rel}" style="max-width:420px;max-height:300px;border:1px solid #ccc;object-fit:contain"></a></div>'

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Cubist Art Gallery</title>
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
                margin-top: 10px;
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
            <h1>Cubist Art Gallery</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
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
    """Render main UI using external template"""
    geom_params_json = json.dumps(GEOMETRY_PARAMETERS)
    
    return render_template(
        'production_ui.html',
        ui_title=UI_TITLE,
        version=VERSION,
        geoms_json=json.dumps(GEOMS),
        geom_params_json=geom_params_json
    )


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
        upload_type = request.args.get("type", "input")
        
        if not f or f.filename == "":
            return jsonify({"error": "no file"}), 400
        
        dest = ROOT / "input"
        dest.mkdir(parents=True, exist_ok=True)
        filename = Path(f.filename).name
        out = dest / filename
        f.save(str(out))
        
        _log(f"Uploaded {upload_type} file: {out}", "success")
        
        # If mask uploaded, detect regions
        regions = None
        if upload_type == "mask" and Image:
            try:
                mask_img = Image.open(out).convert('L')
                from collections import Counter
                pixel_counts = Counter(mask_img.getdata())
                total_pixels = mask_img.size[0] * mask_img.size[1]
                
                regions = []
                for value, count in sorted(pixel_counts.items(), key=lambda x: -x[1])[:10]:
                    percentage = (count / total_pixels) * 100
                    if percentage > 1.0:  # Only show regions > 1%
                        regions.append({
                            'value': value,
                            'count': count,
                            'percentage': round(percentage, 1)
                        })
            except Exception as e:
                _log(f"Could not detect regions: {e}", "warning")
        
        return jsonify({"ok": True, "filename": filename, "regions": regions})
    except Exception as e:
        _log(f"Upload failed: {e}", "error")
        return jsonify({"error": str(e)}), 500

@app.route("/detect_regions")
def detect_regions():
    """Detect regions in mask image for hybrid mode"""
    fname = request.args.get("file", "")
    if not fname or not Image:
        return jsonify({"regions": []})
    
    try:
        mask_path = (ROOT / "input" / fname).resolve()
        if not mask_path.exists():
            return jsonify({"regions": []})
        
        mask_img = Image.open(mask_path).convert('L')
        from collections import Counter
        pixel_counts = Counter(mask_img.getdata())
        total_pixels = mask_img.size[0] * mask_img.size[1]
        
        regions = []
        for value, count in sorted(pixel_counts.items(), key=lambda x: -x[1])[:10]:
            percentage = (count / total_pixels) * 100
            if percentage > 1.0:  # Only show regions > 1%
                regions.append({
                    'value': value,
                    'count': count,
                    'percentage': round(percentage, 1)
                })
        
        return jsonify({"regions": regions})
    except Exception as e:
        return jsonify({"regions": [], "error": str(e)})
    

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
            data.get("geometry_parameters", {}),
            bool(data.get("auto_open", True)),
            bool(data.get("verbose", False)),
            bool(data.get("hybrid_mode", False)),
            data.get("mask_image", ""),
            data.get("background_image", ""),
            data.get("region_assignments", {})
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
    print(f"Cubist Production UI {VERSION} - Phase 2: Hybrid Subdivision")
    print("Server running at http://127.0.0.1:5123")
    try:
        app.run(host="127.0.0.1", port=5123, debug=False)
    except Exception as e:
        print(f"Server failed to start: {e}")