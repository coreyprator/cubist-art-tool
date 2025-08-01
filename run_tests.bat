@echo off
REM Pytest Runner for Cubist Art Project
REM Automatically discovers and runs all tests using pytest

echo Running Cubist Art Tests with pytest...

REM Check if .venv exists and is properly set up
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found or incomplete
    echo Please run setup_env.bat first to create the environment
    pause
    exit /b 1
)

REM Activate the local virtual environment
call .venv\Scripts\activate.bat
echo ✓ Activated local virtual environment

REM Check if pytest is installed
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo Installing pytest...
    python -m pip install pytest pytest-cov
    if errorlevel 1 (
        echo ERROR: Failed to install pytest
        pause
        exit /b 1
    )
)

REM Run pytest with comprehensive options
echo.
echo Running pytest with test discovery...
echo ========================================

REM Run tests with various options based on what's available
if exist "tests\" (
    echo Found tests/ directory - running pytest on tests/
    python -m pytest tests/ -v --tb=short --color=yes
    set TEST_EXIT_CODE=%ERRORLEVEL%
) else (
    echo No tests/ directory found - checking for test_*.py files in root
)

REM Also run any test_*.py files in the root directory
echo.
echo Checking for individual test files...
for %%f in (test_*.py) do (
    if exist "%%f" (
        echo Running %%f...
        python -m pytest "%%f" -v --tb=short --color=yes
        if errorlevel 1 set TEST_EXIT_CODE=1
    )
)

REM Check if any tests were found at all
python -c "import os, glob; tests = glob.glob('test_*.py') + glob.glob('tests/test_*.py'); print('No test files found!') if not tests else print(f'Test discovery complete - found {len(tests)} test files')"

echo.
echo ========================================
if defined TEST_EXIT_CODE (
    if %TEST_EXIT_CODE% neq 0 (
        echo ❌ Some tests failed
    ) else (
        echo ✅ All tests passed
    )
) else (
    echo ✅ Test run complete
)

echo.
echo Tip: To run tests with coverage report, use:
echo   python -m pytest --cov=. --cov-report=html
echo.
pause
