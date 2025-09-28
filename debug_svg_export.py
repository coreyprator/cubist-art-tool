# debug_svg_export.py - Test SVG export phase specifically
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("=== Debugging SVG Export Phase ===")

try:
    import geometry_plugins.rectangles as rect_plugin
    import svg_export
    
    # Step 1: Generate shapes like CLI does
    print("\n1. Generating shapes (CLI simulation):")
    
    input_path = "input/x_your_input_image.jpg"
    kwargs = {
        "total_points": 500,
        "seed": 42,
        "cascade_fill_enabled": True,
        "cascade_intensity": 0.8,
        "verbose": True
    }
    
    shapes = rect_plugin.render(input_path, **kwargs)
    print(f"✅ Generated {len(shapes)} shapes")
    print(f"First shape type: {type(shapes[0])}")
    print(f"First shape keys: {shapes[0].keys() if isinstance(shapes[0], dict) else 'Not a dict'}")
    
    # Step 2: Test plugin exporters
    print("\n2. Testing plugin exporters:")
    
    # Check if rectangles plugin has export functions
    export_functions = ["export_svg", "save_svg", "write_svg"]
    for func_name in export_functions:
        if hasattr(rect_plugin, func_name):
            print(f"✅ Found {func_name} in rectangles plugin")
            try:
                fn = getattr(rect_plugin, func_name)
                print(f"   Function signature: {fn.__code__.co_varnames}")
            except:
                print(f"   Could not inspect {func_name}")
        else:
            print(f"❌ {func_name} not found in rectangles plugin")
    
    # Step 3: Test svg_export fallback
    print("\n3. Testing svg_export fallback:")
    
    try:
        # Test with actual shapes from rectangles
        canvas_size = (3024, 4032)  # Actual image size
        
        print(f"Calling svg_export.export_svg with {len(shapes)} shapes...")
        svg_content = svg_export.export_svg(
            shapes, width=canvas_size[0], height=canvas_size[1]
        )
        
        print(f"✅ svg_export.export_svg succeeded")
        print(f"   SVG content length: {len(svg_content)} chars")
        print(f"   Contains shapes: {svg_content.count('<polygon') + svg_content.count('<circle') + svg_content.count('<path')}")
        
        # Write test file
        test_file = Path("output/test_export.svg")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(svg_content, encoding="utf-8")
        print(f"   Wrote test SVG: {test_file}")
        
    except Exception as e:
        print(f"❌ svg_export.export_svg failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 4: Test shape format compatibility
    print("\n4. Testing shape format compatibility:")
    
    sample_shape = shapes[0]
    print(f"Sample shape: {sample_shape}")
    
    # Check if shape matches svg_export expectations
    if isinstance(sample_shape, dict):
        shape_type = sample_shape.get("type", "unknown")
        print(f"Shape type: {shape_type}")
        
        if shape_type == "polygon":
            points = sample_shape.get("points", [])
            print(f"Points count: {len(points)}")
            print(f"First few points: {points[:3] if points else 'None'}")
        
        fill = sample_shape.get("fill", "none")
        print(f"Fill: {fill}")
        
    # Step 5: Test what happens if we manually call svg_export like CLI does
    print("\n5. Simulating CLI SVG export process:")
    
    try:
        # This is what CLI does when export fails
        print("Testing fallback scenario...")
        
        # Create small test case
        test_shapes = shapes[:10]  # Just first 10 shapes
        
        svg_content2 = svg_export.export_svg(
            test_shapes, width=800, height=600
        )
        
        print(f"✅ Fallback export succeeded with {len(test_shapes)} shapes")
        print(f"   SVG length: {len(svg_content2)} chars")
        
        # Count actual shape elements in SVG
        import re
        polygon_count = len(re.findall(r'<polygon', svg_content2))
        circle_count = len(re.findall(r'<circle', svg_content2))
        path_count = len(re.findall(r'<path', svg_content2))
        
        print(f"   SVG contains: {polygon_count} polygons, {circle_count} circles, {path_count} paths")
        
    except Exception as e:
        print(f"❌ Fallback export failed: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"❌ Debug setup failed: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Debug Complete ===")
