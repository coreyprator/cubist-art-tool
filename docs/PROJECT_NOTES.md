
---

## CP-REPLACE — `docs/PROJECT_NOTES.md`
> Canonical terminology (so it doesn’t diverge from `prompt_conventions.md`). Keep this as the source of truth.

```md
# PROJECT_NOTES (Reference doc: terms we’ll use)

This is the **canonical glossary**. If any other doc conflicts, **this wins**.

## Shorthand

- **ZCP** – Paste a full Continue prompt into VS Code and run it as-is.
- **CP-REPLACE** – Full file content provided. Replace target file verbatim.
- **CP-EDIT** – Precise diff or find/replace instructions.
- **CP-ADD** – Add a new file with given path and content.
- **CP-RUN** – Exact shell/PowerShell command(s) to run from repo root unless stated.
- **CP-VERIFY** – Post-run checks to confirm expected outputs.
- **CP-RECOVER** – Steps to return to a known-good state if something fails.

## Rules

1) Prefer **CP-REPLACE** for anything non-trivial.
2) Use **ZCP** for safe, idempotent automation only.
3) Always follow **CP-RUN** with **CP-VERIFY**.
4) Docs live in `docs/`; code comments/READMEs in component folders override docs for implementation details.

## Quick Examples

- “Replace `scripts/make_gallery.py`” ⇒ **CP-REPLACE**.
- “Change a flag name in README” ⇒ **CP-EDIT**.
- “Add metadata spec doc” ⇒ **CP-ADD** (see `docs/SVG_METADATA_AND_GALLERY_V2.md`).
