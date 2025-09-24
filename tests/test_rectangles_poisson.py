# [stamp:start] Cubist Art — tests/test_rectangles_poisson.py — v2.3.7
from __future__ import annotations
import pathlib, geometry_registry
import pytest
pytestmark = pytest.mark.smoke

def test_rectangles_poisson_deterministic():
    plugin_dir = pathlib.Path(__file__).parent.parent / "geometry_plugins"
    geometry_registry.load_plugins(str(plugin_dir))
    gen = geometry_registry.get_geometry("rectangles")
    a = gen((240, 180), total_points=49, seed=123, seed_mode="poisson", poisson_min_px=22.0)
    b = gen((240, 180), total_points=49, seed=123, seed_mode="poisson", poisson_min_px=22.0)
    assert a == b
    # should look less grid-like: varied widths/heights
    xs = sorted({p[0] for sh in a for p in sh["points"]})
    ys = sorted({p[1] for sh in a for p in sh["points"]})
    assert len(xs) > 4 and len(ys) > 4
