# cubist_art v2.3.7 — tests: poisson-disk plugin
# File: tests/test_poisson_disk_plugin.py

import pathlib

import geometry_registry

def test_poisson_disk_plugin_discovery(tmp_path):
    plugin_dir = pathlib.Path(__file__).parent.parent / "geometry_plugins"
    geometry_registry.load_plugins(str(plugin_dir))
    fn = geometry_registry.get_geometry("poisson_disk")
    assert callable(fn)
    a = fn((160, 120), total_points=100, seed=1234)
    b = fn((160, 120), total_points=100, seed=1234)
    c = fn((160, 120), total_points=100, seed=4321)
    assert a == b
    assert a != c
    assert isinstance(a, list) and len(a) > 0
