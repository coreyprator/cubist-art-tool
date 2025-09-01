# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: publish_v2.2.3.ps1
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:29+02:00
# === CUBIST STAMP END ===
# publish_v2.2.3.ps1
# Safe publishing helper for v2.2.x on Windows/PowerShell
# - Handles paths with spaces by using PowerShell arg arrays
# - Runs static checks, tests, repo hooks, and CLI smoke tests

[CmdletBinding()]
param(
  [string]$Branch = "v2.2",
  [switch]$Push    # set -Push to push tags/commits at the end (optional hook spot)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "=== $msg ===" -ForegroundColor Cyan }

# 0) Verify branch & remote
Write-Step "0) Verify branch & remote"
$repo = (Get-Location).Path
$branchName = (git rev-parse --abbrev-ref HEAD).Trim()
Write-Host $branchName
git remote -v

if ($branchName -ne $Branch) {
  throw "You are on '$branchName', expected '$Branch'. Checkout the correct branch before publishing."
}

# Show working tree summary (informational)
git status -s

# 1) Ensure compiled artifacts aren't tracked (informational; your pre-commit already checks)
Write-Step "1) Ensure compiled artifacts aren't tracked"

# 2) Reinstall deps (defensive; keeps your flow)
Write-Step "2) Re-install deps (defensive)"
$python = (Get-Command python).Path
& $python -m pip install -U pip setuptools wheel
& $python -m pip install -r requirements.txt

# 3) Static checks & formatting
Write-Step "3) Static checks & formatting"
& ruff check . --fix
& ruff format .

# 4) Run tests
Write-Step "4) Run tests (quiet)"
& pytest -q

# 5) Run repo hooks like CI
Write-Step "5) Run repo hooks like CI does"
& pre-commit run --all-files

# 6) Production CLI smoke tests (robust path-safe invocations)
Write-Step "6) Production CLI smoke tests"

# Prepare a temp smoke dir
$tmpRoot = Join-Path $repo "tmp_release_smoke"
if (Test-Path $tmpRoot) { Remove-Item -Recurse -Force $tmpRoot }
New-Item -ItemType Directory -Path $tmpRoot | Out-Null

# 6a) Make a small PNG input using Pillow (write a tiny script safely)
$makeImgPy = @'
from PIL import Image, ImageDraw
import os, sys
out = sys.argv[1]
os.makedirs(os.path.dirname(out), exist_ok=True)
W, H = 256, 256
im = Image.new("RGB", (W, H), "white")
dr = ImageDraw.Draw(im)
dr.rectangle([32, 32, 224, 224], outline="black", width=3)
dr.ellipse([96, 96, 160, 160], fill="red", outline="black")
im.save(out, "PNG")
print("Wrote", out)
'@
$makeImgPath = Join-Path $tmpRoot "make_input.py"
Set-Content -Path $makeImgPath -Value $makeImgPy -Encoding UTF8

$inPng = Join-Path $tmpRoot "in.png"
& $python $makeImgPath $inPng

# 6b) Run CLI: Delaunay → PNG + SVG (argument array to handle spaces)
$outPng   = Join-Path $tmpRoot "out_delaunay.png"
$metrics  = Join-Path $tmpRoot "metrics.json"

$cliArgs1 = @(
  "cubist_cli.py",
  "--input",        $inPng,
  "--geometry",     "delaunay",
  "--points",       "120",
  "--cascade-stages","3",
  "--seed",         "123",
  "--export-svg",
  "--output",       $outPng,
  "--metrics-json", $metrics
)
Write-Host "Running:" $python ($cliArgs1 -join ' ')
& $python @cliArgs1
if ($LASTEXITCODE -ne 0) { throw "PNG -> Delaunay CLI run failed. Exit $LASTEXITCODE" }

# 6c) SVG passthrough test
$svgPath = Join-Path $tmpRoot "simple.svg"
$svg = @"
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <polygon points="10,90 50,10 90,90" fill="#ff0000"/>
</svg>
"@
Set-Content -Path $svgPath -Value $svg -Encoding UTF8

$outDir = Join-Path $tmpRoot "svg_out\"
New-Item -ItemType Directory -Path $outDir | Out-Null

$cliArgs2 = @(
  "cubist_cli.py",
  "--input-svg",   $svgPath,
  "--geometry",    "svg",
  "--export-svg",
  "--output",      $outDir
)
Write-Host "Running:" $python ($cliArgs2 -join ' ')
& $python @cliArgs2
if ($LASTEXITCODE -ne 0) { throw "SVG passthrough CLI run failed. Exit $LASTEXITCODE" }

Write-Step "All checks and smoke tests passed ✅"

# 7) (Optional) Tag & push — left as a clearly marked spot if you want it automated.
# If you want this behavior, uncomment below and set -Push on script call.
# $version = "v2.2.3"
# if ($Push) {
#   git add -A
#   git commit -m "chore(release): $version"
#   git tag $version
#   git push origin $Branch
#   git push origin $version
#   Write-Host "Pushed $version to $Branch." -ForegroundColor Green
# } else {
#   Write-Host "(Skipping push; run with -Push to push tag/commit.)" -ForegroundColor Yellow
# }

# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:29+02:00
# === CUBIST FOOTER STAMP END ===
