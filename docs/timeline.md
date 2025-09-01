# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: docs/timeline.md
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:46+02:00
# === CUBIST STAMP END ===
# Timeline Scrubber & Animation Export

**Status:** v2.3 feature (planned)

## CLI Flags

- `--animate-gif PATH.gif`
  Export an animated GIF from step PNGs.
- `--animate-mp4 PATH.mp4`
  Export an MP4 animation from step PNGs.
- `--fps INT`
  Frames per second (default: 8)
- `--hold-first N`, `--hold-last N`
  Hold first/last frame for N frames (optional)
- `--scale FLOAT`
  Scale output animation (optional)

## UI Features

- Timeline scrubber: slider to preview cascade fill frames interactively.
- Play/pause controls.
- Automated playback export (GIF/MP4).

## Example

```powershell
python cubist_cli.py --input input\your_input_image.jpg --output output\animtest --geometry delaunay --points 100 --cascade-stages 3 --export-svg --animate-gif output\anim.gif --fps 12
```

## Requirements

- Animation export requires `imageio[ffmpeg]` or `moviepy` (installed automatically if needed).

## Tests

- Assemble 10 tiny frames into a GIF; assert output exists and duration/fps match.

---

*See also: [README.md](../README.md)*



# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:46+02:00
# === CUBIST FOOTER STAMP END ===
