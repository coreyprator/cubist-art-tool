# Release Readiness Checklist (CLI + GUI + Gallery)

This doc is the **single source of truth** for go/no-go. If any step fails, fix or defer before release.

---

## 0) Branching & Versioning
- [ ] `git switch -c release/x.y.z`
- [ ] Bump `__version__` (CLI + GUI) and update `CHANGELOG.md`
- [ ] Ensure `prod_sweep.py` prints “✅ All 6 renders succeeded” when `failed == []`

---

## 1) CLI Smoke (Windows, PowerShell)
**Goal:** confirm the six canonical outputs generate with no warnings except INFO.

**CP-RUN**
```powershell
# Clean room
git clean -xfd

# One-liner: 6 renders + gallery
python .\scripts\prod_sweep.py --input .\input\your_input_image.jpg --outdir .\output --open --quiet
```

**CP-VERIFY**

 Console shows 6 “Wrote:” messages + “✅ All 6 renders succeeded” (or summary with failed: []).

 output\prod_*.svg exist and each opens in a browser.

 Visual sanity: Delaunay=triangles, Voronoi=cells, Rectangles=grid—no empty canvases, no weird scaling.

---

## 2) Determinism & Seeds

Goal: same params, same SVG bytes.

**CP-RUN**
```powershell
Remove-Item .\output\determinism\ -Recurse -Force -ErrorAction SilentlyContinue
python .\scripts\prod_sweep.py --input .\input\your_input_image.jpg --outdir .\output\determinism --quiet
Get-ChildItem .\output\determinism\prod_*.svg | Get-FileHash -Algorithm SHA1
# Run twice:
python .\scripts\prod_sweep.py --input .\input\your_input_image.jpg --outdir .\output\determinism2 --quiet
Get-ChildItem .\output\determinism2\prod_*.svg | Get-FileHash -Algorithm SHA1
```

**CP-VERIFY**

 Hashes match 1:1 across runs (same seeds → identical files).

---

## 3) GUI Product Test (feature & persistence)

Goal: the GUI can configure everything the CLI can, run all geometries, and persist parameters.

Use the app’s real entry point, e.g. python .\gui\main.py (adjust if different).

A. Geometry Coverage (single image)

 Load input: .\input\your_input_image.jpg

 Geometry: Delaunay → points=1200, seed=123, cascade stages=3, fill=image, export SVG → opens in default viewer

 Geometry: Voronoi → same template

 Geometry: Rectangles → same template

B. Seed Modes

 set seed mode edge (or default/uniform) → run

 set seed mode poisson, poisson_min_px=22 → run

 (if available) toggle back to uniform → run

 Confirm output filenames or metadata reflect the choices (even before metadata feature lands)

C. Persistence

 Change settings (geometry, points, seed, seed_mode, cascade options)

 Exit app; relaunch; Verify values are restored

 Verify last-used input path & output dir are remembered (or returned via “Recent”)

D. Error Handling / UX

 Missing input → Run is disabled with clear inline message

 Invalid numeric (non-int) in points or poisson_min_px → friendly validation

 Unknown plugin/geometry name → clear error, recover without restart

 Progress or “busy” affordance during long runs; no double-run when clicked twice

E. Pathing (Windows specifics)

 Relative paths OK; spaces in path OK; outdir auto-creates

 CRLF vs LF: generated files use LF (SVG/HTML) or consistent expected line endings

---

## 4) Gallery (current run only)

Goal: gallery shows the 6 generated files from this run—nothing stale.

**CP-RUN**
```powershell
python .\scripts\make_gallery.py output --glob "prod_*.svg" --title "Prod sweep"
start .\output\gallery.html
```

**CP-VERIFY**

 Only prod_*.svg tiles are present.

 Each tile loads without console errors (devtools).

 No { font-family } KeyError—CSS curly braces escaped in template.

---

## 5) RIFF + Git Hygiene

Goal: No nits/lice sneak into main.

**CP-RUN**
```powershell
# Linters/formatters (adapt to your stack)
python -m pip install -U black isort flake8 mypy pytest

black --check .
isort --check-only .
flake8 .
mypy .  # if you maintain type hints
pytest -q

# Docs & README badges
```

**CP-VERIFY**

 Black/isort/flake8/mypy/pytest all pass

 README usage blocks match actual CLI flags (--cascade-stages, --cascade-fill, --param seed_mode=...)

 Example commands run as copied (no typos, no OS-specific gotchas)

 Sample image lives at .\input\your_input_image.jpg

 scripts have shebangs/python invocations correct

---

## 6) Changelog + Tag

 CHANGELOG.md: features, fixes, known issues (metadata planned for next release)

 git commit -am "release: x.y.z" (or signed)

 git tag -a vX.Y.Z -m "x.y.z"

 git push --follow-tags

---

## Go / No-Go Criteria

Go if:

6/6 CLI renders succeed on clean repo

GUI runs all geometries, seed modes, cascades, SVG export, and persists settings

Gallery shows only current run’s images

Linters/tests pass; docs updated

No-Go if any above fails. Fix or defer explicitly to next release.
