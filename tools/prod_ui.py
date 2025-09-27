# tools/prod_ui.py - COMPLETE FIXED VERSION
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

from flask import Flask, jsonify, render_template_string, request, send_file

# Add missing imports
try:
    from PIL import Image

    # ImageCms is optional; use if present for profile->sRGB conversion
    try:
        from PIL import ImageCms
    except Exception:
        ImageCms = None
except Exception:
    Image = None
    ImageCms = None

# ---------------- Paths & constants ----------------
ROOT = Path(__file__).resolve().parents[1]  # .../cubist_art
TOOLS = ROOT / "tools"
OUT_ROOT = ROOT / "output" / "production"
PREFS_PATH = TOOLS / ".prod_ui_prefs.json"

# FIXED: Removed concentric_circles as requested
GEOMS = [
    "delaunay",
    "voronoi",
    "rectangles",
    "poisson_disk",
    "scatter_circles",
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
        "cascade": 3,
        "export_svg": True,
        "enable_plugin_exec": True,
        "verbose_probe": True,
        "auto_open_gallery": True,
        "geoms": GEOMS[:3],
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
    verbose: bool = False,
) -> Tuple[bool, str]:
    """Run a single geometry with enhanced error reporting"""

    geom_output = output_dir / geom / f"frame_{geom}.svg"
    geom_output.parent.mkdir(parents=True, exist_ok=True)

    # Resolve and log input file diagnostic
    try:
        in_p = Path(input_image)
        if not in_p.is_absolute():
            in_p = (ROOT / "input" / input_image).resolve()
        else:
            in_p = in_p.resolve()
        # safety: ensure inside project
        try:
            in_p.relative_to(ROOT)
        except Exception:
            _log(f"[warn] input path {in_p} not under project root", "warning")
        # NEW: log image mode & icc profile presence for diagnostics
        try:
            if Image is not None and in_p.exists():
                with Image.open(str(in_p)) as _im:
                    icc = _im.info.get("icc_profile")
                    _log(
                        f"[debug] input image mode={_im.mode}, size={_im.size}, icc_profile={'yes' if icc else 'no'}",
                        "info",
                    )
        except Exception as e:
            _log(f"[debug] could not inspect input image: {e}", "warning")
        if in_p.exists():
            try:
                _log(
                    f"[debug] geometry={geom} using input file: {in_p} size={in_p.stat().st_size} bytes",
                    "success",
                )
            except Exception:
                _log(f"[debug] geometry={geom} using input file: {in_p}", "success")
        else:
            _log(f"[warning] geometry={geom} input file not found: {in_p}", "warning")
    except Exception as e:
        _log(f"[warning] resolving input path failed: {e}", "warning")

    cmd = [
        "python",
        "cubist_cli.py",
        "--input",
        str(input_image),
        "--output",
        str(output_dir / geom / f"frame_{geom}"),
        "--geometry",
        geom,
        "--points",
        str(points),
        "--seed",
        str(seed),
        "--export-svg",
    ]
    if verbose:
        cmd.append("--verbose")

    _log(f"Running: {geom}")
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=300
        )
        elapsed = time.time() - start_time

        # Forward verbose stdout to UI when requested
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
                if json_line is None and lines:
                    json_line = lines[-1]
                if json_line:
                    data = json.loads(json_line)
                    shapes = data.get("svg_shapes", "unknown")
            except Exception:
                pass
            _log(
                f"✓ {geom}: {shapes} shapes, {svg_size} bytes ({elapsed:.2f}s)",
                "success",
            )
            return True, f"✓ {geom}: {shapes} shapes, {svg_size} bytes ({elapsed:.2f}s)"
        else:
            error_msg = "Unknown error"
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
                    error_msg = data.get(
                        "plugin_exc",
                        result.stderr.strip() if result.stderr else "Unknown error",
                    )
                else:
                    error_msg = (
                        result.stderr.strip() if result.stderr else "Unknown error"
                    )
            except Exception:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            _log(
                f"✗ {geom}: failed with rc={result.returncode} ({elapsed:.2f}s)",
                "error",
            )
            _log(f"  Error: {error_msg}", "error")
            return False, f"✗ {geom}: failed - {error_msg}"
    except subprocess.TimeoutExpired:
        _log(f"✗ {geom}: timed out after 5 minutes", "error")
        return False, f"✗ {geom}: timed out"
    except Exception as e:
        _log(f"✗ {geom}: exception - {e}", "error")
        return False, f"✗ {geom}: {e}"


def _run_batch(
    geoms: List[str],
    input_image: str,
    points: int,
    seed: int,
    auto_open: bool,
    verbose: bool = False,
) -> None:
    """Enhanced batch runner with better logging"""
    global BUSY
    try:
        BUSY = True
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir = OUT_ROOT / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        # Resolve input image and log
        try:
            p = Path(input_image)
            if not p.is_absolute():
                resolved_input = (ROOT / "input" / input_image).resolve()
            else:
                resolved_input = p.resolve()
            try:
                resolved_input.relative_to(ROOT)
            except Exception:
                _log(
                    f"Warning: resolved input {resolved_input} is outside project root",
                    "warning",
                )
        except Exception:
            resolved_input = Path(input_image)

        _log(f"Starting batch with {len(geoms)} geometries")
        _log(f"Running {len(geoms)} geometries into {output_dir}...")
        _log(f"Input image: {resolved_input}")

        results = []
        successful = 0
        for geom in geoms:
            # pass resolved_input explicitly to the geometry runner so plugins get the absolute path
            success, msg = _run_single_geometry(
                geom, str(resolved_input), output_dir, points, seed, verbose
            )
            results.append((geom, success, msg))
            if success:
                successful += 1

        # Generate gallery (now include input preview)
        _generate_gallery(output_dir, results, resolved_input)

        total = len(geoms)
        failed = total - successful
        if failed == 0:
            _log(f"🎉 All {total} geometries completed successfully!", "complete")
        elif successful > 0:
            _log(
                f"⚠ Batch complete: {successful}/{total} successful, {failed} failed",
                "warning",
            )
        else:
            _log(f"⚠ Batch failed: 0/{total} successful", "error")

        _log(f"Wrote gallery -> {output_dir}/index.html")
        _log(f"Generated gallery with {successful}/{total} successful SVGs")

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


def _parse_css_color(s: str):
    """Parse simple CSS color forms: #rgb #rrggbb, rgb(), rgba(), hsl(), common names.
    Returns (r,g,b) ints 0-255 or None on failure."""
    try:
        s = s.strip()
        # hex
        if s.startswith("#"):
            h = s[1:]
            if len(h) == 3:
                h = "".join(ch * 2 for ch in h)
            if len(h) == 6:
                return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
            return None
        # rgb(a)
        m = re.match(
            r"rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)", s, flags=re.I
        )
        if m:
            r, g, b = m.groups()
            return (int(float(r)), int(float(g)), int(float(b)))
        # hsl()
        m = re.match(
            r"hsla?\(\s*([0-9.]+)\s*,\s*([0-9.]+)%\s*,\s*([0-9.]+)%", s, flags=re.I
        )
        if m:
            h, sp, lp = map(float, m.groups())
            # convert HSL to RGB
            h = h % 360 / 360.0
            s = sp / 100.0
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

            if s == 0:
                r = g = b = l
            else:
                q = l * (1 + s) if l < 0.5 else l + s - l * s
                p = 2 * l - q
                r = hue2rgb(p, q, h + 1 / 3)
                g = hue2rgb(p, q, h)
                b = hue2rgb(p, q, h - 1 / 3)
            return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))
        # some common names
        n = s.lower()
        nmap = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "red": (255, 0, 0),
            "green": (0, 128, 0),
            "blue": (0, 0, 255),
        }
        if n in nmap:
            return nmap[n]
    except Exception:
        pass
    return None


def _rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


# Replace / add color conversion + distance helpers (use CIE Lab for perceptual distance)
def _srgb_channel_to_linear(c: float) -> float:
    # c in 0..255
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgb_to_xyz(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    # convert sRGB (0-255) to XYZ (D65)
    r_lin = _srgb_channel_to_linear(rgb[0])
    g_lin = _srgb_channel_to_linear(rgb[1])
    b_lin = _srgb_channel_to_linear(rgb[2])
    # sRGB to XYZ (D65)
    x = r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375
    y = r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750
    z = r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041
    return (x, y, z)


def _xyz_to_lab(xyz: Tuple[float, float, float]) -> Tuple[float, float, float]:
    x, y, z = xyz
    # D65 reference white
    xn, yn, zn = 0.95047, 1.00000, 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t) + (16.0 / 116.0)

    fx = f(x / xn)
    fy = f(y / yn)
    fz = f(z / zn)
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return (L, a, b)


def _rgb_to_lab(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    xyz = _rgb_to_xyz(rgb)
    return _xyz_to_lab(xyz)


def _color_distance(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    """Perceptual distance between two RGB colors using Lab Euclidean distance."""
    try:
        lab_a = _rgb_to_lab(a)
        lab_b = _rgb_to_lab(b)
        # Euclidean distance in Lab (approximate ΔE)
        d = (
            (lab_a[0] - lab_b[0]) ** 2
            + (lab_a[1] - lab_b[1]) ** 2
            + (lab_a[2] - lab_b[2]) ** 2
        ) ** 0.5
        return d
    except Exception:
        # fallback to simple RGB distance if anything goes wrong
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def _top_image_colors(image_path: Path, n: int = 8):
    """Return top n colors from image_path as list of (r,g,b). Handles ICC -> sRGB when possible."""
    if Image is None:
        _log("Pillow not installed; skipping input palette extraction", "warning")
        return []
    try:
        with Image.open(str(image_path)) as im:
            # If an embedded ICC profile exists and ImageCms is available, convert to sRGB for accurate sampling
            try:
                icc = im.info.get("icc_profile")
                if icc and ImageCms is not None:
                    try:
                        # create profiles and convert image to sRGB using the embedded profile bytes
                        srgb_profile = ImageCms.createProfile("sRGB")
                        src_profile = (
                            ImageCms.ImageCmsProfile(io.BytesIO(icc))
                            if isinstance(icc, (bytes, bytearray))
                            else None
                        )
                        if src_profile is not None:
                            im = ImageCms.profileToProfile(
                                im, src_profile, srgb_profile, outputMode="RGB"
                            )
                            _log(
                                "Converted input image from embedded ICC profile to sRGB for palette extraction",
                                "info",
                            )
                        else:
                            _log(
                                "Embedded ICC profile not in expected bytes form; skipping profile conversion",
                                "warning",
                            )
                    except Exception as e:
                        _log(
                            f"ICC->sRGB conversion failed; proceeding without profile conversion ({e})",
                            "warning",
                        )
            except Exception:
                # ignore profile handling errors
                pass

            # Convert to RGBA and downscale to speed up
            im = im.convert("RGBA")
            im.thumbnail((300, 300))

            # Keep only opaque/visible pixels
            pixels = [px for px in im.getdata() if px[3] > 0]
            if not pixels:
                return []

            # Quantize to reduce colors then getcounts
            pal = Image.new("RGBA", im.size)
            pal.putdata(pixels)
            q = pal.convert("P", palette=Image.ADAPTIVE, colors=n)
            p = q.convert("RGB")
            colors = p.getcolors(p.size[0] * p.size[1]) or []
            colors.sort(reverse=True)
            top = [c[1] for c in colors[:n]]
            # ensure unique
            seen = []
            out = []
            for c in top:
                if c not in seen:
                    seen.append(c)
                    out.append(c)
            return out
    except Exception as e:
        _log(f"Failed extracting top image colors: {e}", "warning")
        return []


def _generate_gallery(
    output_dir: Path, results: List[Tuple[str, bool, str]], input_image: str | Path
) -> None:
    """Generate an HTML gallery with the results (writes per-SVG wrapper pages) and include input preview."""
    # Copy input image into the output assets folder so gallery shows exact file used
    preview_rel = None
    preview_abs = None
    try:
        src = Path(input_image)
        if not src.is_absolute():
            src = (ROOT / "input" / str(input_image)).resolve()
        if src.exists() and src.is_file():
            assets = output_dir / "assets"
            assets.mkdir(parents=True, exist_ok=True)
            dest = assets / src.name
            # only copy if different
            try:
                if not dest.exists() or src.resolve() != dest.resolve():
                    shutil.copy2(src, dest)
                preview_rel = f"assets/{src.name}"
                preview_abs = dest
                _log(f"Copied input preview -> {dest}", "success")
            except Exception as e:
                _log(f"Failed copying preview: {e}", "warning")
        else:
            _log(f"No input preview available (not found): {src}", "warning")
    except Exception as e:
        _log(f"Error preparing preview: {e}", "warning")

    # compute top colors of input image (optional if Pillow present)
    input_palette = _top_image_colors(preview_abs, 8) if preview_abs else []

    # --- NEW: build visual palette HTML and log the palette ----------------
    input_palette_html = ""
    if input_palette:
        # log palette as hex list
        try:
            hexes = [_rgb_to_hex(c) for c in input_palette]
            _log(f"Input palette: {', '.join(hexes)}", "info")
        except Exception:
            hexes = []
        # render swatches with hex labels
        items = []
        for c in input_palette:
            try:
                hexc = _rgb_to_hex(c)
            except Exception:
                hexc = "transparent"
            items.append(
                f'<div style="display:inline-block;margin-right:8px;text-align:center;"><span style="display:block;width:34px;height:24px;background:{hexc};border:1px solid #999;margin-bottom:4px;"></span><div style="font-size:11px;color:#444">{hexc}</div></div>'
            )
        input_palette_html = f'<div style="margin-bottom:12px"><h4>Input palette</h4><div>{"".join(items)}</div></div>'
    # -------------------------------------------------------------------------

    gallery_items = []
    for geom, success, msg in results:
        svg_path = output_dir / geom / f"frame_{geom}.svg"
        wrapper_path = output_dir / geom / f"frame_{geom}.html"
        if success and svg_path.exists():
            # FIXED: Better wrapper with proper SVG fitting
            try:
                wrapper_html = f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
html,body{{height:100%;margin:0;padding:0;background:#111;overflow:hidden}}
.frame{{width:100vw;height:100vh;display:flex;align-items:center;justify-content:center;padding:10px;box-sizing:border-box}}
object{{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain}}
</style>
</head><body><div class="frame"><object data="frame_{geom}.svg" type="image/svg+xml"></object></div></body></html>"""
                wrapper_path.parent.mkdir(parents=True, exist_ok=True)
                wrapper_path.write_text(wrapper_html, encoding="utf-8")
            except Exception:
                pass

            rel_wrapper = f"{geom}/frame_{geom}.html"
            rel_svg = f"{geom}/frame_{geom}.svg"
            file_size = svg_path.stat().st_size
            size_str = (
                f"{file_size / 1024:.1f} KB"
                if file_size > 1024
                else f"{file_size} bytes"
            )

            # extract fills and build swatches and mapping to input palette
            shapes = "unknown"
            swatch_html = ""
            mapping_lines = []
            try:
                svg_content = svg_path.read_text(encoding="utf-8")
                shapes = (
                    svg_content.count("<circle")
                    + svg_content.count("<polygon")
                    + svg_content.count("<path")
                )
                fills = re.findall(
                    r'fill=["\']([^"\']+)["\']', svg_content, flags=re.IGNORECASE
                )
                fills += re.findall(
                    r'style=["\'][^"\']*fill:\s*([^;\'"]+)',
                    svg_content,
                    flags=re.IGNORECASE,
                )
                seen = []
                for fcol in fills:
                    col = fcol.strip()
                    if not col or col.lower() == "none":
                        continue
                    if col not in seen:
                        seen.append(col)
                if seen:
                    # swatches
                    swatch_html = '<div style="margin-top:6px">'
                    for c in seen[:8]:
                        rgb = _parse_css_color(c)
                        hexc = _rgb_to_hex(rgb) if rgb else c
                        swatch_html += f'<span title="{c}" style="display:inline-block;width:18px;height:18px;background:{hexc};border:1px solid #999;margin-right:6px;vertical-align:middle"></span>'
                        # find nearest input palette color
                        if input_palette and rgb:
                            best = min(
                                input_palette, key=lambda ip: _color_distance(ip, rgb)
                            )
                            dist = _color_distance(best, rgb)
                            best_hex = _rgb_to_hex(best)
                            mapping_lines.append(f"{c} -> {best_hex} (Δ={dist:.1f})")
                            _log(
                                f"{geom} fill {c} -> closest input {best_hex} Δ={dist:.1f}",
                                "info",
                            )
                        elif rgb:
                            _log(f"{geom} fill {c} parsed as {rgb}", "info")
                    swatch_html += "</div>"
            except Exception as e:
                _log(f"Color extraction failed for {geom}: {e}", "warning")

            # include mapping summary under swatches (if any)
            map_html = ""
            if mapping_lines:
                map_html = (
                    "<div style='font-size:12px;color:#444;margin-top:6px'>"
                    + "<br/>".join(mapping_lines)
                    + "</div>"
                )

            gallery_items.append(f"""
			<div class="gallery-item success">
				<h3>✅ {geom}</h3>
				<p><strong>{shapes} shapes</strong> • {size_str} • <a href="{rel_wrapper}" target="_blank">open (fit)</a> | <a href="{rel_svg}" target="_blank">raw SVG</a></p>
				{swatch_html}
				{map_html}
				<div class="thumbnail-container" onclick="window.open('{rel_wrapper}', '_blank')" style="cursor:pointer;border:1px solid #ddd;background:white;width:300px;height:200px;position:relative;overflow:hidden;">
					<object data="{rel_svg}" type="image/svg+xml" style="width:100%;height:100%;object-fit:contain;pointer-events:none;"></object>
				</div>
			</div>
			""")
        else:
            gallery_items.append(f"""
			<div class="gallery-item error">
				<h3>⚠ {geom}</h3>
				<p>⚠ No SVG for <strong>{geom}</strong> — {svg_path}</p>
			</div>
			""")

    # Build gallery page and include input preview at the top (if available)
    preview_html = ""
    if preview_rel:
        preview_html = f'<div style="display:flex;align-items:center;gap:18px;margin-bottom:16px"><div><h3>Input preview</h3><a href="{preview_rel}" target="_blank"><img src="{preview_rel}" style="max-width:420px;max-height:300px;border:1px solid #ccc"></a></div><div>{input_palette_html}</div></div>'

    # FIXED: Added f before the string to make it an f-string
    html_content = f"""
	<!DOCTYPE html>
	<html>
	<head>
		<title>Cubist Art Gallery</title>
		<style>
			body{{font-family:system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:20px}}
			.gallery{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}}
			.gallery-item{{background:white;padding:15px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}}
		</style>
	</head>
	<body>
		<div class="header">
			<h1>🎨 Cubist Art Gallery</h1>
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
    return render_template_string(
        r"""
<!doctype html><html><head><meta charset="utf-8"><title>Cubist Prod UI</title>
<style>
body{font-family:system-ui,Arial;margin:18px} .row{margin-bottom:12px} input[type=text]{width:520px;padding:6px} select{padding:6px}
.button{padding:8px 12px;border-radius:6px;border:1px solid #888;background:#2d6cdf;color:#fff}
.button.secondary{background:#6c757d} .log{background:#111;color:#eee;padding:12px;height:300px;overflow:auto;font-family:monospace}
.preview{max-width:360px;max-height:200px;border:1px solid #444;border-radius:6px}
</style>
</head><body>
<h1>🎨 Cubist Art — Production UI</h1>

<div class="row">
  <label>Input image</label><br/>
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
  <label>Points</label>
  <select id="points"><option value="100">100</option><option value="500" selected>500</option><option value="1000">1000</option><option value="4000">4000</option></select>
</div>

<div class="row">
  <label>Geometries</label>
  <div>
    {% for g in geoms %}
      <label style="margin-right:12px"><input type="checkbox" id="geom_{{g}}" checked/> {{g}}</label>
    {% endfor %}
  </div>
</div>

<div class="row">
  <label><input id="auto_open" type="checkbox" checked/> Auto-open gallery</label>
  <label style="margin-left:18px"><input id="verbose" type="checkbox"/> Verbose</label>
</div>

<div class="row">
  <button class="button" id="run_btn" onclick="runBatch()">🚀 Run Batch</button>
  <button class="button secondary" onclick="clearLog()">Clear Log</button>
  <button class="button" onclick="copyLog()">Copy Log</button>
  <span id="status_text" style="margin-left:12px"></span>
</div>

<div id="log" class="log"></div>

<script>
const geoms = JSON.parse('{{ geoms_json|safe }}');
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
  if(r.ok && j.filename){ await loadInputFiles(); document.getElementById('input_files_select').value = j.filename; useSelected(); }
  else alert('Upload failed: ' + (j.error || 'unknown'));
}
function clearLog(){ document.getElementById('log').innerHTML = ''; }
function copyLog(){ navigator.clipboard.writeText(document.getElementById('log').innerText).then(()=>{ alert('Log copied') }, ()=> alert('Copy failed')); }

async function savePrefs(obj){
  try{
    const base = { input_image: document.getElementById('input_image').value,
                   points: parseInt(document.getElementById('points').value),
                   geoms: Array.from(geoms).filter(g=>document.getElementById('geom_'+g).checked),
                   auto_open_gallery: document.getElementById('auto_open').checked,
                   verbose_probe: document.getElementById('verbose').checked };
    const payload = Object.assign(base, obj||{});
    await fetch('/save_prefs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  }catch(e){ console.warn('savePrefs', e); }
}

document.addEventListener('DOMContentLoaded', async ()=>{
  // populate geometry checkboxes labels if needed and hook changes to savePrefs
  await loadInputFiles();
  document.getElementById('auto_open').addEventListener('change', ()=> savePrefs());
  document.getElementById('verbose').addEventListener('change', ()=> savePrefs());
  geoms.forEach(g=>{
    const el = document.getElementById('geom_'+g);
    if(el) el.addEventListener('change', ()=> savePrefs());
  });
  // load prefs
  try{
    const p = await (await fetch('/prefs')).json();
    if(p.input_image) document.getElementById('input_image').value = p.input_image;
    if(p.points) document.getElementById('points').value = p.points;
    if(Array.isArray(p.geoms)){
      geoms.forEach(g=>{ const el=document.getElementById('geom_'+g); if(el) el.checked = p.geoms.includes(g); });
    }
    document.getElementById('auto_open').checked = p.auto_open_gallery !== false;
    document.getElementById('verbose').checked = !!(p.verbose_probe || p.verbose);
    setInputPreview(p.input_image || '');
  }catch(e){ console.warn('prefs load', e); }
});

async function runBatch(){
  const inputImage = document.getElementById('input_image').value.trim();
  if(!inputImage){ alert('Specify input'); return; }
  const exists = await (await fetch('/file_exists?file=' + encodeURIComponent(inputImage))).json();
  if(!exists.exists && !confirm('Input not found on server. Continue?')) return;
  const selected = geoms.filter(g=>document.getElementById('geom_'+g).checked);
  if(selected.length===0){ alert('Select at least one geometry'); return; }
  const payload = {
    input_image: inputImage,
    points: parseInt(document.getElementById('points').value),
    seed: 42,
    geoms: selected,
    auto_open: document.getElementById('auto_open').checked,
    verbose: document.getElementById('verbose').checked
  };
  await fetch('/run_batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  document.getElementById('status_text').textContent = 'Batch started...';
}

// polling logs/status
setInterval(async ()=>{
  try{
    const st = await (await fetch('/status')).json();
    document.getElementById('status_text').textContent = st.busy ? 'Running...' : 'Idle';
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
""",
        geoms_json=json.dumps(GEOMS),
        geoms=GEOMS,
    )


@app.route("/input_files")
def input_files():
    input_dir = ROOT / "input"
    files: List[str] = []
    try:
        if input_dir.exists():
            for p in sorted(input_dir.iterdir()):
                if p.is_file() and p.suffix.lower() in (
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".gif",
                    ".webp",
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
            try:
                p_res.relative_to(ROOT)
            except Exception:
                return "Forbidden", 403
        else:
            p_res = (ROOT / "input" / fname).resolve()
            try:
                p_res.relative_to(ROOT)
            except Exception:
                return "Forbidden", 403
        if p_res.exists() and p_res.is_file():
            return send_file(p_res)
    except Exception:
        pass
    return "Not found", 404


@app.route("/file_exists")
def file_exists():
    fname = request.args.get("file", "")
    if not fname:
        return jsonify({"exists": False})
    try:
        p = Path(fname)
        if p.is_absolute():
            p_res = p.resolve()
            try:
                p_res.relative_to(ROOT)
            except Exception:
                return jsonify({"exists": False})
        else:
            p_res = (ROOT / "input" / fname).resolve()
            try:
                p_res.relative_to(ROOT)
            except Exception:
                return jsonify({"exists": False})
        return jsonify({"exists": p_res.exists()})
    except Exception:
        return jsonify({"exists": False})


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
    raw_input = data.get("input_image", "")
    try:
        p = Path(raw_input)
        if p.is_absolute():
            resolved = p.resolve()
        else:
            resolved = (ROOT / "input" / raw_input).resolve()
        try:
            resolved.relative_to(ROOT)
        except Exception:
            _log(f"Warning: input {resolved} outside project root", "warning")
    except Exception:
        resolved = Path(raw_input)
    prefs = _load_prefs()
    prefs.update(data)
    prefs["input_image"] = str(resolved)
    prefs["verbose_probe"] = bool(
        data.get("verbose", prefs.get("verbose_probe", False))
    )
    _save_prefs(prefs)
    RUN_THREAD = threading.Thread(
        target=_run_batch,
        args=(
            data.get("geoms", GEOMS[:3]),
            str(resolved),
            int(data.get("points", 500)),
            int(data.get("seed", 42)),
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


@app.route("/gallery/<path:batch_id>")
def gallery(batch_id):
    gallery_path = OUT_ROOT / batch_id / "index.html"
    if gallery_path.exists():
        return send_file(gallery_path)
    return "Gallery not found", 404


if __name__ == "__main__":
    print("Production UI ready - v2.4.0 enhanced")
    print("🎨 Server running at http://127.0.0.1:5123")
    try:
        app.run(host="127.0.0.1", port=5123, debug=False)
    except KeyboardInterrupt:
        print("\nShutdown complete")