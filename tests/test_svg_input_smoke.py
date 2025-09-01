# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tests/test_svg_input_smoke.py
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:47+02:00
# === CUBIST STAMP END ===

# ======================================================================
# File: test_svg_input_smoke.py
# Stamp: 2025-08-22T17:31:37Z
# (Auto-added header for paste verification)
# ======================================================================
import tempfile
import sys
import subprocess
from pathlib import Path


def test_svg_input_minimal_triangle():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
      <polygon points="10,90 50,10 90,90" fill="#ff0000"/>
    </svg>
    """
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        svg_path = td / "tri.svg"
        out_dir = td / "out"
        out_dir.mkdir()
        metrics_json = out_dir / "metrics.json"
        svg_path.write_text(svg, encoding="utf-8")
        cmd = [
            sys.executable,
            "cubist_cli.py",
            "--input-svg",
            str(svg_path),
            "--geometry",
            "svg",
            "--output",
            str(out_dir),
            "--export-svg",
            "--metrics-json",
            str(metrics_json),
        ]
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        assert proc.returncode == 0, f"CLI failed:\n{proc.stdout}"
        assert (out_dir / "metrics.json").exists()
        # Optionally: check that output SVG exists and is not empty
        svg_outs = list(out_dir.glob("*.svg"))
        assert svg_outs, "No SVG output found"
        assert svg_outs[0].stat().st_size > 100, "SVG output too small"
# ======================================================================
# End of File: test_svg_input_smoke.py  (2025-08-22T17:31:37Z)
# ======================================================================




# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:47+02:00
# === CUBIST FOOTER STAMP END ===
