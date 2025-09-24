# Parameter Corruption Bug Analysis

## Problem Summary
- CLI receives `--points 4000` but plugin sees `total_points=1000`
- Direct plugin call works with 4000 points
- CLI has "SVG export fallback" mechanism activating

## Most Likely Bug Locations

### 1. cubist_cli.py lines 259, 304, 386, 399
These lines show parameter processing. Check for:
```python
# BAD - point limiting:
points = min(args.points, 1000)  # ← BUG HERE

# BAD - fallback with hardcoded limit:
if some_condition:
    points = 1000  # ← BUG HERE
```

### 2. scatter_circles.py plugin
The trace shows scatter_circles logic is involved. Check for:
```python
# BAD - internal point limiting:
def generate(canvas_size, total_points, **kwargs):
    actual_points = min(total_points, 1000)  # ← BUG HERE
```

### 3. SVG Export Fallback
Debug shows "SVG export fallback" - this suggests:
```python
# BAD - fallback reduces points for "performance":
if export_svg:
    points = min(points, 1000)  # ← BUG HERE
```

## Immediate Action Items
1. Search codebase for literal `1000` values
2. Find where `args.points=4000` becomes `total_points=1000`
3. Disable or fix the "SVG export fallback" logic
4. Test CLI with `--points 500` to see if it becomes 500 or still 1000

## Fix Priority
1. **High**: Remove hardcoded 1000 limits in parameter processing
2. **High**: Fix SVG export fallback to preserve user's point count
3. **Medium**: Add parameter validation that warns but doesn't silently change values
