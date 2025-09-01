# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tests/test_scatter_circles.py
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:24:01+02:00
# === CUBIST STAMP END ===

# =============================================================================
# Cubist Art Tool — Scatter Circles Plugin Tests
# File: tests/test_scatter_circles.py
# Version: v2.3
# Date: 2025-08-25
# =============================================================================

import pathlib, sys
from pathlib import Path

def test_scatter_circles_plugin_discovery(tmp_path):
    import geometry_registry
    plugin_dir = pathlib.Path(__file__).parent.parent / "geometry_plugins"
    geometry_registry.load_plugins(str(plugin_dir))
    fn = geometry_registry.get_geometry("scatter_circles")
    assert callable(fn)
    out1 = fn((100, 100), total_points=25, seed=123)
    out2 = fn((100, 100), total_points=25, seed=123)
    out3 = fn((100, 100), total_points=25, seed=124)
    assert out1 == out2
    assert out1 != out3
    assert len(out1) == 25
    # bounds + positive radius
    for (cx, cy, r) in out1:
        assert 0 <= cx < 100
        assert 0 <= cy < 100
        assert r >= 1

def test_scatter_circles_plugin_exec(tmp_path):
    # full CLI run; requires plugin exec enabled
    import subprocess, sys, os
    from PIL import Image

    # make a tiny input image
    img_path = tmp_path / "in.png"
    Image.new("RGB", (120, 80), (90, 110, 130)).save(img_path)

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    cli = sys.executable
    cli_path = pathlib.Path(__file__).parent.parent / "cubist_cli.py"
    svg_path = out_dir / "frame_plugin_scatter_circles_025pts.svg"

    cmd = [
        cli, str(cli_path),
        "--input", str(img_path),
        "--output", str(out_dir),
        "--geometry", "scatter_circles",
        "--points", "25",
        "--seed", "7",
        "--enable-plugin-exec",
        "--export-svg",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.returncode == 0, proc.stdout
    # Should have produced both PNG and SVG
    png = list(out_dir.glob("*.png"))
    svg = list(out_dir.glob("*.svg"))
    assert len(png) == 1
    assert len(svg) == 1



# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:24:01+02:00
# === CUBIST FOOTER STAMP END ===
