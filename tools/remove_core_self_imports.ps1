[CmdletBinding()]
param([string]$FilePath = "cubist_core_logic.py")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $FilePath)) { Write-Error "Not found: $FilePath"; exit 1 }

$lines = (Get-Content -Raw -Encoding UTF8 $FilePath) -split "`r?`n"
$changed = $false
$rx = '^(?:from\s+cubist_core_logic\s+import\s+.*|import\s+cubist_core_logic(?:\s+as\s+\w+)?)\s*(#.*)?$'
for ($i=0; $i -lt $lines.Length; $i++) {
  if ($lines[$i] -match $rx) { $lines[$i] = "# [compat] removed self-import: " + $lines[$i]; $changed = $true }
}
if ($changed) {
  Set-Content -Encoding UTF8 $FilePath ($lines -join "`r`n")
  Write-Host "Commented self-import lines in $FilePath"
} else {
  Write-Host "No self-import lines found in $FilePath"
}
