test:

# Cubist Art Generator

Cubist Art Generator is a Python tool for generating cubist-style images from input photos, with a user-friendly GUI and advanced geometric processing.

## Documentation

Full documentation and project audit: [docs/overview.md](docs/overview.md)

---

See [CHANGELOG.md](CHANGELOG.md) for version history.

Usage

# Cubist Art — PNG/SVG Parity Edition

## Quick Start
```bash
python -m venv .venv
# Activate your venv (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

#triple test
python test_cli.py `
  --input input/your_input_image.jpg `
  --output output `
  --triple-test `
  --points 100 `
  --export-svg `
  --seed 42 `
  --timeout-seconds 120

# single Run 
python cubist_cli.py --input input/your_input_image.jpg --output output --geometry delaunay --points 100 --export-svg --seed 42

Notes

Rectangles mode is grid-based; --points sets grid size (e.g., 100 → ~10x10), not arbitrary N rectangles.

CLI prints a METRICS: line summarizing counts and output paths.

Troubleshooting

Archive only: python test_cli.py --input ... --output ... --archive exits cleanly without requiring --geometry.

If your editor shows “phantom” lines, disable “Code Lens”/Minimap diff overlays and ensure cloud sync (e.g., Google Drive) is paused while editing.


## D) `docs/VALIDATION.md`
```markdown
# Validation Strategy

- **Determinism**: `--seed` locks random sampling across PNG/SVG.
- **Single source geometry**: identical points → identical topology.
- **METRICS line**: emitted by `cubist_cli.py`, parsed by tests.
- **SVG parity test**: counts `<polygon>`/`<path>` (mode-aware) and compares to raster shape count.

### METRICS Example
