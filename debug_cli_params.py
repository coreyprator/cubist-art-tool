# debug_cli_params.py - Test how CLI passes parameters to geometry plugins
import sys
import inspect
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("=== Debugging CLI Parameter Passing ===")

# Test 1: Check what parameters CLI tries to pass
print("\n1. Checking CLI parameter parsing:")
from cubist_cli import parse_params

test_params = ["cascade_fill_enabled=true", "cascade_intensity=0.8", "verbose=true"]
parsed = parse_params(test_params)
print(f"Parsed params: {parsed}")

# Test 2: Check geometry plugin loading like CLI does
print("\n2. Testing geometry plugin loading (CLI style):")
try:
    from cubist_cli import load_geometry
    geom_mod = load_geometry("rectangles")
    print(f"✅ Loaded geometry module: {geom_mod}")
    
    # Check what function the CLI would call
    render_candidates = ("render", "generate", "render_shapes", "run", "build", "make", "create")
    
    for cand in render_candidates:
        if hasattr(geom_mod, cand):
            fn = getattr(geom_mod, cand)
            sig = inspect.signature(fn)
            print(f"✅ Found function: {cand}")
            print(f"   Parameters: {list(sig.parameters.keys())}")
            break
    else:
        print("❌ No suitable function found")

except Exception as e:
    print(f"❌ Geometry loading failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Simulate CLI call with actual parameters
print("\n3. Simulating CLI call with parameters:")
try:
    # Simulate what CLI does
    canvas_size = (800, 600)
    points = 500
    seed = 42
    
    # Parameters that CLI parsed
    params = {
        "cascade_fill_enabled": True,
        "cascade_intensity": 0.8,
        "verbose": True
    }
    
    # Build kwargs like CLI does
    kwargs = {}
    
    fn = getattr(geom_mod, "generate")
    sig = inspect.signature(fn)
    
    # Add core parameters
    if "total_points" in sig.parameters:
        kwargs["total_points"] = points
    elif "points" in sig.parameters:
        kwargs["points"] = points
    
    if "seed" in sig.parameters:
        kwargs["seed"] = seed
    if "canvas_size" in sig.parameters:
        kwargs["canvas_size"] = canvas_size
    if "input_image" in sig.parameters:
        kwargs["input_image"] = None
    if "verbose" in sig.parameters:
        kwargs["verbose"] = True
        
    # Add parsed parameters
    for key, value in params.items():
        if key in sig.parameters:
            kwargs[key] = value
            print(f"   Adding parameter: {key} = {value}")
    
    print(f"Final kwargs: {kwargs}")
    
    # Call like CLI does
    print("\nCalling generate() with CLI-style parameters...")
    result = fn(**kwargs)
    print(f"✅ Generated {len(result)} shapes")
    
except Exception as e:
    print(f"❌ CLI simulation failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check if there's a parameter name mismatch
print("\n4. Checking for parameter name mismatches:")
expected_params = [
    "canvas_size", "total_points", "seed", "input_image", 
    "cascade_fill_enabled", "cascade_intensity", "verbose"
]

fn = getattr(geom_mod, "generate")
sig = inspect.signature(fn)
actual_params = list(sig.parameters.keys())

print(f"Expected: {expected_params}")
print(f"Actual:   {actual_params}")

missing = [p for p in expected_params if p not in actual_params]
if missing:
    print(f"❌ Missing parameters: {missing}")
else:
    print("✅ All expected parameters present")

print("\n=== Debug Complete ===")
