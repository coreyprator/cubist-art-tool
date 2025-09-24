path: docs/PromptForge-README.md
language: markdown
contents:
# PromptForge v1.5 — GUI + CLI

This version adds **tooltips**, a **Help editor**, **in-app scenario/field editing**, and a **Prompt History** database.

## Run
- GUI: `python tools/promptforge.py gui`
- Init config: `python tools/promptforge.py init`
- Make prompt (CLI): `python tools/promptforge.py make --scenario troubleshooting --task "Fix crash"`
  - Also save to DB: add `--save_to_db`

## Where things are stored
- Config JSON: `.promptforge/config.json`
- Prompt files: `.promptforge/out/`
- History DB: `.promptforge/promptforge.db` (SQLite, table `prompts`)

## Tabs

### Prompt
Build a prompt using a scenario:
- **Project Name** (tooltip explains purpose)
- **Scenario** dropdown
- **Task** (one line)
- **Sections** (dynamic for the chosen scenario; each text box has a tooltip)
- **Extra Notes**

Buttons:
- **Build Prompt**: generates the full prompt in the output box and copies to clipboard (if enabled)
- **Save to File**: writes to `.promptforge/out/`
- **Save to DB**: saves to local SQLite history

### Rules
Add/update/delete short, numbered rules (R1, R2, R3...). Edits persist to config.

### Sentinels
Edit **start**, **end**, and **self-check** lines. These are echoed by the assistant at the top/bottom of replies and are useful for linting.

### Output Contract
Define the file-block format the assistant must follow. Include the example to increase compliance.

### Scenarios
Create new scenarios, change titles/descriptions, add/remove **Sections** (label & prompt), and update extra directives. These changes persist to config.

### Help
Two parts:
- **Fields Help**: global help text for UI fields (Project Name, Scenario, Task, Extra Notes).
- **Scenario Help**: per-scenario **Overview** and per-**Section** help.

Tooltips in the UI read from this help, so updating here updates the tooltips.

### History
A list of previously saved prompts (most recent first). Selecting a row previews the content; you can **Export Selected** to a file.

## Best Practices
- Keep **Rules** short and high-salience.
- Scenario **Sections** should ask for information the assistant truly needs.
- Use **Help** to encode your team's conventions so tooltips teach new contributors.
- Save good prompts to DB and reuse them (copy/edit in the Prompt tab).

## Backup/Portability
Use the menu **Export As...** to save a portable JSON snapshot of settings. Use **Load/Import** to restore.
