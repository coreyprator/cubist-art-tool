# Cubist Art Tool v2.3.7 — Release Plan

1. Objectives

Ship Flow-field Hatching (LIC-guided) as a geometry plugin producing deterministic polylines.

Add Poisson-disk seeding as a shared primitive (core + CLI/GUI flags).

Ensure Cascade strategy remains stable: include plain vs cascade in smoke + production tests.

Enforce a strict quality gate before handing off any files.

2. Scope (In / Out)

In: new plugin, seeding mode, tests (unit + smoke + SVG round-trip + determinism), archive completeness.

Out: new external deps beyond NumPy/OpenCV (SciPy optional but not required), major GUI redesign.

3. Deliverables

- geometry_plugins/flow_field_hatching.py

Tests:
- tests/test_flow_field_hatching_plugin.py (discovery, determinism)
- tests/test_flow_field_cascade.py (cascade path)
- tests/test_cascade_smoke_matrix.py (multi-geometry plain vs cascade)
- tests/test_poisson_seed_mode.py (core seeding, determinism/count)

Core: extend sample_points_deterministic(...) with method + poisson_radius; add CLI/GUI flags:
- --seed-mode {uniform,poisson}
- --poisson-radius <px>

Archive: ensure geometry_plugins/** is tracked; optional archive_source.ps1 ExtraInclude support.

4. Architecture notes

Plugin contract: register(register_fn) → register_fn(name, generate_callable); generate(canvas_size, total_points, seed, **params) -> List[shape].

Shapes: polygon, polyline, circle, rect, line, path (dicts with numeric fields; colors as (r,g,b)).

Determinism: seeded random.Random(seed); image-dependent plugins must be stable given the same image + params.

5. Testing strategy

Unit / discovery: plugin import, registry get_geometry, deterministic A==B for same seed.

SVG round-trip: write/read for polygonal geometries; file exists; contains expected elements.

Cascade smoke: render each geometry with/without cascade; verify outputs exist and are deterministic.

Determinism hashes: compare JSON shapes + PNG/SVG hashes (timestamp-insensitive).

CLI sanity: two small seeded runs.

5.1 Test Matrix (plain ✓ / cascade ★)

| Geometry           | Discovery | Determinism | SVG/PNG | Cascade smoke |
|--------------------|-----------|-------------|---------|--------------|
| rectangles         | ✓         | ✓           | ✓       | ★            |
| voronoi (if present)| ✓        | ✓           | ✓       | ★            |
| delaunay (if present)| ✓       | ✓           | ✓       | ★            |
| flow_field_hatching| ✓         | ✓           | ✓ (polyline) | ★      |

6. Acceptance criteria

- Flow-field plugin passes discovery and determinism; outputs non-empty polylines.
- Poisson seeding produces stable counts/positions for same seed and radius.
- Cascade tests pass for all supported geometries.
- ruff check --fix && ruff format && pytest -q are green.
- SVG/PNG smoke outputs exist for each geometry; determinism hashes match for same seed.
- Handoff archive includes geometry_plugins/**.

7. Quality gate (must pass locally before delivery)

- ruff check --fix + ruff format
- pytest -q
- SVG round-trip per geometry
- Cascade smoke matrix
- CLI sanity (2 seeded runs)
- Determinism (JSON + PNG/SVG hash equality)

8. Branching & Tagging

- Branch: milestone/v2.3.7
- Tag after visual sign-off: v2.3.7+flow
- Commit message style: feat(plugin): flow-field hatching / feat(core): poisson seeding / test: cascade matrix

9. Risks & Mitigations

- Cascade regressions: covered by new matrix smoke.
- Archive misses plugins: track folder in Git; optional ExtraInclude in archive_source.ps1.
- Parser/lexical errors: prevented by local gate; deliver full files only.
- Non-determinism from OpenCV ops: pin parameters; avoid nondeterministic threads; use seeded RNG.

10. Rollback plan

- Revert to previous tag; keep golden images + metrics to confirm parity.

11. Post-release

- Create GitHub release; attach sample outputs; note flags and usage examples.
