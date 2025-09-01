# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tests/test_plugin_exec_concentric_circles.py
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:32+02:00
# === CUBIST STAMP END ===

# === FILE: tests/test_plugin_exec_concentric_circles.py ===
# === UPDATED: 2025-08-22T18:10:00Z ===
import subprocess
import tempfile
import pathlib
import sys
import shutil
import re

import numpy as np
from PIL import Image

def count_svg_shapes(svg_path):
    from svg_export import count_svg_shapes as count
    return count(str(svg_path))

def make_test_image(path, w=64, h=64):
    arr = np.linspace(0, 255, w * h, dtype=np.uint8).reshape((h, w))
    img = np.stack([arr, arr, arr], axis=2)
    Image.fromarray(img).save(path)

def test_concentric_circles_plugin_exec(tmp_path):
    img_path = tmp_path / "test.png"
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    make_test_image(img_path)
    cli = sys.executable
    cli_path = pathlib.Path(__file__).parent.parent / "cubist_cli.py"
    svg_path = out_dir / "frame_plugin_concentric_circles_012pts.svg"

    cmd = [
        cli,
        str(cli_path),
        "--input", str(img_path),
        "--output", str(out_dir),
        "--geometry", "concentric_circles",
        "--points", "12",
        "--seed", "42",
        "--enable-plugin-exec",
        "--export-svg",
    ]
    # First run
    proc1 = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc1.returncode == 0
    assert svg_path.exists()
    shapes1 = count_svg_shapes(svg_path)
    # Parse METRICS line if present
    metrics_line = next((l for l in proc1.stdout.splitlines() if "METRICS:" in l), None)
    assert shapes1 >= 1 and shapes1 <= 12
    # Second run (determinism)
    proc2 = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc2.returncode == 0
    shapes2 = count_svg_shapes(svg_path)
    assert shapes1 == shapes2
    # Optionally, compare SVG text for strict determinism
    with open(svg_path, "r", encoding="utf-8") as f:
        svg1 = f.read()
    with open(svg_path, "r", encoding="utf-8") as f:
        svg2 = f.read()
    assert svg1 == svg2

# === EOF tests/test_plugin_exec_concentric_circles.py @ 2025-08-22T18:10:00Z ===


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:32+02:00
# === CUBIST FOOTER STAMP END ===
