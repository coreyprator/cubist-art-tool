# cubist_art v2.3.7 — tests: rectangles plugin
# File: tests/test_rectangles_plugin.py

import pathlib

import geometry_registry

def test_rectangles_plugin_discovery(tmp_path):
    plugin_dir = pathlib.Path(__file__).parent.parent / "geometry_plugins"
    geometry_registry.load_plugins(str(plugin_dir))
    fn = geometry_registry.get_geometry("rectangles")
    assert callable(fn)
    a = fn((128, 96), total_points=32, seed=99)
    b = fn((128, 96), total_points=32, seed=99)
    assert a == b
    assert isinstance(a, list) and len(a) >= 4  # at least a few rectangles
