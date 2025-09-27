#!/usr/bin/env python
"""Debug script for the poisson_disk plugin."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=== POISSON DISK DEBUG ===")

try:
    # Import the plugin directly
    from geometry_plugins import poisson_disk

    # Test with small canvas
    canvas_size = (100, 100)
    test_points = 10

    # Generate shapes
    print(
        f"Generating {test_points} points on {canvas_size[0]}x{canvas_size[1]} canvas..."
    )
    shapes = poisson_disk.generate(canvas_size, total_points=test_points, seed=42)

    print(f"✅ Generated {len(shapes)} shapes")
    if shapes:
        print(f"First shape: {shapes[0]}")

    # Test SVG export
    import svg_export

    svg_content = svg_export.export_svg(
        shapes, width=canvas_size[0], height=canvas_size[1]
    )

    # Write to file for inspection
    test_svg = project_root / "output" / "poisson_disk_test.svg"
    with open(test_svg, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"✅ Wrote test SVG: {test_svg}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()

print("=== DEBUG COMPLETE ===")
