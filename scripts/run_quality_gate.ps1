# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: scripts/run_quality_gate.ps1
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:24:01+02:00
# === CUBIST STAMP END ===
param(
  [Parameter(ValueFromRemainingArguments)]
  [string[]]$Args
)
$src = Join-Path $PSScriptRoot "dev_quality_gate.ps1"
$dst = Join-Path $env:TEMP ("dev_quality_gate_{0}.ps1" -f ([guid]::NewGuid()))
Get-Content -LiteralPath $src -Raw | Set-Content -LiteralPath $dst -Encoding UTF8
try {
  pwsh -NoProfile -ExecutionPolicy Bypass -File $dst @Args
} finally {
  Remove-Item -LiteralPath $dst -Force -ErrorAction SilentlyContinue
}

# --- Dirty tree check ---------------------------------------------------------
if (-not $AllowDirty) {
  $status = git status --porcelain
  if ($status) {
    Write-Host $status
    Write-Host "[INFO] Working tree is dirty. Staging all changes for commit..." -ForegroundColor Yellow
    git add -A
  }
}


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:24:01+02:00
# === CUBIST FOOTER STAMP END ===
