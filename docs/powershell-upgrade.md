# PowerShell Version Guidance for Cubist Art Tool

## Why upgrade PowerShell?

Some advanced scripts (including recent release/publish and packaging scripts) use features only available in **PowerShell 7+** (also called PowerShell Core).
Older Windows systems come with **Windows PowerShell 5.1**, which lacks some modern syntax (like the `?.` operator, `? :` ternary, etc.).

If you see errors like:
- `Unexpected token '?.Source' in expression or statement.`
- `Unexpected token '?' in expression or statement.`

...you are likely running PowerShell 5.1.

## Should you upgrade?

**Recommended:**
- If you want maximum compatibility and fewer script errors, upgrade to PowerShell 7+.

**You can keep both:**
- PowerShell 7+ installs side-by-side with Windows PowerShell 5.1.
- You can launch PowerShell 7+ with `pwsh` (instead of `powershell`).

## How to upgrade

1. **Download PowerShell 7+ (pwsh):**
   - Go to: https://github.com/PowerShell/PowerShell/releases
   - Download the latest stable MSI for Windows.

2. **Install:**
   - Run the MSI installer and follow the prompts.

3. **Verify:**
   - Open a new terminal and run:
     ```
     pwsh
     $PSVersionTable.PSVersion
     ```
   - You should see a version like `7.4.0` or higher.

4. **Use in scripts:**
   - Replace `powershell` with `pwsh` in your script invocations:
     ```
     pwsh -ExecutionPolicy Bypass -File scripts\your_script.ps1 ...
     ```

## Notes

- You can still use `powershell` for legacy scripts.
- All new features and fixes are in PowerShell 7+.
- If you use VS Code, it will detect and use PowerShell 7+ if installed.

---

**Summary:**
Upgrading to PowerShell 7+ is recommended for modern scripting and compatibility with advanced features used in this project.
