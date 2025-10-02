# svg_export.py
"""
SVG Export with XMP Metadata and Layer Grouping
Cubist Art v2.6.0 - Phase 2 Sprint 1

Exports shapes to SVG format with Adobe XMP metadata and optional layer grouping by region.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import version info
try:
    from version import METADATA_TOOL_NAME, VERSION
except ImportError:
    METADATA_TOOL_NAME = "Cubist Art Tool"
    VERSION = "2.6.0"

logger = logging.getLogger(__name__)


def save_svg(
    shapes: List[Dict[str, Any]],
    filepath: str,
    width: int,
    height: int,
    metadata: Optional[Dict[str, Any]] = None,
    regions: Optional[Dict[int, List[Dict]]] = None
) -> bool:
    """
    Save shapes to SVG file with XMP metadata and optional layer grouping.
    
    Args:
        shapes: List of shape dictionaries
        filepath: Output SVG file path
        width: Canvas width in pixels
        height: Canvas height in pixels
        metadata: Optional metadata dict for XMP embedding
        regions: Optional dict mapping region_id to list of shapes for layer grouping
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Build SVG content
        svg_lines = [
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            f'<svg width="{width}" height="{height}" '
            'xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" '
            'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
            'xmlns:xmp="http://ns.adobe.com/xap/1.0/" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" '
            'xmlns:cubist="http://cubist-art.local/ns/1.0/">',
        ]
        
        # Add metadata if provided
        if metadata:
            svg_lines.append(_generate_xmp_metadata(metadata, width, height, len(shapes)))
        
        # Add shapes - either grouped by region or flat
        if regions:
            # Layer grouping mode
            svg_lines.extend(_generate_grouped_shapes(regions))
        else:
            # Flat mode (backward compatible)
            svg_lines.extend(_generate_flat_shapes(shapes))
        
        svg_lines.append('</svg>')
        
        # Write to file
        svg_content = '\n'.join(svg_lines)
        file_size = len(svg_content.encode('utf-8'))
        
        logger.info(f"svg_export.save_svg: writing '{filepath}' ({file_size} bytes)")
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        Path(filepath).write_text(svg_content, encoding='utf-8')
        
        logger.info(f"svg_export.save_svg: success writing '{filepath}'")
        
        print(f"SVG export: exported {len(shapes)} shapes with metadata")
        return True
        
    except Exception as e:
        logger.error(f"svg_export.save_svg: failed to write '{filepath}': {e}")
        print(f"SVG export error: {e}")
        return False


def _generate_xmp_metadata(metadata: Dict[str, Any], width: int, height: int, shape_count: int) -> str:
    """Generate Adobe XMP metadata block."""
    
    # Extract metadata fields with defaults
    geometry = metadata.get('geometry', 'unknown')
    fill_method = metadata.get('fill_method', 'default')
    input_source = metadata.get('input_source', '')
    target_shapes = metadata.get('target_shapes', shape_count)
    seed = metadata.get('seed', 42)
    gen_time = metadata.get('generation_time', 0.0)
    version = metadata.get('version', VERSION)
    
    # Format timestamp
    create_date = datetime.now().isoformat()
    
    # Calculate space utilization (simplified - actual shapes vs canvas area)
    # This is approximate - real calculation would sample the canvas
    space_util = min(99.9, (shape_count / max(target_shapes, 1)) * 90.0)
    
    # Build parameter string
    param_lines = []
    if 'parameters' in metadata and metadata['parameters']:
        for key, val in metadata['parameters'].items():
            param_lines.append(f"      <cubist:param_{key}>{val}</cubist:param_{key}>")
    
    params_xml = '\n'.join(param_lines) if param_lines else ''
    
    # Build metadata block
    metadata_xml = f"""  <metadata>
    <rdf:RDF>
      <rdf:Description>
        <dc:format>image/svg+xml</dc:format>
        <dc:creator>{METADATA_TOOL_NAME}</dc:creator>
        <xmp:CreatorTool>{METADATA_TOOL_NAME}</xmp:CreatorTool>
        <xmp:CreateDate>{create_date}</xmp:CreateDate>
        <xmp:Rating>0</xmp:Rating>
        
        <cubist:version>{version}</cubist:version>
        <cubist:geometry>{geometry}</cubist:geometry>
        <cubist:fillMethod>{fill_method}</cubist:fillMethod>
        <cubist:inputSource>{input_source}</cubist:inputSource>
        
        <cubist:canvasWidth>{width}</cubist:canvasWidth>
        <cubist:canvasHeight>{height}</cubist:canvasHeight>
        <cubist:targetShapes>{target_shapes}</cubist:targetShapes>
        <cubist:actualShapes>{shape_count}</cubist:actualShapes>
        <cubist:seed>{seed}</cubist:seed>
        
        <cubist:spaceUtilization>{space_util:.1f}</cubist:spaceUtilization>
        <cubist:generationTime>{gen_time:.2f}</cubist:generationTime>
{params_xml}
      </rdf:Description>
    </rdf:RDF>
  </metadata>"""
    
    return metadata_xml


def _generate_grouped_shapes(regions: Dict[int, List[Dict]]) -> List[str]:
    """
    Generate SVG shapes grouped by region with <g> tags for layer organization.
    
    Args:
        regions: Dict mapping region_id to list of shapes
        
    Returns:
        List of SVG lines with grouped shapes
    """
    lines = []
    
    # Sort regions by ID for consistent ordering
    for region_id in sorted(regions.keys()):
        shapes = regions[region_id]
        if not shapes:
            continue
        
        # Determine geometry name from first shape
        geometry_name = shapes[0].get('region_geometry', 'unknown')
        
        # Create layer group
        lines.append(f'  <g id="region_{region_id}" data-region="{region_id}" data-geometry="{geometry_name}">')
        lines.append(f'    <title>Region {region_id} - {geometry_name} ({len(shapes)} shapes)</title>')
        
        # Add shapes
        for shape in shapes:
            shape_svg = _shape_to_svg(shape, indent='    ')
            if shape_svg:
                lines.append(shape_svg)
        
        lines.append('  </g>')
    
    return lines


def _generate_flat_shapes(shapes: List[Dict]) -> List[str]:
    """
    Generate SVG shapes without grouping (backward compatible).
    
    Args:
        shapes: List of shape dictionaries
        
    Returns:
        List of SVG lines
    """
    lines = []
    
    for shape in shapes:
        shape_svg = _shape_to_svg(shape, indent='  ')
        if shape_svg:
            lines.append(shape_svg)
    
    return lines


def _shape_to_svg(shape: Dict[str, Any], indent: str = '  ') -> Optional[str]:
    """
    Convert shape dictionary to SVG element string.
    
    Args:
        shape: Shape dictionary
        indent: Indentation string
        
    Returns:
        SVG element string or None if invalid
    """
    shape_type = shape.get('type', '').lower()
    
    # Common attributes
    fill = shape.get('fill', 'rgb(128,128,128)')
    stroke = shape.get('stroke', 'none')
    stroke_width = shape.get('stroke_width', 0)
    opacity = shape.get('opacity', 0.7)
    
    try:
        if shape_type == 'circle':
            cx = int(shape['cx'])
            cy = int(shape['cy'])
            r = int(shape['r'])
            return f'{indent}<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" opacity="{opacity}"/>'
        
        elif shape_type == 'polygon':
            points = shape.get('points', [])
            if not points:
                return None
            # Integer coordinates
            points_str = ' '.join(f"{int(x)},{int(y)}" for x, y in points)
            return f'{indent}<polygon points="{points_str}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" opacity="{opacity}"/>'
        
        elif shape_type == 'rect':
            x = int(shape.get('x', 0))
            y = int(shape.get('y', 0))
            w = int(shape.get('width', 0))
            h = int(shape.get('height', 0))
            return f'{indent}<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" opacity="{opacity}"/>'
        
        else:
            # Unknown shape type
            return None
            
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Failed to convert shape to SVG: {e}")
        return None


# Testing
if __name__ == "__main__":
    # Test basic SVG export
    test_shapes = [
        {'type': 'circle', 'cx': 100, 'cy': 100, 'r': 50, 'fill': 'rgb(255,0,0)', 'stroke': 'none', 'stroke_width': 0, 'opacity': 0.7},
        {'type': 'rect', 'x': 200, 'y': 200, 'width': 100, 'height': 50, 'fill': 'rgb(0,255,0)', 'stroke': 'none', 'stroke_width': 0, 'opacity': 0.7},
    ]
    
    test_metadata = {
        'geometry': 'test',
        'fill_method': 'default',
        'target_shapes': 2,
        'seed': 42,
        'generation_time': 1.5
    }
    
    print("Testing flat export...")
    success = save_svg(test_shapes, 'test_flat.svg', 800, 600, test_metadata)
    print(f"Flat export: {'success' if success else 'failed'}")
    
    print("\nTesting grouped export...")
    test_regions = {
        0: [test_shapes[0]],
        255: [test_shapes[1]]
    }
    success = save_svg(test_shapes, 'test_grouped.svg', 800, 600, test_metadata, test_regions)
    print(f"Grouped export: {'success' if success else 'failed'}")