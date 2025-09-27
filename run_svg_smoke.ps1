# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: run_svg_smoke.ps1
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:44+02:00
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
# Geometries supported by the current test_cli (keep in sync with CLI)
$Geometries = @("delaunay","voronoi","rectangles")
# test_cli does not accept a --verbose flag; keep verbose control inside CLI if needed
$VerboseRun = $false

# Set python output encoding up-front so child processes print utf-8 to the console
$env:PYTHONIOENCODING = "utf-8"

$results = @()
$svgs = @()     # collect generated svg paths
$failed = @()   # collect failed geometry names (and short reason)
$exit_status = 0

foreach ($geometry in $Geometries) {
    $stem = "$OutDir\smoke_${geometry}_${Points}"
#    $png = "${stem}.png"
    $svg = "${stem}.svg"

    # Build argument array (use explicit args for safety)
    $args = @("test_cli.py", "--input", $Image, "--output", $OutDir, "--geometry", $geometry, "--cascade_fill", "$DoCascade", "--points", "$Points", "--export-svg", "--timeout-seconds", "$Timeout")
    # test_cli does not accept --verbose; do not pass it here

    Write-Host "`nSTART: $(Get-Date -Format 'HH:mm:ss') python $($args -join ' ')" -ForegroundColor Yellow
    $startTime = Get-Date

    # Ensure logs dir exists
    if (!(Test-Path logs)) { New-Item -ItemType Directory -Path logs | Out-Null }

    # Run python directly and capture output to a per-geometry log with Tee-Object so transcript + file capture both
    $geomLog = "logs\${geometry}_run_${timestamp}.log"
    try {
        # Ensure Python uses utf-8 for stdout to avoid UnicodeEncodeError on Windows consoles
        & python @args 2>&1 | Tee-Object -FilePath $geomLog
        $exitCode = $LASTEXITCODE
    } catch {
        $exitCode = 1
        Write-Host "Exception running python: $_" -ForegroundColor Red
    }

    $elapsed = (Get-Date) - $startTime
    $svgExists = Test-Path $svg
    Write-Host "EXIT: $geometry code=$exitCode elapsed=$($elapsed.TotalSeconds) sec"

    # Always dump full per-geometry log to terminal for full visibility
    if (Test-Path $geomLog) {
        Write-Host "`n=== GEOMETRY LOG: $geometry ($geomLog) — FULL OUTPUT BEGIN ===" -ForegroundColor Cyan
        Get-Content $geomLog -ReadCount 1000 | ForEach-Object { Write-Host $_ }
        Write-Host "=== GEOMETRY LOG: $geometry — FULL OUTPUT END ===`n" -ForegroundColor Cyan
    } else {
        Write-Host "No per-geometry log found at $geomLog" -ForegroundColor Yellow
    }

    if ($exitCode -ne 0) {
        # surface quick hints but do not stop transcription here; record failure
        $failed += @{ geom = $geometry; code = $exitCode; svg = $svgExists }
        Write-Host "FAILED: $geometry (exit $exitCode, SVG exists: $svgExists)" -ForegroundColor Red
        $exit_status = 3
        # continue to next geometry so we collect all logs
        continue
    }

    if ($svgExists) {
        # Quick scan: check for lots of black/white fills to detect B/W outputs
        try {
            $svgText = Get-Content $svg -Raw
            $blackCount = ([regex]::Matches($svgText, 'fill=["'']?black["'']?', 'IgnoreCase')).Count
            $whiteCount = ([regex]::Matches($svgText, 'fill=["'']?white["'']?', 'IgnoreCase')).Count
            $fillCount = ([regex]::Matches($svgText, 'fill=', 'IgnoreCase')).Count
            if ($fillCount -gt 0) {
                $pctBW = (($blackCount + $whiteCount) / $fillCount) * 100
                if ($pctBW -ge 70) {
                    Write-Host "WARNING: SVG appears mostly black/white ({0:N1}% B/W fills). See $geomLog" -f $pctBW -ForegroundColor Magenta
                }
            }
        } catch {
            Write-Host "Could not inspect SVG fills: $_" -ForegroundColor Yellow
        }
        $svgs += (Resolve-Path $svg).Path
        Write-Host "CREATED: $svg (log: $geomLog)" -ForegroundColor Green
    } else {
        Write-Host "SVG NOT FOUND: $svg" -ForegroundColor Yellow
        $failed += @{ geom = $geometry; code = 0; svg = $false }
        $exit_status = 3
    }
}

Write-Host "`n=== Output Summary ===" -ForegroundColor Cyan
Get-ChildItem $OutDir -Include *.png,*.svg -File | Select-Object Name,Length | Format-Table -AutoSize

if (Test-Path "logs\run_log.txt") {
    Write-Host "`n=== Last 80 lines of run log ===" -ForegroundColor Cyan
    Get-Content "logs\run_log.txt" -Tail 80
}

Write-Host "Latest results are in: .\output" -ForegroundColor Yellow

# Prepare palette-diff variables (ensure they are defined)
$pythonExe = "python"
$inputImage = $Image
$outDirPath = (Resolve-Path $OutDir).Path
$avgThreshold = 40.0
$pctThreshold = 0.30

# after generating outputs and before Stop-Transcript, add palette diff check
# Run palette diff and record status (prints to terminal already)
Write-Host "`nRunning palette diff check (avg Δ threshold=$avgThreshold, pct unmatched threshold=$pctThreshold)" -ForegroundColor Cyan
$pdArgs = @("tools\palette_diff.py", "--input", $inputImage, "--out", $outDirPath, "--avg-threshold", $avgThreshold.ToString(), "--pct-threshold", $pctThreshold.ToString())
try {
    & $pythonExe @pdArgs
    $pdCode = $LASTEXITCODE
} catch {
    Write-Host "Palette diff invocation failed: $_" -ForegroundColor Yellow
    $pdCode = 0
}
if ($pdCode -ne 0) {
    Write-Host "Palette diff FAILED (exit $pdCode). Marking smoke run as failed." -ForegroundColor Red
    $exit_status = 4
} else {
    Write-Host "Palette diff OK" -ForegroundColor Green
}

# Final: print concise failed summary (single block)
if ($failed.Count -gt 0) {
    Write-Host "`n=== FAILED GEOMETRIES SUMMARY ===" -ForegroundColor Red
    foreach ($f in $failed) {
        Write-Host ("{0}: exit={1} svg_exists={2}" -f $f.geom, $f.code, $f.svg)
    }
    Write-Host "`nSmoke run had failures; see per-geometry logs in logs\\ if needed." -ForegroundColor Red
}

Stop-Transcript

# Final exit: success when at least one SVG produced and no fatal palette diff
if ($exit_status -ne 0) { exit $exit_status }
if ($svgs.Count -gt 0) { exit 0 } else { exit 2 }

# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:44+02:00
# === CUBIST FOOTER STAMP END ===
    foreach ($f in $failed) {
        Write-Host ("{0}: exit={1} svg_exists={2}" -f $f.geom, $f.code, $f.svg)
    }
    Write-Host "`nSmoke run had failures; see per-geometry logs in logs\\ for details." -ForegroundColor Red
    Stop-Transcript
    exit 3


# Final success if we produced at least one SVG
if ($svgs.Count -gt 0) { exit 0 } else { exit 2 }

# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:44+02:00
# === CUBIST FOOTER STAMP END ===
