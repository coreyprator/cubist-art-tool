# === CUBIST STAMP BEGIN ===
# Project : Cubist Art
# File    : cubist_cli.py
# Purpose : Command-line interface that runs the core geometry pipeline and writes SVG.
# Version : v2.3.7 (CLI)
# Note    : Full-file replacement.
# === CUBIST STAMP END ===

from __future__ import annotations


# --- Back-compat: public entrypoint (hoisted) ---
def run_cubist(*args, **kwargs):
    """
    Thin shim so rom cubist_core_logic import run_cubist works without circulars.
    Resolves the real function at *call* time.
    """
    fn = globals().get("run_pipeline", None)
    if fn is not None:
        return fn(*args, **kwargs)
    from cubist_api import run_cubist as _rc  # lazy to avoid import-time cycles

    return _rc(*args, **kwargs)


# --- End back-compat ---


import argparse
from pathlib import Path
from typing import Any, Dict, List

# Core + export
try:
    from cubist_core_logic import run_cubist  # expects (W,H,shapes) back
except Exception as e:
    raise SystemExit(
        f"[cli] FATAL: could not import run_cubist from cubist_core_logic.py — {e}"
    )

try:
    import svg_export  # expects write_svg(shapes, filename, width=..., height=..., metadata=...)
except Exception as e:
    raise SystemExit(f"[cli] FATAL: could not import svg_export — {e}")


def _kv_pairs(items: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for item in items or []:
        if "=" in item:
            k, v = item.split("=", 1)
            v_str = v.strip()
            if v_str.lower() in ("true", "false"):
                val: Any = v_str.lower() == "true"
            else:
                try:
                    val = float(v_str) if "." in v_str else int(v_str)
                except Exception:
                    val = v_str
            out[k.strip()] = val
        else:
            out[item.strip()] = True
    return out


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Cubist Art — Pipeline CLI (writes SVG)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    iog = p.add_argument_group("I/O")
    iog.add_argument("--input", dest="input", help="Input image path")
    iog.add_argument("--input-svg", dest="input_svg", default=None)
    iog.add_argument(
        "--output", dest="output", default="output/out.svg", help="Output SVG filepath"
    )
    iog.add_argument("--output-dir", dest="output_dir", default=None)
    iog.add_argument("--mask", dest="mask", default=None)

    pipe = p.add_argument_group("Pipeline")
    pipe.add_argument(
        "--geometry",
        dest="geometry",
        default="delaunay",
        help="Geometry name. Built-ins: delaunay | voronoi | rectangles. For plugins use --enable-plugin-exec.",
    )
    pipe.add_argument("--points", dest="points", type=int, default=800)
    pipe.add_argument("--seed", dest="seed", type=int, default=123)
    pipe.add_argument(
        "--param",
        dest="params",
        action="append",
        default=[],
        help="Extra params as key=value (repeatable)",
    )
    pipe.add_argument("--cascade-stages", dest="cascade_stages", type=int, default=1)
    pipe.add_argument(
        "--cascade-fill",
        dest="cascade_fill",
        choices=["image", "solid", "none"],
        default="image",
    )
    pipe.add_argument("--export-svg", dest="export_svg", action="store_true")
    pipe.add_argument(
        "--svg-limit", dest="svg_limit", type=int, default=0, help="0 = no limit"
    )
    pipe.add_argument("--metrics-json", dest="metrics_json", default=None)

    adv = p.add_argument_group("Advanced")
    adv.add_argument("--timeout-seconds", dest="timeout_seconds", type=int, default=0)
    adv.add_argument(
        "--enable-plugin-exec",
        dest="enable_plugin_exec",
        action="store_true",
        help="If geometry isn’t a built-in, try geometry_plugins/<name>.py",
    )

    p.add_argument(
        "--pipeline",
        dest="pipeline",
        action="store_true",
        help="Run pipeline mode (default behavior)",
    )
    q = p.add_mutually_exclusive_group()
    q.add_argument("--quiet", dest="quiet", action="store_true")
    q.add_argument("--no-quiet", dest="no_quiet", action="store_true")
    p.add_argument("--verbose", dest="verbose", action="store_true")
    p.add_argument(
        "--log-level",
        dest="log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
    )

    return p.parse_args(argv)


def _ensure_parent(path: Path) -> Path:
    p = Path(path)
    if p.suffix.lower() != ".svg":
        p = p.with_suffix(".svg")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _maybe_limit(shapes: List[dict], limit: int) -> List[dict]:
    if limit and limit > 0:
        return shapes[:limit]
    return shapes


def _run_plugin(args, outfile: str, quiet: bool = False) -> int:
    """Execute geometry_plugins/<geometry>.py if present.
    Contract: module.generate(input_path, points, seed, params) -> (W,H,shapes)
    """
    import importlib

    name = f"geometry_plugins.{args.geometry}"
    try:
        mod = importlib.import_module(name)
    except Exception as e:
        raise SystemExit(
            f"[cli] Plugin '{args.geometry}' not found or failed to import: {e}"
        )
    if not hasattr(mod, "generate"):
        raise SystemExit(
            f"[cli] Plugin '{args.geometry}' missing generate(input_path, points, seed, params)"
        )

    W, H, shapes = mod.generate(
        args.input, int(args.points), int(args.seed), _kv_pairs(args.params)
    )
    svg_export.write_svg(
        shapes,
        outfile,
        width=W,
        height=H,
        metadata={"geometry": args.geometry, "plugin": True},
    )
    if not quiet:
        print(f"[plugin] Wrote: {outfile}")
    return 0


def _sample_colors_from_image(shapes, image_path, verbose: bool = False, **kwargs):
    """Sample colors from the input image at each shape's center/coordinates.
    Ensure we set 'fill' (and 'color') so svg_export will pick up sampled colors.
    Verbose: print sampling diagnostics when enabled.
    """
    from PIL import Image

    try:
        with Image.open(image_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            width, height = img.size
            if verbose:
                print(
                    f"[debug] sampling colors from {image_path} size={width}x{height} shapes={len(shapes)}"
                )
            sampled = 0
            for i, shape in enumerate(shapes):
                x = y = None
                if shape.get("type") == "circle":
                    x, y = shape.get("cx", None), shape.get("cy", None)
                elif shape.get("type") in ("rect", "rectangle"):
                    if all(k in shape for k in ("x", "y", "w", "h")):
                        x = shape["x"] + shape["w"] / 2.0
                        y = shape["y"] + shape["h"] / 2.0
                elif "points" in shape and shape["points"]:
                    pts = shape["points"]
                    x = sum(p[0] for p in pts) / len(pts)
                    y = sum(p[1] for p in pts) / len(pts)
                if x is None or y is None:
                    x = shape.get("cx", shape.get("x", None))
                    y = shape.get("cy", shape.get("y", None))
                if x is None or y is None:
                    if verbose:
                        print(f"[debug] skipping shape[{i}] no sample coord")
                    continue
                sx = max(0, min(int(round(x)), width - 1))
                sy = max(0, min(int(round(y)), height - 1))
                try:
                    r, g, b = img.getpixel((sx, sy))
                except Exception as e:
                    if verbose:
                        print(
                            f"[debug] sample failed for shape[{i}] at ({sx},{sy}): {e}"
                        )
                    r, g, b = (128, 128, 128)
                color = f"rgb({r},{g},{b})"
                shape["fill"] = color
                shape["color"] = color
                sampled += 1
                if verbose and (i < 5 or i % 100 == 0):
                    print(f"[debug] shape[{i}] sample at ({sx},{sy}) -> {color}")
            if verbose:
                print(f"[debug] sampled colors for {sampled}/{len(shapes)} shapes")
    except Exception as e:
        print(f"Warning: Color sampling failed: {e}")
    return shapes


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    quiet = args.quiet and not args.no_quiet
    params = _kv_pairs(args.params)

    out_p = Path(args.output)
    if args.output_dir:
        # If output_dir is given, put <geometry>.svg inside it.
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_p = out_dir / (f"{args.geometry}.svg")

    # Try built-in pipeline first
    try:
        W, H, shapes = run_cubist(
            input_path=args.input,
            geometry=args.geometry,
            points=int(args.points),
            seed=int(args.seed),
            cascade_stages=int(args.cascade_stages),
            cascade_fill=str(args.cascade_fill),
            extra_params=params,
            quiet=quiet,
            log_level=args.log_level,
        )
    except ValueError:
        # Probably unknown geometry -> plugin path if allowed
        if args.enable_plugin_exec:
            _ensure_parent(out_p)
            return _run_plugin(args, str(out_p), quiet=quiet)
        raise

    # Apply color sampling from input image when available
    if args.input:
        shapes = _sample_colors_from_image(shapes, args.input, verbose=args.verbose)

    shapes = _maybe_limit(shapes, int(args.svg_limit))
    out_p = _ensure_parent(out_p)
    svg_export.write_svg(
        shapes,
        str(out_p),
        width=W,
        height=H,
        metadata={"geometry": args.geometry, "params": params},
    )
    if not quiet:
        print(f"[pipeline] Wrote: {out_p.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# === CUBIST FOOTER ===
# Lines   : (add_headers.py will stamp)


# --- Back-compat: public entrypoint (added by make_run_cubist_top_level.ps1)
def run_cubist(*args, **kwargs):
    """
    Thin shim so rom cubist_core_logic import run_cubist works without circulars.
    Resolves the real function at *call* time.
    """
    fn = globals().get("run_pipeline", None)
    if fn is not None:
        return fn(*args, **kwargs)
    # Lazy import to avoid import-time cycles
    from cubist_api import run_cubist as _rc

    return _rc(*args, **kwargs)


# --- End back-compat
