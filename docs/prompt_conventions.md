# Prompt & File Conventions

**ZCP** (Zero-Click Prompt): paste into the Continue chat; it issues instructions/actions.
**CP-REPLACE**: I’m giving you a full file; replace the file verbatim.
**CP-EDIT**: change specific lines/blocks in an existing file.
**CP-ADD**: add a new file with the given content.
**CP-RUN**: run this exact command in your shell/PowerShell/terminal.

Tips:
- Prefer CP-REPLACE for bigger refactors or when correctness matters.
- Prefer CP-EDIT for tiny diffs you can eyeball.
- When in doubt, **CP-REPLACE**.
