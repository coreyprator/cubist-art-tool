# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: ENVIRONMENT_SETUP.md
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:27+02:00
# === CUBIST STAMP END ===
# Environment Setup Guide

## Project-Specific Python Environment

This project uses a local virtual environment (`.venv`) to ensure package isolation and reproducibility.

## Quick Start

### Option 1: Automated Setup (Recommended)
1. Run `setup_env.bat` to create and configure the environment (auto-installs from requirements.txt)
2. Run `launch_vscode.bat` to launch VS Code with the proper environment (includes validation checks)
3. Use `run_tests.bat` for comprehensive pytest-based testing
4. Use `export_requirements.bat` to update requirements.txt after installing new packages

### Option 2: Manual Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate environment (Windows)
.venv\Scripts\activate.bat

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Launch VS Code
code .
```

### Option 3: PowerShell Users
```powershell
# You may need to set execution policy first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run:
.\launch_vscode.ps1
```

## Environment Structure

```
cubist_art/
├── .venv/                     # Local Python virtual environment
│   ├── Scripts/
│   │   ├── python.exe        # Project-specific Python interpreter
│   │   ├── activate.bat      # Environment activation script
│   │   └── ...
│   └── Lib/                  # Project-specific packages
├── .vscode/
│   ├── settings.json         # VS Code configuration (points to .venv)
│   ├── tasks.json           # Build and test tasks
│   └── launch.json          # Debug configurations
├── requirements.txt          # Project dependencies (auto-managed)
├── setup_env.bat            # Environment setup script
├── launch_vscode.bat        # VS Code launcher with environment
├── launch_vscode.ps1        # PowerShell version of launcher
├── run_tests.bat           # Pytest-based test runner
├── export_requirements.bat  # Export environment to requirements.txt
└── test_environment.py      # Environment verification script
```

## Key Benefits

✅ **Package Isolation**: Each project has its own dependencies
✅ **Reproducibility**: Same environment across different machines
✅ **VS Code Integration**: Automatic interpreter detection
✅ **No Global Conflicts**: Avoid issues with system Python packages

## VS Code Configuration

The `.vscode/settings.json` automatically configures:
- Python interpreter path to `.venv\Scripts\python.exe`
- Terminal environment activation
- Testing configuration for pytest
- Linting with flake8
- File exclusions for Python cache files

## Troubleshooting

### "Python not found"
Ensure Python 3.8+ is installed and added to your system PATH.

### "Cannot activate environment"
- For batch files: Ensure you're running from the project root directory
- For PowerShell: You may need to set the execution policy (see Option 3 above)

### "VS Code not using correct Python"
1. Open VS Code in the project folder
2. Press `Ctrl+Shift+P` and type "Python: Select Interpreter"
3. Choose the interpreter from `.venv\Scripts\python.exe`

### Package Installation Issues
Make sure you've activated the virtual environment before installing packages:
```bash
.venv\Scripts\activate.bat
pip install package_name
```

## Removing Old Global Environment

If you previously used a global environment at `C:\Users\Owner\venv`, you can safely:
1. Delete or rename that folder
2. Update any shortcuts or scripts that referenced it
3. Use the project-specific environment instead

## Development Workflow

1. **Starting work**: Run `launch_vscode.bat` or activate `.venv` manually
2. **Installing packages**: Always activate `.venv` first, then `pip install`
3. **Running tests**: Use `run_tests.bat` for comprehensive pytest testing
4. **Exporting dependencies**: Run `export_requirements.bat` after installing new packages
5. **Regular maintenance**: Export requirements.txt periodically to keep it updated

### Key Scripts:
- `setup_env.bat` - Initial environment setup with auto-requirements detection
- `launch_vscode.bat` - Launch VS Code with environment validation and auto-setup
- `run_tests.bat` - Run all tests using pytest with comprehensive options
- `export_requirements.bat` - Export current environment to requirements.txt with backup

# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:27+02:00
# === CUBIST FOOTER STAMP END ===
