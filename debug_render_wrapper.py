# debug_render_wrapper.py - Test the render wrapper function specifically
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("=== Debugging Render Wrapper Function ===")

try:
    import geometry_plugins.rectangles as rect_plugin

    # Test 1: Call render function like CLI does
    print("\n1. Testing render() function with cascade enabled:")

    input_path = "input/x_your_input_image.jpg"

    kwargs = {
        "total_points": 500,
        "seed": 42,
        "cascade_fill_enabled": True,
        "cascade_intensity": 0.8,
        "verbose": True
    }

    print(f"Calling render('{input_path}', **{kwargs})")

    try:
        result = rect_plugin.render(input_path, **kwargs)
        print(f"✅ render() succeeded: {len(result)} shapes")

        # Check first shape to see if it looks correct
        if result:
            first_shape = result[0]
            print(f"First shape: {first_shape}")

    except Exception as e:
        print(f"❌ render() failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Call render with cascade disabled
    print("\n2. Testing render() function with cascade disabled:")

    kwargs_disabled = {
        "total_points": 500,
        "seed": 42,
        "cascade_fill_enabled": False,
        "verbose": True
    }

    try:
        result2 = rect_plugin.render(input_path, **kwargs_disabled)
        print(f"✅ render() succeeded: {len(result2)} shapes")

    except Exception as e:
        print(f"❌ render() failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Compare render vs generate directly
    print("\n3. Comparing render() vs generate() calls:")

    try:
        # Direct generate call
        from PIL import Image
        with Image.open(input_path) as img:
            canvas_size = img.size
            if img.mode != "RGB":
                input_image = img.convert("RGB")
            else:
                input_image = img.copy()

        direct_result = rect_plugin.generate(
            canvas_size=canvas_size,
            input_image=input_image,
            total_points=500,
            seed=42,
            cascade_fill_enabled=True,
            verbose=True
        )

        print(f"Direct generate(): {len(direct_result)} shapes")
        print(f"Render wrapper: {len(result) if 'result' in locals() else 'failed'} shapes")

        if 'result' in locals() and len(result) != len(direct_result):
            print(f"❌ MISMATCH: render={len(result)} vs generate={len(direct_result)}")
        elif 'result' in locals():
            print(f"✅ MATCH: Both functions returned {len(result)} shapes")

    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"❌ Failed to import rectangles plugin: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Debug Complete ===")
