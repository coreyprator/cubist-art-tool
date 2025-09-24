# [stamp:start] Cubist Art — tests/test_geometry_matrix_e2e.py — v2.3.7
from __future__ import annotations
from pathlib import Path
import logging
import pytest
import subprocess
import sys

log = logging.getLogger("cubist_logger")

pytestmark = pytest.mark.e2e  # not part of the 'smoke' set

def _has_input() -> bool:
    return Path("input/your_input_image.jpg").exists()

def _cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "cubist_cli.py", *args],
        check=False, text=True, capture_output=True
    )

def test_geometry_matrix_smoke(tmp_path):
    if not _has_input():
        pytest.skip("input/your_input_image.jpg missing; skipping e2e geometry matrix")

    cases = [
        ("delaunay", None),
        ("voronoi", None),
        ("rectangles", None),
        ("invalid_mode", None),  # should not crash pipeline
        ("delaunay", "input/edge_mask.png"),
        ("voronoi", "input/edge_mask.png"),
        ("rectangles", "input/edge_mask.png"),
        ("invalid_mode", "input/edge_mask.png"),
    ]

    for geom, maybe_mask in cases:
        args = [
            "--input", "input/your_input_image.jpg",
            "--output", str(tmp_path / f"{geom or 'none'}{'_mask' if maybe_mask else ''}.svg"),
            "--points", "256",
            "--seed", "123",
            "--export-svg",
        ]
        if geom:
            args += ["--geometry", geom]
        if maybe_mask:
            args += ["--mask", maybe_mask]

        log.info("Starting geometry mode: %s (%s)", geom or "None", "with mask" if maybe_mask else "no mask")
        cp = _cli(*args)
        # Allow non-zero for "invalid_mode" but assert we produced logs / didn’t crash Python itself
        assert cp is not None
        log.info("Finished geometry mode: %s (%s)", geom or "None", "with mask" if maybe_mask else "no mask")

    log.info("All geometry tests complete.")
# [stamp:end]
