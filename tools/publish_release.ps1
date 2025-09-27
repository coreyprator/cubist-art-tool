<# =====================================================================
 publish_release.ps1  — release helper with smoke (SVG+PNG) and handoff
 ----------------------------------------------------------------------
 Features
   • Stamps repo (tools/stamp_repo.py) with VERSION + build ts
   • Formats (ruff), runs tests (pytest -q)
   • Smoke test for core geometries: SVG required; PNG validated.
       - If PNG missing, converts SVG→PNG with CairoSVG (if present)
   • Commits, tags, pushes
   • Optional GitHub release via gh CLI
   • NEW: -EmitHandoff builds a portable zip by calling tools/archive_source.ps1
           (-HandoffAttach uploads the zip to the GitHub release)

 Examples
   pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass `
     -File .\tools\publish_release.ps1 `
     -Branch "milestone/v2.3.7.5  PF Handoff" -Diag -EmitHandoff -HandoffAttach

   # CI-ish, but skip GitHub release page:
   pwsh -File .\tools\publish_release.ps1 -NoRelease -EmitHandoff
===================================================================== #>

[CmdletBinding()]
param(
  [string]$Branch,
  [switch]$Diag,
  [switch]$NoRelease,
  [switch]$Force,

  # Handoff bundle options
  [switch]$EmitHandoff,
  [string]$HandoffOutRoot = ".\handoff",
  [switch]$HandoffAttach
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Stamp([string]$msg) {
  $ts = Get-Date -Format s
  Write-Host "$ts $msg"
}

function Get-RepoRoot {
  try {
    $r = (git rev-parse --show-toplevel 2>$null)
    if ($r) { return $r }
  } catch { }
  if ($PSScriptRoot) {
    $parent = Split-Path $PSScriptRoot -Parent
    if (Test-Path (Join-Path $parent ".git")) { return $parent }
    $parent2 = Split-Path $parent -Parent
    if (Test-Path (Join-Path $parent2 ".git")) { return $parent2 }
  }
  return (Get-Location).Path
}

function Prefer-Python {
  $repo = Get-RepoRoot
  $venv = Join-Path $repo ".venv\Scripts\python.exe"
  if (Test-Path $venv) { return $venv }
  return "python"
}

function Require-CleanTree {
  param([switch]$AllowDirty)
  if ($AllowDirty) { return }
  $st = git status --porcelain
  if ($st) {
    throw "Working tree is dirty. Commit/stash or rerun with -Force."
  }
}

function Run-Exec {
  param(
    [Parameter(Mandatory)] [string]$Exe,
    [Parameter(Mandatory)] [string[]]$Args
  )
  Write-Stamp "RUN> $Exe $($Args -join ' ')"
  $p = Start-Process -FilePath $Exe -ArgumentList $Args -Wait -NoNewWindow -PassThru -RedirectStandardOutput "STDOUT.tmp" -RedirectStandardError "STDERR.tmp"
  $out = (Get-Content "STDOUT.tmp" -Raw) 2>$null
  $err = (Get-Content "STDERR.tmp" -Raw) 2>$null
  if ($out) { Write-Output $out.TrimEnd() }
  if ($err) { Write-Output $err.TrimEnd() }
  Remove-Item "STDOUT.tmp","STDERR.tmp" -Force -ErrorAction SilentlyContinue
  return $p.ExitCode
}

function Has-Command($name) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  return [bool]$cmd
}

# --- Begin --------------------------------------------------------------------

$repo = Get-RepoRoot
Set-Location $repo
$python = Prefer-Python

$VERSION_FILE = Join-Path $repo "VERSION"
$Version = (Test-Path $VERSION_FILE) ? ((Get-Content $VERSION_FILE -Raw).Trim()) : "0.0.0"
$BuildTs = Get-Date -Format s

if (-not $Branch) {
  $Branch = (git branch --show-current).Trim()
}

Write-Stamp "[repo] root = $repo"
Write-Stamp "[python] $python"
Write-Stamp "[version] $Version"
Write-Stamp "[build] $BuildTs"
Write-Stamp "[git] Already on branch: $Branch"
Write-Stamp "[branch] active = $Branch"

# Guard dirty tree unless -Force
Require-CleanTree -AllowDirty:$Force

# 1) Stamp repo
$stampArgs = @((Join-Path $repo "tools\stamp_repo.py"), "--version", $Version, "--build-ts", $BuildTs)
$code = Run-Exec $python $stampArgs
Write-Output $code

# 2) Format / lint
$code = Run-Exec "ruff" @("check","--fix"); Write-Output $code
$code = Run-Exec "ruff" @("format"); Write-Output $code

# 3) Tests
$code = Run-Exec "pytest" @("-q")
if ($code -ne 0) { throw "pytest failed with exit $code" }

# 4) Smoke (SVG + PNG verification)
$smokeRoot = Join-Path $repo ("output\release_smoke\" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $smokeRoot | Out-Null
Write-Stamp "[smoke] root = $smokeRoot"

# Make an input PNG
$makeInput = @"
from PIL import Image, ImageDraw
img = Image.new('RGB',(320,240),'white')
d = ImageDraw.Draw(img)
d.rectangle((20,20,300,220), outline=(0,0,0), width=3)
d.ellipse((120,60,200,140), outline=(200,0,0), width=3)
img.save(r'$($smokeRoot.Replace('\','\\'))\in.png')
"@
$tmpPy = Join-Path $smokeRoot "make_input.py"
$makeInput | Set-Content -Encoding utf8 $tmpPy
$code = Run-Exec $python @($tmpPy)
Write-Stamp ("created " + (Join-Path $smokeRoot "in.png"))

$geos = @("delaunay","voronoi","rectangles")
foreach ($g in $geos) {
  $outDir = Join-Path $smokeRoot $g
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null
  $args = @(
    (Join-Path $repo "tools\run_cli.py"),
    "--input", (Join-Path $smokeRoot "in.png"),
    "--output", $outDir,
    "--geometry", $g,
    "--points", "300",
    "--seed", "123",
    "--cascade-stages", "2",
    "--export-svg"
  )
  $code = Run-Exec $python $args
  if ($code -ne 0) { throw "run_cli failed for $g (exit $code)" }

  $svg = Join-Path $outDir "$g.svg"
  if (-not (Test-Path $svg)) { throw "Smoke: missing SVG for $g: $svg" }
  $svgSize = (Get-Item $svg).Length
  if ($svgSize -lt 100) { throw "Smoke: $g SVG too small ($svgSize bytes)" }
  Write-Stamp "[smoke] ok: $g SVG => $svg ($svgSize bytes)"

  # PNG check or fallback via CairoSVG
  $png = Join-Path $outDir "$g.png"
  if (-not (Test-Path $png)) {
    # Try cairosvg (if installed)
    $tryCairo = @()
    try {
      $tryCairo = & $python -m pip show cairosvg 2>$null
    } catch { $tryCairo = @() }
    if ($tryCairo) {
      Write-Stamp "[smoke] PNG missing for $g; generating via CairoSVG"
      $code = Run-Exec $python @("-m","cairosvg","-f","png","-o",$png,$svg)
      if ($code -ne 0) { throw "CairoSVG failed for $g (exit $code)" }
    }
  }

  if (-not (Test-Path $png)) {
    throw "Smoke: missing PNG for $g after fallback: $png"
  }
  $pngSize = (Get-Item $png).Length
  if ($pngSize -lt 100) { throw "Smoke: $g PNG too small ($pngSize bytes)" }
  Write-Stamp "[smoke] ok: $g PNG => $png ($pngSize bytes)"
}
Write-Stamp "[smoke] All geometries passed."

# 5) Commit (run twice if pre-commit mutates)
$null = Run-Exec "git" @("add","-A")
$msg1 = "v$Version — automated release publish"
$code = Run-Exec "git" @("commit","-m",$msg1)
if ($code -ne 0) {
  Write-Stamp "[commit] Retrying commit after pre-commit changes."
  $null = Run-Exec "git" @("add","-A")
  $msg2 = "v$Version — fixup after pre-commit"
  $code2 = Run-Exec "git" @("commit","-m",$msg2)
  if ($code2 -ne 0) {
    Write-Stamp "[commit] Nothing to commit or commit failed again; continuing."
  }
}

# 6) Tag & push
$tag = "v$Version"
$null = Run-Exec "git" @("tag","-a",$tag,"-m","$tag release")
$null = Run-Exec "git" @("push","--set-upstream","origin",$Branch)
$null = Run-Exec "git" @("push","--tags")

# 7) GitHub Release (optional)
$gh = (Has-Command "gh") ? "gh" : $null
$didRelease = $false
if (-not $NoRelease -and $gh) {
  try {
    $code = Run-Exec $gh @("release","view",$tag)
    if ($code -ne 0) {
      $code = Run-Exec $gh @("release","create",$tag,"--target",$Branch,"-t",$tag,"-n","$tag release")
      if ($code -ne 0) { throw "gh release create failed (exit $code)" }
    }
    $didRelease = $true
  } catch {
    Write-Stamp "[gh] Release step skipped: $($_.Exception.Message)"
  }
} else {
  Write-Stamp "[gh] Skipped GitHub release (NoRelease or gh not installed)."
}

# 8) (NEW) Emit handoff bundle (and optionally attach to release)
if ($EmitHandoff) {
  $archiver = Join-Path $repo "tools\archive_source.ps1"
  if (-not (Test-Path $archiver)) {
    Write-Stamp "[handoff] WARNING: missing tools/archive_source.ps1 — skipping bundle."
  } else {
    Write-Stamp "[handoff] Building bundle…"
    # Track newest zip before
    $before = Get-ChildItem $HandoffOutRoot -Filter "*.zip" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    $args = @(
      "-NoLogo","-NoProfile","-ExecutionPolicy","Bypass",
      "-File", $archiver,
      "-OutRoot", $HandoffOutRoot,
      "-IncludeLogs","-IncludeSmoke","-RunFreeze","-Zip",
      "-Branch", $Branch,
      "-Tag", $tag
    )
    $code = Run-Exec "pwsh" $args
    if ($code -ne 0) { Write-Stamp "[handoff] archive_source exited $code (continuing)" }

    Start-Sleep -Milliseconds 500
    $after = Get-ChildItem $HandoffOutRoot -Filter "*.zip" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    $zipPath = $null
    if ($after) {
      if (-not $before -or $after.LastWriteTime -gt $before.LastWriteTime) {
        $zipPath = $after.FullName
      }
    }
    if ($zipPath) {
      Write-Stamp "[handoff] DONE: $zipPath"
      if ($HandoffAttach -and $didRelease -and $gh) {
        Write-Stamp "[handoff] Uploading to release $tag…"
        $code = Run-Exec $gh @("release","upload",$tag,$zipPath,"--clobber")
        if ($code -ne 0) {
          Write-Stamp "[handoff] upload failed (exit $code)"
        }
      } elseif ($HandoffAttach -and -not $didRelease) {
        Write-Stamp "[handoff] Skipping attach: no GitHub release was created."
      }
    } else {
      Write-Stamp "[handoff] Could not locate newly created handoff zip."
    }
  }
}

Write-Stamp "[done] Published $tag on branch $Branch"
exit 0
