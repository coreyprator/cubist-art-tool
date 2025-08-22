# ======================================================================
# File: tests/test_cascade_metrics_smoke.py
# Stamp: 2025-08-22T13:51:03Z
# (Auto-added header for paste verification)
# ======================================================================

# ======================================================================
# File: tests/test_cascade_metrics_smoke.py
# Stamp: 2025-08-22T00:00:00Z
#
# Purpose:
#   Smoke-test determinism and the metrics contract for cascade runs.
#   The authoritative stage count is len(j["stages"]). If the producer
#   also includes totals["stages"], it must match that value.
# ======================================================================

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


def run_cmd(args: list[str]) -> subprocess.CompletedProcess:
    """Run a subprocess and assert it succeeds, returning the process."""
    proc = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    assert (
        proc.returncode == 0
    ), f"CLI failed with exit {proc.returncode}:\n{proc.stdout}"
    return proc


def make_img(p: Path) -> None:
    """Create a small test image at path p."""
    img = Image.new("RGB", (64, 64), (128, 128, 128))
    img.save(p)


def test_cascade_determinism_and_metrics() -> None:
    """Two identical runs should produce identical metrics and expected totals."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        in_png = td_path / "in.png"
        make_img(in_png)

        out_svg1 = td_path / "out1.svg"
        out_svg2 = td_path / "out2.svg"
        m1 = td_path / "m1.json"
        m2 = td_path / "m2.json"

        # Invoke the canonical CLI at repo root (not a test copy).
        cli = sys.executable
        cli_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "cubist_cli.py")
        )
        assert os.path.exists(cli_path), f"Expected CLI at {cli_path}"

        cmd_base = [
            cli,
            cli_path,
            "--input",
            str(in_png),
            "--points",
            "50",
            "--geometry",
            "delaunay",
            "--export-svg",
            "--metrics-json",
            str(m1),
            "--cascade-stages",
            "3",
            "--seed",
            "123",
            "--output",
            str(out_svg1),
        ]

        # First run
        run_cmd(cmd_base)

        # Second run with new metrics/output paths
        cmd_run2 = cmd_base.copy()
        cmd_run2[cmd_run2.index(str(m1))] = str(m2)
        cmd_run2[cmd_run2.index(str(out_svg1))] = str(out_svg2)
        run_cmd(cmd_run2)

        j1 = json.loads(Path(m1).read_text(encoding="utf-8"))
        j2 = json.loads(Path(m2).read_text(encoding="utf-8"))

        # Deterministic across identical runs
        assert j1 == j2

        # Contract checks
        assert j1["totals"]["points"] == 50

        stages = j1["stages"]
        stage_count = len(stages)  # Authoritative
        # If mirrored in totals, it must match
        if "stages" in j1.get("totals", {}):
            assert j1["totals"]["stages"] == stage_count
        # For this scenario we expect exactly 3
        assert stage_count == 3

        # Non-decreasing point allocation across stages
        assert [s["points"] for s in stages] == sorted([s["points"] for s in stages])
        assert stages[-1]["points"] == 50

        # If SVG shape count is tracked, ensure we produced something
        if stages[-1].get("svg_shape_count") is not None:
            assert stages[-1]["svg_shape_count"] > 0

        # A different seed should change metrics
        m3 = td_path / "m3.json"
        cmd3 = cmd_base.copy()
        # swap metrics path and output
        mj_i = cmd3.index("--metrics-json") + 1
        cmd3[mj_i] = str(m3)
        out_svg3 = td_path / "out3.svg"
        out_i = cmd3.index("--output") + 1
        cmd3[out_i] = str(out_svg3)
        # change seed
        seed_i = cmd3.index("--seed") + 1
        cmd3[seed_i] = "456"

        run_cmd(cmd3)
        j3 = json.loads(Path(m3).read_text(encoding="utf-8"))
        assert j3 != j1

# ======================================================================
# End of File: tests/test_cascade_metrics_smoke.py  (2025-08-22T00:00:00Z)
# ======================================================================

# ======================================================================
# End of File: tests/test_cascade_metrics_smoke.py  (2025-08-22T13:51:03Z)
# ======================================================================
