# cubist_art v2.3.7 — tests: voronoi plugin
# File: tests/test_voronoi_plugin.py

import pathlib

import geometry_registry

def test_voronoi_plugin_discovery(tmp_path):
    plugin_dir = pathlib.Path(__file__).parent.parent / "geometry_plugins"
    geometry_registry.load_plugins(str(plugin_dir))
    fn = geometry_registry.get_geometry("voronoi")
    assert callable(fn)
    a = fn((100, 80), total_points=12, seed=123)
    b = fn((100, 80), total_points=12, seed=123)
    assert a == b  # determinism
    assert isinstance(a, list) and len(a) > 0
