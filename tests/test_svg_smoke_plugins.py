# [stamp:start] Cubist Art — tests/test_svg_smoke_plugins.py — v2.3.7
# Auto-discovered SVG smoke test: one SVG per registered plugin.
# Deterministic seed; graceful skips; marked as 'smoke'.
# [stamp:end]

from __future__ import annotations

from pathlib import Path
import pytest

# Allow selective execution: pytest -m smoke
pytestmark = pytest.mark.smoke


def _discover_plugin_names() -> list[str]:
    """
    Try registry-provided listing first; if unavailable, scan geometry_plugins/
    and keep only names that are actually registered.
    """
    try:
        import geometry_registry  # type: ignore
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"geometry_registry unavailable: {exc}")
        return []

    plugin_dir = Path(__file__).resolve().parents[1] / "geometry_plugins"
    try:
        geometry_registry.load_plugins(str(plugin_dir))
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"failed loading plugins: {exc}")
        return []

    # Preferred: use registry listing if exposed
    names: list[str] | None = None
    try:
        names = list(geometry_registry.list_geometries())  # type: ignore[attr-defined]
    except Exception:
        names = None

    if not names:
        # Fallback: scan directory and filter to actually registered names
        candidates = sorted(p.stem for p in plugin_dir.glob("*.py") if p.name != "__init__.py")
        names = []
        for name in candidates:
            try:
                geometry_registry.get_geometry(name)
            except KeyError:
                continue
            else:
                names.append(name)

    return sorted(set(names))


PLUGIN_NAMES = _discover_plugin_names()


@pytest.fixture(scope="module")
def _svg_export():
    try:
        import svg_export  # type: ignore
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"svg_export unavailable: {exc}")
    return svg_export


@pytest.mark.parametrize("geometry_name", PLUGIN_NAMES)
def test_svg_smoke_per_plugin(_svg_export, tmp_path: Path, geometry_name: str):
    """
    For each discovered plugin:
      1) Generate a tiny shape set with a fixed seed.
      2) Write an SVG via svg_export.write_svg.
      3) Assert the file exists and contains an <svg> element and at least one common shape tag.
    """
    import geometry_registry  # type: ignore

    generate = geometry_registry.get_geometry(geometry_name)

    canvas_size = (256, 192)
    shapes = generate(canvas_size=canvas_size, total_points=64, seed=123)
    assert isinstance(shapes, list), f"{geometry_name}: shapes must be a list"
    assert len(shapes) > 0, f"{geometry_name}: shapes list is empty"

    out_svg = tmp_path / f"smoke_{geometry_name}.svg"
    _svg_export.write_svg(shapes, str(out_svg))

    assert out_svg.exists(), f"{geometry_name}: SVG not created"
    txt = out_svg.read_text(encoding="utf-8", errors="ignore").lower()
    assert "<svg" in txt, f"{geometry_name}: output does not contain <svg>"
    assert any(tag in txt for tag in ("<polygon", "<path", "<circle", "<rect")), f"{geometry_name}: no common shape tags found"
