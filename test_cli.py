#!/usr/bin/env python3
"""
Cubist Art Generator CLI Test Script

This script allows testing all geometry modes with cascade fill on/off.
Usage examples:
  python test_cli.py --input input/your_input_image.jpg --geometry delaunay --cascade_fill true
  python test_cli.py --input input/your_input_image.jpg --geometry voronoi --cascade_fill false
  python test_cli.py --run_all_tests --input input/your_input_image.jpg
"""

import argparse
import sys
import os
from pathlib import Path
import time
from typing import List, Tuple

# Import logging
from cubist_logger import logger

# Import the archive function
try:
    from archive_output import archive_output_folder
except ImportError:
    logger.warning("Could not import archive_output.py - archive functionality disabled")
    archive_output_folder = None

# Import the core logic
try:
    from cubist_core_logic import run_cubist
except ImportError:
    logger.error("Could not import cubist_core_logic.py")
    print("ERROR: Could not import cubist_core_logic.py")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)


def parse_bool(value: str) -> bool:
    """Parse string boolean values."""
    if isinstance(value, bool):
        return value
    if value.lower() in ('yes', 'true', 't', 'y', '1', 'on'):
        return True
    elif value.lower() in ('no', 'false', 'f', 'n', '0', 'off'):
        return False
    else:
        raise argparse.ArgumentTypeError(f'Boolean value expected, got: {value}')


def run_single_test(input_path: str, output_dir: str, geometry_mode: str, 
                   use_cascade_fill: bool, total_points: int = 1000, 
                   mask_path: str = None, save_step_frames: bool = False,
                   verbose: bool = True) -> str:
    """Run a single cubist generation test."""
    
    logger.info(f"run_single_test() ENTRY: mode={geometry_mode}, cascade={use_cascade_fill}, points={total_points}")
    print(f"\n{'='*60}")
    print(f"🎨 Testing: {geometry_mode.upper()} | Cascade: {'ON' if use_cascade_fill else 'OFF'}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        logger.info(f"Starting test: {geometry_mode}")
        
        output_path = run_cubist(
            input_path=input_path,
            output_dir=output_dir,
            mask_path=mask_path,
            total_points=total_points,
            clip_to_alpha=True,
            verbose=verbose,
            geometry_mode=geometry_mode,
            use_cascade_fill=use_cascade_fill,
            save_step_frames=save_step_frames
        )
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Test completed successfully in {duration:.2f}s: {output_path}")
        
        print(f"✅ SUCCESS: Generated in {duration:.2f} seconds")
        print(f"📁 Output: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"❌ ERROR: {str(e)}")
        return None


def run_all_tests(input_path: str, output_dir: str, total_points: int = 1000,
                 mask_path: str = None, save_step_frames: bool = False,
                 verbose: bool = True, mask_only_tests: bool = False) -> List[Tuple[str, str, bool, str]]:
    """Run all geometry modes with both cascade fill on and off."""
    
    logger.info(f"run_all_tests() ENTRY: points={total_points}, save_frames={save_step_frames}, mask_only={mask_only_tests}")
    geometry_modes = ['delaunay', 'voronoi', 'rectangles']
    cascade_options = [False, True]
    results = []
    
    # Override mask behavior for mask-only tests
    if mask_only_tests:
        if not mask_path:
            logger.error("mask_only_tests requires a mask path")
            raise ValueError("--mask_only_tests requires --mask to be specified")
        test_mask_path = mask_path
        test_description = "masked-only"
    else:
        test_mask_path = mask_path
        test_description = "standard" + (" with mask" if mask_path else "")
    
    print(f"\n🚀 Running comprehensive test suite ({test_description})...")
    print(f"📄 Input: {input_path}")
    print(f"📁 Output directory: {output_dir}")
    print(f"🔢 Points: {total_points}")
    print(f"🎭 Mask: {test_mask_path if test_mask_path else 'None'}")
    print(f"🎬 Step frames: {'Yes' if save_step_frames else 'No'}")
    if mask_only_tests:
        print(f"🎭 Mode: Masked-only tests (no unmasked tests will be run)")
    logger.info(f"Starting test suite with {len(geometry_modes)} modes × {len(cascade_options)} cascade options")
    
    total_tests = len(geometry_modes) * len(cascade_options)
    current_test = 0
    
    for geometry_mode in geometry_modes:
        for use_cascade_fill in cascade_options:
            current_test += 1
            
            print(f"\n🔄 Test {current_test}/{total_tests}")
            logger.info(f"Starting test {current_test}/{total_tests}: {geometry_mode} with cascade={use_cascade_fill}")
            
            output_path = run_single_test(
                input_path=input_path,
                output_dir=output_dir,
                geometry_mode=geometry_mode,
                use_cascade_fill=use_cascade_fill,
                total_points=total_points,
                mask_path=test_mask_path,
                save_step_frames=save_step_frames,
                verbose=verbose
            )
            
            cascade_str = "cascade" if use_cascade_fill else "regular"
            if output_path:
                logger.info(f"Test {current_test} SUCCESS: {geometry_mode} ({cascade_str}) -> {output_path}")
            else:
                logger.error(f"Test {current_test} FAILED: {geometry_mode} ({cascade_str})")
            results.append((geometry_mode, cascade_str, use_cascade_fill, output_path))
    
    logger.info(f"run_all_tests() EXIT: Completed {len(results)} tests")
    return results


def print_summary(results: List[Tuple[str, str, bool, str]], mask_only_tests: bool = False):
    """Print a summary of all test results."""
    
    logger.info("print_summary() ENTRY: Generating test summary")
    test_type = "MASKED-ONLY TEST" if mask_only_tests else "TEST"
    print(f"\n{'='*80}")
    print(f"📊 {test_type} SUMMARY")
    print(f"{'='*80}")
    
    successful_tests = [r for r in results if r[3] is not None]
    failed_tests = [r for r in results if r[3] is None]
    
    print(f"✅ Successful: {len(successful_tests)}/{len(results)}")
    logger.info(f"Test results: {len(successful_tests)} successful, {len(failed_tests)} failed")
    print(f"❌ Failed: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        print(f"\n📁 Generated Files:")
        for geometry, cascade_type, cascade_bool, output_path in successful_tests:
            if output_path:
                filename = Path(output_path).name
                mask_indicator = "🎭" if "_masked" in filename else "  "
                print(f"  {mask_indicator} {geometry:>10} | {cascade_type:>7} | {filename}")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for geometry, cascade_type, cascade_bool, _ in failed_tests:
            print(f"  • {geometry:>10} | {cascade_type:>7}")
    
    if mask_only_tests:
        print(f"\n💡 Tip: All outputs are masked - compare them with unmasked versions!")
        print(f"💡 Notice: The '_masked' suffix in filenames indicates these used a mask")
    else:
        print(f"\n💡 Tip: Compare the 'cascade' vs 'regular' outputs to see the difference!")
    print(f"💡 Enhanced CascadeFill features:")
    print(f"   - Spatial optimization for better space utilization")
    print(f"   - Adjacency-based placement reduces gaps")
    print(f"   - Adaptive shape sizing based on available space")
    print(f"   - Rotational variety in rectangles mode")
    print(f"   - Organic shape generation in voronoi mode")


def validate_input_file(input_path: str) -> bool:
    """Validate that the input file exists and is a valid image."""
    if not os.path.exists(input_path):
        print(f"❌ ERROR: Input file not found: {input_path}")
        return False
    
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    if Path(input_path).suffix.lower() not in valid_extensions:
        print(f"⚠ WARNING: Input file may not be a valid image: {input_path}")
        print(f"Valid extensions: {', '.join(valid_extensions)}")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Test Cubist Art Generator with different geometry modes and cascade fill options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test single geometry mode
  python test_cli.py --input input/image.jpg --geometry delaunay --cascade_fill true
  
  # Test all combinations with clean output folder
  python test_cli.py --run_all_tests --input input/image.jpg --archive_output
  
  # Test with custom points and step frames
  python test_cli.py --input input/image.jpg --geometry voronoi --cascade_fill false --points 500 --step_frames
  
  # Test with mask and archive existing output
  python test_cli.py --input input/image.jpg --mask input/mask.png --geometry rectangles --cascade_fill true --archive_output
  
  # Test all modes with mask only (no archiving - keeps unmasked results for comparison)
  python test_cli.py --mask_only_tests --input input/image.jpg --mask input/mask.png --points 200
        """
    )
    
    # Input/Output arguments
    parser.add_argument('--input', '-i', required=True,
                       help='Path to input image file')
    parser.add_argument('--output', '-o', default='output',
                       help='Output directory (default: output)')
    parser.add_argument('--mask', '-m',
                       help='Path to mask image file (optional)')
    
    # Test mode arguments
    parser.add_argument('--run_all_tests', action='store_true',
                       help='Run all geometry modes with both cascade fill on/off')
    parser.add_argument('--mask_only_tests', action='store_true',
                       help='Run all geometry modes with both cascade fill on/off, but only with the mask (requires --mask)')
    parser.add_argument('--geometry', '-g', 
                       choices=['delaunay', 'voronoi', 'rectangles'],
                       help='Geometry mode (required if not using --run_all_tests)')
    parser.add_argument('--cascade_fill', '-c', type=parse_bool,
                       help='Use cascade fill (true/false)')
    
    # Configuration arguments
    parser.add_argument('--points', '-p', type=int, default=1000,
                       help='Number of points to sample (default: 1000)')
    parser.add_argument('--step_frames', action='store_true',
                       help='Save step frames for animation (cascade fill only)')
    parser.add_argument('--archive_output', action='store_true',
                       help='Archive existing output folder contents before running tests')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.run_all_tests and not args.mask_only_tests:
        if args.geometry is None:
            parser.error("--geometry is required when not using --run_all_tests or --mask_only_tests")
        if args.cascade_fill is None:
            parser.error("--cascade_fill is required when not using --run_all_tests or --mask_only_tests")
    
    if args.mask_only_tests:
        if args.mask is None:
            parser.error("--mask_only_tests requires --mask to be specified")
        if args.run_all_tests:
            parser.error("Cannot use both --run_all_tests and --mask_only_tests at the same time")
    
    # Validate input file
    if not validate_input_file(args.input):
        logger.error(f"Input file validation failed: {args.input}")
        sys.exit(1)
    
    # Create output directory
    Path(args.output).mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory created/verified: {args.output}")
    
    # Archive existing output if requested
    if args.archive_output:
        if archive_output_folder is not None:
            logger.info("Archiving existing output folder contents")
            print("📦 Archiving existing output folder contents...")
            try:
                archive_path = archive_output_folder(dry_run=False)
                if archive_path:
                    print(f"✅ Successfully archived to: {archive_path}")
                    logger.info(f"Output archived to: {archive_path}")
                else:
                    print("ℹ️  No files to archive - output folder was already empty")
                    logger.info("No files to archive - output folder was already empty")
            except Exception as e:
                print(f"⚠️  Warning: Archive failed: {str(e)}")
                logger.warning(f"Archive failed: {str(e)}")
                print("   Continuing with test execution...")
        else:
            print("⚠️  Archive functionality not available (archive_output.py not found)")
            logger.warning("Archive functionality not available")
    elif args.mask_only_tests:
        print("📁 Output folder NOT archived - masked results will be added alongside existing files")
        logger.info("Output folder not archived for mask-only tests to preserve comparison files")
    
    verbose = not args.quiet
    
    try:
        if args.run_all_tests:
            logger.info("Starting comprehensive test suite")
            # Run comprehensive test suite
            results = run_all_tests(
                input_path=args.input,
                output_dir=args.output,
                total_points=args.points,
                mask_path=args.mask,
                save_step_frames=args.step_frames,
                verbose=verbose,
                mask_only_tests=False
            )
            print_summary(results, mask_only_tests=False)
            logger.info("Comprehensive test suite completed")
            
        elif args.mask_only_tests:
            logger.info("Starting masked-only test suite")
            # Run masked-only test suite
            results = run_all_tests(
                input_path=args.input,
                output_dir=args.output,
                total_points=args.points,
                mask_path=args.mask,
                save_step_frames=args.step_frames,
                verbose=verbose,
                mask_only_tests=True
            )
            print_summary(results, mask_only_tests=True)
            logger.info("Masked-only test suite completed")
            
        else:
            logger.info(f"Starting single test: {args.geometry} with cascade={args.cascade_fill}")
            # Run single test
            output_path = run_single_test(
                input_path=args.input,
                output_dir=args.output,
                geometry_mode=args.geometry,
                use_cascade_fill=args.cascade_fill,
                total_points=args.points,
                mask_path=args.mask,
                save_step_frames=args.step_frames,
                verbose=verbose
            )
            
            if output_path:
                print(f"\n🎉 Test completed successfully!")
                print(f"📁 Output saved to: {output_path}")
                logger.info(f"Single test completed successfully: {output_path}")
            else:
                print(f"\n❌ Test failed!")
                logger.error("Single test failed")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print(f"\n\n⚠ Test interrupted by user")
        logger.warning("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    logger.info("test_cli.py started")
    main()
    logger.info("test_cli.py completed")
