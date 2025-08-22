import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from svg_export import write_svg


def test_svg_export_basic(tmp_path):
    # Write a basic SVG with Delaunay geometry
    svg_path = tmp_path / "basic.svg"
    shapes = [((0, 0), (1, 0), (0, 1))]
    metadata = {"geometry": "delaunay", "cascade": "test", "points": "3"}
    write_svg(
        shapes=shapes,
        filename=str(svg_path),
        geometry="delaunay",
        layer_name="Layer1",
        metadata=metadata,
        stroke="black",
        fill_mode="none",
        use_mask=False,
    )
    assert svg_path.exists()
    content = svg_path.read_text()
    # Should contain geometry placeholder
    assert "delaunay" in content
    assert "<polygon" in content


def test_svg_export_with_mask(tmp_path):
    # Write SVG with mask placeholder
    svg_path = tmp_path / "mask.svg"
    shapes = [((0, 0), (1, 0), (0, 1))]
    metadata = {"geometry": "voronoi", "cascade": "test", "points": "3"}
    write_svg(
        shapes=shapes,
        filename=str(svg_path),
        geometry="voronoi",
        layer_name="Layer2",
        metadata=metadata,
        stroke="black",
        fill_mode="none",
        use_mask=True,
    )
    content = svg_path.read_text()
    # Should contain mask placeholder
    assert "<mask" in content or "MASK_PLACEHOLDER" in content
