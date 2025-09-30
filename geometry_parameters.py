# geometry_parameters.py
"""
Central parameter registry for all geometry plugins.
Defines UI controls, validation ranges, and default values for each geometry type.
"""

from typing import Dict, Any, List

# Parameter registry structure:
# {
#   "geometry_name": {
#     "param_name": {
#       "min": float,
#       "max": float, 
#       "default": float,
#       "step": float,
#       "label": str,
#       "description": str
#     }
#   }
# }

GEOMETRY_PARAMETERS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "poisson_disk": {
        "min_dist_factor": {
            "min": 0.005,
            "max": 0.030,
            "default": 0.025,
            "step": 0.001,
            "label": "Spacing Density",
            "description": "Controls point spacing (lower = denser packing)"
        },
        "radius_multiplier": {
            "min": 0.25,
            "max": 1.2,
            "default": 1.0,
            "step": 0.05,
            "label": "Coverage Ratio",
            "description": "Circle size relative to spacing (1.0 = overlapping, 0.25 = dots with gaps)"
        },
        "cascade_intensity": {
            "min": 0.1,
            "max": 1.0,
            "default": 0.8,
            "step": 0.05,
            "label": "Cascade Intensity",
            "description": "Gap-fill aggressiveness (cascade fill only)"
        },
        "opacity": {
            "min": 0.1,
            "max": 1.0,
            "default": 0.7,
            "step": 0.05,
            "label": "Shape Opacity",
            "description": "Transparency (1.0 = opaque, 0.1 = very transparent)"
        }
    },
    
    "scatter_circles": {
        "min_dist_factor": {
            "min": 0.005,
            "max": 0.030,
            "default": 0.008,
            "step": 0.001,
            "label": "Spacing Density",
            "description": "Controls point spacing (lower = denser packing)"
        },
        "radius_multiplier": {
            "min": 0.25,
            "max": 1.2,
            "default": 1.0,
            "step": 0.05,
            "label": "Coverage Ratio",
            "description": "Circle size relative to spacing (1.0 = overlapping, 0.25 = dots with gaps)"
        },
        "jitter": {
            "min": 0.0,
            "max": 1.0,
            "default": 0.25,
            "step": 0.05,
            "label": "Position Jitter",
            "description": "Random position variation (0 = grid, 1 = high randomness)"
        },
        "cascade_intensity": {
            "min": 0.1,
            "max": 1.0,
            "default": 0.8,
            "step": 0.05,
            "label": "Cascade Intensity",
            "description": "Gap-fill aggressiveness (cascade fill only)"
        },
        "opacity": {
            "min": 0.1,
            "max": 1.0,
            "default": 0.7,
            "step": 0.05,
            "label": "Shape Opacity",
            "description": "Transparency (1.0 = opaque, 0.1 = very transparent)"
        }
    },
    
    "rectangles": {
        "min_size_multiplier": {
            "min": 0.1,
            "max": 1.0,
            "default": 0.25,
            "step": 0.05,
            "label": "Min Size Multiplier",
            "description": "Smallest rectangle size as fraction of average"
        },
        "max_size_multiplier": {
            "min": 1.0,
            "max": 10.0,
            "default": 5.0,
            "step": 0.5,
            "label": "Max Size Multiplier",
            "description": "Largest rectangle size as fraction of average"
        },
        "aspect_ratio_variance": {
            "min": 1.0,
            "max": 10.0,
            "default": 4.0,
            "step": 0.5,
            "label": "Aspect Ratio Variance",
            "description": "Width/height variation (1.0 = square, 10.0 = extreme)"
        },
        "overlap_tolerance": {
            "min": -10.0,
            "max": 0.0,
            "default": -3.0,
            "step": 0.5,
            "label": "Overlap Tolerance",
            "description": "Collision detection strictness (0 = strict, -10 = loose)"
        },
        "cascade_intensity": {
            "min": 0.1,
            "max": 1.0,
            "default": 0.8,
            "step": 0.05,
            "label": "Cascade Intensity",
            "description": "Gap-fill aggressiveness (cascade fill only)"
        },
        "opacity": {
            "min": 0.1,
            "max": 1.0,
            "default": 0.7,
            "step": 0.05,
            "label": "Shape Opacity",
            "description": "Transparency (1.0 = opaque, 0.1 = very transparent)"
        }
    },
    
    # Placeholder for future geometries
    "delaunay": {
        "cascade_intensity": {
            "min": 0.1,
            "max": 1.0,
            "default": 0.8,
            "step": 0.05,
            "label": "Cascade Intensity",
            "description": "Gap-fill aggressiveness (cascade fill only)"
        },
        "opacity": {
            "min": 0.1,
            "max": 1.0,
            "default": 0.7,
            "step": 0.05,
            "label": "Shape Opacity",
            "description": "Transparency (1.0 = opaque, 0.1 = very transparent)"
        }
    },
    
    "voronoi": {
        "cascade_intensity": {
            "min": 0.1,
            "max": 1.0,
            "default": 0.8,
            "step": 0.05,
            "label": "Cascade Intensity",
            "description": "Gap-fill aggressiveness (cascade fill only)"
        },
        "opacity": {
            "min": 0.1,
            "max": 1.0,
            "default": 0.7,
            "step": 0.05,
            "label": "Shape Opacity",
            "description": "Transparency (1.0 = opaque, 0.1 = very transparent)"
        }
    }
}


def get_geometry_parameters(geometry: str) -> Dict[str, Dict[str, Any]]:
    """Get parameter definitions for a specific geometry."""
    return GEOMETRY_PARAMETERS.get(geometry, {})


def get_parameter_default(geometry: str, param_name: str) -> Any:
    """Get default value for a specific parameter."""
    geom_params = GEOMETRY_PARAMETERS.get(geometry, {})
    param_def = geom_params.get(param_name, {})
    return param_def.get("default", None)


def validate_parameter(geometry: str, param_name: str, value: Any) -> tuple[bool, float, str]:
    """
    Validate a parameter value against its defined constraints.
    
    Returns:
        (is_valid, clamped_value, error_message)
    """
    geom_params = GEOMETRY_PARAMETERS.get(geometry, {})
    if param_name not in geom_params:
        return True, value, ""  # Unknown parameter, pass through
    
    param_def = geom_params[param_name]
    min_val = param_def["min"]
    max_val = param_def["max"]
    
    try:
        float_val = float(value)
    except (ValueError, TypeError):
        return False, param_def["default"], f"Invalid number: {value}"
    
    if float_val < min_val:
        return False, min_val, f"Value {float_val} below minimum {min_val}"
    
    if float_val > max_val:
        return False, max_val, f"Value {float_val} above maximum {max_val}"
    
    return True, float_val, ""


def get_all_geometries() -> List[str]:
    """Get list of all registered geometries."""
    return list(GEOMETRY_PARAMETERS.keys())


def get_factory_defaults(geometry: str) -> Dict[str, float]:
    """Get factory default values for all parameters of a geometry."""
    geom_params = GEOMETRY_PARAMETERS.get(geometry, {})
    return {
        param_name: param_def["default"]
        for param_name, param_def in geom_params.items()
    }
