# Debug the delaunay scaling bug
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import geometry_plugins.delaunay as d
import inspect

print("=== Delaunay Scaling Bug Analysis ===")

# Get the complete source code
try:
    full_source = inspect.getsource(d.generate)
    print("=== Complete delaunay.generate() source ===")
    print(full_source)
    print("\n" + "=" * 60)

    # Test scaling behavior with verbose output
    canvas_size = (3024, 4032)

    print("\n=== Detailed Scaling Test ===")
    for points in [10, 50, 200, 1000, 4000]:
        print(f"\n--- Testing {points} points ---")
        try:
            shapes = d.generate(canvas_size, points, seed=42)

            if shapes:
                # Collect all coordinates
                all_x, all_y = [], []
                for shape in shapes:
                    if "points" in shape:
                        for point in shape["points"]:
                            all_x.append(point[0])
                            all_y.append(point[1])

                if all_x and all_y:
                    x_min, x_max = min(all_x), max(all_x)
                    y_min, y_max = min(all_y), max(all_y)
                    x_span = x_max - x_min
                    y_span = y_max - y_min

                    print(f"  Shapes generated: {len(shapes)}")
                    print(f"  Total coordinates: {len(all_x)}")
                    print(f"  X range: {x_min:.1f} - {x_max:.1f} (span: {x_span:.1f})")
                    print(f"  Y range: {y_min:.1f} - {y_max:.1f} (span: {y_span:.1f})")
                    print(
                        f"  Coverage: X={x_span/3024*100:.1f}%, Y={y_span/4032*100:.1f}%"
                    )

                    # Show sample coordinates for debugging
                    print(
                        f"  Sample coords: {[(round(x,1), round(y,1)) for x,y in zip(all_x[:3], all_y[:3])]}"
                    )

                    # Identify the problem pattern
                    if x_span < 500:
                        print("  ❌ PROBLEM: Very narrow X coverage!")
                    elif x_span < 1500:
                        print("  ⚠️  WARNING: Limited X coverage")
                    else:
                        print("  ✅ OK: Reasonable X coverage")

                else:
                    print("  ❌ No coordinates found in shapes")
            else:
                print("  ❌ No shapes generated")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback

            traceback.print_exc()

except Exception as e:
    print(f"Failed to get source or run tests: {e}")
    import traceback

    traceback.print_exc()

print("\n=== Bug Pattern Analysis ===")
print("If X coverage decreases as point count increases:")
print("1. There may be a parameter mixup in the random generation")
print("2. A fallback algorithm might activate for high point counts")
print("3. Random seed behavior might change with iteration count")
print("4. Memory/performance limits might force a simpler algorithm")
