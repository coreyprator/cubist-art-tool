# hybrid_subdivision.py
"""
Hybrid Subdivision System - Mask-Based Multi-Geometry Composition
Cubist Art v2.6.0 - Phase 2 Sprint 1

Enables combining multiple geometries in a single artwork using mask-based regions.
Supports optional background image for compositional control.

MASK CONVENTION (Industry Standard):
- White/light areas (128-255) = Subject/Foreground
- Black/dark areas (0-127) = Background
"""

from __future__ import annotations
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter

try:
    from PIL import Image
except ImportError:
    Image = None

# Import geometry loader and cascade fill
try:
    from geometry_loader import load_geometry_plugins
    from cascade_fill_system import apply_universal_cascade_fill, sample_image_color
except ImportError:
    def load_geometry_plugins():
        return {}
    def apply_universal_cascade_fill(shapes, canvas_size, target_count, shape_generator, seed=42, verbose=False):
        return shapes
    def sample_image_color(input_image, x, y, canvas_width, canvas_height):
        return "rgb(128,128,128)"


class MaskBasedSubdivision:
    """
    Manages mask-based canvas subdivision for multi-geometry composition.
    
    Three-image input model:
    - Input image: Primary color source (typically the subject)
    - Mask image: Defines regions (grayscale, 0-255)
    - Background image: Optional secondary color source for background regions
    
    MASK CONVENTION (Industry Standard):
    - White/light areas (128-255) = Subject/Foreground (samples from input_image)
    - Black/dark areas (0-127) = Background (samples from background_image if provided)
    """
    
    def __init__(
        self,
        canvas_size: Tuple[int, int],
        input_image: Image.Image,
        mask_image: Optional[Image.Image] = None,
        background_image: Optional[Image.Image] = None,
        verbose: bool = False
    ):
        """
        Initialize mask-based subdivision system.
        
        Args:
            canvas_size: (width, height) in pixels
            input_image: PIL Image - primary color source (subject)
            mask_image: PIL Image - grayscale region mask (None = single region)
            background_image: PIL Image - optional background color source
            verbose: Enable debug logging
        """
        self.canvas_size = canvas_size
        self.width, self.height = canvas_size
        self.input_image = input_image.resize(canvas_size) if input_image else None
        self.background_image = background_image.resize(canvas_size) if background_image else None
        self.verbose = verbose
        
        # Process mask or create single-region fallback
        if mask_image:
            self.mask = mask_image.convert('L').resize(canvas_size)
            self.regions = self._detect_regions()
        else:
            # No mask = single region covering entire canvas
            self.mask = None
            self.regions = {128: {'bbox': (0, 0, self.width, self.height), 'count': self.width * self.height}}
        
        if self.verbose:
            print(f"[hybrid_subdivision] Canvas: {self.width}x{self.height}")
            print(f"[hybrid_subdivision] Detected {len(self.regions)} regions: {list(self.regions.keys())}")
            if self.background_image:
                print(f"[hybrid_subdivision] Background image provided for compositing")
    
    def _detect_regions(self) -> Dict[int, Dict[str, Any]]:
        """
        Detect distinct regions from mask image.
        
        Returns:
            Dict mapping pixel values to region info:
            {
                pixel_value: {
                    'bbox': (x_min, y_min, x_max, y_max),
                    'count': pixel_count
                }
            }
        """
        if not self.mask:
            return {}
        
        # Count occurrences of each pixel value
        pixel_counts = Counter(self.mask.getdata())
        
        if self.verbose:
            print(f"[hybrid_subdivision] Mask analysis: {len(pixel_counts)} unique values")
            for value, count in sorted(pixel_counts.items(), key=lambda x: -x[1])[:5]:
                print(f"  Value {value}: {count} pixels ({count / (self.width * self.height) * 100:.1f}%)")
        
        # For each unique pixel value, calculate bounding box
        regions = {}
        mask_data = self.mask.load()
        
        for pixel_value in pixel_counts:
            x_coords = []
            y_coords = []
            
            # Sample mask to find region extent
            for y in range(self.height):
                for x in range(self.width):
                    if mask_data[x, y] == pixel_value:
                        x_coords.append(x)
                        y_coords.append(y)
            
            if x_coords and y_coords:
                bbox = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
                regions[pixel_value] = {
                    'bbox': bbox,
                    'count': pixel_counts[pixel_value]
                }
        
        return regions
    
    def get_color_for_position(self, x: float, y: float) -> str:
        """
        Sample color from appropriate image based on mask region.
        
        MASK CONVENTION:
        - Light values (>= 128) = Subject, sample from input_image
        - Dark values (< 128) = Background, sample from background_image (or input_image if not provided)
        
        Args:
            x, y: Position on canvas
            
        Returns:
            RGB color string "rgb(r,g,b)"
        """
        # Clamp coordinates to canvas
        x = max(0, min(self.width - 1, int(x)))
        y = max(0, min(self.height - 1, int(y)))
        
        # No mask = always use input image
        if not self.mask:
            if self.input_image:
                return sample_image_color(self.input_image, x, y, self.width, self.height)
            return "rgb(128,128,128)"
        
        # Sample mask to determine region
        mask_value = self.mask.getpixel((x, y))
        
        # INDUSTRY STANDARD CONVENTION:
        # Light values (>= 128) = subject, use input image
        # Dark values (< 128) = background, use background image if available
        if mask_value >= 128:
            # Subject region - use input image
            if self.input_image:
                return sample_image_color(self.input_image, x, y, self.width, self.height)
        else:
            # Background region - use background image if provided, else input image
            if self.background_image:
                return sample_image_color(self.background_image, x, y, self.width, self.height)
            elif self.input_image:
                return sample_image_color(self.input_image, x, y, self.width, self.height)
        
        return "rgb(128,128,128)"
    
    def is_position_in_region(self, x: float, y: float, region_id: int) -> bool:
        """
        Check if position belongs to specified region.
        
        Args:
            x, y: Position on canvas
            region_id: Mask pixel value defining region
            
        Returns:
            True if position is in region
        """
        if not self.mask:
            # No mask = all positions in default region
            return region_id == 128
        
        x = max(0, min(self.width - 1, int(x)))
        y = max(0, min(self.height - 1, int(y)))
        
        mask_value = self.mask.getpixel((x, y))
        return mask_value == region_id
    
    def generate_hybrid_artwork(
        self,
        region_assignments: Dict[int, Dict[str, Any]],
        seed: int = 42,
        cascade_fill_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Generate multi-geometry artwork based on region assignments.
        
        Args:
            region_assignments: Dict mapping region IDs to geometry config:
                {
                    region_id: {
                        'geometry': 'poisson_disk',
                        'target_count': 500,
                        'params': {...}
                    }
                }
            seed: Random seed for reproducibility
            cascade_fill_enabled: Apply cascade fill after base generation
            
        Returns:
            Dict with:
            - 'shapes': List of all shapes
            - 'regions': Dict mapping region_id to list of shapes in that region
            - 'metadata': Generation metadata
        """
        if self.verbose:
            print(f"[hybrid_subdivision] Generating hybrid artwork")
            print(f"[hybrid_subdivision] {len(region_assignments)} region assignments")
        
        # Load geometry plugins
        geometries = load_geometry_plugins()
        
        # Track shapes by region for layer grouping
        shapes_by_region = {}  # region_id -> list of shapes
        all_base_shapes = []
        total_target = 0
        
        for region_id, assignment in region_assignments.items():
            geometry_name = assignment['geometry']
            target_count = assignment['target_count']
            params = assignment.get('params', {})
            
            total_target += target_count
            
            if geometry_name not in geometries:
                if self.verbose:
                    print(f"[hybrid_subdivision] Warning: Geometry '{geometry_name}' not found, skipping region {region_id}")
                continue
            
            if self.verbose:
                print(f"[hybrid_subdivision] Region {region_id}: {geometry_name} with {target_count} shapes")
            
            # Generate shapes for this region with cascade disabled (we'll apply globally later)
            region_params = params.copy()
            region_params['cascade_fill_enabled'] = False
            region_params['seed'] = seed + region_id  # Different seed per region
            region_params['verbose'] = self.verbose
            
            try:
                region_shapes = geometries[geometry_name](
                    canvas_size=self.canvas_size,
                    total_points=target_count,
                    input_image=self.input_image,  # Pass input image for initial color sampling
                    **region_params
                )
                
                # Filter shapes: keep only those in this region
                filtered_shapes = []
                for shape in region_shapes:
                    shape_center = self._get_shape_center(shape)
                    if shape_center and self.is_position_in_region(*shape_center, region_id):
                        # Update color based on mask-aware sampling
                        shape['fill'] = self.get_color_for_position(*shape_center)
                        # Add region metadata to shape
                        shape['region_id'] = region_id
                        shape['region_geometry'] = geometry_name
                        filtered_shapes.append(shape)
                
                # Store by region for layer grouping
                shapes_by_region[region_id] = filtered_shapes
                all_base_shapes.extend(filtered_shapes)
                
                if self.verbose:
                    print(f"[hybrid_subdivision] Region {region_id}: Generated {len(region_shapes)} shapes, kept {len(filtered_shapes)} in region")
            
            except Exception as e:
                if self.verbose:
                    print(f"[hybrid_subdivision] Error generating region {region_id}: {e}")
                continue
        
        if self.verbose:
            print(f"[hybrid_subdivision] Total base shapes: {len(all_base_shapes)}")
        
        # Apply cascade fill to entire canvas if enabled
        final_shapes = all_base_shapes
        cascade_shapes = []
        
        if cascade_fill_enabled and len(all_base_shapes) < total_target:
            if self.verbose:
                print(f"[hybrid_subdivision] Applying cascade fill to reach {total_target} shapes")
            
            # Use first region's geometry for cascade shapes (could be smarter)
            first_assignment = list(region_assignments.values())[0]
            cascade_geometry = first_assignment['geometry']
            
            def generate_cascade_shape() -> Dict:
                """Generate small generic shape for cascade fill."""
                rng = random.Random(seed + 10000)
                size = rng.uniform(5, 15)
                return {
                    'type': 'circle',
                    'cx': 0,
                    'cy': 0,
                    'r': int(size),
                    'fill': 'rgb(128,128,128)',
                    'stroke': 'none',
                    'stroke_width': 0,
                    'opacity': 0.7
                }
            
            enhanced_shapes = apply_universal_cascade_fill(
                shapes=all_base_shapes,
                canvas_size=self.canvas_size,
                target_count=total_target,
                shape_generator=generate_cascade_shape,
                seed=seed + 1000,
                verbose=self.verbose
            )
            
            # Update colors for cascade shapes based on mask
            cascade_shapes = enhanced_shapes[len(all_base_shapes):]
            for shape in cascade_shapes:
                center = self._get_shape_center(shape)
                if center:
                    shape['fill'] = self.get_color_for_position(*center)
                    # Determine which region this cascade shape belongs to
                    for region_id in shapes_by_region.keys():
                        if self.is_position_in_region(*center, region_id):
                            shape['region_id'] = region_id
                            shape['region_geometry'] = 'cascade_fill'
                            shapes_by_region[region_id].append(shape)
                            break
            
            final_shapes = enhanced_shapes
            
            if self.verbose:
                print(f"[hybrid_subdivision] Cascade fill added {len(cascade_shapes)} shapes")
        
        if self.verbose:
            print(f"[hybrid_subdivision] Final shape count: {len(final_shapes)}")
        
        # Return structured data for layer grouping
        return {
            'shapes': final_shapes,
            'regions': shapes_by_region,
            'metadata': {
                'total_shapes': len(final_shapes),
                'base_shapes': len(all_base_shapes),
                'cascade_shapes': len(cascade_shapes),
                'regions': list(shapes_by_region.keys()),
                'region_counts': {rid: len(shapes) for rid, shapes in shapes_by_region.items()}
            }
        }
    
    def _get_shape_center(self, shape: Dict) -> Optional[Tuple[float, float]]:
        """Get center point of any shape type."""
        shape_type = shape.get('type', '').lower()
        
        if shape_type == 'circle':
            return (shape.get('cx', 0), shape.get('cy', 0))
        
        elif 'points' in shape and shape['points']:
            points = shape['points']
            cx = sum(p[0] for p in points) / len(points)
            cy = sum(p[1] for p in points) / len(points)
            return (cx, cy)
        
        return None


def create_simple_binary_mask(width: int, height: int, threshold: float = 0.5) -> Image.Image:
    """
    Create a simple binary mask for testing (subject in center).
    
    USES INDUSTRY STANDARD: White = subject, Black = background
    
    Args:
        width, height: Canvas dimensions
        threshold: Radius threshold (0-1) for subject region
        
    Returns:
        PIL Image in L mode
    """
    if not Image:
        return None
    
    mask = Image.new('L', (width, height), 0)  # Black background
    
    # Create circular subject region in center (white)
    center_x, center_y = width // 2, height // 2
    radius = min(width, height) * threshold
    
    for y in range(height):
        for x in range(width):
            dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            if dist < radius:
                mask.putpixel((x, y), 255)  # White subject
    
    return mask


# Testing function
if __name__ == "__main__":
    print("Testing MaskBasedSubdivision...")
    
    if not Image:
        print("PIL not available, cannot run tests")
    else:
        # Create test images
        canvas_size = (800, 600)
        
        # Create dummy input image (gradient)
        input_img = Image.new('RGB', canvas_size)
        for y in range(canvas_size[1]):
            for x in range(canvas_size[0]):
                input_img.putpixel((x, y), (x % 256, y % 256, 128))
        
        # Create simple mask (circle in center) - WHITE = subject
        mask_img = create_simple_binary_mask(*canvas_size, threshold=0.3)
        
        # Test subdivision
        subdivision = MaskBasedSubdivision(
            canvas_size=canvas_size,
            input_image=input_img,
            mask_image=mask_img,
            verbose=True
        )
        
        # Test region assignments with corrected convention
        assignments = {
            255: {  # Subject (white in mask) - CORRECTED
                'geometry': 'rectangles',
                'target_count': 300,
                'params': {}
            },
            0: {  # Background (black in mask) - CORRECTED
                'geometry': 'poisson_disk',
                'target_count': 500,
                'params': {}
            }
        }
        
        print("\nGenerating hybrid artwork...")
        result = subdivision.generate_hybrid_artwork(assignments, seed=42)
        print(f"Generated {result['metadata']['total_shapes']} total shapes")
        print("Test complete!")