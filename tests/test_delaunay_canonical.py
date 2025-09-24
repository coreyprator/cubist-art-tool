# cubist_art v2.3.7 — tests: delaunay canonical ordering
# File: tests/test_delaunay_canonical.py

import pathlib
import geometry_registry

def test_delaunay_canonical_ordering(tmp_path):
    plugin_dir = pathlib.Path(__file__).parent.parent / "geometry_plugins"
    geometry_registry.load_plugins(str(plugin_dir))
    del_fn = geometry_registry.get_geometry("delaunay")
    # Same seed, should be identical order
    a = del_fn((100, 100), total_points=10, seed=42)
    b = del_fn((100, 100), total_points=10, seed=42)
    assert a == b
    # Using seed_points, order should also be canonical
    seed_points = [(10.0, 10.0), (50.0, 20.0), (80.0, 70.0), (30.0, 60.0), (60.0, 80.0)]
    c = del_fn((100, 100), total_points=5, seed=123, seed_points=seed_points)
    d = del_fn((100, 100), total_points=5, seed=123, seed_points=seed_points)
    assert c == d
