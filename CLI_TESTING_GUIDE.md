# Cubist Art CLI Testing Guide

## 🚀 Quick Start

### Option 1: Interactive Quick Test (Easiest)
```bash
quick_test.bat
```
This launches an interactive menu where you can choose:
1. Run all tests (all geometries, cascade on/off)
2. Test specific geometry mode
3. Custom test with additional options

### Option 2: Command Line Interface
```bash
# Test all geometries with both cascade fill on/off
python test_cli.py --run_all_tests --input input/your_input_image.jpg

# Test specific geometry mode
python test_cli.py --input input/your_input_image.jpg --geometry delaunay --cascade_fill true
python test_cli.py --input input/your_input_image.jpg --geometry voronoi --cascade_fill false
python test_cli.py --input input/your_input_image.jpg --geometry rectangles --cascade_fill true
```

### Option 3: VS Code Tasks
1. Press `Ctrl+Shift+P`
2. Type "Tasks: Run Task"
3. Choose:
   - **"Test All Geometries (CLI)"** - Runs comprehensive test
   - **"Quick Test Runner"** - Interactive batch script

## 📋 CLI Command Reference

### Basic Usage
```bash
python test_cli.py --input INPUT_IMAGE [options]
```

### Required Arguments
- `--input`, `-i`: Path to input image file

### Test Mode Options
- `--run_all_tests`: Run all geometry modes with both cascade fill on/off
- `--geometry`, `-g`: Single geometry mode (`delaunay`, `voronoi`, `rectangles`)
- `--cascade_fill`, `-c`: Use cascade fill (`true`/`false`)

### Configuration Options
- `--output`, `-o`: Output directory (default: `output`)
- `--mask`, `-m`: Path to mask image file (optional)
- `--points`, `-p`: Number of points to sample (default: 1000)
- `--step_frames`: Save step frames for animation (cascade fill only)
- `--quiet`, `-q`: Reduce output verbosity

## 🎯 Example Commands

### Test All Combinations
```bash
# Test everything with default settings
python test_cli.py --run_all_tests --input input/your_input_image.jpg

# Test with custom point count
python test_cli.py --run_all_tests --input input/your_input_image.jpg --points 2000

# Test with step frames (for animation)
python test_cli.py --run_all_tests --input input/your_input_image.jpg --step_frames

# Test with mask
python test_cli.py --run_all_tests --input input/your_input_image.jpg --mask input/edge_mask.png
```

### Test Individual Geometries
```bash
# Delaunay triangulation with cascade fill
python test_cli.py --input input/your_input_image.jpg --geometry delaunay --cascade_fill true

# Voronoi diagram without cascade fill
python test_cli.py --input input/your_input_image.jpg --geometry voronoi --cascade_fill false

# Rectangles with cascade fill and step frames
python test_cli.py --input input/your_input_image.jpg --geometry rectangles --cascade_fill true --step_frames
```

### Advanced Usage
```bash
# High point count with custom output directory
python test_cli.py --input input/your_input_image.jpg --geometry delaunay --cascade_fill true --points 5000 --output high_res_output

# Quiet mode (minimal output)
python test_cli.py --run_all_tests --input input/your_input_image.jpg --quiet

# With mask and step frames
python test_cli.py --input input/your_input_image.jpg --geometry voronoi --cascade_fill true --mask input/mask.png --step_frames
```

## 📁 Output Structure

When you run the CLI tests, outputs are saved with descriptive filenames:

```
output/
├── your_input_image_01000pts_delaunay_regular_20250731_143022.png
├── your_input_image_01000pts_delaunay_cascade_20250731_143045.png
├── your_input_image_01000pts_voronoi_regular_20250731_143112.png
├── your_input_image_01000pts_voronoi_cascade_20250731_143134.png
├── your_input_image_01000pts_rectangles_regular_20250731_143156.png
└── your_input_image_01000pts_rectangles_cascade_20250731_143218.png
```

**Filename Format:** `{input_name}_{points}pts_{geometry}_{cascade_flag}_{timestamp}.png`

## 🎬 Step Frames (Animation)

When using `--step_frames` with cascade fill, intermediate frames are saved:

```
output/
├── cascade_step_0000_delaunay.png
├── cascade_step_0010_delaunay.png
├── cascade_step_0020_delaunay.png
└── ... (every 10th step)
```

## 🔍 Test Results Summary

The CLI provides a comprehensive summary after running tests:

```
📊 TEST SUMMARY
================================================================================
✅ Successful: 6/6
❌ Failed: 0/6

📁 Generated Files:
  •    delaunay | regular | your_input_image_01000pts_delaunay_regular_20250731_143022.png
  •    delaunay | cascade | your_input_image_01000pts_delaunay_cascade_20250731_143045.png
  •     voronoi | regular | your_input_image_01000pts_voronoi_regular_20250731_143112.png
  •     voronoi | cascade | your_input_image_01000pts_voronoi_cascade_20250731_143134.png
  •  rectangles | regular | your_input_image_01000pts_rectangles_regular_20250731_143156.png
  •  rectangles | cascade | your_input_image_01000pts_rectangles_cascade_20250731_143218.png

💡 Tip: Compare the 'cascade' vs 'regular' outputs to see the difference!
```

## 🛠️ Environment Setup

Make sure your environment is set up before running tests:

```bash
# First time setup
setup_env.bat

# Launch with environment
launch_vscode.bat

# Or activate manually
.venv\Scripts\activate.bat
```

## 🎨 Comparing Results

### Regular vs Cascade Fill

**Regular Fill:**
- Uses traditional tessellation (Delaunay triangulation, Voronoi diagrams, grid rectangles)
- Uniform distribution of shapes
- Consistent with original algorithm

**Cascade Fill:**
- Places non-overlapping shapes of decreasing size
- Organic, artistic appearance
- Large shapes filled first, then progressively smaller ones
- Creates unique texture and visual hierarchy

### Geometry Modes

**Delaunay:**
- Triangular shapes based on Delaunay triangulation
- Sharp, angular aesthetic
- Good for geometric art styles

**Voronoi:**
- Polygonal cells based on Voronoi diagrams
- Organic, cellular appearance
- Natural-looking boundaries

**Rectangles:**
- Grid-based rectangular shapes
- Clean, structured look
- Good for pixelated or mosaic effects

## 🚨 Troubleshooting

### Common Issues

**"Could not import cubist_core_logic.py"**
- Make sure you're running from the project root directory
- Ensure the virtual environment is activated

**"Input file not found"**
- Check the file path is correct
- Make sure the image file exists

**"Virtual environment not found"**
- Run `setup_env.bat` first
- Make sure `.venv` directory exists and is properly set up

### Input Requirements

- **Supported formats:** `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`
- **Recommended:** RGB or RGBA images
- **Size:** Any size (larger images take longer to process)

---

## Option 4: SVG Export (`--export-svg`)

You can export SVG files for any geometry mode using the `--export-svg` flag.

**Usage:**
```
python main.py --geometry delaunay --export-svg
```

**Behavior:**
- Exports an SVG file alongside PNG output.
- SVG includes layers/groups, optional mask placeholder, and metadata (geometry, cascade, points).
- Compatible with Adobe Illustrator.

**Tips:**
- Use the SVG in vector editors for further editing.
- Mask placeholder can be used for advanced compositing.

## 🎉 Ready to Test!

Choose your preferred method:
1. **Interactive:** `quick_test.bat`
2. **Command line:** `python test_cli.py --run_all_tests --input your_image.jpg`
3. **VS Code:** Ctrl+Shift+P → Tasks → "Test All Geometries (CLI)"

Happy testing! 🎨
