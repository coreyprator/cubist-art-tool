[CmdletBinding()]
param([string]$FilePath = "cubist_core_logic.py")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $FilePath)) { Write-Error "Not found: $FilePath"; exit 1 }
$content = Get-Content -Raw -Encoding UTF8 $FilePath
if ($content -match "(?ms)^\s*def\s+run_cubist\s*\(") { Write-Host "Shim already present."; exit 0 }
$shim = @"
# --- Back-compat shim: run_cubist -> run_pipeline ---
def run_cubist(*args, **kwargs):
    try:
        fn = globals().get("run_pipeline", None)
        if fn is None:
            from cubist_cli import run_pipeline as fn
        return fn(*args, **kwargs)
    except Exception as e:
        raise RuntimeError(f"run_cubist shim failed: {e}")
# --- End shim
"@
Add-Content -Encoding UTF8 $FilePath $shim
Write-Host "Appended run_cubist shim to $FilePath"
