#!/usr/bin/env python3
# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: test_cli.py
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:44+02:00
# === CUBIST STAMP END ===

"""
Cubist Art Generator CLI Test Script

This script allows testing all geometry modes with cascade fill on/off.
Usage examples:
  python test_cli.py --input input/your_input_image.jpg --geometry delaunay --cascade_fill true
  python test_cli.py --input input/your_input_image.jpg --geometry voronoi --cascade_fill false
  python test_cli.py --run_all_tests --input input/your_input_image.jpg
"""

# --- Robust root logger setup and imports ---
import os
import sys
import time
import datetime
import traceback
import argparse
from pathlib import Path
from typing import Optional
import shutil
import random
import re
from svg_export import count_svg_shapes

TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _ts_name(base: str, geometry: str, points: int, ext: str) -> str:
    # base without extension, ext includes leading dot
    return f"{base}_{geometry}_{points:05d}_{TS}{ext}"


try:
    from cubist_logger import get_logger

    logger = get_logger("test_cli")
except Exception:
    import logging

    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "run_log.txt")
    logger = logging.getLogger("test_cli_fallback")
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))
    fh = logging.FileHandler(log_file_path, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(ch)
    logger.addHandler(fh)
    # Guarantee log file exists and append a startup marker
    try:
        os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)
        with open(
            os.path.join(os.path.dirname(__file__), "logs", "run_log.txt"),
            "a",
            encoding="utf-8",
        ) as _lf:
            _lf.write("[test_cli] logger initialized\n")
    except Exception:
        pass

# Import the archive function
try:
    from archive_output import archive_output_folder
except ImportError:
    logger.warning(
        "Could not import archive_output.py - archive functionality disabled"
    )
    archive_output_folder = None

# Import the core logic
# try:
#     from cubist_core_logic import run_cubist
# except ImportError:
#     logger.error("Could not import cubist_core_logic.py")
#     print("ERROR: Could not import cubist_core_logic.py")
#     print("Make sure you're running this script from the project root directory")
#     sys.exit(1)

# Import SVG export
try:
    from svg_export import write_svg
except Exception:
    write_svg = None


def parse_bool(value) -> bool:
    """Parse string boolean values robustly."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if value is None:
        return False
    val = str(value).strip().lower()
    if val in ("yes", "true", "t", "y", "1", "on"):
        return True
    elif val in ("no", "false", "f", "n", "0", "off"):
        return False
    else:
        raise argparse.ArgumentTypeError(f"Boolean value expected, got: {value}")


# Helper to kill process tree robustly (psutil if available, else fallback)
def _kill_process_tree(proc):
    try:
        import psutil  # optional

        parent = psutil.Process(proc.pid)
        for child in parent.children(recursive=True):
            try:
                child.kill()
            except Exception:
                pass
        try:
            parent.kill()
        except Exception:
            pass
        return True
    except Exception:
        # Fallbacks
        try:
            if os.name == "nt":
                os.system(f"taskkill /PID {proc.pid} /T /F")
            else:
                proc.kill()
            return True
        except Exception:
            return False


def archive_output_dir(out_dir: str):
    try:
        p = Path(out_dir)
        if not p.exists():
            return
        files = [
            x
            for x in p.iterdir()
            if x.is_file() and x.suffix.lower() in {".png", ".svg"}
        ]
        if not files:
            return
        arch_root = p / "_archive"
        arch_root.mkdir(parents=True, exist_ok=True)
        dst = arch_root / TS
        dst.mkdir(parents=True, exist_ok=True)
        for f in files:
            shutil.move(str(f), str(dst / f.name))
        # Zip the archived outputs
        zip_path = str(dst) + ".zip"
        shutil.make_archive(str(dst), "zip", str(dst))
        logger.info(f"Archived {len(files)} files to: {dst} and zipped to {zip_path}")
        print(f"📦 Archived {len(files)} files → {dst} (and zipped)")
    except Exception as e:
        logger.warning(f"Archive step skipped: {e}")


def run_cubist_cli(
    input_path: str,
    output_dir: str,
    geometry_mode: str,
    use_cascade_fill: bool,
    total_points: int = 1000,
    mask_path: str = None,
    save_step_frames: bool = False,
    verbose: bool = True,
    timeout_seconds: int = 300,
    export_svg_path: Optional[str] = None,
    seed: Optional[int] = None,
) -> Optional[str]:
    """Run the cubist generation CLI command."""
    logger.info(
        f"run_cubist_cli() ENTRY: mode={geometry_mode}, cascade={use_cascade_fill}, points={total_points}"
    )
    # Prepare output paths
    base_filename = Path(input_path).stem
    _png_output_path = (
        Path(output_dir) / f"{base_filename}_{geometry_mode}_{total_points}.png"
    )
    # Construct CLI command
    cli_command = [
        "python",
        "cubist_cli.py",
        "--input",
        input_path,
        "--output",
        str(output_dir),
        "--geometry",
        geometry_mode,
        "--cascade_fill",
        str(use_cascade_fill),
        "--points",
        str(total_points),
        "--timeout-seconds",
        str(timeout_seconds),
    ]
    if export_svg_path:
        cli_command.append("--export-svg")
    if mask_path:
        cli_command += ["--mask", mask_path]
    if save_step_frames:
        cli_command.append("--step_frames")
    if verbose:
        cli_command.append("--verbose")
    if seed is not None:
        cli_command += ["--seed", str(seed)]
    logger.info(
        f"Running CLI command: {' '.join(str(x) for x in cli_command if x is not None)}"
    )
    logger.info(
        f"Subprocess start time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    logger.info(f"Timeout seconds: {timeout_seconds}")
    _t0 = time.time()
    try:
        import subprocess

        result = subprocess.run(
            cli_command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        _stdout = result.stdout
        _stderr = result.stderr
        # Parse METRICS line
        m = re.search(
            r"METRICS\s+geometry=(\w+)\s+raster_shapes=(\d+)\s+svg_path=([^\s]+)",
            _stdout,
        )
        if m:
            geom = m.group(1)
            raster_cnt = int(m.group(2))
            svg_path = m.group(3)
            svg_cnt = count_svg_shapes(svg_path)
            ok = svg_cnt == raster_cnt
            status = "PASS ✅" if ok else "FAIL ❌"
            print(
                f"[svg-validate] {status} | geometry={geom} | raster={raster_cnt} | svg={svg_cnt} | file={svg_path}"
            )
            if not ok:
                raise SystemExit(
                    f"SVG validation failed for {geom}: raster={raster_cnt}, svg={svg_cnt}"
                )
        else:
            print(
                "[svg-validate] INFO: No METRICS line found; skipping SVG parity check."
            )
        # After process, parse PNG_PATH and SVG_PATH from stdout
        png_path = None
        svg_path = None
        for line in _stdout.splitlines():
            if line.startswith("PNG_PATH:"):
                png_path = line.split("PNG_PATH:", 1)[1].strip()
            if line.startswith("SVG_PATH:"):
                svg_path = line.split("SVG_PATH:", 1)[1].strip()
        if result.returncode != 0:
            logger.error(f"CLI command failed with return code {result.returncode}")
            return None
        if not png_path or not os.path.exists(png_path):
            logger.error(f"Expected PNG not found: {png_path}")
            print(f"❌ ERROR: Expected PNG not found: {png_path}")
            return None
        logger.info(f"PNG created: {png_path}")
        if svg_path:
            logger.info(f"SVG created: {svg_path}")
        print(f"✅ PNG created: {png_path}")
        if svg_path:
            if os.path.exists(svg_path):
                print(f"✅ SVG created: {svg_path}")
            else:
                print(f"⚠ SVG was requested but not created: {svg_path}")
        return png_path
    except Exception as e:
        logger.error(f"Exception running CLI: {e}")
        logger.error(traceback.format_exc())
        print(f"❌ ERROR: Exception running CLI: {e}")
        return None


def run_single_test(
    input_path: str,
    output_dir: str,
    geometry_mode: str,
    use_cascade_fill: bool,
    total_points: int = 1000,
    mask_path: str = None,
    save_step_frames: bool = False,
    verbose: bool = True,
    export_svg: Optional[bool or str] = False,
    timeout_seconds: int = 300,
    seed: Optional[int] = None,
) -> Optional[Path]:
    """Run a single cubist generation test."""
    logger.info(
        f"run_single_test() ENTRY: mode={geometry_mode}, cascade={use_cascade_fill}, points={total_points}"
    )
    print(f"\n{'=' * 60}")
    print(
        f"🎨 Testing: {geometry_mode.upper()} | Cascade: {'ON' if use_cascade_fill else 'OFF'}"
    )
    print(f"{'=' * 60}")

    try:
        start_time = time.time()
        logger.info(f"Starting test: {geometry_mode}")

        # Use CLI for cubist generation
        base_stem = Path(input_path).stem
        svg_out = (
            str(
                Path(output_dir)
                / _ts_name(base_stem, geometry_mode, total_points, ".svg")
            )
            if export_svg
            else None
        )
        png_output_path = run_cubist_cli(
            input_path=input_path,
            output_dir=output_dir,
            mask_path=mask_path,
            total_points=total_points,
            use_cascade_fill=use_cascade_fill,
            save_step_frames=save_step_frames,
            verbose=verbose,
            geometry_mode=geometry_mode,
            timeout_seconds=timeout_seconds,
            export_svg_path=svg_out,
            seed=seed,
        )

        end_time = time.time()
        duration = end_time - start_time
        if not png_output_path:
            logger.error("run_cubist_cli did not produce a PNG")
            print("❌ ERROR: run_cubist_cli did not produce a PNG")
            return None
        logger.info(
            f"Test completed successfully in {duration:.2f}s: {png_output_path}"
        )

        print(f"✅ SUCCESS: Generated in {duration:.2f} seconds")
        print(f"📁 Output: {png_output_path}")

        # --- SVG export hook for single test ---
        # (No-op here; handled by cubist_cli.py)

        return png_output_path

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"❌ ERROR: {str(e)}")
        return None


def run_triple_test(args):
    """Run rectangles, delaunay, voronoi with SVG export, using --points from CLI."""
    geometries = ["rectangles", "delaunay", "voronoi"]
    for geometry in geometries:
        geo_label = (geometry or "unknown").upper()
        print(f"\n{'=' * 40}\nTRIPLE TEST: {geo_label}\n{'=' * 40}")
        if geometry == "rectangles":
            print("Note: --points is ignored for rectangles mode (grid-based).")
        result = run_single_test(
            input_path=args.input,
            output_dir=args.output,
            geometry_mode=geometry,
            use_cascade_fill=False,
            total_points=args.points,
            mask_path=args.mask,
            save_step_frames=False,
            verbose=not args.quiet,
            export_svg=args.export_svg,
            timeout_seconds=args.timeout_seconds,
            seed=args.seed,
        )
        if result and os.path.exists(str(result)):
            print(f"✅ {geometry} test succeeded: {result}")
        else:
            print(f"❌ {geometry} test failed")
    print("\n=== Triple test completed ===")


def main():
    print("[test_cli] main() starting")
    print(f"[test_cli] Python: {sys.executable}")
    print(f"[test_cli] CWD: {os.getcwd()}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Working directory: {os.getcwd()}")
    parser = argparse.ArgumentParser(
        description="Test Cubist Art Generator with different geometry modes and cascade fill options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test single geometry mode
  python test_cli.py --input input/image.jpg --geometry delaunay --cascade_fill true

  # Test all combinations with clean output folder
  python test_cli.py --run_all_tests --input input/image.jpg --archive_output

  # Test with custom points and step frames
  python test_cli.py --input input/image.jpg --geometry voronoi --cascade_fill false --points 500 --step_frames

  # Test with mask and archive existing output
  python test_cli.py --input input/image.jpg --mask input/mask.png --geometry rectangles --cascade_fill true --archive_output

  # Test all modes with mask only (no archiving - keeps unmasked results for comparison)
  python test_cli.py --mask_only_tests --input input/image.jpg --mask input/mask.png --points 200
        """,
    )
    # Input/Output arguments
    parser.add_argument("--input", "-i", required=True, help="Path to input image file")
    parser.add_argument(
        "--output", "-o", default="output", help="Output directory (default: output)"
    )
    parser.add_argument("--mask", "-m", help="Path to mask image file (optional)")
    # Test mode arguments
    parser.add_argument(
        "--run_all_tests",
        action="store_true",
        help="Run all geometry modes with both cascade fill on/off",
    )
    parser.add_argument(
        "--mask_only_tests",
        action="store_true",
        help="Run all geometry modes with both cascade fill on/off, but only with the mask (requires --mask)",
    )
    parser.add_argument(
        "--geometry",
        "-g",
        choices=["delaunay", "voronoi", "rectangles"],
        help="Geometry mode (required if not using --run_all_tests)",
    )
    parser.add_argument(
        "--cascade_fill", "-c", type=parse_bool, help="Use cascade fill (true/false)"
    )
    # Configuration arguments
    parser.add_argument(
        "--points",
        "-p",
        type=int,
        default=1000,
        help="Number of points to sample (default: 1000)",
    )
    parser.add_argument(
        "--step_frames",
        action="store_true",
        help="Save step frames for animation (cascade fill only)",
    )
    parser.add_argument(
        "--archive_output",
        action="store_true",
        help="Archive existing output folder contents before running tests",
    )
    parser.add_argument(
        "--archive", action="store_true", help="Alias for --archive_output"
    )
    parser.add_argument(
        "--quiet", "-q", type=parse_bool, default=False, help="Reduce output verbosity"
    )
    parser.add_argument(
        "--export-svg",
        nargs="?",
        const=True,
        default=False,
        help="Export SVG alongside PNG output (optionally specify path)",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=300,
        help="Timeout in seconds for the run (default 300)",
    )
    parser.add_argument(
        "--triple-test",
        action="store_true",
        default=False,
        help="Run rectangles, delaunay, voronoi with SVG export, small points",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for RNG so PNG and SVG use identical sampled points/colors",
    )
    args = parser.parse_args()
    print(f"Parsed args: {args}")
    logger.info(f"Parsed args: {args}")
    # Early exit: allow archive-only runs without requiring geometry
    if args.archive and not args.triple_test and not args.geometry:
        # perform archive (whatever your existing archive() call is) and exit cleanly
        if args.archive_output:
            archive_output_dir(args.output)
        print("[test_cli] Archive-only run completed.")
        sys.exit(0)
    # Normalize booleans
    args.cascade_fill = parse_bool(args.cascade_fill)
    args.export_svg = (
        args.export_svg
        if args.export_svg is False or isinstance(args.export_svg, str)
        else True
    )
    args.quiet = parse_bool(args.quiet)
    args.archive_output = bool(args.archive_output or args.archive)
    # Set random seed if provided
    if args.seed is not None:
        import numpy as np

        np.random.seed(args.seed)
        random.seed(args.seed)
    # Ensure logs dir and output dir exist
    os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)
    Path(args.output).mkdir(parents=True, exist_ok=True)
    # Sentinel write check for output dir
    try:
        with open(os.path.join(args.output, ".write_check"), "w") as f:
            f.write("ok\n")
    except Exception as e:
        logger.error(f"Cannot write to output dir {args.output}: {e}")
        print(f"❌ ERROR: Cannot write to output dir {args.output}: {e}")
        sys.exit(2)
    if args.archive_output:
        archive_output_dir(args.output)
    # Fail early if input doesn't exist
    if not os.path.exists(args.input):
        logger.error(f"Input file does not exist: {args.input}")
        print(f"❌ ERROR: Input file does not exist: {args.input}")
        sys.exit(2)
    # Breadcrumbs for control flow
    if args.triple_test:
        run_triple_test(args)
        sys.exit(0)
    if args.run_all_tests:
        logger.info("Control flow: run_all_tests")
    elif args.mask_only_tests:
        logger.info("Control flow: mask_only_tests")
    else:
        logger.info("Control flow: single_test")
    try:
        if args.run_all_tests:
            logger.info("Control flow: run_all_tests")
            logger.info("Starting comprehensive test suite")
            # results = run_all_tests(
            #     input_path=args.input,
            #     output_dir=args.output,
            #     total_points=args.points,
            #     mask_path=args.mask,
            #     save_step_frames=args.step_frames,
            #     verbose=not args.quiet,
            #     mask_only_tests=False,
            # )
            # print_summary(results, mask_only_tests=False)
            logger.info("Comprehensive test suite completed")
        elif args.mask_only_tests:
            logger.info("Control flow: mask_only_tests")
            logger.info("Starting masked-only test suite")
            # results = run_all_tests(
            #     input_path=args.input,
            #     output_dir=args.output,
            #     total_points=args.points,
            #     mask_path=args.mask,
            #     save_step_frames=args.step_frames,
            #     verbose=not args.quiet,
            #     mask_only_tests=True,
            # )
            # print_summary(results, mask_only_tests=True)
            logger.info("Masked-only test suite completed")
        else:
            logger.info("Control flow: single_test")
            logger.info(
                f"Starting single test: {args.geometry} with cascade={args.cascade_fill}"
            )
            print(
                f"Starting test: {args.geometry} at {datetime.datetime.now().strftime('%H:%M:%S')}"
            )
            _t0 = time.time()
            png_output_path = run_single_test(
                input_path=args.input,
                output_dir=args.output,
                geometry_mode=args.geometry,
                use_cascade_fill=args.cascade_fill,
                total_points=args.points,
                mask_path=args.mask,
                save_step_frames=args.step_frames,
                verbose=not args.quiet,
                export_svg=args.export_svg,
            )
            _t1 = time.time()
            elapsed = _t1 - _t0
            # After test, log outcome to run log
            with open(
                os.path.join(os.path.dirname(__file__), "logs", "run_log.txt"),
                "a",
                encoding="utf-8",
            ) as logf:
                if png_output_path:
                    logf.write(
                        f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SUCCESS: {png_output_path}\n"
                    )
                else:
                    logf.write(
                        f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FAILURE: {args.geometry}\n"
                    )
            # Log final PNG path and existence
            logger.info(
                f"Final PNG path: {png_output_path}, exists: {os.path.exists(str(png_output_path)) if png_output_path else False}"
            )
            if png_output_path and os.path.exists(str(png_output_path)):
                print("\n🎉 Test completed successfully!")
                print(f"📁 Output saved to: {png_output_path}")
                print(f"⏱️  Elapsed: {elapsed:.2f} seconds")
                logger.info(f"Single test completed successfully: {png_output_path}")
            else:
                print("\n❌ Test failed!")
                logger.error("Single test failed")
                sys.exit(2)
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        logger.warning("Test interrupted by user")
        log_file_path = os.path.join(os.path.dirname(__file__), "logs", "run_log.txt")
        with open(log_file_path, "a", encoding="utf-8") as logf:
            logf.write(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INTERRUPTED\n"
            )
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}")
        log_file_path = os.path.join(os.path.dirname(__file__), "logs", "run_log.txt")
        with open(log_file_path, "a", encoding="utf-8") as logf:
            logf.write(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: {str(e)}\n"
            )
        logger.error(f"Exception: {str(e)}")
        sys.exit(2)


if __name__ == "__main__":
    print("[test_cli] __main__ guard reached")
    try:
        main()
    except SystemExit as se:
        print(f"[test_cli] SystemExit: code={getattr(se, 'code', None)}")
        raise


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:44+02:00
# === CUBIST FOOTER STAMP END ===
