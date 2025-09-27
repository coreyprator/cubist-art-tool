from __future__ import annotations
import argparse
import sys
import os
import json
import importlib
import traceback
import hashlib
import inspect
from pathlib import Path
from time import time
import logging

# Ensure logging goes to terminal (stdout) so smoke runner captures it directly
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)


def sha256_file(path: Path) -> str:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def ensure_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def load_geometry(name: str):
    tried = []
    # 1) New namespace
    try:
        return importlib.import_module(f"geometry_plugins.{name}")
    except Exception as e:
        tried.append(("geometry_plugins", e))
    # 2) Legacy namespace
    try:
        return importlib.import_module(f"geometries.{name}")
    except Exception as e:
        tried.append(("geometries", e))
    # 3) Attribute on package (both styles)
    for pkg in ("geometry_plugins", "geometries"):
        try:
            mod = importlib.import_module(pkg)
            if hasattr(mod, name):
                return getattr(mod, name)
        except Exception as e:
            tried.append((pkg, e))
    msgs = "; ".join([f"{space}: {err}" for space, err in tried])
    raise ImportError(f"Could not load geometry '{name}' via any namespace ({msgs})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--geometry", required=True)
    ap.add_argument("--points", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--param", action="append")
    ap.add_argument("--export-svg", action="store_true")
    ap.add_argument("--cascade-stages", type=int, default=3)
    ap.add_argument("--enable-plugin-exec", action="store_true")
    ap.add_argument("--pipeline")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument(
        "--verbose", action="store_true"
    )  # <-- ADDED: allow verbose flag to be passed through
    args = ap.parse_args()

    root = Path(__file__).resolve().parent
    root_src = root / "src"
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root_src))
    os.environ["PYTHONPATH"] = os.pathsep.join(
        [str(root), str(root_src), os.environ.get("PYTHONPATH", "")]
    ).strip(os.pathsep)

    inp = Path(args.input)
    out_base = Path(args.output)
    expected_svg = out_base.with_suffix(".svg")

    info = {
        "ts": None,
        "input": str(inp),
        "output": str(out_base),
        "geometry": args.geometry,
        "points": args.points,
        "seed": args.seed,
        "rc": 0,
        "outputs": {
            "expected_svg": str(expected_svg),
            "svg_exists": False,
            "svg_path": None,
            "svg_size": 0,
            "svg_sha256": "",
            "svg_shapes": 0,
        },
        "plugin_exc": "",
        "forced_write": False,
        "forced_write_reason": "",
    }

    t0 = time()
    try:
        geom_mod = load_geometry(args.geometry)
    except Exception as e:
        info["rc"] = 1
        info["plugin_exc"] = f"ImportError: {e}"
        print(json.dumps(info, ensure_ascii=False))
        return

    try:
        ensure_dir(expected_svg)
    except Exception as e:
        info["rc"] = 1
        info["plugin_exc"] = f"DirError: {e}"
        print(json.dumps(info, ensure_ascii=False))
        return

    # Get canvas size and load input image
    canvas_size = None
    input_image = None
    try:
        from PIL import Image

        with Image.open(str(inp)) as img:
            canvas_size = img.size
            # Convert to RGB if needed and keep a copy for geometry plugins
            if img.mode != "RGB":
                input_image = img.convert("RGB")
            else:
                input_image = img.copy()
    except Exception:
        canvas_size = (1200, 800)
        input_image = None

    # Generate shapes using multiple candidate methods
    doc_or_shapes = None
    render_candidates = (
        "render",
        "generate",
        "render_shapes",
        "run",
        "build",
        "make",
        "create",
    )

    try:
        for cand in render_candidates:
            if hasattr(geom_mod, cand):
                try:
                    fn = getattr(geom_mod, cand)
                    sig = inspect.signature(fn)
                    kwargs = {}

                    # Add parameters that the function accepts
                    # FIXED: Check for total_points first, then points
                    if "total_points" in sig.parameters:
                        kwargs["total_points"] = args.points
                    elif "points" in sig.parameters:
                        kwargs["points"] = args.points

                    if "seed" in sig.parameters:
                        kwargs["seed"] = args.seed
                    if "cascade_stages" in sig.parameters:
                        kwargs["cascade_stages"] = args.cascade_stages
                    if "canvas_size" in sig.parameters:
                        kwargs["canvas_size"] = canvas_size
                    # FIXED: Pass input_image to geometry plugins
                    if "input_image" in sig.parameters:
                        kwargs["input_image"] = input_image

                    # Call with appropriate parameters
                    if cand == "render":
                        doc_or_shapes = fn(str(inp), **kwargs)
                    else:
                        doc_or_shapes = fn(**kwargs)
                    break
                except Exception:
                    continue
    except Exception:
        info["rc"] = 1
        info["plugin_exc"] = traceback.format_exc()
        print(json.dumps(info, ensure_ascii=False))
        return

    # Export SVG
    if args.export_svg:
        try:
            exported = False

            # Try plugin exporters first
            for export_name in ("export_svg", "save_svg", "write_svg"):
                if hasattr(geom_mod, export_name):
                    try:
                        getattr(geom_mod, export_name)(doc_or_shapes, str(expected_svg))
                        exported = True
                        break
                    except Exception:
                        continue

            # Try document object exporter
            if not exported and hasattr(doc_or_shapes, "write_svg"):
                try:
                    doc_or_shapes.write_svg(str(expected_svg))
                    exported = True
                except Exception:
                    pass

            # Fallback to svg_export module
            if not exported:
                try:
                    import svg_export

                    svg_content = svg_export.export_svg(
                        doc_or_shapes, width=canvas_size[0], height=canvas_size[1]
                    )
                    with open(str(expected_svg), "w", encoding="utf-8") as f:
                        f.write(svg_content)
                    exported = True
                except Exception as e:
                    info["rc"] = 1
                    info["plugin_exc"] = f"ExportError: {e}"
                    print(json.dumps(info, ensure_ascii=False))
                    return

            if not exported:
                info["rc"] = 1
                info["plugin_exc"] = "No working exporter found"
                print(json.dumps(info, ensure_ascii=False))
                return

        except Exception:
            info["rc"] = 1
            info["plugin_exc"] = traceback.format_exc()
            print(json.dumps(info, ensure_ascii=False))
            return

    # Verify file was written
    if expected_svg.exists():
        size = expected_svg.stat().st_size
        info["outputs"]["svg_exists"] = True
        info["outputs"]["svg_path"] = str(expected_svg)
        info["outputs"]["svg_size"] = size
        info["outputs"]["svg_sha256"] = sha256_file(expected_svg)
        try:
            from tools.svg_audit import count_shapes

            info["outputs"]["svg_shapes"] = int(count_shapes(expected_svg))
        except Exception:
            info["outputs"]["svg_shapes"] = 0
    else:
        folder = expected_svg.parent
        prefix = expected_svg.stem
        cand = sorted(p for p in folder.glob("*.svg") if p.stem.startswith(prefix))
        if cand:
            p = cand[0]
            size = p.stat().st_size
            info["outputs"]["svg_exists"] = True
            info["outputs"]["svg_path"] = str(p)
            info["outputs"]["svg_size"] = size
            info["outputs"]["svg_sha256"] = sha256_file(p)
        else:
            info["rc"] = info["rc"] or 2

    info["elapsed_s"] = round(time() - t0, 3)
    print(json.dumps(info, ensure_ascii=False))


def run_pipeline(
    input: str,
    output: str,
    geometry: str,
    points: int = 4000,
    seed: int = 42,
    export_svg: bool = True,
    cascade_stages: int = 3,
    enable_plugin_exec: bool = False,
    pipeline: str | None = None,
    quiet: bool = True,
):
    """Adapter-friendly pipeline used by tests and CLI callers."""
    from pathlib import Path
    import sys
    import os
    import importlib
    import inspect
    import traceback as _tb
    from time import time as _time

    root = Path(__file__).resolve().parent
    root_src = root / "src"
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root_src))
    os.environ["PYTHONPATH"] = os.pathsep.join(
        [str(root), str(root_src), os.environ.get("PYTHONPATH", "")]
    ).strip(os.pathsep)

    inp = Path(input)
    out_base = Path(output)
    expected_svg = out_base.with_suffix(".svg")

    _canvas_size = None
    _input_image = None
    try:
        from PIL import Image

        with Image.open(str(inp)) as _im:
            _canvas_size = _im.size
            # Convert to RGB if needed and keep a copy for geometry plugins
            if _im.mode != "RGB":
                _input_image = _im.convert("RGB")
            else:
                _input_image = _im.copy()
    except Exception:
        pass
    if _canvas_size is None:
        _canvas_size = (1200, 800)

    info = {
        "ts": None,
        "input": str(inp),
        "output": str(out_base),
        "geometry": geometry,
        "points": int(points),
        "seed": int(seed),
        "rc": 0,
        "outputs": {
            "expected_svg": str(expected_svg),
            "svg_exists": False,
            "svg_path": None,
            "svg_size": 0,
            "svg_sha256": "",
            "svg_shapes": 0,
        },
        "plugin_exc": "",
        "forced_write": False,
        "forced_write_reason": "",
    }

    def _call_with_best_effort(fn, *a, **k):
        sig = inspect.signature(fn)
        use = {}
        accepts_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )
        for key, val in dict(k).items():
            if key in sig.parameters or accepts_kwargs:
                use[key] = val
        return fn(*a, **use)

    def _get_attr(container, name):
        try:
            if container is None:
                return None
            if isinstance(container, dict):
                return container.get(name)
            if hasattr(container, name):
                return getattr(container, name)
        except Exception:
            return None

    t0 = _time()

    try:
        geom_mod = load_geometry(geometry)
    except Exception as e:
        info["rc"] = 1
        info["plugin_exc"] = f"ImportError: {e}"
        info["elapsed_s"] = round(_time() - t0, 3)
        return info

    reg = None
    try:
        if hasattr(geom_mod, "register"):
            reg = _call_with_best_effort(geom_mod.register, canvas_size=_canvas_size)
    except Exception:
        reg = None

    try:
        expected_svg.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        info["rc"] = 1
        info["plugin_exc"] = f"DirError: {e}"
        info["elapsed_s"] = round(_time() - t0, 3)
        return info

    doc_or_shapes = None
    render_candidates = (
        _get_attr(reg, "render")
        or _get_attr(reg, "generate")
        or _get_attr(reg, "render_shapes"),
        "render",
        "generate",
        "render_shapes",
        "run",
        "build",
        "make",
        "create",
    )
    try:
        for cand in render_candidates:
            if callable(cand):
                doc_or_shapes = _call_with_best_effort(
                    cand,
                    str(inp),
                    total_points=int(points),  # FIXED: Use total_points
                    points=int(points),  # Keep points for legacy compatibility
                    seed=int(seed),
                    cascade_stages=int(cascade_stages),
                    input=str(inp),
                    input_path=str(inp),
                    image=str(inp),
                    path=str(inp),
                    canvas_size=_canvas_size,
                    input_image=_input_image,  # FIXED: Pass input_image
                )
                break
            elif isinstance(cand, str) and hasattr(geom_mod, cand):
                doc_or_shapes = _call_with_best_effort(
                    getattr(geom_mod, cand),
                    total_points=int(points),  # FIXED: Use total_points
                    points=int(points),  # Keep points for legacy compatibility
                    seed=int(seed),
                    cascade_stages=int(cascade_stages),
                    canvas_size=_canvas_size,
                    input_image=_input_image,  # FIXED: Pass input_image
                )
                break
    except Exception:
        info["rc"] = 1
        info["plugin_exc"] = _tb.format_exc()

    def _write_svg_from(doc_or_shapes, out_path: Path):
        # 1) Try plugin exporters
        for container in (geom_mod, reg):
            for name in ("export_svg", "save_svg", "write_svg"):
                fn = _get_attr(container, name)
                if callable(fn):
                    try:
                        return fn(doc_or_shapes, str(out_path))
                    except Exception:
                        try:
                            return fn(str(inp), str(out_path))
                        except Exception:
                            try:
                                return _call_with_best_effort(
                                    fn,
                                    input=str(inp),
                                    output=str(out_path),
                                    canvas_size=_canvas_size,
                                    doc=doc_or_shapes,
                                    shapes=doc_or_shapes,
                                )
                            except Exception:
                                pass
        # 3) Fallback: repo svg_export helpers
        try:
            svg_export = importlib.import_module("svg_export")
            for name in ("export_svg", "write_svg", "save_svg"):
                if hasattr(svg_export, name):
                    fn = getattr(svg_export, name)
                    if name == "export_svg":
                        # Fix: export_svg expects (shapes, width, height) but we need to write to file
                        svg_content = fn(
                            doc_or_shapes, width=_canvas_size[0], height=_canvas_size[1]
                        )
                        with open(str(out_path), "w", encoding="utf-8") as f:
                            f.write(svg_content)
                        print(
                            f"SVG export success: wrote {len(doc_or_shapes)} shapes to {out_path}"
                        )
                        return True
                    else:
                        result = fn(doc_or_shapes, str(out_path))
                        print(
                            f"SVG export success: wrote {len(doc_or_shapes)} shapes to {out_path}"
                        )
                        return result
        except Exception as e:
            print(f"SVG export failed: {e}")
            pass
        raise RuntimeError(
            "No exporter found (plugin/register/export helpers unavailable)"
        )

    if export_svg and info["rc"] == 0:
        try:
            _write_svg_from(doc_or_shapes, expected_svg)
        except Exception:
            info["rc"] = 1
            info["plugin_exc"] = _tb.format_exc()

    if expected_svg.exists():
        size = expected_svg.stat().st_size
        info["outputs"]["svg_exists"] = True
        info["outputs"]["svg_path"] = str(expected_svg)
        info["outputs"]["svg_size"] = size
        try:
            from tools.svg_audit import count_shapes

            info["outputs"]["svg_shapes"] = int(count_shapes(expected_svg))
        except Exception:
            info["outputs"]["svg_shapes"] = 0
        try:
            from hashlib import sha256

            with open(expected_svg, "rb") as f:
                info["outputs"]["svg_sha256"] = sha256(f.read()).hexdigest()
        except Exception:
            pass
    else:
        info["rc"] = info["rc"] or 2

    info["elapsed_s"] = round(_time() - t0, 3)
    return info


def _write_svg_safe(path, svg_text):
    try:
        logging.info("Writing SVG -> %s", path)
        print(f"Writing SVG -> {path}", flush=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg_text)
    except Exception:
        traceback.print_exc()
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        print(f"Unexpected error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
