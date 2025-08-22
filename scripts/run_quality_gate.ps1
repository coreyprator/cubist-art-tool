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
