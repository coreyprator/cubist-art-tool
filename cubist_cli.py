#!/usr/bin/env python3
"""
Cubist CLI - Metadata Integration
Collects generation parameters and passes to SVG export for metadata embedding.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import geometry system and export
from geometry_loader import load_geometry_plugins
from svg_export import save_svg

# Import PIL for image loading
try:
    from PIL import Image
except ImportError:
    Image = None


def main():
    parser = argparse.ArgumentParser(description="Cubist Art CLI with Metadata")
    parser.add_argument("--input", required=True, help="Input image path")
    parser.add_argument("--output", required=True, help="Output path (without extension)")
    parser.add_argument("--geometry", required=True, help="Geometry type")
    parser.add_argument("--points", type=int, default=500, help="Number of shapes")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--export-svg", action="store_true", help="Export SVG")
    parser.add_argument("--param", action="append", help="Parameter in format name=value")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Parse parameters
    params = {}
    if args.param:
        for p in args.param:
            if "=" in p:
                key, val = p.split("=", 1)
                # Try to parse as number
                try:
                    if "." in val:
                        params[key] = float(val)
                    else:
                        params[key] = int(val)
                except ValueError:
                    # Parse boolean
                    if val.lower() in ("true", "false"):
                        params[key] = val.lower() == "true"
                    else:
                        params[key] = val
    
    # Load input image
    input_image = None
    if Image:
        try:
            input_image = Image.open(args.input).convert("RGB")
        except Exception as e:
            print(f"Warning: Could not load image: {e}", file=sys.stderr)
    
    # Get canvas size from image
    if input_image:
        canvas_size = input_image.size
    else:
        canvas_size = (800, 600)
    
    # Load geometry plugins
    geometries = load_geometry_plugins()
    
    if args.geometry not in geometries:
        print(f"Error: Geometry '{args.geometry}' not found", file=sys.stderr)
        print(f"Available: {', '.join(geometries.keys())}", file=sys.stderr)
        sys.exit(1)
    
    # Generate shapes with timing
    start_time = time.time()
    
    try:
        shapes = geometries[args.geometry](
            canvas_size=canvas_size,
            total_points=args.points,
            seed=args.seed,
            input_image=input_image,
            verbose=args.verbose,
            **params
        )
    except Exception as e:
        print(f"Error generating shapes: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    generation_time = time.time() - start_time
    
    # Export SVG with metadata
    if args.export_svg:
        svg_path = Path(args.output).with_suffix(".svg")
        
        # Collect metadata
        metadata = {
            "geometry": args.geometry,
            "fill_method": "cascade" if params.get("cascade_fill_enabled") else "default",
            "input_source": str(Path(args.input).resolve()),
            "target_shapes": args.points,
            "seed": args.seed,
            "generation_time": generation_time,
            "parameters": {k: v for k, v in params.items() if isinstance(v, (int, float))}
        }
        
        success = save_svg(
            shapes=shapes,
            filepath=str(svg_path),
            width=canvas_size[0],
            height=canvas_size[1],
            metadata=metadata
        )
        
        if not success:
            print(f"Error: Failed to write SVG to {svg_path}", file=sys.stderr)
            sys.exit(1)
        
        # Output JSON summary
        result = {
            "ts": None,
            "input": args.input,
            "output": args.output,
            "geometry": args.geometry,
            "points": args.points,
            "seed": args.seed,
            "rc": 0,
            "outputs": {
                "expected_svg": str(svg_path),
                "svg_exists": svg_path.exists(),
                "svg_path": str(svg_path),
                "svg_size": svg_path.stat().st_size if svg_path.exists() else 0,
                "svg_shapes": len(shapes)
            },
            "plugin_exc": "",
            "forced_write": False,
            "forced_write_reason": "",
            "elapsed_s": generation_time
        }
        
        print(json.dumps(result))


if __name__ == "__main__":
    main()