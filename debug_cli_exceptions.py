# debug_cli_exceptions.py - Find where CLI exceptions are swallowed
import sys
import inspect
import traceback
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("=== Debugging CLI Exception Handling ===")

def debug_cli_geometry_call():
    """Simulate exactly what CLI does to call geometry"""

    # Step 1: Load geometry module like CLI
    try:
        from cubist_cli import load_geometry
        geom_mod = load_geometry("rectangles")
        print(f"✅ Loaded geometry module: {geom_mod}")
    except Exception as e:
        print(f"❌ Failed to load geometry: {e}")
        return

    # Step 2: Prepare inputs like CLI
    inp = Path("input/x_your_input_image.jpg")

    # Get canvas size and input image like CLI
    canvas_size = None
    input_image = None
    try:
        from PIL import Image
        with Image.open(str(inp)) as img:
            canvas_size = img.size
            if img.mode != "RGB":
                input_image = img.convert("RGB")
            else:
                input_image = img.copy()
        print(f"✅ Loaded input image: {canvas_size}")
    except Exception as e:
        print(f"❌ Failed to load input image: {e}")
        canvas_size = (1200, 800)
        input_image = None

    # Step 3: Parse parameters like CLI
    from cubist_cli import parse_params
    params = parse_params(["cascade_fill_enabled=true", "cascade_intensity=0.8", "verbose=true"])
    print(f"✅ Parsed parameters: {params}")

    # Step 4: Simulate CLI render candidate loop with DETAILED EXCEPTION HANDLING
    render_candidates = (
        "render",
        "generate",
        "render_shapes",
        "run",
        "build",
        "make",
        "create",
    )

    doc_or_shapes = None

    print(f"\n--- Simulating CLI Render Candidate Loop ---")

    for cand in render_candidates:
        if hasattr(geom_mod, cand):
            print(f"\n🔍 Trying candidate: {cand}")

            try:
                fn = getattr(geom_mod, cand)
                sig = inspect.signature(fn)
                kwargs = {}

                # Add parameters exactly like CLI does
                if "total_points" in sig.parameters:
                    kwargs["total_points"] = 500
                elif "points" in sig.parameters:
                    kwargs["points"] = 500

                if "seed" in sig.parameters:
                    kwargs["seed"] = 42
                if "cascade_stages" in sig.parameters:
                    kwargs["cascade_stages"] = 3
                if "canvas_size" in sig.parameters:
                    kwargs["canvas_size"] = canvas_size
                if "input_image" in sig.parameters:
                    kwargs["input_image"] = input_image
                if "verbose" in sig.parameters:
                    kwargs["verbose"] = True

                # Add all parsed parameters
                for key, value in params.items():
                    if key in sig.parameters:
                        kwargs[key] = value
                        print(f"   Adding parameter: {key} = {value}")

                print(f"   Final kwargs keys: {list(kwargs.keys())}")

                # Call exactly like CLI does
                print(f"   Calling {cand}...")
                if cand == "render":
                    doc_or_shapes = fn(str(inp), **kwargs)
                else:
                    doc_or_shapes = fn(**kwargs)

                print(f"✅ {cand} succeeded: {len(doc_or_shapes)} shapes")
                break

            except Exception as e:
                print(f"❌ {cand} failed with exception: {e}")
                print(f"   Exception type: {type(e).__name__}")
                print(f"   Full traceback:")
                traceback.print_exc(limit=3)
                print(f"   --- Continuing to next candidate (like CLI does) ---")
                continue  # This is what CLI does!
    else:
        print("❌ ALL CANDIDATES FAILED - no shapes generated")
        return None

    print(f"\n--- Final Result ---")
    if doc_or_shapes:
        print(f"✅ Generated {len(doc_or_shapes)} shapes using {cand}")
        print(f"First shape sample: {doc_or_shapes[0] if doc_or_shapes else 'None'}")
        return doc_or_shapes
    else:
        print("❌ No shapes generated - CLI would fall back to default")
        return None

# Step 5: Test what CLI does when geometry generation fails
def test_cli_fallback():
    """Test what happens when geometry generation fails"""
    print(f"\n--- Testing CLI Fallback Behavior ---")

    # This is probably what CLI does when all geometry candidates fail
    try:
        import svg_export

        # CLI might generate some default shapes
        print("Testing default shape generation...")

        # Maybe CLI has some default shape generation?
        # Let's check what generates exactly 64 shapes

        # One possibility: CLI generates a grid of rectangles as fallback
        default_shapes = []
        for i in range(8):
            for j in range(8):  # 8x8 = 64 shapes
                default_shapes.append({
                    "type": "rect",
                    "x": i * 50,
                    "y": j * 50,
                    "w": 40,
                    "h": 40,
                    "fill": f"hsl({(i+j)*45%360},70%,50%)"
                })

        print(f"Generated {len(default_shapes)} default shapes")

        # Test exporting these
        svg_content = svg_export.export_svg(default_shapes, width=400, height=400)
        print(f"Default SVG length: {len(svg_content)} chars")

        # Count shapes in SVG
        import re
        shape_count = (
            svg_content.count("<rect") +
            svg_content.count("<circle") +
            svg_content.count("<polygon")
        )
        print(f"Shapes in default SVG: {shape_count}")

    except Exception as e:
        print(f"❌ Fallback test failed: {e}")

if __name__ == "__main__":
    result = debug_cli_geometry_call()
    test_cli_fallback()

    print(f"\n=== Summary ===")
    if result:
        print(f"✅ Geometry generation succeeded with {len(result)} shapes")
        print("❌ But CLI is somehow not using this result - check CLI exception handling")
    else:
        print("❌ Geometry generation failed - CLI fallback explains 64 shapes")
