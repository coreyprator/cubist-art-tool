Cubist Hotfix — UI & Logging (v9)
=================================
What you get
- Progress text “Running {geom} (n/m)…“ + progress bar
- Checkboxes: export SVG / enable plugin exec / Verbose + Probe / Auto‑open gallery
- Copy log + Save log buttons; larger scrollable log pane
- Per‑run persistent run.log inside output/production/<timestamp>/
- Auto‑opens the gallery page after the run (toggleable)
- tools/run_cli.py shim: calls cubist_cli.py without passing --verbose
- tools/diagnostics/plugin_env_probe.py for quick environment dump
- tools/svg_audit.py for gallery shape counts

Install:
  python tools/apply_from_zip.py --root . --backup --verify "tools/cubist_hotfix_ui_logging_9.zip"

Run the UI:
  python tools/prod_ui.py
