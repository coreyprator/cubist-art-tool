# Cubist Art Tool v2.3.7 — Task Checklist

## Owners

Core/Plugins: Owner: <name>
Tests/QA: Owner: <name>
Release/Archive: Owner: <name>

---

## Plugin: Flow-field Hatching

- [ ] Implement geometry_plugins/flow_field_hatching.py (deterministic polylines)
- [ ] Parameters: spacing_px, step_px, max_len, integrator={rk2|rk4}, jitter, stroke_width
- [ ] tests/test_flow_field_hatching_plugin.py (discovery, determinism)
- [ ] tests/test_flow_field_cascade.py (cascade on, outputs exist)
- [ ] SVG smoke output verified

## Poisson-disk Seeding

- [ ] Extend core sample_points_deterministic(method, poisson_radius)
- [ ] CLI/GUI flags: --seed-mode {uniform,poisson}, --poisson-radius <px>
- [ ] tests/test_poisson_seed_mode.py (determinism, approximate count)
- [ ] Update docs (CLI guide) with examples

## Cascade Matrix Smoke

- [ ] tests/test_cascade_smoke_matrix.py (rectangles, voronoi*, delaunay*, flow_field_hatching)
- [ ] Mark tests to skip gracefully if a plugin isn’t present

## Release Hygiene

- [ ] Track geometry_plugins/** in Git (verify git ls-files)
- [ ] (Optional) Update tools/archive_source.ps1 with -ExtraInclude "geometry_plugins/**"
- [ ] ruff check --fix && ruff format
- [ ] pytest -q
- [ ] Run SVG/PNG smoke (plain + cascade)
- [ ] Determinism hashes equal for same seed (JSON + PNG/SVG)
- [ ] Tag v2.3.7+flow and push branch/tag

---

## Definition of Done (DoD)

- [ ] All acceptance criteria in the release plan met
- [ ] Golden images/metrics updated (if necessary)
- [ ] Handoff zip verified to include plugins + tests
- [ ] README/CLI docs updated with new flags
- [ ] Final visual sign-off completed

---

## Commands (copy-paste)

```powershell
# Activate
.\.venv\Scripts\Activate.ps1

# Lint/format/tests
ruff check --fix; ruff format; pytest -q

# Example: flow-field plugin smoke
python cubist_cli.py --geometry flow_field_hatching --cascade false --seed 123 --out .\out\flow_plain
python cubist_cli.py --geometry flow_field_hatching --cascade true  --seed 123 --out .\out\flow_cascade

# Poisson seeding smoke (once core flags are added)
python cubist_cli.py --geometry rectangles --seed-mode poisson --poisson-radius 10 --seed 42 --out .\out\rect_poisson

# Archive verification
pwsh .\tools\archive_source.ps1 -Out ".\dist\cubist_art_v2.3.7.zip"
```

---

## Notes

- Full files only — no diffs.
- Run the local quality gate before delivering any file.
