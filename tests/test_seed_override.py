# cubist_art v2.3.7 — tests: seed_points override
# File: tests/test_seed_override.py

import pathlib
import geometry_registry

def test_seed_points_override_determinism(tmp_path):
    plugin_dir = pathlib.Path(__file__).parent.parent / "geometry_plugins"
    geometry_registry.load_plugins(str(plugin_dir))
    seed_points = [(10.0, 10.0), (50.0, 20.0), (80.0, 70.0), (30.0, 60.0)]
    # Voronoi
    vor_fn = geometry_registry.get_geometry("voronoi")
    a1 = vor_fn((100, 100), total_points=4, seed=123, seed_points=seed_points)
    a2 = vor_fn((100, 100), total_points=4, seed=123, seed_points=seed_points)
    assert a1 == a2
    # Delaunay
    del_fn = geometry_registry.get_geometry("delaunay")
    b1 = del_fn((100, 100), total_points=4, seed=123, seed_points=seed_points)
    b2 = del_fn((100, 100), total_points=4, seed=123, seed_points=seed_points)
    assert b1 == b2
    # Changing seed_points changes output
    seed_points2 = [(11.0, 10.0), (50.0, 20.0), (80.0, 70.0), (30.0, 60.0)]
    a3 = vor_fn((100, 100), total_points=4, seed=123, seed_points=seed_points2)
    b3 = del_fn((100, 100), total_points=4, seed=123, seed_points=seed_points2)
    assert a1 != a3
    assert b1 != b3
