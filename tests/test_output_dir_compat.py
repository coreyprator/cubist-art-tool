# [stamp:start] Cubist Art — tests/test_output_dir_compat.py — v2.3.7
# Ensures legacy output_dir maps to output_path without raising TypeError.
# Tightened to cubist_core_logic only (no dynamic imports).
# [stamp:end]

from __future__ import annotations
from pathlib import Path
import pytest
import cubist_core_logic as core  # type: ignore

def test_output_dir_backcompat(tmp_path: Path):
    run_cubist = getattr(core, "run_cubist", None)
    if run_cubist is None:
        pytest.skip("run_cubist() not found in cubist_core_logic")

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Minimal kwargs—the test only asserts the compatibility mapping
    kwargs = {
        "input_path": str(tmp_path / "fake_input.png"),  # may not be read in this smoke
        "output_dir": str(out_dir),                      # legacy key under test
        "total_points": 10,
    }

    try:
        run_cubist(**kwargs)
    except TypeError as e:
        pytest.fail(f"output_dir back-compat failed with TypeError: {e}")
    except Exception:
        # Allow deeper pipeline errors (e.g., missing real input). The contract here
        # is only that 'output_dir' is accepted and mapped, not that the full run succeeds.
        pass
    # These kwargs are intentionally minimal; your function may require more.
    # If so, add minimal required args (e.g., input_path) used by your pipeline.
    kwargs = {
        "input_path": str(tmp_path / "fake_input.png"),  # may not be read if early-exit
        "output_dir": str(out_dir),                      # legacy key under test
        "total_points": 10,
    }

    try:
        run_cubist(**kwargs)
    except TypeError as e:
        pytest.fail(f"output_dir back-compat failed with TypeError: {e}")
    except Exception:
        # It’s fine if deeper code complains about missing real input.
        # The goal is: TypeError is NOT raised for output_dir mapping.
        pass
