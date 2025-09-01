# === FILE: REPO_STATUS_AND_PLAN.md ===
# === UPDATED: 2025-08-22T14:30:00Z ===

## (A) Repo Layout Confirmation & Risks

**Current Layout:**
- `cubist_cli.py` — Main CLI, metrics, geometry selection
- `cubist_core_logic.py` — Core logic, geometry modes
- `svg_export.py`, `metrics_utils.py` — Output and metrics helpers
- `geometry_plugins/` — (to be created) for plugin modules
- `tools/` — Utility scripts (e.g., header stamping)
- `tests/` — Test suite (pytest, covers CLI, geometry, metrics)
- `archive/`, `scripts/legacy_tests/` — Legacy/experimental code (not production)
- `.venv/`, `tmp_release_smoke/` — Ignored/temporary

**Risks for v2.3:**
- **Plugin system**: Must not break existing geometry modes; registry must be robust to import errors and missing plugins.
- **Path handling**: Windows path quoting and spaces must be handled everywhere (CLI, tests, plugins).
- **Metrics contract**: Any new geometry/plugin must not break JSON contract or determinism.
- **Test hygiene**: Plugins must be discoverable and testable without polluting global state.
- **Header stamping**: New files must be stamped per repo convention.

---

## (B) Minimal Task Plan (PR-sized steps)

1. **Geometry Plugin Skeleton**
   - Create `geometry_registry.py` (plugin registry/loader)
   - Add `geometry_plugins/example_plugin.py` (toy plugin)
   - Add/modify `tests/test_geometry_plugins.py` (detection, determinism)
   - Update `cubist_cli.py` if needed for plugin support

2. **SVG Pipeline Improvements**
   - Ensure fill/stroke round-trip, mask placeholder in SVG output
   - Add/adjust tests for SVG pipeline

3. **Metrics Stability**
   - Harden metrics contract, especially for cascade stages
   - Add/adjust tests for metrics JSON

4. **CLI Polish**
   - Improve help text, error messages, and path quoting
   - Add/adjust CLI tests for edge cases

5. **Repo Hygiene**
   - Ensure all tests and hooks pass after changes
   - Confirm no tmp artifacts or legacy code tracked

6. **Documentation & Examples**
   - Update README, add plugin usage docs/examples

---

# === EOF REPO_STATUS_AND_PLAN.md @ 2025-08-22T14:30:00Z ===
