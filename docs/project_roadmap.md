**File 2: `docs/project_roadmap.md`**
```markdown
# Cubist Art Tool - Project Roadmap
**Current Version**: v2.6.1  
**Last Updated**: 2025-10-02  
**Branch**: phase2-multi-geometry

---

## Phase 1 (v2.5.0) - Foundation ✅ COMPLETE

### Deliverables
- ✅ Universal cascade fill (5 geometries)
- ✅ Rectangle coverage algorithm
- ✅ Integer coordinate optimization (20% file size reduction)
- ✅ XMP metadata system
- ✅ Parameter UI with sliders
- ✅ Plugin discovery system

### Metrics
- Sub-15 second generation
- 90%+ canvas coverage
- Production-ready gallery

---

## Phase 2 (v2.6.x) - Multi-Geometry & Workflow

### Sprint 1 (v2.6.1) ✅ COMPLETE

**Duration**: 3 weeks  
**Deliverables**:
1. ✅ Hybrid subdivision (mask-based multi-geometry)
2. ✅ Gallery parameter display
3. ✅ Version unification system
4. ✅ SVG layer grouping (Illustrator-compatible)

**Key Features**:
- Mask-based region assignment
- Background image compositing
- Per-region geometry/parameters
- `<g>` tags for layer organization

---

### Sprint 2 (v2.7.0) - Batch Processing 🚀 NEXT

**Duration**: 3-4 weeks  
**Priority**: Production workflow automation

**Week 1**: Refactor prod_ui.py
- Extract HTML template
- Create templates/production_ui.html
- Fix version substitution
- Regression testing

**Week 2-3**: Batch features
- Folder input processing
- Preset cycling
- Progress tracking UI
- Error handling (skip failures)
- Batch gallery generation

**Week 4**: Polish
- Performance optimization
- Documentation
- Sprint 3 prep

**Success Criteria**:
- Process 50 images unattended
- <2 min per image (4000 shapes)
- Clean error recovery

---

### Sprint 3 (v2.7.5) - Rating System

**Duration**: 1 week  
**Features**:
- Star ratings (1-5) in gallery
- SQLite persistence
- CSV export
- Filter by rating

**Purpose**: Training data for Phase 3 AI

---

### Sprint 4 (v2.8.0) - Preset Management

**Duration**: 1 week  
**Features**:
- Save/load named presets
- CRUD operations
- Import/export JSON
- Built-in presets

---

## Phase 3 (v2.9.0) - HASL AI & Optimization

**Duration**: 6-8 weeks  
**Prerequisites**: 100+ rated artworks

### HASL Framework
- Parameter recommendations based on image analysis
- ML model (rating correlation)
- Confidence scoring

### Advanced Optimization
- 95%+ space utilization
- Sub-10 second generation
- Parallel processing

---

## Phase 4 (v3.0.0+) - Advanced Geometries

**New Geometry Types**:
1. Hexagonal tessellation
2. Organic curves (Bezier/spline)
3. Concentric patterns
4. Text/typography integration

---

## Success Metrics

### Technical (Current)
- ✅ Performance: <15s generation
- ✅ Space utilization: 90%+
- ✅ File size: 20% reduction
- ✅ Layer organization: Illustrator groups

### Workflow
- ✅ Production UI working
- ⏳ Batch processing (Sprint 2)
- ⏳ Preset system (Sprint 4)

---

## Technical Environment

**Stack**:
- Python 3.13 (.venv)
- Flask (web UI)
- PIL (image processing)
- numpy/scipy (geometry)

**Working Features**:
- 5 geometries + hybrid mode
- Cascade fill
- Parameter sliders
- XMP metadata
- SVG layer grouping
- Version management

---

## Known Issues

1. **Web page title** - Hardcoded (fix Sprint 2)
2. **Flask caching** - Restart after code changes
3. **Cascade efficiency** - Acceptable but could improve

---

## Architecture
cubist_art/
├── version.py                # Version management
├── cubist_cli.py            # CLI interface
├── hybrid_subdivision.py    # Multi-geometry
├── svg_export.py           # Layer grouping
├── tools/prod_ui.py        # Web UI (needs refactoring)
├── geometry_plugins/       # 5 geometries
└── docs/                   # Handoffs & roadmap

---

## Next Steps

1. **Immediate**: Git commit Sprint 1
2. **This week**: Start Sprint 2 refactoring
3. **Next month**: Complete batch processing
4. **Q1 2026**: Rating system + presets
5. **Q2 2026**: Phase 3 HASL AI

---

**Current**: Phase 2 Sprint 1 ✅ COMPLETE  
**Next**: Phase 2 Sprint 2 🚀 READY  
**Timeline**: Sprint 2 completes in 3-4 weeks
