# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: scripts/archive_source.ps1
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:47+02:00
# === CUBIST STAMP END ===
<#
.SYNOPSIS
    Package Cubist Art Tool source files into a clean ZIP archive for handoff.

.DESCRIPTION
    Collects all .py, .ps1, .bat, .md, .txt, and docs/scripts from the repo,
    excluding output/, archive/, logs, caches, venvs, and other generated files.

.USAGE
    powershell -ExecutionPolicy Bypass -File scripts\archive_source.ps1 [-ZipName "cubist_art_v23_prep.zip"]

.PARAMETER ZipName
    The name of the output zip file (default: cubist_art_v23_prep.zip).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\archive_source.ps1
    powershell -ExecutionPolicy Bypass -File scripts\archive_source.ps1 -ZipName "my_custom_name.zip"

.NOTES
    Run from the repo root. The archive will include only source and documentation files,
    not outputs or virtual environments.
#>

param(
    [string]$ZipName = "cubist_art_v23_prep.zip"
)

$RepoRoot = Resolve-Path "." | Select-Object -ExpandProperty Path
$IncludeExtensions = @("*.py","*.ps1","*.bat","*.md","*.txt")
$IncludeDirs       = @("docs","scripts")

$ExcludeDirs = @(
    "output","Archived Output","archive","logs","debug",
    "__pycache__",".pytest_cache",".mypy_cache",".ruff_cache",".ipynb_checkpoints",
    ".venv","venv","env",".idea",".vscode",".git"
)

Write-Host "[INFO] Packaging source files for handoff..."

$TempStaging = Join-Path $RepoRoot "package_staging"
if (Test-Path $TempStaging) { Remove-Item -Recurse -Force $TempStaging }
New-Item -ItemType Directory -Path $TempStaging | Out-Null

# Helper: is path under any excluded dir?
function Is-Excluded($file) {
    $parts = $file.DirectoryName.Split([IO.Path]::DirectorySeparatorChar)
    foreach ($ex in $ExcludeDirs) {
        if ($parts -contains $ex) { return $true }
    }
    return $false
}

# Collect files by extension
foreach ($ext in $IncludeExtensions) {
    Get-ChildItem -Path $RepoRoot -Recurse -Include $ext -File | Where-Object {
        -not (Is-Excluded $_)
    } | ForEach-Object {
        $rel = $_.FullName.Substring($RepoRoot.Length).TrimStart("\","/")
        $dest = Join-Path $TempStaging $rel
        $destDir = Split-Path $dest -Parent
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        Copy-Item $_.FullName -Destination $dest -Force
    }
}

# Collect include dirs fully if present (but skip excluded subdirs)
foreach ($dir in $IncludeDirs) {
    $src = Join-Path $RepoRoot $dir
    if (Test-Path $src) {
        Copy-Item $src -Destination $TempStaging -Recurse -Force -Exclude $ExcludeDirs
    }
}

# Create the zip
$ZipPath = Join-Path $RepoRoot $ZipName
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path "$TempStaging\*" -DestinationPath $ZipPath -Force

Write-Host "[INFO] Packaged archive created: $ZipPath"
Remove-Item -Recurse -Force $TempStaging



# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:47+02:00
# === CUBIST FOOTER STAMP END ===
