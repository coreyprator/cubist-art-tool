CUBIST HOTFIX — ENV + UI + DIAGNOSTICS

FILES
- tools/prod_ui.py
- tools/run_cli.py
- tools/diagnostics/plugin_env_probe.py
- tools/svg_audit.py

WHAT'S FIXED / ADDED
- UI: buttons enabled, progress bar, file path + preview, verbose logging, auto-open browser & gallery
- ENV: subprocesses get PYTHONPATH=(repo_root; repo_root\src) so plugins import correctly
- DIAG: run_cli returns JSON with rc, expected svg path, existence, stdout/stderr tails
- GALLERY: simple index.html written per run

USAGE
1) Apply this zip with:
   python tools\apply_from_zip.py --root . --backup --verify tools\cubist_hotfix_env_ui_diag.zip

2) Start the UI:
   python tools\prod_ui.py

3) In the UI:
   - Paste your input image absolute path, click Preview (ensures the server can read it)
   - Select geometries
   - Leave "export SVG" on
   - Click Run
   - Watch verbose log
   - After completion, gallery opens automatically
