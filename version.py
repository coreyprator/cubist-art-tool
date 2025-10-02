"""
Cubist Art Tool Version Management
Centralized version constant for consistency across all modules
"""

from datetime import datetime

# Version follows semantic versioning: MAJOR.MINOR.PATCH
VERSION_MAJOR = 2
VERSION_MINOR = 6
VERSION_PATCH = 1

# Phase description
PHASE = "Phase 2 Sprint 1"
PHASE_DESCRIPTION = "Hybrid Subdivision & Multi-Geometry"

# Build timestamp (set at import time)
BUILD_TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Full version string
VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
VERSION_FULL = f"v{VERSION} - {PHASE}: {PHASE_DESCRIPTION}"
VERSION_WITH_TIMESTAMP = f"{VERSION_FULL} (built {BUILD_TIMESTAMP})"

# For display in UI
UI_TITLE = f"Cubist Art — Production UI v{VERSION} - {PHASE}"

# For metadata embedding
METADATA_VERSION = VERSION
METADATA_TOOL_NAME = f"Cubist Art Tool v{VERSION}"

def get_version_info():
    """Return version information as dictionary"""
    return {
        "version": VERSION,
        "version_full": VERSION_FULL,
        "version_with_timestamp": VERSION_WITH_TIMESTAMP,
        "major": VERSION_MAJOR,
        "minor": VERSION_MINOR,
        "patch": VERSION_PATCH,
        "phase": PHASE,
        "phase_description": PHASE_DESCRIPTION,
        "build_timestamp": BUILD_TIMESTAMP
    }

if __name__ == "__main__":
    # Test version display
    print(VERSION_FULL)
    print(VERSION_WITH_TIMESTAMP)