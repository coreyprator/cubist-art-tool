[CmdletBinding()]
param([string]$File = "cubist_core_logic.py")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $File)) { Write-Error "Not found: $File"; exit 1 }
$lines = (Get-Content -Raw -Encoding UTF8 $File) -split "`r?`n"

# Find insertion index after the last __future__ import near the top
$insertAt = 0
for ($i=0; $i -lt [math]::Min($lines.Length, 50); $i++) {
  if ($lines[$i] -match '^\s*from\s+__future__\s+import\s+') { $insertAt = $i + 1 }
  elseif ($insertAt -gt 0 -and -not ($lines[$i] -match '^\s*from\s+__future__\s+import\s+')) { break }
}

$stub = @"
# --- Back-compat: public entrypoint (hoisted) ---
def run_cubist(*args, **kwargs):
    """
    Thin shim so `from cubist_core_logic import run_cubist` works without circulars.
    Resolves the real function at *call* time.
    """
    fn = globals().get("run_pipeline", None)
    if fn is not None:
        return fn(*args, **kwargs)
    from cubist_api import run_cubist as _rc  # lazy to avoid import-time cycles
    return _rc(*args, **kwargs)
# --- End back-compat ---
"@

# Only insert if a top-level def isn't already present near file start
$head = ($lines[0..([math]::Min($lines.Length-1,120))] -join "`n")
if ($head -notmatch "(?ms)^\s*def\s+run_cubist\s*\(") {
  $before = if ($insertAt -gt 0) { $lines[0..($insertAt-1)] } else { @() }
  $after  = if ($insertAt -lt $lines.Length) { $lines[$insertAt..($lines.Length-1)] } else { @() }
  ($before + @($stub) + @("") + $after) -join "`r`n" | Set-Content -Encoding utf8NoBOM $File
  Write-Host "Inserted hoisted run_cubist at top of $File"
} else {
  Write-Host "Top-level run_cubist already present near file start; skipping."
}
