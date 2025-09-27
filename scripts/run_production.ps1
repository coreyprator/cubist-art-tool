param(
    [Parameter(Mandatory=$true)][string]$Image,
    [int]$Points = 4000,
    [string]$Geometries = "delaunay,voronoi,rectangles",
    [switch]$ExportSvg,
    [switch]$VerboseLog
)

# Configuration
$RepoRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$CliPath = Join-Path $RepoRoot "cubist_cli.py"
$TimeStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutRoot = Join-Path $RepoRoot "output\prod_$TimeStamp"

Write-Host "Using Python: $PythonExe"
Write-Host "Repo root:    $RepoRoot"
Write-Host "CLI path:     $CliPath"
Write-Host "OutRoot:      $OutRoot"

# Ensure output directory exists
New-Item -ItemType Directory -Path $OutRoot -Force | Out-Null

# Parse geometries
$GeomList = $Geometries -split ","

# Configuration matrix
$Configs = @()
foreach ($Geom in $GeomList) {
    $Configs += @{
        Name = "${Geom}_regular"
        Geometry = $Geom
        Points = $Points
        Seed = 123
        Stages = 1
    }
    $Configs += @{
        Name = "${Geom}_regular_seed456"
        Geometry = $Geom
        Points = $Points
        Seed = 456
        Stages = 1
    }
    $Configs += @{
        Name = "${Geom}_cascade3"
        Geometry = $Geom
        Points = $Points
        Seed = 123
        Stages = 3
    }
    $Configs += @{
        Name = "${Geom}_cascade3_seed456"
        Geometry = $Geom
        Points = $Points
        Seed = 456
        Stages = 3
    }
}

# Results tracking
$Results = @()
$ErrorLogPath = Join-Path $OutRoot "run_errors.log"

# Process each configuration
foreach ($Config in $Configs) {
    $ConfigName = $Config.Name
    $OutDir = Join-Path $OutRoot $ConfigName
    $LogPath = Join-Path $OutDir "run.log"
    $ErrorPath = Join-Path $OutDir "run_error.log"

    Write-Host "Running $ConfigName (geom=$($Config.Geometry), points=$($Config.Points), stages=$($Config.Stages), seed=$($Config.Seed))"

    # Ensure config output directory exists
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

    # Construct the full command as a single string for proper space handling
    $OutputPath = Join-Path $OutDir $ConfigName

    $CliCommand = "& `"$PythonExe`" `"$CliPath`" --input `"$Image`" --output `"$OutputPath`" --geometry $($Config.Geometry) --points $($Config.Points) --seed $($Config.Seed) --cascade-stages $($Config.Stages)"

    if ($ExportSvg) {
        $CliCommand += " --export-svg"
    }

    if (!$VerboseLog) {
        $CliCommand += " --quiet"
    }

    if ($VerboseLog) {
        Write-Host "  Command: $CliCommand"
    }

    try {
        # Use Invoke-Expression to handle the quoted paths properly
        $Output = Invoke-Expression "$CliCommand 2>`"$ErrorPath`"" | Out-File -FilePath $LogPath -Encoding UTF8
        $ExitCode = $LASTEXITCODE

        if ($ExitCode -eq 0) {
            Write-Host "  SUCCESS (exit=$ExitCode)"
            $Results += @{
                Name = $ConfigName
                Status = "SUCCESS"
                ExitCode = $ExitCode
                OutputDir = $OutDir
                LogPath = $LogPath
            }
        } else {
            Write-Host "  FAIL (exit=$ExitCode)"
            $Results += @{
                Name = $ConfigName
                Status = "FAIL"
                ExitCode = $ExitCode
                OutputDir = $OutDir
                LogPath = $LogPath
                ErrorPath = $ErrorPath
            }

            # Log the error details
            $ErrorContent = ""
            if (Test-Path $ErrorPath) {
                $ErrorContent = Get-Content $ErrorPath -Raw
            }

            $ErrorDetails = @"
---- $ConfigName (geom=$($Config.Geometry), points=$($Config.Points), stages=$($Config.Stages), seed=$($Config.Seed)) ----
EXCEPTION: $ErrorContent
OutDir: $OutDir
Log:    $LogPath
Exit:   $ExitCode

"@
            Add-Content -Path $ErrorLogPath -Value $ErrorDetails
        }
    } catch {
        Write-Host "  ERROR: $($_.Exception.Message)"
        $Results += @{
            Name = $ConfigName
            Status = "ERROR"
            Exception = $_.Exception.Message
            OutputDir = $OutDir
        }

        $ErrorDetails = @"
---- $ConfigName (geom=$($Config.Geometry), points=$($Config.Points), stages=$($Config.Stages), seed=$($Config.Seed)) ----
EXCEPTION: $($_.Exception.Message)
OutDir: $OutDir

"@
        Add-Content -Path $ErrorLogPath -Value $ErrorDetails
    }
}

# Summary
Write-Host ""
Write-Host "=== PRODUCTION BATCH SUMMARY ==="
$SuccessCount = ($Results | Where-Object { $_.Status -eq "SUCCESS" }).Count
$FailCount = ($Results | Where-Object { $_.Status -ne "SUCCESS" }).Count

foreach ($Result in $Results) {
    if ($Result.Status -eq "SUCCESS") {
        Write-Host "$($Result.Status) $($Result.Name)  ->  $($Result.OutputDir)" -ForegroundColor Green
    } else {
        Write-Host "$($Result.Status) $($Result.Name)  ->  $($Result.OutputDir)" -ForegroundColor Red
        if ($Result.ErrorPath) {
            Write-Host "     error log: $($Result.ErrorPath)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "All outputs live in: $OutRoot"
if ($FailCount -gt 0) {
    Write-Host "Consolidated errors:  $ErrorLogPath" -ForegroundColor Red
}
Write-Host "Success: $SuccessCount, Failed: $FailCount"
