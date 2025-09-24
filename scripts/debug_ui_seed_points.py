# Debug the seed_points being passed from UI to delaunay
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=== UI → Delaunay Data Flow Debug ===")

# We need to intercept the actual call from UI to delaunay.generate()
# Let's monkey patch the delaunay.generate function to log what's passed to it

import geometry_plugins.delaunay as d

# Store original function
original_generate = d.generate


def debug_generate(*args, **kwargs):
    print("\n🔍 INTERCEPTED delaunay.generate() call:")
    print(f"  args: {args}")
    print(f"  kwargs keys: {list(kwargs.keys())}")

    if "seed_points" in kwargs:
        seed_points = kwargs["seed_points"]
        print(f"  seed_points provided: {seed_points is not None}")
        if seed_points:
            print(f"  seed_points count: {len(seed_points)}")
            if len(seed_points) > 0:
                print(f"  seed_points sample: {seed_points[:5]}")
                # Analyze the clustering
                if len(seed_points) > 2:
                    xs = [pt[0] for pt in seed_points]
                    ys = [pt[1] for pt in seed_points]
                    x_min, x_max = min(xs), max(xs)
                    y_min, y_max = min(ys), max(ys)
                    x_span, y_span = x_max - x_min, y_max - y_min
                    print("  📊 SEED ANALYSIS:")
                    print(
                        f"    X range: {x_min:.1f} - {x_max:.1f} (span: {x_span:.1f})"
                    )
                    print(
                        f"    Y range: {y_min:.1f} - {y_max:.1f} (span: {y_span:.1f})"
                    )

                    if x_span < 500:
                        print("    ❌ FOUND THE BUG: Narrow X seed_points!")
                    elif x_span < 1500:
                        print("    ⚠️  WARNING: Limited X seed_points")
                    else:
                        print("    ✅ OK: Reasonable X seed_points spread")
    else:
        print("  seed_points: Not provided")

    if "total_points" in kwargs:
        print(f"  total_points: {kwargs['total_points']}")

    print(f"  canvas_size: {args[0] if args else 'Not provided'}")

    # Call original function
    result = original_generate(*args, **kwargs)
    print(f"  → Generated {len(result)} shapes")
    return result


# Patch the function
d.generate = debug_generate

print("\n✅ Delaunay debug patch applied!")
print("\n🎯 Next Steps:")
print("1. Run your UI/GUI application")
print("2. Generate art from your sculpture image")
print("3. Watch console output for intercepted calls")
print("4. The bug will be visible in the seed_points analysis")

print("\n💡 Expected Discovery:")
print("- UI passes clustered seed_points with narrow X range")
print("- total_points=4000 gets ignored")
print("- This causes narrow triangulation patterns")

# Keep the patch active
input("\nPress Enter after testing with UI to restore original function...")

# Restore original
d.generate = original_generate
print("✅ Original delaunay.generate() restored")
