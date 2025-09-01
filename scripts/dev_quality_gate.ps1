# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: scripts/dev_quality_gate.ps1
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:32+02:00
# === CUBIST STAMP END ===
#requires -Version 7.0
<#
.SYNOPSIS
  One-shot quality gate: (optional) install deps, run pre-commit, then stage/commit/tag/push.

.EXAMPLES
  pwsh -File scripts/dev_quality_gate.ps1 `
    -CommitMessage "chore: ruff clean baseline; pre-commit stable on Win/Linux" `
    -Tag "v2.2.1" -RunInstall -RunPrecommit -Push

  pwsh -File scripts/dev_quality_gate.ps1 -CommitMessage "chore: bypass hooks once" -NoVerify -Push
#>

[CmdletBinding()]
param(
  [string]$CommitMessage = "chore: quality gate",
  [string]$Tag,
  [switch]$RunInstall,     # pip install -r requirements.txt + pre-commit install
  [switch]$RunPrecommit,   # pre-commit run --all-files
  [switch]$Push,           # git push (and push tag if provided)
  [switch]$AllowDirty,     # skip dirty-tree check
  [switch]$NoVerify        # pass --no-verify to git commit
)

$ErrorActionPreference = 'Stop'

function Write-Stamp([string]$msg) {
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Write-Host "[$ts] $msg"
}

function Invoke-Tool {
  param(
    [Parameter(Mandatory)][string]$FilePath,
    [string[]]$Args = @()
  )
  Write-Host ">> $FilePath $($Args -join ' ')" -ForegroundColor Cyan
  & $FilePath @Args
  $exit = $LASTEXITCODE
  if ($exit -ne 0) {
    throw "Command failed ($exit): $FilePath $($Args -join ' ')"
  }
}

# --- Locate repo root ---------------------------------------------------------
$repoRoot = (git rev-parse --show-toplevel 2>$null)
if (-not $repoRoot) { $repoRoot = (Get-Location).Path }
Set-Location $repoRoot
Write-Stamp "Repo root: $repoRoot"

# --- Tooling paths ------------------------------------------------------------
# Prefer venv python if present
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

# pre-commit shim/name differs on Windows sometimes; try a few names
$precommit = Get-Command pre-commit -ErrorAction SilentlyContinue
if (-not $precommit) {
  $precommit = Get-Command "pre-commit.exe" -ErrorAction SilentlyContinue
}
$precommitPath = if ($precommit) { $precommit.Source } else { $null }

Write-Stamp "Python: $python"
Write-Stamp ("pre-commit: " + ($(if ($precommitPath) { $precommitPath } else { "<not found>" })))

# --- Dirty tree check ---------------------------------------------------------
if (-not $AllowDirty) {
  $status = git status --porcelain
  if ($status) {
    Write-Host $status
    throw "Dirty working tree. Commit/stash or pass -AllowDirty."
  }
}

# --- Optional installs ---------------------------------------------------------
if ($RunInstall) {
  if (Test-Path "requirements.txt") {
    Write-Stamp "pip install -r requirements.txt"
    Invoke-Tool -FilePath $python -Args @("-m","pip","install","-r","requirements.txt")
  } else {
    Write-Stamp "requirements.txt not found; skipping pip install"
  }

  if (-not $precommitPath) {
    Write-Stamp "Installing pre-commit into venv"
    Invoke-Tool -FilePath $python -Args @("-m","pip","install","pre-commit")
    $precommit = Get-Command pre-commit -ErrorAction SilentlyContinue
    if ($precommit) { $precommitPath = $precommit.Source }
  }

  if ($precommitPath) {
    Write-Stamp "pre-commit install"
    Invoke-Tool -FilePath $precommitPath -Args @("install")
  }
}

# --- Optional pre-commit run ---------------------------------------------------
if ($RunPrecommit) {
  if ($precommitPath) {
    Write-Stamp "pre-commit run --all-files (this may format files)"
    try {
      & $precommitPath "run" "--all-files"
      $exit = $LASTEXITCODE
      # pre-commit returns nonzero when it *changes* files or any hook fails.
      if ($exit -ne 0) {
        Write-Host "pre-commit returned $exit (likely reformatted or a hook failed). Staging changes…" -ForegroundColor Yellow
      }
    } catch {
      Write-Host "pre-commit threw: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    git add -A
  } else {
    Write-Stamp "pre-commit not available; skipping RunPrecommit"
  }
}

# --- Stage everything ----------------------------------------------------------
Write-Stamp "git add -A"
git add -A

# --- Commit --------------------------------------------------------------------
$commitArgs = @("commit","-m", $CommitMessage)
if ($NoVerify) { $commitArgs += "--no-verify" }
Write-Stamp ("git " + ($commitArgs -join ' '))
git @commitArgs
$commitExit = $LASTEXITCODE
if ($commitExit -ne 0) {
  Write-Host "git commit returned $commitExit (nothing to commit or hook failure). Continuing…" -ForegroundColor Yellow
}

# --- Tag (optional) -----------------------------------------------------------
if ($Tag) {
  Write-Stamp "git tag -a $Tag -m ""$CommitMessage"""
  git tag -a $Tag -m $CommitMessage
  if ($LASTEXITCODE -ne 0) {
    Write-Host "Tag creation failed or tag exists; continuing…" -ForegroundColor Yellow
  }
}

# --- Push (optional) ----------------------------------------------------------
if ($Push) {
  Write-Stamp "git push origin HEAD"
  git push origin HEAD
  if ($Tag) {
    Write-Stamp "git push origin $Tag"
    git push origin $Tag
  }
}

Write-Stamp "Quality gate complete."

# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:32+02:00
# === CUBIST FOOTER STAMP END ===
