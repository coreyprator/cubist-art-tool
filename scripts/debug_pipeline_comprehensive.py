# Comprehensive pipeline debug - find the systemic failure
import sys
import os
from pathlib import Path

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=== COMPREHENSIVE PIPELINE DEBUG ===")

# Test both images
test_images = [
    "G:/My Drive/Code/Python/cubist_art/input/x_your_input_image.jpg",
    "G:/My Drive/Code/Python/cubist_art/input/reference_artwork.jpg",
]

# Import all geometry plugins
geometry_plugins = {}
try:
    import geometry_plugins.delaunay as delaunay
    import geometry_plugins.voronoi as voronoi
    import geometry_plugins.rectangles as rectangles
    import geometry_plugins.scatter_circles as scatter_circles
    import geometry_plugins.concentric_circles as concentric_circles
    import geometry_plugins.poisson_disk as poisson_disk

    geometry_plugins = {
        "delaunay": delaunay,
        "voronoi": voronoi,
        "rectangles": rectangles,
        "scatter_circles": scatter_circles,
        "concentric_circles": concentric_circles,
        "poisson_disk": poisson_disk,
    }
    print(f"✅ Loaded {len(geometry_plugins)} geometry plugins")
except Exception as e:
    print(f"❌ Failed to load geometry plugins: {e}")
    import traceback

    traceback.print_exc()


# Test image loading
def test_image_loading(image_path):
    print(f"\n=== IMAGE LOADING TEST: {Path(image_path).name} ===")

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return None

    try:
        from PIL import Image

        img = Image.open(image_path)
        print(f"✅ Image loaded: {img.size}, mode: {img.mode}")

        # Convert to RGB if needed
        if img.mode != "RGB":
            img = img.convert("RGB")
            print(f"✅ Converted to RGB: {img.mode}")

        # Test color sampling
        width, height = img.size
        colors = []
        for i in range(min(10, width)):
            for j in range(min(10, height)):
                pixel = img.getpixel((i * width // 10, j * height // 10))
                colors.append(pixel)

        print(f"✅ Sample colors: {colors[:5]}")

        # Check if image is mostly white/empty
        unique_colors = set(colors)
        if len(unique_colors) < 3:
            print(f"⚠️  WARNING: Very few unique colors ({len(unique_colors)})")
        else:
            print(f"✅ Good color diversity: {len(unique_colors)} unique colors")

        return img

    except Exception as e:
        print(f"❌ Image loading failed: {e}")
        import traceback

        traceback.print_exc()
        return None


# Test geometry plugin with detailed logging
def test_geometry_plugin(plugin_name, plugin_module, canvas_size, test_points=100):
    print(f"\n=== PLUGIN TEST: {plugin_name.upper()} ===")

    try:
        if hasattr(plugin_module, "generate"):
            print("✅ Has generate() function")

            # Test with small point count first
            shapes = plugin_module.generate(canvas_size, test_points, seed=42)

            print(f"📊 Results with {test_points} points:")
            print(f"  Generated shapes: {len(shapes) if shapes else 0}")

            if shapes:
                # Analyze shape structure
                shape_types = {}
                for shape in shapes[:3]:  # Sample first 3
                    shape_type = shape.get("type", "unknown")
                    shape_types[shape_type] = shape_types.get(shape_type, 0) + 1

                    print(f"  Sample shape: type={shape_type}")
                    if "points" in shape:
                        print(f"    Points: {len(shape['points'])}")
                        print(f"    Sample coords: {shape['points'][:2]}")
                    if "fill" in shape:
                        print(f"    Fill color: {shape['fill']}")
                        if shape["fill"] == (255, 255, 255) or shape["fill"] == (
                            0,
                            0,
                            0,
                        ):
                            print("    ⚠️  WARNING: Basic color (white/black)")
                    if "stroke" in shape:
                        print(f"    Stroke: {shape['stroke']}")

                print(f"  Shape types: {shape_types}")

                # Test scaling behavior
                larger_shapes = plugin_module.generate(
                    canvas_size, test_points * 10, seed=42
                )
                print(
                    f"  Scaling test ({test_points * 10} points): {len(larger_shapes) if larger_shapes else 0} shapes"
                )

                if larger_shapes and len(larger_shapes) <= len(shapes):
                    print("    ❌ SCALING BUG: More points = same/fewer shapes!")
                else:
                    print("    ✅ Scaling works correctly")

            else:
                print("  ❌ No shapes generated!")

        else:
            print("❌ No generate() function found")

    except Exception as e:
        print(f"❌ Plugin test failed: {e}")
        import traceback

        traceback.print_exc()


# Main test execution
def main():
    canvas_size = (3024, 4032)  # Your production canvas size

    # Test image loading for both images
    for image_path in test_images:
        test_image_loading(image_path)

    print(f"\n{'='*60}")
    print("GEOMETRY PLUGIN TESTING")
    print(f"{'='*60}")

    # Test each geometry plugin
    for plugin_name, plugin_module in geometry_plugins.items():
        test_geometry_plugin(plugin_name, plugin_module, canvas_size)

    print(f"\n{'='*60}")
    print("SYSTEMIC ISSUE ANALYSIS")
    print(f"{'='*60}")

    print("🔍 Looking for common failure patterns:")
    print("1. Image loading issues → All plugins get bad colors")
    print("2. Point generation issues → All plugins get few points")
    print("3. Canvas scaling issues → All plugins generate at wrong scale")
    print("4. Preprocessing pipeline issues → Shared code fails")

    print("\n💡 Next Steps:")
    print("1. Check if reference image works better")
    print("2. Test with smaller canvas sizes")
    print("3. Test individual plugins in isolation")
    print("4. Check for shared preprocessing code issues")


if __name__ == "__main__":
    main()
