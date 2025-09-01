# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tests/test_geometry_plugins.py
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:47+02:00
# === CUBIST STAMP END ===

# =============================================================================
# tests/test_geometry_plugins.py
# v2.3 — plugin registry discovery and determinism smoke tests
# =============================================================================

from __future__ import annotations

import pathlib
import types
import pytest

import geometry_registry

# Repo-relative plugins directory
PLUGINS_DIR = pathlib.Path(__file__).parent.parent / "geometry_plugins"


def test_discovery_repo_relative():
    """Registry should discover plugins from the repo-relative folder."""
    geometry_registry.load_plugins(str(PLUGINS_DIR))
    names = set(getattr(geometry_registry, "names", lambda: [])())
    # We ship at least one example; allow either to pass the gate.
    assert any(n in names for n in {"toy_triangles", "concentric_circles"}), names


@pytest.mark.parametrize("name", ["toy_triangles", "concentric_circles"])
def test_registered_callable_if_present(name: str):
    """If a known example plugin is present, it must resolve to a callable."""
    geometry_registry.load_plugins(str(PLUGINS_DIR))
    fn = geometry_registry.get_geometry(name)
    if fn is None:
        pytest.skip(f"plugin '{name}' not present in this build")
    assert isinstance(fn, types.FunctionType) or callable(fn)


@pytest.mark.parametrize("name", ["toy_triangles", "concentric_circles"])
def test_determinism_if_present(name: str):
    """Plugins must be deterministic for the same (shape, total_points, seed)."""
    geometry_registry.load_plugins(str(PLUGINS_DIR))
    fn = geometry_registry.get_geometry(name)
    if fn is None:
        pytest.skip(f"plugin '{name}' not present in this build")
    shape = (64, 96, 3)
    a = fn(shape, total_points=9, seed=42)
    b = fn(shape, total_points=9, seed=42)
    assert a == b, f"non-deterministic output for {name}"


def test_discovery_idempotent():
    """Calling load_plugins multiple times should not duplicate or mutate entries."""
    geometry_registry.load_plugins(str(PLUGINS_DIR))
    names1 = set(getattr(geometry_registry, "names", lambda: [])())
    # Re-load; should be safe and idempotent
    geometry_registry.load_plugins(str(PLUGINS_DIR))
    names2 = set(getattr(geometry_registry, "names", lambda: [])())
    assert names1 == names2




# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:47+02:00
# === CUBIST FOOTER STAMP END ===
