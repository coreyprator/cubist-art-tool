@echo off
REM Quick Environment Setup for Cubist Art Project
REM Run this once to set up the local Python environment

echo Setting up Cubist Art Project Environment...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and ensure it's added to your PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating local virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements with auto-detection
if exist "requirements.txt" (
    echo Installing project dependencies from requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install some dependencies
        echo Please check requirements.txt and try again
        pause
        exit /b 1
    )
    echo ✓ Dependencies installed successfully
) else (
    echo Warning: requirements.txt not found
    echo Creating empty requirements.txt for future use...
    echo # Cubist Art Project Dependencies > requirements.txt
    echo # Add your project dependencies here >> requirements.txt
    echo # Example: numpy==1.21.0 >> requirements.txt
)

REM Verify installation
echo.
echo Environment setup complete!
echo Python version: 
python --version
echo.
echo Virtual environment location: %VIRTUAL_ENV%
echo.
echo To activate this environment manually, run:
echo   .venv\Scripts\activate.bat
echo.
echo To launch VS Code with this environment, run:
echo   launch_vscode.bat
echo.
echo To export current environment to requirements.txt:
echo   .venv\Scripts\activate.bat ^&^& pip freeze ^> requirements.txt
echo.
echo Tip: Run the export command regularly to keep requirements.txt updated
echo.

pause
