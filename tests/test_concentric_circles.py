# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tests/test_concentric_circles.py
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:32+02:00
# === CUBIST STAMP END ===

# === FILE: tests/test_concentric_circles.py ===
# === UPDATED: 2025-08-22T18:00:00Z ===
import sys
import tempfile
import pathlib

def test_concentric_circles_plugin_discovery(tmp_path):
    import geometry_registry
    plugin_dir = pathlib.Path(__file__).parent.parent / "geometry_plugins"
    geometry_registry.load_plugins(str(plugin_dir))
    fn = geometry_registry.get_geometry("concentric_circles")
    assert callable(fn)
    circles1 = fn((100, 100), total_points=8, seed=42)
    circles2 = fn((100, 100), total_points=8, seed=42)
    assert circles1 == circles2
    assert all(isinstance(c, tuple) and len(c) == 3 for c in circles1)
    assert all(c[2] > 0 for c in circles1)
    assert "concentric_circles" in geometry_registry._registry

# === EOF tests/test_concentric_circles.py @ 2025-08-22T18:00:00Z ===


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:32+02:00
# === CUBIST FOOTER STAMP END ===
