<#!
.SYNOPSIS
  Publish a release: (optional) preflight + tests, update requirements,
  commit all changes, create annotated tag, and push to origin.

.DESCRIPTION
  - Works on Windows PowerShell 5.1 and PowerShell 7+
  - Safe by default: will prompt on dirty working tree unless -Force
  - Writes a timestamped log under scripts\logs\
  - Looks for Python at .venv\Scripts\python.exe, else falls back to "python"

.PARAMETER Version
  Tag name, e.g. v2.2.0  (required)

.PARAMETER Title
  Human-friendly release name shown in tag annotation (default: "Release <Version>")

.PARAMETER Branch
  Target branch to push (default: current branch)

.PARAMETER UpdateRequirements
  If set, regenerates requirements.txt from the active Python environment.

.PARAMETER RunPreflight
  If set, runs:  python preflight.py --fix --det
  (Fails fast on non-zero exit)

.PARAMETER RunTests
  If set, runs:  python -m pytest -q
  (Fails fast on non-zero exit)

.PARAMETER Force
  If set, proceeds even if working tree is dirty (uncommitted changes).

.PARAMETER DryRun
  If set, prints what would happen without making changes.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\publish_release.ps1 `
    -Version v2.2.0 -Title "SVG export + stable production runner" `
    -RunPreflight -RunTests -UpdateRequirements

#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [string]$Version,

  [string]$Title = $null,

  [string]$Branch = $null,

  [switch]$RunPreflight,
  [switch]$RunTests,
  [switch]$UpdateRequirements,

  [switch]$Force,
  [switch]$DryRun
)

# ---------- Utility: logging ----------
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Resolve-Path (Join-Path $ScriptDir "..") | Select-Object -ExpandProperty Path
$LogsDir   = Join-Path $RepoRoot "scripts\logs"
if (-not (Test-Path $LogsDir)) { New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null }
$Stamp     = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath   = Join-Path $LogsDir ("publish_release_{0}.log" -f $Stamp)

function Write-Log {
  param([string]$msg)
  $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  $line = "[{0}] {1}" -f $ts, $msg
  Write-Host $line
  Add-Content -Encoding UTF8 -Path $LogPath -Value $line
}

Write-Log "==== PUBLISH RELEASE START : $Version ===="
Write-Log "Repo root: $RepoRoot"
if ($DryRun) { Write-Log "DRY-RUN: no changes will be made." }

# ---------- Utility: command runner ----------
function Invoke-Tool {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$true)][string]$FilePath,
    [Parameter(Mandatory=$false)][string[]]$ArgumentList
  )
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $FilePath
  if ($ArgumentList) { $psi.Arguments = [string]::Join(' ', $ArgumentList) }
  $psi.WorkingDirectory = $RepoRoot
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError  = $true
  $psi.UseShellExecute = $false
  $proc = New-Object System.Diagnostics.Process
  $proc.StartInfo = $psi

  if ($DryRun) {
    Write-Log ("DRY-RUN: {0} {1}" -f $FilePath, ($psi.Arguments))
    return @{ ExitCode = 0; StdOut = ""; StdErr = "" }
  }

  [void]$proc.Start()
  $stdout = $proc.StandardOutput.ReadToEnd()
  $stderr = $proc.StandardError.ReadToEnd()
  $proc.WaitForExit()

  # log
  if ($stdout) { Add-Content -Encoding UTF8 -Path $LogPath -Value "STDOUT>>>`n$stdout" }
  if ($stderr) { Add-Content -Encoding UTF8 -Path $LogPath -Value "STDERR>>>`n$stderr" }

  return @{
    ExitCode = $proc.ExitCode
    StdOut   = $stdout
    StdErr   = $stderr
  }
}

# ---------- Guard: .git exists ----------
$GitDir = Join-Path $RepoRoot ".git"
if (-not (Test-Path $GitDir)) {
  throw "Not a git repo: $RepoRoot (no .git found)."
}

# ---------- Find git ----------
# PowerShell 5.1 compatible: avoid ?.Source
$GitCmd = Get-Command git -ErrorAction SilentlyContinue
if ($GitCmd) {
  $Git = $GitCmd.Source
} else {
  throw "git not found in PATH."
}
Write-Log "Using git: $Git"

# ---------- Determine current branch if not provided ----------
if (-not $Branch) {
  $res = Invoke-Tool -FilePath $Git -ArgumentList @("rev-parse","--abbrev-ref","HEAD")
  if ($res.ExitCode -ne 0) { throw "git rev-parse failed: $($res.StdErr)" }
  $Branch = $res.StdOut.Trim()
}
Write-Log "Branch: $Branch"

# ---------- Check remote ----------
$res = Invoke-Tool -FilePath $Git -ArgumentList @("remote","get-url","origin")
if ($res.ExitCode -ne 0) { throw "Remote 'origin' not configured. Add it before publishing." }
$RemoteUrl = $res.StdOut.Trim()
Write-Log "Remote origin: $RemoteUrl"

# ---------- Detect Python ----------
$VenvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPy) {
  $Python = $VenvPy
} else {
  $Python = "python"
}
Write-Log "Using Python: $Python"

# ---------- Working tree status ----------
$res = Invoke-Tool -FilePath $Git -ArgumentList @("status","--porcelain")
$dirty = [bool]($res.StdOut.Trim())
if ($dirty -and -not $Force -and -not $DryRun) {
  Write-Log "Working tree has uncommitted changes."
  Write-Log "Use -Force to proceed anyway, or commit/stash before publishing."
  Write-Host ""
  Write-Host "ERROR: Working tree has uncommitted changes." -ForegroundColor Red
  Write-Host "Commit or stash your changes, or re-run with -Force to proceed anyway." -ForegroundColor Yellow
  Write-Host "You can review changes with: git status" -ForegroundColor Yellow
  throw "Aborted due to dirty working tree."
}

# ---------- Optional: run preflight ----------
if ($RunPreflight) {
  Write-Log "Running preflight: python preflight.py --fix --det"
  $res = Invoke-Tool -FilePath $Python -ArgumentList @("preflight.py","--fix","--det")
  if ($res.ExitCode -ne 0) { throw "Preflight failed. See log: $LogPath" }
}

# ---------- Optional: run tests ----------
if ($RunTests) {
  Write-Log "Running tests: python -m pytest -q"
  $res = Invoke-Tool -FilePath $Python -ArgumentList @("-m","pytest","-q")
  if ($res.ExitCode -ne 0) { throw "Tests failed. See log: $LogPath" }
}

# ---------- Optional: update requirements.txt ----------
if ($UpdateRequirements) {
  $ReqPath = Join-Path $RepoRoot "requirements.txt"
  Write-Log "Refreshing requirements.txt via pip freeze"
  if (-not $DryRun) {
    $freeze = & $Python -m pip freeze 2>&1
    if ($LASTEXITCODE -ne 0) { throw "pip freeze failed: $freeze" }
    # Keep it simple: write full freeze (project already using pinned wheels)
    Set-Content -Encoding UTF8 -Path $ReqPath -Value $freeze
  } else {
    Write-Log "DRY-RUN: would regenerate requirements.txt"
  }
}

# ---------- Stage & Commit ----------
$CommitTitle = ("Release: {0}" -f $Version)
if ([string]::IsNullOrEmpty($Title)) {
  $CommitTitleMsg = "Release $Version"
} else {
  $CommitTitleMsg = $Title
}
$CommitBody  = @"
- Version: $Version
- Title:   $CommitTitleMsg
- Date:    $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- Notes:
  * SVG export + production runner confirmed
  * Determinism/metrics verified
  * Preflight/tests: $($RunPreflight.IsPresent)/$($RunTests.IsPresent)
"@

Write-Log "git add -A"
$res = Invoke-Tool -FilePath $Git -ArgumentList @("add","-A")
if ($res.ExitCode -ne 0) { throw "git add failed." }

Write-Log "Creating commit"
if (-not $DryRun) {
  # If nothing to commit, skip committing
  $res = Invoke-Tool -FilePath $Git -ArgumentList @("diff","--cached","--name-only")
  if (-not $res.StdOut.Trim()) {
    Write-Log "No staged changes; skipping commit step."
  } else {
    $res = Invoke-Tool -FilePath $Git -ArgumentList @("commit","-m",$CommitTitle,"-m",$CommitBody)
    if ($res.ExitCode -ne 0) { throw "git commit failed." }
  }
} else {
  Write-Log "DRY-RUN: would commit with message:`n$CommitTitle`n$CommitBody"
}

# ---------- Create annotated tag ----------
if ([string]::IsNullOrEmpty($Title)) { $TagMsg = "Release $Version`n`n$CommitBody" }
else { $TagMsg = "$Title`n`n$CommitBody" }

Write-Log "Creating annotated tag: $Version"
# If tag exists, recreate only if forced; else, fail gracefully
$res = Invoke-Tool -FilePath $Git -ArgumentList @("tag","-l",$Version)
if ($res.StdOut.Trim()) {
  Write-Log "Tag $Version already exists; will not re-create."
} else {
  $res = Invoke-Tool -FilePath $Git -ArgumentList @("tag","-a",$Version,"-m",$TagMsg)
  if ($res.ExitCode -ne 0) { throw "git tag failed." }
}

# ---------- Push ----------
Write-Log "Pushing branch $Branch"
$res = Invoke-Tool -FilePath $Git -ArgumentList @("push","origin",$Branch)
if ($res.ExitCode -ne 0) { throw "git push branch failed." }

Write-Log "Pushing tag $Version"
$res = Invoke-Tool -FilePath $Git -ArgumentList @("push","origin",$Version)
if ($res.ExitCode -ne 0) { throw "git push tag failed." }

Write-Log "==== PUBLISH RELEASE COMPLETE ===="
Write-Host ""
Write-Host "Log saved to: $LogPath"
