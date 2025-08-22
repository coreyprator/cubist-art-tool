@echo off
REM Quick Test Runner for Cubist Art Generator
REM Tests all geometry modes with cascade fill on/off

echo 🎨 Cubist Art Generator - Quick Test Runner
echo ============================================

REM Check if .venv exists and is properly set up
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found or incomplete
    echo Please run setup_env.bat first to create the environment
    pause
    exit /b 1
)

REM Activate the local virtual environment
call .venv\Scripts\activate.bat
echo ✓ Virtual environment activated

REM Check for input image
if not exist "input\your_input_image.jpg" (
    echo ⚠ Warning: Default input image not found at input\your_input_image.jpg
    echo You can specify a different input with: --input path\to\your\image.jpg
    echo.
)

echo.
echo Available test options:
echo 1. Run all tests (all geometries, cascade on/off)
echo 2. Test specific geometry mode
echo 3. Custom test with options
echo.

set /p choice="Enter your choice (1-3) or press Enter for option 1: "

if "%choice%"=="" set choice=1
if "%choice%"=="1" goto run_all_tests
if "%choice%"=="2" goto specific_test
if "%choice%"=="3" goto custom_test

:run_all_tests
echo.
echo 🚀 Running all tests...
if exist "input\your_input_image.jpg" (
    python test_cli.py --run_all_tests --input input\your_input_image.jpg
) else (
    echo Please specify input image path:
    set /p input_path="Input image path: "
    python test_cli.py --run_all_tests --input "%input_path%"
)
goto end

:specific_test
echo.
echo Available geometry modes:
echo 1. delaunay
echo 2. voronoi
echo 3. rectangles
echo.
set /p geo_choice="Choose geometry (1-3): "

if "%geo_choice%"=="1" set geometry=delaunay
if "%geo_choice%"=="2" set geometry=voronoi
if "%geo_choice%"=="3" set geometry=rectangles

echo.
echo Cascade fill options:
echo 1. On (true)
echo 2. Off (false)
echo.
set /p cascade_choice="Choose cascade fill (1-2): "

if "%cascade_choice%"=="1" set cascade=true
if "%cascade_choice%"=="2" set cascade=false

echo.
echo Running test: %geometry% with cascade fill %cascade%
if exist "input\your_input_image.jpg" (
    python test_cli.py --input input\your_input_image.jpg --geometry %geometry% --cascade_fill %cascade%
) else (
    echo Please specify input image path:
    set /p input_path="Input image path: "
    python test_cli.py --input "%input_path%" --geometry %geometry% --cascade_fill %cascade%
)
goto end

:custom_test
echo.
echo Custom test mode - you can add additional parameters
echo Example: --points 2000 --step_frames --mask input\mask.png
echo.
set /p custom_args="Enter additional arguments: "

if exist "input\your_input_image.jpg" (
    python test_cli.py --run_all_tests --input input\your_input_image.jpg %custom_args%
) else (
    echo Please specify input image path:
    set /p input_path="Input image path: "
    python test_cli.py --run_all_tests --input "%input_path%" %custom_args%
)
goto end

:end
echo.
echo 🎉 Test complete! Check the output\ directory for generated images.
echo.
echo Tip: Compare the 'cascade' vs 'regular' versions to see the differences!
echo.
pause
