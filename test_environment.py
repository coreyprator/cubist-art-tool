"""
Environment Verification Test
This script verifies that the local .venv environment is working correctly.
"""

import sys
import os
from pathlib import Path
from cubist_logger import logger

def test_environment():
    """Test that the environment is set up correctly."""
    logger.info("test_environment() ENTRY: Starting environment verification")
    print("Environment Verification Test")
    print("=" * 50)
    
    # Check Python executable location
    python_exe = sys.executable
    print(f"Python executable: {python_exe}")
    logger.info(f"Python executable: {python_exe}")
    
    # Check if we're in a virtual environment
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        print(f"Virtual environment: {venv_path}")
        logger.info(f"Virtual environment active: {venv_path}")
    else:
        print("Warning: VIRTUAL_ENV not set (may not be activated)")
        logger.warning("VIRTUAL_ENV not set - may not be activated")
    
    # Check if the Python executable is in the project .venv
    project_root = Path(__file__).parent
    expected_venv = project_root / ".venv"
    
    if str(expected_venv) in python_exe:
        print("✓ Using project-specific virtual environment")
    else:
        print("⚠ Warning: Not using project .venv environment")
        print(f"  Expected: {expected_venv}")
        print(f"  Actual: {python_exe}")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check key packages
    packages_to_check = [
        'numpy', 'cv2', 'scipy', 'matplotlib', 'PIL'
    ]
    
    print("\nPackage availability:")
    for package in packages_to_check:
        try:
            if package == 'cv2':
                import cv2
                print(f"✓ OpenCV: {cv2.__version__}")
            elif package == 'PIL':
                from PIL import Image
                print(f"✓ Pillow (PIL): Available")
            else:
                module = __import__(package)
                version = getattr(module, '__version__', 'Unknown')
                print(f"✓ {package}: {version}")
        except ImportError:
            print(f"✗ {package}: Not installed")
    
    # Check project structure
    print("\nProject structure check:")
    required_files = [
        'cubist_core_logic.py',
        'requirements.txt',
        '.vscode/settings.json',
        'setup_env.bat',
        'launch_vscode.bat'
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
            logger.info(f"Required file found: {file_path}")
        else:
            print(f"✗ {file_path} (missing)")
            logger.warning(f"Required file missing: {file_path}")

if __name__ == "__main__":
    logger.info("test_environment.py started")
    test_environment()
    logger.info("test_environment.py completed")    
    print("\nEnvironment test complete!")

if __name__ == "__main__":
    test_environment()
