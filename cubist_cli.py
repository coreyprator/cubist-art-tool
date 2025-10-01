#!/usr/bin/env python3
"""
Cubist CLI - Phase 2: Hybrid Subdivision Support
Enhanced with mask-based multi-geometry composition
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

# Import hybrid subdivision
try:
    from hybrid_subdivision import MaskBasedSubdivision
except ImportError:
    MaskBasedSubdivision = None
    print("Warning: hybrid_subdivision not available", file=sys.stderr)

# Import PIL for image loading
try:
    from PIL import Image
except ImportError:
    Image = None


def main():
    parser = argparse.ArgumentParser(
        description="Cubist Art CLI with Hybrid Multi-Geometry Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single geometry (standard mode)
  python cubist_cli.py --input photo.jpg --output result --geometry rectangles --points 500 --export-svg
  
  # Hybrid mode with mask (2 regions)
  python cubist_cli.py --input portrait.jpg --mask subject_mask.png \\
    --region 0:rectangles:500 --region 255:poisson_disk:1000 \\
    --output hybrid_result --export-svg
  
  # Hybrid mode with background image
  python cubist_cli.py --input portrait.jpg --mask subject_mask.png \\
    --background sunset.jpg --region 0:rectangles:500 --region 255:scatter_circles:800 \\
    --output composite --export-svg
  
  # Region syntax: <mask_value>:<geometry>:<point_count>
  # Optional per-region parameters: <mask_value>:<geometry>:<point_count>:param1=val1:param2=val2
        """
    )
    
    # Standard arguments
    parser.add_argument("--input", required=True, help="Input image path")
    parser.add_argument("--output", required=True, help="Output path (without extension)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--export-svg", action="store_true", help="Export SVG")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    # Single geometry mode (original)
    parser.add_argument("--geometry", help="Geometry type (single mode)")
    parser.add_argument("--points", type=int, default=500, help="Number of shapes (single mode)")
    parser.add_argument("--param", action="append", help="Parameter in format name=value")
    
    # Hybrid multi-geometry mode
    parser.add_argument("--mask", help="Mask image path for hybrid mode")
    parser.add_argument("--background", help="Optional background image for hybrid mode")
    parser.add_argument("--region", action="append", help="Region assignment: mask_value:geometry:points[:param=val...]")
    parser.add_argument("--cascade", action="store_true", help="Enable cascade fill (hybrid mode)")
    
    args = parser.parse_args()
    
    # Determine mode: hybrid or single geometry
    hybrid_mode = bool(args.mask and args.region)
    
    if hybrid_mode and not MaskBasedSubdivision:
        print("Error: Hybrid mode requires hybrid_subdivision.py", file=sys.stderr)
        sys.exit(1)
    
    if hybrid_mode:
        return run_hybrid_mode(args)
    else:
        return run_single_geometry_mode(args)


def run_single_geometry_mode(args):
    """Original single-geometry mode"""
    if not args.geometry:
        print("Error: --geometry required for single geometry mode", file=sys.stderr)
        sys.exit(1)
    
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


def run_hybrid_mode(args):
    """New hybrid multi-geometry mode"""
    if not args.region:
        print("Error: --region required for hybrid mode", file=sys.stderr)
        print("Example: --region 0:rectangles:500 --region 255:poisson_disk:1000", file=sys.stderr)
        sys.exit(1)
    
    # Load images
    input_image = None
    mask_image = None
    background_image = None
    
    if not Image:
        print("Error: PIL required for hybrid mode", file=sys.stderr)
        sys.exit(1)
    
    try:
        input_image = Image.open(args.input).convert("RGB")
        mask_image = Image.open(args.mask).convert("L")
        
        if args.background:
            background_image = Image.open(args.background).convert("RGB")
    except Exception as e:
        print(f"Error loading images: {e}", file=sys.stderr)
        sys.exit(1)
    
    canvas_size = input_image.size
    
    # Parse region assignments
    region_assignments = {}
    
    for region_spec in args.region:
        parts = region_spec.split(":")
        if len(parts) < 3:
            print(f"Error: Invalid region spec: {region_spec}", file=sys.stderr)
            print("Format: mask_value:geometry:points[:param=val...]", file=sys.stderr)
            sys.exit(1)
        
        mask_value = int(parts[0])
        geometry = parts[1]
        points = int(parts[2])
        
        # Parse optional parameters
        params = {}
        for param_spec in parts[3:]:
            if "=" in param_spec:
                key, val = param_spec.split("=", 1)
                try:
                    if "." in val:
                        params[key] = float(val)
                    else:
                        params[key] = int(val)
                except ValueError:
                    if val.lower() in ("true", "false"):
                        params[key] = val.lower() == "true"
                    else:
                        params[key] = val
        
        region_assignments[mask_value] = {
            'geometry': geometry,
            'target_count': points,
            'params': params
        }
    
    if args.verbose:
        print(f"[cli] Hybrid mode: {len(region_assignments)} regions", file=sys.stderr)
        for mask_val, assignment in region_assignments.items():
            print(f"[cli]   Region {mask_val}: {assignment['geometry']} x{assignment['target_count']}", file=sys.stderr)
    
    # Create subdivision system
    start_time = time.time()
    
    try:
        subdivision = MaskBasedSubdivision(
            canvas_size=canvas_size,
            input_image=input_image,
            mask_image=mask_image,
            background_image=background_image,
            verbose=args.verbose
        )
        
        shapes = subdivision.generate_hybrid_artwork(
            region_assignments=region_assignments,
            seed=args.seed,
            cascade_fill_enabled=args.cascade
        )
    except Exception as e:
        print(f"Error generating hybrid artwork: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    generation_time = time.time() - start_time
    
    # Export SVG
    if args.export_svg:
        svg_path = Path(args.output).with_suffix(".svg")
        
        # Collect metadata
        metadata = {
            "geometry": "hybrid_multi",
            "fill_method": "cascade" if args.cascade else "default",
            "input_source": str(Path(args.input).resolve()),
            "mask_source": str(Path(args.mask).resolve()),
            "background_source": str(Path(args.background).resolve()) if args.background else "",
            "target_shapes": sum(a['target_count'] for a in region_assignments.values()),
            "seed": args.seed,
            "generation_time": generation_time,
            "parameters": {
                "regions": len(region_assignments),
                "cascade_enabled": args.cascade
            }
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
            "mode": "hybrid",
            "input": args.input,
            "mask": args.mask,
            "background": args.background or "",
            "output": args.output,
            "regions": len(region_assignments),
            "seed": args.seed,
            "cascade": args.cascade,
            "rc": 0,
            "outputs": {
                "expected_svg": str(svg_path),
                "svg_exists": svg_path.exists(),
                "svg_path": str(svg_path),
                "svg_size": svg_path.stat().st_size if svg_path.exists() else 0,
                "svg_shapes": len(shapes)
            },
            "plugin_exc": "",
            "elapsed_s": generation_time
        }
        
        print(json.dumps(result))


if __name__ == "__main__":
    main()