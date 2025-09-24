# cubist_art v2.3.7 — tests: delaunay plugin
# File: tests/test_delaunay_plugin.py

import pathlib

import geometry_registry

def test_delaunay_plugin_discovery(tmp_path):
    plugin_dir = pathlib.Path(__file__).parent.parent / "geometry_plugins"
    geometry_registry.load_plugins(str(plugin_dir))
    fn = geometry_registry.get_geometry("delaunay")
    assert callable(fn)
    a = fn((120, 90), total_points=40, seed=7)
    b = fn((120, 90), total_points=40, seed=7)
    assert a == b
    assert isinstance(a, list) and len(a) > 0
