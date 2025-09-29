# Cubist Art Tool v2.5.0 - Development Roadmap
## Updated: Sprint 1 Complete - Rectangle Enhancement & File Optimization

## Current Status (v2.5.0 - Phase 1: 50% Complete)

### ✅ Completed This Sprint
- **Rectangle Algorithm**: Coverage-first with bold size variance (0.25x-5.0x)
- **Integer Coordinate Optimization**: Applied across all 5 geometries (~20% file size reduction)
- **SVG Export Enhancement**: Standardized coordinate formatting in svg_export.py
- **Metadata Architecture**: Adobe XMP-compatible structure designed for HASL

### ✅ Previously Completed
- All 5 geometry plugins sample actual pixel colors from input images
- Performance fixes for high point counts (4000+)
- Production-quality gallery UI with thumbnails and clickable links
- Universal cascade fill integration across all 5 geometries
- Side-by-side Default Fill vs Cascade Fill comparison in production UI

---

## Phase 1 Progress Tracker

**Overall: 50% Complete (2 of 4 priorities finished)**

1. ✅ **Cascade Fill** - COMPLETED
2. ✅ **Rectangle Enhancement** - COMPLETED
3. ⏳ **Parameter System** - NEXT SPRINT
4. ⏳ **Size Constraints** - NEXT SPRINT

---

## Validated Technical Discoveries

### Universal Spacing Formula (Circle Geometries)
Successfully validated across Poisson Disk and Scatter Circles:
```python
# Dense coverage (no white space):
min_dist_factor = 0.008
radius_multiplier = 1.0

# Blue noise dots (visible gaps):
min_dist_factor = 0.025
radius_multiplier = 0.25
Visual Effect Progression:

radius < 0.5 × spacing → Scattered, lots of white space
radius = 0.25 × spacing → Blue noise dots with gaps
radius = 0.8 × spacing → Near-touching mosaic
radius ≥ 1.0 × spacing → Complete overlapping coverage

Rectangle Size Variance Discovery
Finding: 20x size range (0.25x to 5.0x average) with power-law distribution creates organic compositions.
Distribution: 70% small (detail) + 20% medium + 10% large (structure)
Result: Complete coverage through intentional overlap vs. systematic gaps from tessellation.
File Size Optimization
Finding: Integer coordinate rounding provides 15-25% file size reduction with no visual quality loss.
Implementation: Centralized in svg_export.py, applies to all geometries automatically.

Priority 2: Parameter System Integration - NEXT SPRINT
Objective
Expose validated spacing/radius controls for circle geometries via production UI sliders.
Circle Geometry Parameters (Poisson Disk & Scatter Circles)
Spacing Density Slider (min_dist_factor)

Range: 0.005 to 0.030
Default: 0.008 (dense) or 0.025 (sparse)
Effect: Lower = denser packing, more shapes

Coverage Ratio Slider (radius_multiplier)

Range: 0.25 to 1.2
Default: 1.0 (complete coverage)
Effect: 0.25 = blue noise dots, 1.0 = overlapping

UI Requirements:

Geometry-specific sliders (show only when geometry selected)
Real-time parameter validation
Visual feedback for parameter effects

Rectangle Parameters (Future)
Size Range Sliders

Minimum Size Multiplier: 0.1 to 1.0
Maximum Size Multiplier: 1.0 to 10.0
Aspect Ratio Variance: 1.0 to 5.0


Priority 3: Metadata & Learning Foundation
SVG Metadata Implementation
Adobe XMP-Compatible Structure (for Adobe Bridge integration):
Standard namespace declarations (W3C/Adobe public specifications):

xmlns:rdf = W3C RDF standard
xmlns:xmp = Adobe XMP public spec
xmlns:dc = Dublin Core metadata standard
xmlns:cubist = Custom Cubist namespace (our original work)

Example metadata structure:
xml<metadata>
  <rdf:RDF>
    <rdf:Description>
      <dc:format>image/svg+xml</dc:format>
      <dc:creator>Cubist Art Tool</dc:creator>
      <xmp:CreatorTool>Cubist Art Tool v2.5.0</xmp:CreatorTool>
      <xmp:CreateDate>2025-09-28T21:33:57</xmp:CreateDate>
      <xmp:Rating>0</xmp:Rating>

      <cubist:version>2.5.0</cubist:version>
      <cubist:geometry>rectangles</cubist:geometry>
      <cubist:fillMethod>default</cubist:fillMethod>
      <cubist:inputSource>path/to/input.jpg</cubist:inputSource>

      <cubist:canvasWidth>3024</cubist:canvasWidth>
      <cubist:canvasHeight>4032</cubist:canvasHeight>
      <cubist:targetShapes>8000</cubist:targetShapes>
      <cubist:actualShapes>8000</cubist:actualShapes>
      <cubist:seed>42</cubist:seed>

      <cubist:spaceUtilization>94.3</cubist:spaceUtilization>
      <cubist:generationTime>4.8</cubist:generationTime>

      <cubist:artisticStyle></cubist:artisticStyle>
      <cubist:visualComplexity>high</cubist:visualComplexity>
    </rdf:Description>
  </rdf:RDF>
</metadata>
Space Utilization Calculation
Accurate Method (sampling-based, accounts for overlaps):
pythondef calculate_space_utilization(shapes, canvas_width, canvas_height, sample_density=100):
    """Returns percentage of canvas with at least one shape (0-100%)."""
    filled = 0
    total = sample_density * sample_density
    step_x, step_y = canvas_width / sample_density, canvas_height / sample_density

    for i in range(sample_density):
        for j in range(sample_density):
            x, y = (i + 0.5) * step_x, (j + 0.5) * step_y
            if point_in_any_shape(x, y, shapes):
                filled += 1

    return (filled / total) * 100.0

Deferred Items
Advanced Space Optimization → Phase 3

95%+ utilization algorithms
Advanced gap detection
Intelligent cascade strategies

Reasoning: Current 90%+ coverage is sufficient for Phase 1. Diminishing returns for additional complexity.
Rectangle Parameter Sliders → Priority 2

Min/max size multiplier controls
Aspect ratio variance slider
Placement strategy options

Reasoning: Complete circle parameters first to establish UI patterns.

Development Sequence
Phase 1 (v2.5.0): Foundation Enhancement - 50% COMPLETE
Timeline: 3-4 weeks total (2 weeks completed)

✅ Cascade Fill (Week 1)
✅ Rectangle Enhancement (Week 2)
⏳ Parameter System Integration (Week 3)
⏳ Size Constraints & Presets (Week 4)

Next Deliverable: Circle parameter sliders in production UI

Phase 2 (v2.6.0): Multi-Geometry & Workflow
Status: Ready after Phase 1
Timeline: 3-4 weeks

Hybrid Subdivision (multi-geometry combinations)
Batch Processing (multi-image with presets)
Rating System (star ratings + metadata)
Adobe Bridge integration validation


Phase 3 (v2.7.0): AI & Advanced Optimization
Status: Architecture ready
Timeline: 4-6 weeks

HASL Framework (parameter correlation analysis)
Parameter Recommendations (AI suggestions)
Advanced Space Optimization (95%+ algorithms)
Performance Optimization (sub-10 second targets)


Phase 4 (v3.0.0+): Advanced Geometries
Status: Foundation-dependent
Timeline: TBD

Success Metrics
Technical Metrics

✅ Shape Count: User-specified counts achieved (75%+ validated)
✅ Space Utilization: 90%+ coverage achieved
✅ Performance: <15 second generation times
✅ File Size: 15-25% reduction via integer coordinates
⏳ Parameter Control: Real-time spacing/coverage control
⏳ User Control: Intuitive slider-based interface

Creative Metrics

✅ Visual Quality: Recognizable source features in geometric interpretation
✅ Coverage: Organic compositions with minimal white space
⏳ Artistic Range: 5+ distinct styles via parameter control
⏳ Consistency: Repeatable results via saved presets

Workflow Metrics

✅ Production UI: Side-by-side fill comparison working
⏳ Learning Curve: 5-minute time-to-first-artwork
⏳ Iteration Speed: <30 second parameter-to-preview cycle
⏳ Metadata Foundation: XMP structure for HASL learning


Technical Environment

Version: v2.5.0 Phase 1 (50% complete)
Branch: handoff-to-claude
Python: .venv virtual environment
UI: Flask production UI (tools/prod_ui.py)
Dependencies: PIL, Flask (requirements.txt)

Working Features

All 5 geometries with cascade fill
Integer coordinate SVG export
Side-by-side fill method comparison
Rectangle coverage-first algorithm
Production-ready gallery UI


Next Sprint Requirements
Parameter UI Testing

All slider additions validated through production UI
Parameter changes produce visually different outputs
Spacing=0.008 + Coverage=1.0 → dense overlapping
Spacing=0.025 + Coverage=0.25 → scattered dots

E2E Validation
bashpython tools\prod_ui.py
# Load image, Points: 1500
# Select: poisson_disk or scatter_circles
# Adjust: Spacing Density and Coverage Ratio sliders
# Expected: Visible parameter effects
# Gallery: output/production/<timestamp>/index.html
Performance Maintenance

Generation times remain <15 seconds
Parameter updates feel responsive
No regressions in existing geometries


Lessons Learned

Coverage Strategy: Random placement with intentional overlap beats tessellation for coverage
Size Variance: 20x range with power-law distribution creates natural compositions
Optimization: Integer coordinates provide significant file size wins with no visual cost
Transparency: Hardcoded opacity=0.7 creates layering effects (future: make configurable)
Centralization: svg_export.py changes apply to all geometries automatically


Status: Ready for Parameter System Integration sprint
Blockers: None
Dependencies: Completed rectangle work provides reference patterns for parameter implementation
