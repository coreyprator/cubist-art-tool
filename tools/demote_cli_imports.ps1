[CmdletBinding()]
param([string]$FilePath = "cubist_core_logic.py")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $FilePath)) { Write-Error "Not found: $FilePath"; exit 1 }
$text = Get-Content -Raw -Encoding UTF8 $FilePath

# Comment out any top-level imports of cubist_cli to avoid core<->cli circulars
$pattern = '^(?:from\s+cubist_cli\s+import\s+.*|import\s+cubist_cli(?:\s+as\s+\w+)?)(\s*#.*)?$'
$lines = $text -split "`r?`n"
$changed = $false
for ($i=0; $i -lt $lines.Length; $i++) {
  if ($lines[$i] -match $pattern) {
    $lines[$i] = "# [compat] moved to runtime import: " + $lines[$i]
    $changed = $true
  }
}

if ($changed) {
  Set-Content -Encoding UTF8 $FilePath ($lines -join "`r`n")
  Write-Host "Commented top-level CLI imports in $FilePath"
} else {
  Write-Host "No top-level CLI imports found in $FilePath (or already commented)."
}
