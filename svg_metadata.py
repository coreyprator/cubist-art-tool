#!/usr/bin/env python3
"""
SVG Metadata System
Calculates and embeds Adobe XMP-compatible metadata for HASL learning system.
"""

import math
from datetime import datetime
from typing import Dict, List, Tuple, Any


def calculate_space_utilization(
    shapes: List[Dict],
    canvas_width: int,
    canvas_height: int,
    sample_density: int = 100
) -> float:
    """
    Calculate actual canvas coverage using grid sampling.
    Returns percentage of canvas with at least one shape (0-100%).
    
    Args:
        shapes: List of shape dictionaries
        canvas_width: Canvas width in pixels
        canvas_height: Canvas height in pixels  
        sample_density: Grid density for sampling (default: 100x100)
    
    Returns:
        Percentage of canvas covered by at least one shape
    """
    filled_samples = 0
    total_samples = sample_density * sample_density
    
    step_x = canvas_width / sample_density
    step_y = canvas_height / sample_density
    
    for i in range(sample_density):
        for j in range(sample_density):
            # Sample at cell center
            sample_x = (i + 0.5) * step_x
            sample_y = (j + 0.5) * step_y
            
            if _point_in_any_shape(sample_x, sample_y, shapes):
                filled_samples += 1
    
    return (filled_samples / total_samples) * 100.0


def _point_in_any_shape(x: float, y: float, shapes: List[Dict]) -> bool:
    """Check if point (x,y) is inside any shape."""
    for shape in shapes:
        shape_type = shape.get("type", "").lower()
        
        if shape_type == "circle":
            cx = shape.get("cx", 0)
            cy = shape.get("cy", 0)
            r = shape.get("r", 0)
            if math.sqrt((x - cx)**2 + (y - cy)**2) <= r:
                return True
        
        elif shape_type == "polygon" or "points" in shape:
            if _point_in_polygon(x, y, shape.get("points", [])):
                return True
    
    return False


def _point_in_polygon(x: float, y: float, points: List[Tuple[float, float]]) -> bool:
    """Ray casting algorithm for point-in-polygon test."""
    if len(points) < 3:
        return False
    
    n = len(points)
    inside = False
    
    p1x, p1y = points[0]
    for i in range(1, n + 1):
        p2x, p2y = points[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def calculate_total_area_coverage(
    shapes: List[Dict],
    canvas_width: int,
    canvas_height: int
) -> float:
    """
    Calculate total area of all shapes (includes overlaps).
    Returns percentage of canvas area.
    """
    total_area = 0.0
    canvas_area = canvas_width * canvas_height
    
    for shape in shapes:
        shape_type = shape.get("type", "").lower()
        
        if shape_type == "circle":
            r = shape.get("r", 0)
            total_area += math.pi * r * r
        
        elif shape_type == "polygon" or "points" in shape:
            points = shape.get("points", [])
            total_area += _calculate_polygon_area(points)
    
    return (total_area / canvas_area) * 100.0


def _calculate_polygon_area(points: List[Tuple[float, float]]) -> float:
    """Calculate area using shoelace formula."""
    if len(points) < 3:
        return 0.0
    
    area = 0.0
    for i in range(len(points)):
        j = (i + 1) % len(points)
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    
    return abs(area) / 2.0


def calculate_shape_statistics(shapes: List[Dict]) -> Dict[str, Any]:
    """Calculate shape size statistics."""
    areas = []
    
    for shape in shapes:
        shape_type = shape.get("type", "").lower()
        
        if shape_type == "circle":
            r = shape.get("r", 0)
            areas.append(math.pi * r * r)
        
        elif shape_type == "polygon" or "points" in shape:
            points = shape.get("points", [])
            areas.append(_calculate_polygon_area(points))
    
    if not areas:
        return {
            "min": 0,
            "max": 0,
            "median": 0,
            "average": 0
        }
    
    areas.sort()
    
    return {
        "min": int(round(areas[0])),
        "max": int(round(areas[-1])),
        "median": int(round(areas[len(areas) // 2])),
        "average": int(round(sum(areas) / len(areas)))
    }


def generate_xmp_metadata(
    geometry: str,
    fill_method: str,
    input_source: str,
    canvas_width: int,
    canvas_height: int,
    target_shapes: int,
    actual_shapes: int,
    seed: int,
    shapes: List[Dict],
    generation_time: float,
    parameters: Dict[str, float] = None
) -> str:
    """
    Generate Adobe XMP-compatible metadata XML.
    
    Returns:
        XML metadata string for embedding in SVG
    """
    # Calculate metrics
    space_util = calculate_space_utilization(shapes, canvas_width, canvas_height)
    total_coverage = calculate_total_area_coverage(shapes, canvas_width, canvas_height)
    shape_stats = calculate_shape_statistics(shapes)
    
    # Prepare parameters string
    params_xml = ""
    if parameters:
        for param_name, param_value in parameters.items():
            params_xml += f'      <cubist:{param_name}>{param_value}</cubist:{param_name}>\n'
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    metadata = f"""  <metadata>
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
             xmlns:dc="http://purl.org/dc/elements/1.1/"
             xmlns:xmp="http://ns.adobe.com/xap/1.0/"
             xmlns:cubist="http://cubist-art.local/schema/1.0/">
      
      <!-- Dublin Core Basic Metadata -->
      <rdf:Description rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:creator>Cubist Art Tool</dc:creator>
        <dc:title>{geometry} - {fill_method} fill</dc:title>
      </rdf:Description>
      
      <!-- XMP Basic (Adobe Bridge Compatible) -->
      <rdf:Description rdf:about="">
        <xmp:CreatorTool>Cubist Art Tool v2.5.0</xmp:CreatorTool>
        <xmp:CreateDate>{timestamp}</xmp:CreateDate>
        <xmp:Rating>0</xmp:Rating>
      </rdf:Description>
      
      <!-- Cubist Generation Metadata -->
      <rdf:Description rdf:about="">
        <!-- Application Info -->
        <cubist:version>2.5.0</cubist:version>
        <cubist:geometry>{geometry}</cubist:geometry>
        <cubist:fillMethod>{fill_method}</cubist:fillMethod>
        
        <!-- Source -->
        <cubist:inputSource>{input_source}</cubist:inputSource>
        
        <!-- Canvas Properties -->
        <cubist:canvasWidth>{canvas_width}</cubist:canvasWidth>
        <cubist:canvasHeight>{canvas_height}</cubist:canvasHeight>
        <cubist:canvasArea>{canvas_width * canvas_height}</cubist:canvasArea>
        
        <!-- Generation Parameters -->
        <cubist:targetShapes>{target_shapes}</cubist:targetShapes>
        <cubist:actualShapes>{actual_shapes}</cubist:actualShapes>
        <cubist:seed>{seed}</cubist:seed>
        
        <!-- Geometry-Specific Parameters -->
{params_xml}        
        <!-- Quality Metrics -->
        <cubist:spaceUtilization>{space_util:.1f}</cubist:spaceUtilization>
        <cubist:totalAreaCoverage>{total_coverage:.1f}</cubist:totalAreaCoverage>
        <cubist:averageShapeArea>{shape_stats['average']}</cubist:averageShapeArea>
        <cubist:minShapeArea>{shape_stats['min']}</cubist:minShapeArea>
        <cubist:maxShapeArea>{shape_stats['max']}</cubist:maxShapeArea>
        <cubist:medianShapeArea>{shape_stats['median']}</cubist:medianShapeArea>
        <cubist:generationTime>{generation_time:.2f}</cubist:generationTime>
        
        <!-- HASL Learning Fields -->
        <cubist:artisticStyle></cubist:artisticStyle>
        <cubist:visualComplexity></cubist:visualComplexity>
      </rdf:Description>
    </rdf:RDF>
  </metadata>
"""
    return metadata
