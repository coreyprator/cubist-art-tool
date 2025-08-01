@echo off
REM Export Current Environment to requirements.txt
REM Run this after installing new packages to keep requirements.txt updated

echo Exporting Python environment to requirements.txt...

REM Check if .venv exists and is properly set up
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found or incomplete
    echo Please run setup_env.bat first to create the environment
    pause
    exit /b 1
)

REM Activate the local virtual environment
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✓ Virtual environment activated

REM Backup existing requirements.txt if it exists
if exist "requirements.txt" (
    echo Creating backup of existing requirements.txt...
    copy requirements.txt requirements.txt.backup >nul
    echo ✓ Backup created as requirements.txt.backup
)

REM Export current environment
echo Exporting installed packages...
python -m pip freeze > requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to export package list
    if exist "requirements.txt.backup" (
        echo Restoring backup...
        copy requirements.txt.backup requirements.txt >nul
    )
    pause
    exit /b 1
)

REM Show what was exported
echo.
echo ✅ Successfully exported environment to requirements.txt
echo.
echo Current packages:
python -m pip list --format=columns
echo.
echo Requirements.txt contents:
type requirements.txt
echo.
echo Tip: Commit this requirements.txt to version control
echo      so other developers can recreate the exact environment
echo.

pause
