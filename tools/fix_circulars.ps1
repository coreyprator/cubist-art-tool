[CmdletBinding()]
param([string]$File = "cubist_cli.py")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $File)) { Write-Host "Note: $File not found — skipping"; exit 0 }

$text = Get-Content -Raw -Encoding UTF8 $File
$orig = $text

# Replace common forms of the legacy import with the facade
$text = $text -replace 'from\s+cubist_core_logic\s+import\s+run_cubist', 'from cubist_api import run_cubist'
$text = $text -replace 'import\s+cubist_core_logic\s+as\s+core', 'import cubist_api as core'

if ($text -ne $orig) {
  Set-Content -Encoding UTF8 $File $text
  Write-Host "Updated $File to import via cubist_api"
} else {
  Write-Host "No legacy core imports found in $File"
}
