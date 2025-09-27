<# =======================================================================
  Cubist Art — Fast Source Archiver (handoff builder) w/ Progress
  File: tools/archive_source.ps1

  Creates a compact handoff ZIP without staging a full copy:
    • Base = tracked files only (git ls-files)
    • Extras (opt-in): latest release_smoke dir, logs/, pip freeze
    • Writes in %TEMP% (fast), then moves one artifact into OutDir

  Shows progress for:
    - Collecting files
    - Dependency snapshot (pip freeze)
    - Compression (true % with 7-Zip; per-file % when streaming)
    - Final move

  Usage (from repo root):
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\tools\archive_source.ps1
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\tools\archive_source.ps1 `
      -OutDir .\handoff -IncludeLogs:$false -NoProgress

  Exit code: 0 on success; throws on failure.
======================================================================= #>

[CmdletBinding()]
param(
  [string]$OutDir = ".\handoff",
  [switch]$IncludeSmoke = $true,
  [switch]$IncludeLogs  = $true,
  [switch]$IncludeFreeze = $true,
  [switch]$EmitManifest = $true,
  # Suppress Write-Progress (useful for CI)
  [switch]$NoProgress = $false
)

$ErrorActionPreference = "Stop"

function Write-Log([string]$msg) {
  $ts = (Get-Date).ToString("s")
  Write-Host "$ts [archive] $msg"
}

function Update-Progress([int]$Id, [string]$Activity, [string]$Status, [int]$Percent) {
  if (-not $NoProgress) {
    Write-Progress -Id $Id -Activity $Activity -Status $Status -PercentComplete $Percent
  }
}
function Complete-Progress([int]$Id) {
  if (-not $NoProgress) { Write-Progress -Id $Id -Completed }
}

function Get-RepoRoot {
  try {
    $root = (git rev-parse --show-toplevel).Trim()
    if ([string]::IsNullOrWhiteSpace($root)) { throw "git rev-parse returned empty path." }
    return $root
  } catch {
    throw "Not inside a Git repository (git rev-parse failed)."
  }
}

function Get-VersionString([string]$RepoRoot) {
  $vf = Join-Path $RepoRoot "VERSION"
  if (Test-Path $vf) {
    try { return (Get-Content $vf -Raw).Trim() } catch { return "v0.0.0" }
  }
  return "v0.0.0"
}

function Get-TrackedFiles([string]$RepoRoot) {
  Push-Location $RepoRoot
  try {
    # Use tracked files only; skip anything that no longer exists in the working tree
    $trackedRel = (git ls-files) | Where-Object { $_ -and ($_ -ne "") }
    $missing = 0
    $existingAbs = foreach ($rel in $trackedRel) {
      $abs = Join-Path $RepoRoot $rel
      if (Test-Path -LiteralPath $abs) {
        # Normalize to absolute full path
        (Resolve-Path -LiteralPath $abs -ErrorAction SilentlyContinue).Path
      } else {
        $missing++
        Write-Log "WARN: tracked but missing in working tree: $rel"
      }
    }
    if ($missing -gt 0) { Write-Log "INFO: skipped $missing missing tracked file(s)" }
    return $existingAbs | Where-Object { $_ } | Sort-Object -Unique
  } finally { Pop-Location }
}

function Get-LatestSmokeFiles([string]$RepoRoot) {
  $smokeRoot = Join-Path $RepoRoot "output\release_smoke"
  if (-not (Test-Path $smokeRoot)) { return @() }
  $latest = Get-ChildItem $smokeRoot -Directory -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $latest) { return @() }
  return Get-ChildItem $latest.FullName -File -Recurse | ForEach-Object { (Resolve-Path $_.FullName).Path }
}

function Get-LogFiles([string]$RepoRoot) {
  $logRoot = Join-Path $RepoRoot "logs"
  if (-not (Test-Path $logRoot)) { return @() }
  return Get-ChildItem $logRoot -Recurse -File | ForEach-Object { (Resolve-Path $_.FullName).Path }
}

function Ensure-Freeze([string]$RepoRoot, [int]$ProgressId) {
  $req = Join-Path $RepoRoot "requirements.txt"
  Update-Progress $ProgressId "Dependency snapshot" "pip freeze → requirements.txt" 0
  try {
    python -m pip freeze | Set-Content -Encoding utf8 $req
    Update-Progress $ProgressId "Dependency snapshot" "pip freeze complete" 100
    return (Resolve-Path $req).Path
  } catch {
    Update-Progress $ProgressId "Dependency snapshot" "pip freeze failed; continuing" 100
    Write-Log "WARN: pip freeze failed: $($_.Exception.Message)"
    return $null
  } finally {
    Complete-Progress $ProgressId
  }
}

function New-Zip-Stream {
  param(
    [Parameter(Mandatory=$true)][string]$ZipPath,
    [Parameter(Mandatory=$true)][string[]]$Files,
    [Parameter(Mandatory=$true)][string]$RepoRoot,
    [int]$ProgressId = 3
  )
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $mode     = [System.IO.FileMode]::Create
  $fs       = [System.IO.File]::Open($ZipPath, $mode, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
  $zipMode  = [System.IO.Compression.ZipArchiveMode]::Create
  $zip      = New-Object System.IO.Compression.ZipArchive($fs, $zipMode, $false)

  try {
    $n = [double]$Files.Count
    $i = 0
    foreach ($abs in $Files) {
      $i++
      # Compute a repo-relative entry name (fallback to filename)
      $rel = $abs
      $rootWithSep = if ($RepoRoot.EndsWith('\') -or $RepoRoot.EndsWith('/')) { $RepoRoot } else { $RepoRoot + [IO.Path]::DirectorySeparatorChar }
      if ($abs.StartsWith($rootWithSep, [StringComparison]::OrdinalIgnoreCase)) {
        $rel = $abs.Substring($rootWithSep.Length)
      } else {
        $rel = Split-Path -Leaf $abs
      }
      # Normalize to forward slashes inside zip
      $rel = $rel -replace '\\','/'

      $entry = $zip.CreateEntry($rel, [System.IO.Compression.CompressionLevel]::Optimal)
      $in  = [System.IO.File]::OpenRead($abs)
      try {
        $out = $entry.Open()
        try { $in.CopyTo($out) } finally { $out.Dispose() }
      } finally { $in.Dispose() }

      $pct = [int](($i / $n) * 100)
      Update-Progress $ProgressId "Compressing (stream)" "$i / $([int]$n) files" $pct
    }
    Update-Progress $ProgressId "Compressing (stream)" "Finalizing…" 100
  } finally {
    $zip.Dispose()
    $fs.Dispose()
    Complete-Progress $ProgressId
  }
}

function New-FastHandoffZip {
  param(
    [Parameter(Mandatory=$true)][string]$RepoRoot,
    [Parameter(Mandatory=$true)][string]$OutDir,
    [switch]$IncludeSmoke,
    [switch]$IncludeLogs,
    [switch]$IncludeFreeze,
    [switch]$EmitManifest
  )

  $pCollect = 1
  $pFreeze  = 2
  $pZip     = 3
  $pMove    = 4

  # Build list
  Update-Progress $pCollect "Collecting files" "Enumerating tracked files…" 0

  $files = @()
  $tracked = Get-TrackedFiles $RepoRoot
  $files += $tracked
  $countTracked = $tracked.Count
  Update-Progress $pCollect "Collecting files" "Tracked: $countTracked" 25

  $smoke = @()
  if ($IncludeSmoke) {
    $smoke = Get-LatestSmokeFiles $RepoRoot
    $files += $smoke
  }
  Update-Progress $pCollect "Collecting files" ("Smoke: {0}" -f $smoke.Count) 50

  $logs = @()
  if ($IncludeLogs) {
    $logs = Get-LogFiles $RepoRoot
    $files += $logs
  }
  Update-Progress $pCollect "Collecting files" ("Logs: {0}" -f $logs.Count) 75

  if ($IncludeFreeze) {
    $req = Ensure-Freeze $RepoRoot $pFreeze
    if ($req) { $files += $req }
  }

  # De-dup and sort (stable)
  $files = $files | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Sort-Object -Unique
  if ($files.Count -eq 0) { throw "No files to archive." }
  Update-Progress $pCollect "Collecting files" ("Total: {0}" -f $files.Count) 100
  Complete-Progress $pCollect

  # Output names
  $ver = Get-VersionString $RepoRoot
  $ts  = (Get-Date).ToString("yyyyMMdd-HHmmss")
  $zipName = "handoff_${ver}_${ts}.zip"
  $zipTemp = Join-Path $env:TEMP $zipName
  if (Test-Path $zipTemp) { Remove-Item $zipTemp -Force }

  # Prefer 7-Zip if available (true progress)
  $sevenCandidates = @(
    "C:\Program Files\7-Zip\7z.exe",
    "C:\Program Files (x86)\7-Zip\7z.exe"
  )
  $seven = $sevenCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

  if ($seven) {
    Write-Log "Using 7-Zip"
    # Write absolute file list for robustness; 7z needs -spf2 to allow that.
    $listPath = Join-Path $env:TEMP ("filelist_" + [guid]::NewGuid() + ".txt")
    $files | Set-Content -Encoding utf8 $listPath

    Update-Progress $pZip "Compressing (7-Zip)" "Starting…" 0
    $args = @(
      "a", "-mx=6", "-mmt=on", "-bt", "-bsp1", "-bso0", "-spf2",
      $zipTemp, "@$listPath"
    )
    & $seven @args 2>&1 | ForEach-Object {
      $line = $_.ToString()
      $m = [regex]::Match($line, '(\d{1,3})%')
      if ($m.Success) {
        $pct = [int]$m.Groups[1].Value
        if ($pct -gt 100) { $pct = 100 }
        Update-Progress $pZip "Compressing (7-Zip)" $line $pct
      }
    }
    Update-Progress $pZip "Compressing (7-Zip)" "Finalizing…" 100
    Complete-Progress $pZip
    Remove-Item $listPath -Force -ErrorAction SilentlyContinue
  }
  else {
    Write-Log "Using streaming ZIP (no staging; .NET)"
    New-Zip-Stream -ZipPath $zipTemp -Files $files -RepoRoot $RepoRoot -ProgressId $pZip
  }

  # Move artifact into repo
  Update-Progress $pMove "Finalizing" "Moving artifact into output folder" 0
  $outAbs = Join-Path $RepoRoot $OutDir
  if (-not (Test-Path $outAbs)) { New-Item -ItemType Directory -Force $outAbs | Out-Null }
  $finalZip = Join-Path $outAbs (Split-Path $zipTemp -Leaf)
  Move-Item $zipTemp $finalZip -Force
  Update-Progress $pMove "Finalizing" "Done" 100
  Complete-Progress $pMove

  if ($EmitManifest) {
    $manifest = [ordered]@{
      version   = $ver
      created   = (Get-Date).ToString("o")
      repoRoot  = $RepoRoot
      outDir    = (Resolve-Path $outAbs).Path
      zip       = (Resolve-Path $finalZip).Path
      counts    = @{
        tracked = $tracked.Count
        smoke   = $smoke.Count
        logs    = $logs.Count
        total   = $files.Count
      }
    }
    $manifestPath = [System.IO.Path]::ChangeExtension($finalZip, ".json")
    ($manifest | ConvertTo-Json -Depth 5) | Set-Content -Encoding utf8 $manifestPath
  }

  return $finalZip
}

# ------------------------- Main -------------------------
$repo = Get-RepoRoot
Write-Log "repo = $repo"
try {
  $pythonCmd = (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
  Write-Log ("python = " + ($pythonCmd ?? "<not found>"))
} catch {
  Write-Log "python = <not found>"
}
try {
  $gitCmd = (Get-Command git -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
  Write-Log ("git = " + ($gitCmd ?? "<not found>"))
} catch {
  Write-Log "git = <not found>"
}

$zip = New-FastHandoffZip -RepoRoot $repo `
                          -OutDir $OutDir `
                          -IncludeSmoke:$IncludeSmoke `
                          -IncludeLogs:$IncludeLogs `
                          -IncludeFreeze:$IncludeFreeze `
                          -EmitManifest:$EmitManifest

Write-Host "Handoff ready: $zip"
exit 0
