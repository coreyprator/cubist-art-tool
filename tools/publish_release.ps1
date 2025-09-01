<#
===============================================================================
 Cubist Art — Release Publisher (with Ruff + Prod Smoke gate)
 File: tools/publish_release.ps1
 Version: v2.3.9
 Build: 2025-09-01T10:28:00
===============================================================================

What it does (in order):
  1) Resolve repo root, Python, branch, version (param or VERSION file)
  2) Optionally stamp headers/footers via tools/stamp_repo.py
  3) Run Ruff (format + fix)  ← gate (fail stops)
  4) Run tests (pytest -q)    ← gate (fail stops)
  5) Run Production Smoke     ← gate (fail stops)
     - Generates tiny PNG input
     - Runs tools/run_cli.py for: delaunay, voronoi, rectangles
     - Verifies at least one SVG (>0 bytes) per geometry
  6) Commit changes (robust to pre-commit modifying files)
  7) Create tag if missing and push branch + tags
  8) Optionally create a GitHub Release if `gh` is available

Examples:
  pwsh -f tools/publish_release.ps1
  pwsh -f tools/publish_release.ps1 -Version v2.3.9 -BuildTs (Get-Date -Format s) -Branch milestone/v2.3.9

Parameters:
  -Version         Version string; if omitted, reads ./VERSION
  -BuildTs         Build timestamp (ISO). Default = now (local time)
  -Branch          Branch to publish from. Default = current branch
  -ReleaseNotes    Path to release notes used by GitHub release (optional)
  -NoStamp         Skip stamping headers/footers
  -NoTests         Skip pytest (Ruff and Smoke still run unless disabled)
  -NoRuff          Skip Ruff lint/format (not recommended)
  -NoSmoke         Skip production smoke (not recommended)
  -NoTag           Skip creating/pushing tag
  -NoRelease       Skip GitHub release creation
  -Force           Proceed even if working tree is dirty
  -DryRun          Print actions but don’t execute
===============================================================================
#>

[CmdletBinding(PositionalBinding=$false)]
param(
  [string]$Version,
  [string]$BuildTs,
  [string]$Branch,
  [string]$ReleaseNotes,
  [switch]$NoStamp,
  [switch]$NoTests,
  [switch]$NoRuff,
  [switch]$NoSmoke,
  [switch]$NoTag,
  [switch]$NoRelease,
  [switch]$Force,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function TS([string]$Msg) {
  $t = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
  Write-Host "$t $Msg"
}

function Invoke-Proc {
  param(
    [Parameter(Mandatory=$true)][string]$FilePath,
    [Parameter()][string[]]$Arguments = @(),
    [switch]$IgnoreExit
  )
  TS "RUN> $FilePath $($Arguments -join ' ')"
  if ($DryRun) { return 0 }
  & $FilePath @Arguments
  $code = $LASTEXITCODE
  if (-not $IgnoreExit -and $code -ne 0) {
    throw "Command failed ($code): $FilePath $($Arguments -join ' ')"
  }
  return $code
}

function Git-Top {
  try {
    $top = (git rev-parse --show-toplevel).Trim()
    if (-not $top) { throw "not a git repo" }
    return $top
  } catch {
    throw "This directory is not a Git repository."
  }
}

function Git-CurrentBranch {
  try { (git branch --show-current).Trim() } catch { return "" }
}

function Git-IsClean {
  $status = (git status --porcelain)
  return [string]::IsNullOrWhiteSpace($status)
}

function Ensure-Branch([string]$RepoRoot, [string]$Desired) {
  $current = Git-CurrentBranch
  if ([string]::IsNullOrEmpty($Desired)) {
    if ([string]::IsNullOrEmpty($current)) { throw "Detached HEAD; specify -Branch." }
    TS "[git] Using current branch: $current"
    return $current
  }
  if ($current -eq $Desired) {
    TS "[git] Already on branch: $Desired"
    return $Desired
  }
  try {
    Invoke-Proc -FilePath "git" -Arguments @("switch", $Desired) -IgnoreExit
  } catch {
    TS "[git] Branch '$Desired' not found; creating it."
    Invoke-Proc -FilePath "git" -Arguments @("switch", "-c", $Desired)
  }
  return $Desired
}

function Ensure-File([string]$Path) {
  if (-not (Test-Path $Path)) { throw "Required file not found: $Path" }
}

# --- Resolve repo context ----------------------------------------------------
$RepoRoot = Git-Top
Set-Location $RepoRoot
TS "[repo] root = $RepoRoot"

# Resolve Python (prefer venv)
$VenvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Python = (Test-Path $VenvPy) ? $VenvPy : "python"
TS "[python] $Python"

# Resolve Version
if (-not $Version) {
  $verFile = Join-Path $RepoRoot "VERSION"
  if (Test-Path $verFile) { $Version = (Get-Content $verFile -Raw).Trim() }
  else { throw "No -Version provided and VERSION file not found." }
}
if (-not $Version.StartsWith("v")) { $Version = "v$Version" }
TS "[version] $Version"

# Resolve BuildTs
if (-not $BuildTs) { $BuildTs = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") }
TS "[build] $BuildTs"

# Resolve/Ensure branch
$Branch = Ensure-Branch -RepoRoot $RepoRoot -Desired $Branch
TS "[branch] active = $Branch"

# Safety: clean tree unless forced
if (-not $Force -and -not (Git-IsClean)) {
  throw "Working tree is dirty. Commit/stash or rerun with -Force."
}

# --- Required project files --------------------------------------------------
$StampScript = Join-Path $RepoRoot "tools\stamp_repo.py"
Ensure-File $StampScript
$VersioningPy = Join-Path $RepoRoot "versioning.py"
Ensure-File $VersioningPy
$RunCli = Join-Path $RepoRoot "tools\run_cli.py"
Ensure-File $RunCli

# --- Actions ----------------------------------------------------------------
# 1) Stamp (unless skipped)
if (-not $NoStamp) {
  Invoke-Proc -FilePath $Python -Arguments @($StampScript, "--version", $Version, "--build-ts", $BuildTs)
} else {
  TS "[stamp] Skipped by -NoStamp"
}

# 2) Ruff (unless skipped)  ← gate
if (-not $NoRuff) {
  Invoke-Proc -FilePath "ruff" -Arguments @("check", "--fix")
  Invoke-Proc -FilePath "ruff" -Arguments @("format")
} else {
  TS "[ruff] Skipped by -NoRuff"
}

# 3) Tests (unless skipped) ← gate
if (-not $NoTests) {
  Invoke-Proc -FilePath "pytest" -Arguments @("-q")
} else {
  TS "[tests] Skipped by -NoTests"
}

# 4) Production Smoke (unless skipped) ← gate
function Make-TestImage([string]$PythonExe, [string]$OutPng) {
  $code = @'
from PIL import Image
import sys
p=sys.argv[1]
img=Image.new("RGB",(160,120),(90,110,130))
img.save(p)
print("created",p)
'@
  $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("mkimg_"+[Guid]::NewGuid().ToString()+".py")
  Set-Content -Path $tmp -Value $code -Encoding UTF8
  try {
    & $PythonExe $tmp $OutPng
    if ($LASTEXITCODE -ne 0) { throw "python image gen failed ($LASTEXITCODE)" }
  } finally {
    Remove-Item -Path $tmp -ErrorAction SilentlyContinue
  }
}

function Assert-NonEmptyFile([string]$Path, [string]$Desc) {
  if (-not (Test-Path $Path)) { throw ("Smoke: missing {0}: {1}" -f $Desc, $Path) }
  $len = (Get-Item $Path).Length
  if ($len -lt 64) { throw ("Smoke: {0} too small ({1} bytes): {2}" -f $Desc, $len, $Path) }
  TS ("[smoke] ok: {0} => {1} ({2} bytes)" -f $Desc, $Path, $len)
}

function Run-Geom([string]$Geom, [string]$InPng, [string]$OutDir) {
  New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
  $args = @(
    $RunCli,
    "--input", $InPng,
    "--output", $OutDir,
    "--geometry", $Geom,
    "--points", "300",
    "--seed", "123",
    "--cascade-stages", "2",
    "--export-svg"
  )
  Invoke-Proc -FilePath $Python -Arguments $args
  # verify: at least one SVG non-empty
  $svgs = Get-ChildItem -Path $OutDir -Filter *.svg -ErrorAction SilentlyContinue
  if (-not $svgs) { throw ("Smoke: {0}: no SVG produced in {1}" -f $Geom, $OutDir) }
  $first = $svgs[0].FullName
  Assert-NonEmptyFile -Path $first -Desc ("{0} SVG" -f $Geom)
}

if (-not $NoSmoke) {
  $smokeRoot = Join-Path $RepoRoot ("output\release_smoke\" + (Get-Date -Format "yyyyMMdd-HHmmss"))
  New-Item -ItemType Directory -Force -Path $smokeRoot | Out-Null
  TS "[smoke] root = $smokeRoot"
  $inPng = Join-Path $smokeRoot "in.png"
  Make-TestImage -PythonExe $Python -OutPng $inPng
  Run-Geom -Geom "delaunay"  -InPng $inPng -OutDir (Join-Path $smokeRoot "delaunay")
  Run-Geom -Geom "voronoi"   -InPng $inPng -OutDir (Join-Path $smokeRoot "voronoi")
  Run-Geom -Geom "rectangles"-InPng $inPng -OutDir (Join-Path $smokeRoot "rectangles")
  TS "[smoke] All geometries passed."
} else {
  TS "[smoke] Skipped by -NoSmoke"
}

# 5) Commit (robust to pre-commit mutations)
function Do-Commit([string]$Msg) {
  Invoke-Proc -FilePath "git" -Arguments @("add", "-A")
  $code = Invoke-Proc -FilePath "git" -Arguments @("commit", "-m", $Msg) -IgnoreExit
  return $code
}
$commitMsg = "$($Version): automated release publish"
$code = Do-Commit -Msg $commitMsg
if ($code -ne 0) {
  TS "[commit] Retrying commit after pre-commit changes…"
  $code = Do-Commit -Msg "$($Version): fixup after pre-commit"
  if ($code -ne 0) { TS "[commit] Nothing to commit or commit failed again; continuing." }
}

# 6) Tag & Push
if (-not $NoTag) {
  $tagExists = $false
  try {
    git show-ref --tags --verify --quiet "refs/tags/$Version"
    if ($LASTEXITCODE -eq 0) { $tagExists = $true }
  } catch { }
  if (-not $tagExists) {
    Invoke-Proc -FilePath "git" -Arguments @("tag", "-a", $Version, "-m", "$($Version) release")
  } else {
    TS "[tag] $Version already exists; skipping."
  }
} else {
  TS "[tag] Skipped by -NoTag"
}

Invoke-Proc -FilePath "git" -Arguments @("push", "--set-upstream", "origin", $Branch) -IgnoreExit
if (-not $NoTag) {
  Invoke-Proc -FilePath "git" -Arguments @("push", "--tags") -IgnoreExit
}

# 7) GitHub Release (optional)
function Has-GH { try { gh --version > $null 2>&1; return $true } catch { return $false } }
if (-not $NoRelease -and (Has-GH)) {
  $rnArgs = @()
  if ($ReleaseNotes) {
    if (-not (Test-Path $ReleaseNotes)) { throw "Release notes file not found: $ReleaseNotes" }
    $rnArgs = @("-F", (Resolve-Path $ReleaseNotes).Path)
  } else {
    $rnArgs = @("--generate-notes")
  }
  $exists = $false
  try {
    gh release view $Version > $null 2>&1
    if ($LASTEXITCODE -eq 0) { $exists = $true }
  } catch { }
  if (-not $exists) {
    Invoke-Proc -FilePath "gh" -Arguments @("release", "create", $Version, "-t", $Version) + $rnArgs
  } else {
    TS "[gh] Release $Version exists; skipping creation."
  }
} else {
  TS "[gh] Skipped GitHub release (NoRelease or gh not installed)."
}

TS "[done] Published $Version on branch $Branch"
exit 0
