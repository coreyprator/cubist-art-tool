#!/usr/bin/env python3
"""
Geometry Plugin Loader
Discovers and loads geometry plugins from geometry_plugins/ directory.
"""

import importlib
import sys
from pathlib import Path
from typing import Dict, Callable


def load_geometry_plugins(plugins_dir: str = None) -> Dict[str, Callable]:
    """
    Discover and load all geometry plugins from the plugins directory.
    
    Args:
        plugins_dir: Path to plugins directory (default: ./geometry_plugins)
        
    Returns:
        Dictionary mapping geometry names to their generate() functions
    """
    if plugins_dir is None:
        # Default to geometry_plugins in same directory as this file
        loader_path = Path(__file__).resolve().parent
        plugins_dir = loader_path / "geometry_plugins"
    else:
        plugins_dir = Path(plugins_dir)
    
    if not plugins_dir.exists():
        print(f"Warning: Plugins directory not found: {plugins_dir}")
        return {}
    
    # Add plugins directory to path if not already there
    plugins_dir_str = str(plugins_dir.parent)
    if plugins_dir_str not in sys.path:
        sys.path.insert(0, plugins_dir_str)
    
    geometries = {}
    
    # Discover all .py files in plugins directory
    for plugin_file in plugins_dir.glob("*.py"):
        # Skip __init__.py and private modules
        if plugin_file.name.startswith("_"):
            continue
        
        plugin_name = plugin_file.stem  # filename without .py
        
        try:
            # Import the module
            module = importlib.import_module(f"geometry_plugins.{plugin_name}")
            
            # Look for generate() function
            if hasattr(module, "generate"):
                geometries[plugin_name] = module.generate
                print(f"[geometry_loader] Loaded: {plugin_name}")
            else:
                print(f"[geometry_loader] Warning: {plugin_name} has no generate() function")
        
        except Exception as e:
            print(f"[geometry_loader] Error loading {plugin_name}: {e}")
            continue
    
    if not geometries:
        print(f"[geometry_loader] Warning: No geometry plugins loaded from {plugins_dir}")
    else:
        print(f"[geometry_loader] Successfully loaded {len(geometries)} geometries: {', '.join(geometries.keys())}")
    
    return geometries


def list_available_geometries(plugins_dir: str = None) -> list:
    """
    List all available geometry plugin names.
    
    Args:
        plugins_dir: Path to plugins directory (default: ./geometry_plugins)
        
    Returns:
        List of geometry names
    """
    geometries = load_geometry_plugins(plugins_dir)
    return sorted(geometries.keys())


if __name__ == "__main__":
    # Test the loader
    print("Testing geometry plugin loader...")
    geometries = load_geometry_plugins()
    
    if geometries:
        print(f"\nFound {len(geometries)} geometries:")
        for name in sorted(geometries.keys()):
            print(f"  - {name}")
    else:
        print("\nNo geometries found!")
