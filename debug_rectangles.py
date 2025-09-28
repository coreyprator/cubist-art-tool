# debug_rectangles.py - Check which rectangles plugin is being used
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("=== Debugging Rectangles Plugin ===")

# Test 1: Check if cascade_fill_system imports
print("\n1. Testing cascade_fill_system import:")
try:
    from cascade_fill_system import apply_universal_cascade_fill, sample_image_color
    print("✅ cascade_fill_system imported successfully")
except ImportError as e:
    print(f"❌ cascade_fill_system import failed: {e}")

# Test 2: Check rectangles plugin import and inspect
print("\n2. Testing rectangles plugin import:")
try:
    import geometry_plugins.rectangles as rect_plugin
    print("✅ rectangles plugin imported successfully")

    # Check if it has the new cascade parameters
    import inspect
    sig = inspect.signature(rect_plugin.generate)
    params = list(sig.parameters.keys())
    print(f"Parameters: {params}")

    if "cascade_fill_enabled" in params:
        print("✅ Enhanced rectangles.py with cascade support detected")
    else:
        print("❌ Old rectangles.py without cascade support - NEEDS REPLACEMENT")

    # Check if verbose parameter exists
    if "verbose" in params:
        print("✅ Verbose parameter present")
    else:
        print("❌ Verbose parameter missing")

except ImportError as e:
    print(f"❌ rectangles plugin import failed: {e}")

# Test 3: Test a minimal call to see what happens
print("\n3. Testing minimal rectangles call:")
try:
    canvas_size = (800, 600)

    # Test with cascade enabled
    print("Testing with cascade_fill_enabled=True...")
    shapes = rect_plugin.generate(
        canvas_size=canvas_size,
        total_points=100,
        seed=42,
        cascade_fill_enabled=True,
        verbose=True
    )
    print(f"✅ Generated {len(shapes)} shapes with cascade enabled")

    # Test with cascade disabled
    print("Testing with cascade_fill_enabled=False...")
    shapes2 = rect_plugin.generate(
        canvas_size=canvas_size,
        total_points=100,
        seed=42,
        cascade_fill_enabled=False,
        verbose=True
    )
    print(f"✅ Generated {len(shapes2)} shapes with cascade disabled")

    if len(shapes) != len(shapes2):
        print(f"✅ DIFFERENCE DETECTED: Cascade={len(shapes)} vs Default={len(shapes2)}")
    else:
        print(f"❌ NO DIFFERENCE: Both generated {len(shapes)} shapes")

except Exception as e:
    print(f"❌ Test call failed: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Debug Complete ===")
