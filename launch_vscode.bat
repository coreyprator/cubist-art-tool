@echo off
REM Cubist Art Project - VS Code Launcher with Local .venv
REM This script ensures the project uses its own virtual environment

echo Starting Cubist Art Project with local .venv...

REM Check if .venv exists, create it if it doesn't
if not exist ".venv" (
    echo Creating local virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Make sure Python is installed and available in PATH
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    REM Check if .venv is properly set up (has python.exe)
    if not exist ".venv\Scripts\python.exe" (
        echo ERROR: Virtual environment exists but is incomplete
        echo Missing .venv\Scripts\python.exe - environment may be corrupted
        echo Please delete .venv folder and run setup_env.bat
        pause
        exit /b 1
    )
    echo ✓ Virtual environment found and verified
)

REM Activate the local virtual environment
echo Activating local virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install/update requirements if requirements.txt exists
if exist "requirements.txt" (
    echo Checking and installing/updating packages from requirements.txt...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Warning: Some packages failed to install
        echo You may need to update requirements.txt or check package availability
    ) else (
        echo ✓ All dependencies installed successfully
    )
) else (
    echo No requirements.txt found - skipping package installation
)

REM Launch VS Code in current directory
echo Launching VS Code with project environment...
code .

REM Keep the window open briefly to show any messages
timeout /t 2 /nobreak >nul

echo VS Code launched. You can close this window.
