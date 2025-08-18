5) Proposed roadmap (v2.2 - 2.3)
v2.2 — Cascade & test hardening

Cascade (vector aware): re-enable cascade pipeline so each cascade stage reuses the exact sampled points (or seeded deltas). Ensure METRICS aggregates per-stage.

Unit tests for validator: extract SVG counting helper; add PyTest to compare METRICS vs parsed SVG shape counts.

CI: GitHub Actions job running the triple-test on a tiny input to keep it fast.

v2.2 — Curves & palette controls

Bezier/curved modes:

Tri-to-curve smoothing: replace triangle edges with quadratic/cubic Béziers (control points derived from vertex angle bisectors or centroid offsets).

Voronoi rounded cells: approximate polygons with smooth paths (Douglas–Peucker simplification → corner rounding).

Colorization knobs:

Palette selection (--palette basic|vintage|coolwarm|image-sampled).

Fill strategies (mean, median, dominant-color, gradient across cell).

Optional strokes with per-mode defaults (--stroke-width, --stroke-alpha).

SVG size/DPI options: --svg-width/--svg-height/--svg-scale.

v2.3 — Performance & UX

Speed: numba or vectorized hotspots for sampling/triangulation where feasible.

CLI polish:

--export-svg <auto|path> (already mostly there, refine).

--metrics-json <path> to save structured run data.

Repro packs: --archive-output bundles input, outputs, METRICS, and a small JSON manifest.