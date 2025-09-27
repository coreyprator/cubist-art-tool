[CmdletBinding()]
param([string]$FilePath = "cubist_core_logic.py")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $FilePath)) { Write-Error "Not found: $FilePath"; exit 1 }
$text = Get-Content -Raw -Encoding UTF8 $FilePath

# 1) Remove the earlier inline shim, if present
$shimBlock = '(?ms)^# --- Back-compat shim:.*?# --- End shim\s*'
$text2 = [regex]::Replace($text, $shimBlock, '')

# 2) Append a module-level __getattr__ that late-binds run_cubist (no circular import)
if ($text2 -notmatch 'def\s+__getattr__\s*\(') {
  $redirect = @"
# --- Legacy attribute redirect (added by fix_legacy_run_cubist.ps1)
def __getattr__(name):
    if name == "run_cubist":
        # Prefer in-module pipeline if available (no extra imports)
        fn = globals().get("run_pipeline", None)
        if fn is not None:
            def _run_cubist(*args, **kwargs):
                return fn(*args, **kwargs)
            return _run_cubist
        # Fallback to facade (keeps internals free to evolve)
        from cubist_api import run_cubist as _rc
        return _rc
    raise AttributeError(name)
# --- End legacy redirect
"@
  $text2 = $text2.TrimEnd() + "`r`n`r`n" + $redirect
}

Set-Content -Encoding UTF8 $FilePath $text2
Write-Host "Updated $FilePath"
