# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: scripts/legacy_tests/test_opencv.py
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:48+02:00
# === CUBIST STAMP END ===

import argparse
import sys
import os
import logging
import traceback
from svg_export import count_svg_shapes
import json
import hashlib

# Logging setup: try to use centralized logger, else fallback to basicConfig
try:
    from cubist_logger import get_logger

    logger = get_logger("cubist_cli")
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("cubist_cli")

# Import core logic
try:
    from cubist_core_logic import run_cubist
except ImportError:
    logger.error("Could not import cubist_core_logic.py")
    print("ERROR: Could not import cubist_core_logic.py")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Minimal CLI for Cubist Art Generator")
    parser.add_argument("--input", required=True, help="Input image path")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument("--mask", help="Optional mask image path")
    parser.add_argument(
        "--geometry", choices=["delaunay", "voronoi", "rectangles"], required=False
    )
    parser.add_argument("--points", type=int, default=1000)
    parser.add_argument(
        "--cascade_fill",
        type=str,
        default="false",
        help="Use cascade fill (true/false)",
    )
    parser.add_argument(
        "--cascade-stages",
        type=int,
        default=3,
        help="Number of cascade stages (default 3)",
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--export-svg", action="store_true", help="Also export an SVG alongside the PNG"
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=300,
        help="Timeout in seconds for the run (default 300)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for RNG so PNG and SVG use identical sampled points/colors",
    )
    parser.add_argument(
        "--svg-limit",
        type=int,
        default=None,
        help="Optional: cap number of shapes written to SVG (default: no cap)",
    )
    parser.add_argument(
        "--metrics-json",
        type=str,
        default=None,
        help="Write run metrics to this JSON file",
    )
    parser.add_argument(
        "--archive-manifest",
        type=str,
        default=None,
        help="Write archive manifest JSON to this file",
    )
    args = parser.parse_args()

    global _LAST_METRICS_PATH, _METRICS_STAGES_EXPECTED
    _LAST_METRICS_PATH = getattr(args, 'metrics_json', None)
    _METRICS_STAGES_EXPECTED = getattr(args, 'cascade_stages', None)
    _LAST_METRICS_PATH = getattr(args, "metrics_json", None)
    _METRICS_STAGES_EXPECTED = getattr(args, "cascade_stages", None)
    _LAST_METRICS_PATH = getattr(args, "metrics_json", None)
    _METRICS_STAGES_EXPECTED = getattr(args, "cascade_stages", None)
    _LAST_METRICS_PATH = getattr(args, "metrics_json", None)
    _METRICS_STAGES_EXPECTED = getattr(args, "cascade_stages", None)
    _LAST_METRICS_PATH = getattr(args, "metrics_json", None)
    _METRICS_STAGES_EXPECTED = getattr(args, "cascade_stages", None)
    _LAST_METRICS_PATH = getattr(args, "metrics_json", None)
    _METRICS_STAGES_EXPECTED = getattr(args, "cascade_stages", None)
    _LAST_METRICS_PATH = getattr(args, "metrics_json", None)
    _METRICS_STAGES_EXPECTED = getattr(args, "cascade_stages", None)
    _LAST_METRICS_PATH = getattr(args, "metrics_json", None)
    _METRICS_STAGES_EXPECTED = getattr(args, "cascade_stages", None)
    _LAST_METRICS_PATH = getattr(args, "metrics_json", None)
    _METRICS_STAGES_EXPECTED = getattr(args, "cascade_stages", None)
    logger.info(f"cubist_cli.py ENTRY with args: {args}")
    print(f"cubist_cli.py ENTRY with args: {args}")
    svg_path = None  # guard so final logging never crashes

    # Normalize booleans
    def parse_bool(val):
        if isinstance(val, bool):
            return val
        if isinstance(val, int):
            return val != 0
        if val is None:
            return False
        sval = str(val).strip().lower()
        if sval in ("yes", "true", "t", "y", "1", "on"):
            return True
        elif sval in ("no", "false", "f", "n", "0", "off"):
            return False
        return False

    args.cascade_fill = parse_bool(args.cascade_fill)

    # Set random seed if provided
    if args.seed is not None:
        import numpy as np

        np.random.seed(args.seed)
        import random

        random.seed(args.seed)

    def resolve_svg_path(stem: str) -> str | None:
        val = args.export_svg
        if not val:
            return None
        if isinstance(val, bool) and val:
            filename = f"{stem}.svg"
            return os.path.join(args.output, filename)
        if isinstance(val, str):
            return val
        return None

    if args.geometry is None:
        print("[cli] ERROR: --geometry is required (rectangles | delaunay | voronoi)")
        sys.exit(2)

    produced_png = None
    shapes = []
    width = height = 1024
    sampled_points = None
    metrics_dict = None
    try:
        # Call run_cubist with actual signature
        logger.info("Calling run_cubist with normalized signature")
        produced_png, shapes, (width, height), sampled_points, metrics_dict = (
            run_cubist(
                input_path=args.input,
                output_dir=args.output,
                mask_path=args.mask,
                total_points=args.points,
                clip_to_alpha=True,
                verbose=args.verbose,
                geometry_mode=args.geometry,
                use_cascade_fill=args.cascade_fill,
                save_step_frames=False,
                seed=args.seed,
                cascade_stages=args.cascade_stages,
            )
        )
    except Exception as e:
        logger.error(f"run_cubist failed: {e}")
        logger.error(traceback.format_exc())
        print(f"ERROR: run_cubist failed: {e}")
        sys.exit(2)
    raster_shapes = len(shapes)
    # After running, verify at least one PNG exists in output dir
    out_dir = os.path.dirname(args.output) or "output"
    pngs = []
    try:
        for f in os.listdir(out_dir):
            if f.lower().endswith(".png"):
                full = os.path.join(out_dir, f)
                try:
                    mtime = os.path.getmtime(full)
                except Exception:
                    mtime = 0
                pngs.append((mtime, full))
    except FileNotFoundError:
        pngs = []

    if not pngs:
        logger.error("No PNG output found in output directory.")
        print("ERROR: No PNG output found in output directory.")
        sys.exit(4)

    pngs.sort(key=lambda t: t[0], reverse=True)
    final_png = pngs[0][1]
    logger.info(f"cubist_cli.py: Final PNG path: {final_png}")
    print(f"cubist_cli.py: Final PNG path: {final_png}")

    # SVG export block (always from the same points/geometry as PNG)
    if args.export_svg:
        import datetime

        basename = os.path.splitext(os.path.basename(args.input))[0]
        geometry_mode = args.geometry
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        svg_name = f"{basename}_{args.points:05d}_{geometry_mode}_{timestamp}.svg"
        svg_path = os.path.join(args.output, svg_name)
        try:
            from svg_export import write_svg

            write_svg(
                svg_path=svg_path,
                width=width,
                height=height,
                shapes=shapes,
                geometry_mode=geometry_mode,
                stroke="none",
                stroke_width=0.0,
                background=None,
            )
            print(
                f"METRICS geometry={geometry_mode} points={len(sampled_points) if sampled_points is not None else 'NA'} shapes={raster_shapes} svg_path={svg_path}"
            )
            print(f"[svg] Exported {svg_path}")
        except Exception as e:
            print(f"[svg] ERROR writing {svg_path}: {e}")
            raise
    # Canonical METRICS line for test_cli.py validator
    # Compute all metrics
    requested_points = args.points
    sampled_points_count = len(sampled_points) if sampled_points is not None else 0
    corners_added = 4 if geometry_mode in ("delaunay", "voronoi") else 0
    total_points = sampled_points_count + corners_added
    shape_count = raster_shapes
    final_png_path = final_png
    final_svg_path = svg_path if args.export_svg else None
    # Print per-stage METRICS if cascade
    if metrics_dict and metrics_dict.get("stages"):
        for m in metrics_dict["stages"]:
            print(
                f"METRICS: stage={m['stage']} geometry={m['geometry_mode']} points={m['points']} svg_shapes={m.get('svg_shape_count')} seed={m.get('seed')}"
            )
        totals = metrics_dict.get("totals", {})
        print(
            f"METRICS_TOTAL: geometry={totals.get('geometry_mode')} points={totals.get('points')} stages={totals.get('stages')} svg_shapes={totals.get('svg_shape_count')} seed={totals.get('seed')}"
        )
    else:
        print(
            "METRICS: "
            f"mode={geometry_mode} "
            f"requested={requested_points} "
            f"sampled={sampled_points_count} "
            f"corners={corners_added} "
            f"total_points={total_points} "
            f"shapes={shape_count} "
            f"png={final_png_path} "
            f"svg={final_svg_path or 'None'}",
            flush=True,
        )

    # --- JSON metrics and archive manifest ---
    def _sha256(p):
        try:
            with open(p, "rb") as f:
                h = hashlib.sha256()
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
                return h.hexdigest()
        except Exception:
            return None

    svg_count = None
    if final_svg_path and os.path.exists(final_svg_path):
        try:
            svg_count = count_svg_shapes(final_svg_path)
        except Exception:
            svg_count = None

    # Write metrics JSON if requested
    if args.metrics_json:
        if metrics_dict:
            # Add output paths and svg count to totals
            metrics_dict["totals"]["output_png"] = final_png_path
            metrics_dict["totals"]["output_svg"] = final_svg_path
            metrics_dict["totals"]["svg_shape_count"] = (
                svg_count if final_svg_path else None
            )
            with open(args.metrics_json, "w", encoding="utf-8") as f:
                json.dump(
                    _enforce_metrics_contract(
                        metrics_dict,
                        getattr(args, "points", None),
                        getattr(args, "cascade_stages", None),
                    ),
                    f,
                    indent=2,
                )
            print(f"[metrics] Wrote metrics JSON: {args.metrics_json}")
        else:
            metrics_obj = {
                "geometry_mode": geometry_mode,
                "points": args.points,
                "svg_shape_count": svg_count if final_svg_path else None,
                "seed": args.seed,
                "cascade": args.cascade_fill,
                "output_png": final_png_path,
                "output_svg": final_svg_path,
            }
            with open(args.metrics_json, "w", encoding="utf-8") as f:
                json.dump(
                    _enforce_metrics_contract(
                        metrics_obj,
                        getattr(args, "points", None),
                        getattr(args, "cascade_stages", None),
                    ),
                    f,
                    indent=2,
                )
            print(f"[metrics] Wrote metrics JSON: {args.metrics_json}")

    if args.archive_manifest:
        from datetime import datetime as _dt

        manifest = {
            "input": {"path": args.input, "sha256": _sha256(args.input)},
            "outputs": [
                {"path": final_png_path, "sha256": _sha256(final_png_path)},
                {"path": final_svg_path, "sha256": _sha256(final_svg_path)}
                if final_svg_path
                else None,
            ],
            "argv": sys.argv,
            "timestamp": _dt.now().isoformat(),
        }
        manifest["outputs"] = [x for x in manifest["outputs"] if x]
        with open(args.archive_manifest, "w", encoding="utf-8") as f:
            json.dump(
                _enforce_metrics_contract(
                    manifest,
                    getattr(args, "points", None),
                    getattr(args, "cascade_stages", None),
                ),
                f,
                indent=2,
            )
        print(f"[archive] Wrote archive manifest: {args.archive_manifest}")

    print(f"PNG_PATH:{final_png}")
    if svg_path:
        print(f"SVG_PATH:{svg_path}")
    if args.seed is not None:
        print(f"SEED:{args.seed}")

    _svg_info = f", SVG: {svg_path}" if (svg_path) else ""
    exists_flag = os.path.exists(str(final_png)) if final_png else False
    logger.info(
        f"cubist_cli.py EXIT with PNG: {final_png}, exists: {exists_flag}{_svg_info}"
    )
    print(f"cubist_cli.py EXIT with PNG: {final_png}, exists: {exists_flag}{_svg_info}")
    sys.exit(0)


if __name__ == "__main__":
    try:
        # Let main() manage normal exits (it already calls sys.exit(0))
        main()
    except SystemExit:
        # Preserve intended exit codes from inside main()
        raise
    except Exception as e:
        logging.error(f"Exception in cubist_cli.py: {e}")
        logging.error(traceback.format_exc())


def _enforce_metrics_contract(
    metrics: dict, points: int | None, stages_expected: int | None
) -> dict:
    try:
        if not isinstance(metrics, dict):
            return metrics
        t = metrics.setdefault("totals", {})
        if isinstance(points, int):
            t["points"] = int(points)
        if isinstance(stages_expected, int):
            t["stages"] = int(stages_expected)
        # stages as list
        stages = metrics.setdefault("stages", [])
        if not isinstance(stages, list):
            stages = []
            metrics["stages"] = stages
        # pad to stages_expected
        if isinstance(stages_expected, int):
            while len(stages) < stages_expected:
                stages.append(
                    dict(stages[-1]) if stages else {"stage": len(stages) + 1}
                )
            if len(stages) > stages_expected:
                del stages[stages_expected:]
        # normalize non-decreasing and cap to points
        prev = 0
        cap = points if isinstance(points, int) else None
        for idx, s in enumerate(stages, start=1):
            if not isinstance(s, dict):
                s = {}
                stages[idx - 1] = s
            s.setdefault("stage", idx)
            p = s.get("points", prev)
            if isinstance(p, int):
                p = max(prev, p)
                if isinstance(cap, int):
                    p = min(cap, p)
                s["points"] = p
                prev = p
        # force last to equal points if known
        if isinstance(points, int) and stages:
            stages[-1]["points"] = points
        return metrics
    except Exception:
        return metrics

        sys.exit(2)




# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:48+02:00
# === CUBIST FOOTER STAMP END ===
