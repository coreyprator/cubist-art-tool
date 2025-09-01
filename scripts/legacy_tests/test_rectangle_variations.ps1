# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: scripts/legacy_tests/test_rectangle_variations.ps1
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:33+02:00
# === CUBIST STAMP END ===
param(
  [string]$Image = ".\input\your_image.jpg",
  [string]$Mask  = "",
  [int]$Points = 200
)

$ErrorActionPreference = "Stop"

# Set correct input file path
$Image = "input\your_input_image.jpg"

# Robust mask argument handling
if ($Mask -and -not [string]::IsNullOrWhiteSpace($Mask) -and (Test-Path -Path $Mask -PathType Leaf)) {
    $maskArg = @('--mask', $Mask)
} else {
    $maskArg = @()
}

# Robust SVG smoke runner with transcript and archiving

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$transcript = "logs\smoke_transcript_$timestamp.log"
if (!(Test-Path logs)) { New-Item -ItemType Directory -Path logs | Out-Null }
Start-Transcript -Path $transcript

Write-Host "=== SVG Smoke @ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" -ForegroundColor Cyan

# Archive previous outputs if any
$archiveDir = ".\output\archive\$timestamp"
if (Test-Path .\output) {
    $pngs = Get-ChildItem .\output\*.png -ErrorAction SilentlyContinue
    $svgs = Get-ChildItem .\output\*.svg -ErrorAction SilentlyContinue
    if ($pngs.Count -eq 0 -and $svgs.Count -eq 0) {
        Write-Host "No prior outputs to archive"
    } else {
        New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null
        foreach ($f in $pngs + $svgs) {
            Move-Item $f.FullName $archiveDir\
        }
        Write-Host "Archived prior outputs to $archiveDir"
    }
}

$Image = "input\your_input_image.jpg"
$OutDir = "output"
$Points = 120
$DoCascade = $true
$Timeout = 180
$Geometries = @("rectangles","delaunay","voronoi")

$results = @()
foreach ($geometry in $Geometries) {
    $stem = "$OutDir\smoke_${geometry}_${Points}"
    $png = "${stem}.png"
    $svg = "${stem}.svg"
    $cmd = "python test_cli.py --input `"$Image`" --output `"$OutDir`" --geometry $geometry --cascade_fill $DoCascade --points $Points --export-svg --timeout-seconds $Timeout --quiet:$false"
    Write-Host "`nSTART: $(Get-Date -Format 'HH:mm:ss') $cmd" -ForegroundColor Yellow
    $startTime = Get-Date
    $proc = Start-Process -FilePath "python" -ArgumentList "test_cli.py", "--input", $Image, "--output", $OutDir, "--geometry", $geometry, "--cascade_fill", "$DoCascade", "--points", "$Points", "--export-svg", "--timeout-seconds", "$Timeout", "--quiet:$false" -NoNewWindow -Wait -PassThru
    $exitCode = $proc.ExitCode
    $elapsed = (Get-Date) - $startTime
    $pngExists = Test-Path $png
    $svgExists = Test-Path $svg
    Write-Host "EXIT: $geometry code=$exitCode elapsed=$($elapsed.TotalSeconds) sec"
    if ($exitCode -ne 0 -or -not $pngExists) {
        Write-Host "FAILED: $geometry (exit $exitCode, PNG exists: $pngExists)" -ForegroundColor Red
        continue
    }
    Write-Host "CREATED: $png" -ForegroundColor Green
    if ($svgExists) {
        Write-Host "CREATED: $svg" -ForegroundColor Green
    } else {
        Write-Host "SVG NOT FOUND: $svg" -ForegroundColor Red
    }
    $results += $png
}

Write-Host "`n=== Output Summary ===" -ForegroundColor Cyan
Get-ChildItem $OutDir -Include *.png,*.svg -File | Select-Object Name,Length | Format-Table -AutoSize

if (Test-Path "logs\run_log.txt") {
    Write-Host "`n=== Last 80 lines of run log ===" -ForegroundColor Cyan
    Get-Content "logs\run_log.txt" -Tail 80
}

Write-Host "Latest results are in: .\output" -ForegroundColor Yellow

Stop-Transcript

if ($results.Count -gt 0) { exit 0 } else { exit 2 }

# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:33+02:00
# === CUBIST FOOTER STAMP END ===
