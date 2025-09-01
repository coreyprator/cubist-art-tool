# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: scripts/run_production.ps1
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:24:01+02:00
# === CUBIST STAMP END ===
<#  run_production.ps1
    Batch runner for cubist_cli.py across geometries/stages/seeds.

    PowerShell 5.1 compatible:
      - no null‑coalescing, safe‑navigation, or ternary operators
      - uses System.Diagnostics.Process for robust stdout/stderr capture

    Examples:
      powershell -ExecutionPolicy Bypass -File scripts\run_production.ps1 `
        -Image "input\your_input_image.jpg" `
        -Points 200 `
        -Geometries delaunay,voronoi,rectangles `
        -CascadeStages 1,3 `
        -Seeds 123,456 `
        -SvgLimit 150 `
        -TimeoutSeconds 120 `
        -ExportSvg `
        -VerboseLog

      # Example usage for all geometries in one command:
      # (from PowerShell prompt, in your repo root)
powershell -ExecutionPolicy Bypass -File scripts\run_production.ps1 `
  -Image "input\your_input_image.jpg" `
  -Points 200 `
  -Geometries "delaunay,voronoi,rectangles" `
  -CascadeStages "1,3" `
  -Seeds "123,456" `
  -SvgLimit 150 `
  -TimeoutSeconds 120 `
  -ExportSvg `
  -VerboseLog
      # This will run all geometries (rectangles, delaunay, voronoi) in all scenarios:
      powershell -ExecutionPolicy Bypass -File scripts\run_production.ps1 `
        -Image "input\your_input_image.jpg" `
        -Points 120 `
        -Geometries rectangles,delaunay,voronoi `
        -SvgLimit 150 `
        -TimeoutSeconds 180 `
        -VerboseLog
#>

[CmdletBinding()]
param(
  [string]$Image = "input\your_input_image.jpg",
  [int]$Points = 100,
  [string]$Geometries = "delaunay,voronoi,rectangles",   # <-- now a comma-separated string, not array
  [string]$CascadeStages = "1,3",                        # <-- now a comma-separated string, not array
  [string]$Seeds = "123,456",                            # <-- now a comma-separated string, not array
  [int]$SvgLimit = 0,
  [int]$TimeoutSeconds = 0,
  [switch]$StepFrames,
  [switch]$VerboseLog,
  [string]$Mask = "",
  [switch]$NoExportSvg,
  [switch]$ExportSvg,
  [switch]$DryRun
)

# ---------- helpers ----------
function Split-List([string]$s) {
  if ([string]::IsNullOrWhiteSpace($s)) { return @() }
  return ($s -split '\s*,\s*' | Where-Object { $_ -ne "" })
}

function Quote-Arg([string]$a) {
  if ($a -match '[\s"]') {
    return '"' + ($a -replace '"','\"') + '"'
  }
  return $a
}

function Get-RunName([string]$Geom, [int]$StageCount, [int]$Seed) {
  if ($StageCount -le 1) {
    if ($Seed -ne 123) { return ($Geom + "_regular_seed" + $Seed) }
    return ($Geom + "_regular")
  } else {
    if ($Seed -ne 123) { return ($Geom + "_cascade" + $StageCount + "_seed" + $Seed) }
    return ($Geom + "_cascade" + $StageCount)
  }
}

# ---------- resolve paths & python ----------
$repoRoot = Split-Path -Parent $PSScriptRoot
$cliPath  = Join-Path $repoRoot "cubist_cli.py"

if (-not (Test-Path -LiteralPath $cliPath)) {
  throw "Cannot find cubist_cli.py at: $cliPath"
}

# Prefer venv python if present unless user provided one
if ([string]::IsNullOrWhiteSpace($PythonPath)) {
  $venvPy = Join-Path $repoRoot ".venv\Scripts\python.exe"
  if (Test-Path -LiteralPath $venvPy) { $PythonPath = $venvPy }
  else { $PythonPath = "python" }
}
$Python = $PythonPath

# Input image absolute path
try {
  $imgAbs = (Resolve-Path -LiteralPath $Image -ErrorAction Stop).Path
} catch {
  throw "Input image not found: $Image"
}

if ($VerboseLog) {
  Write-Host "Using Python: $Python"
  Write-Host "Repo root:    $repoRoot"
  Write-Host "CLI path:     $cliPath"
}

# ---------- expand sets ----------
$geomList  = $Geometries -split '\s*,\s*'
$stageList = $CascadeStages -split '\s*,\s*' | ForEach-Object { [int]$_ }
$seedList  = $Seeds -split '\s*,\s*' | ForEach-Object { [int]$_ }

if (-not $geomList -or $geomList.Count -eq 0) { throw "No geometries provided." }
if (-not $stageList -or $stageList.Count -eq 0) { throw "No cascade stages provided." }
if (-not $seedList  -or $seedList.Count  -eq 0) { throw "No seeds provided." }

# ---------- output root ----------
$stamp   = Get-Date -Format "yyyyMMdd_HHmmss"
$outRoot = Join-Path $repoRoot ("output\prod_{0}" -f $stamp)
New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
if ($VerboseLog) {
  Write-Host "OutRoot:      $outRoot"
}

# root consolidated errors
$rootErrLog = Join-Path $outRoot "run_errors.log"
Remove-Item -LiteralPath $rootErrLog -Force -ErrorAction SilentlyContinue | Out-Null

# ---------- run a single job ----------
function Invoke-CubistJob {
  param(
    [string] $Geom,
    [int]    $StageCount,
    [int]    $Seed
  )

  $runName = Get-RunName -Geom $Geom -StageCount $StageCount -Seed $Seed
  $outDir  = Join-Path $outRoot $runName
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null

  $logPath = Join-Path $outDir "run.log"
  $errPath = Join-Path $outDir "run_error.log"
  Remove-Item -LiteralPath $logPath -Force -ErrorAction SilentlyContinue | Out-Null
  Remove-Item -LiteralPath $errPath -Force -ErrorAction SilentlyContinue | Out-Null

  Write-Host ("Running {0} (geom={1}, points={2}, stages={3}, seed={4})" -f $runName,$Geom,$Points,$StageCount,$Seed)

  # build CLI args
  $args = @()
  $args += $cliPath
  $args += "--input";           $args += $imgAbs
  $args += "--output";          $args += $outDir
  $args += "--points";          $args += $Points.ToString()
  $args += "--geometry";        $args += $Geom
  $args += "--seed";            $args += $Seed.ToString()
  $args += "--cascade-stages";  $args += $StageCount.ToString()
  $args += "--metrics-json";    $args += (Join-Path $outDir "metrics.json")
  if ($ExportSvg) {
    $args += "--export-svg"
    if ($SvgLimit -gt 0) { $args += "--svg-limit"; $args += $SvgLimit.ToString() }
  }
  if ($TimeoutSeconds -gt 0) { $args += "--timeout-seconds"; $args += $TimeoutSeconds.ToString() }
  if ($StepFrames) { $args += "--save-step-frames" }
  if ($VerboseLog) { $args += "--verbose" }

  # Use System.Diagnostics.Process to avoid NativeCommandError
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $Python
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError  = $true
  # Proper quoting for arguments:
  $psi.Arguments = ($args | ForEach-Object { Quote-Arg $_ }) -join ' '

  $proc = New-Object System.Diagnostics.Process
  $proc.StartInfo = $psi

  $null = $proc.Start()
  $stdOut = $proc.StandardOutput.ReadToEnd()
  $stdErr = $proc.StandardError.ReadToEnd()
  if ($TimeoutSeconds -gt 0) {
    $finished = $proc.WaitForExit($TimeoutSeconds * 1000)
    if (-not $finished) { try { $proc.Kill() } catch {} }
  } else {
    $proc.WaitForExit()
  }

  # write logs
  if ($stdOut) { $stdOut | Out-File -FilePath $logPath -Encoding UTF8 -Force }
  if ($stdErr) { $stdErr | Out-File -FilePath $errPath -Encoding UTF8 -Force }

  $exit = $proc.ExitCode

  if ($exit -eq 0) {
    Write-Host ("  OK  (exit=0)")
    return @{ Ok=$true; Name=$runName; Dir=$outDir; Log=$logPath; Err=$errPath; Exit=$exit }
  } else {
    Write-Host ("  FAIL (exit={0})" -f $exit)
    # Append concise record into root error log
    Add-Content -Path $rootErrLog -Encoding UTF8 -Value ""
    Add-Content -Path $rootErrLog -Encoding UTF8 -Value ("---- {0} (geom={1}, points={2}, stages={3}, seed={4}) ----" -f $runName,$Geom,$Points,$StageCount,$Seed)
    if ($stdErr) {
      Add-Content -Path $rootErrLog -Encoding UTF8 -Value ("EXCEPTION: " + ($stdErr.Split("`n")[0]))
    }
    Add-Content -Path $rootErrLog -Encoding UTF8 -Value ""
    Add-Content -Path $rootErrLog -Encoding UTF8 -Value ("OutDir: {0}" -f $outDir)
    Add-Content -Path $rootErrLog -Encoding UTF8 -Value ("Log:    {0}" -f $logPath)
    Add-Content -Path $rootErrLog -Encoding UTF8 -Value ("Exit:   {0}" -f $exit)
    # small snippet from stdout if present
    if (Test-Path -LiteralPath $logPath) {
      $snippet = Get-Content -LiteralPath $logPath -TotalCount 10
      Add-Content -Path $rootErrLog -Encoding UTF8 -Value "=== LOG SNIPPET START ==="
      $snippet | ForEach-Object { Add-Content -Path $rootErrLog -Encoding UTF8 -Value $_ }
      Add-Content -Path $rootErrLog -Encoding UTF8 -Value "=== LOG SNIPPET END ==="
    }
    return @{ Ok=$false; Name=$runName; Dir=$outDir; Log=$logPath; Err=$errPath; Exit=$exit }
  }
}

function Build-Args {
  param(
    [string]$Geometry,
    [int]$Points,
    [int]$CascadeStages,
    [int]$Seed,
    [string]$Image,
    [string]$OutDir,
    [string]$MetricsJson
  )

  $args = @("$Cli",
            "--input", (Resolve-Path $Image).Path,
            "--points", "$Points",
            "--geometry", $Geometry,
            "--metrics-json", $MetricsJson,
            "--cascade-stages", "$CascadeStages",
            "--seed", "$Seed",
            "--output", (Resolve-Path $OutDir).Path)

  if ($ExportSvg)      { $args += "--export-svg" }
  if ($NoExportSvg)    { } # do nothing, disables export
  if ($VerboseLog)     { $args += "--verbose" }
  if ($Mask)           { $args += @("--mask", (Resolve-Path $Mask).Path) }
  if ($SvgLimit -gt 0) { $args += @("--svg-limit", "$SvgLimit") }
  if ($TimeoutSeconds -gt 0) { $args += @("--timeout-seconds", "$TimeoutSeconds") }
  if ($StepFrames)     { $args += "--save-step-frames" }

  return $args
}

# ---------- execute grid ----------
$results = @()
foreach ($g in $geomList) {
  foreach ($st in $stageList) {
    foreach ($seed in $seedList) {
      $res = Invoke-CubistJob -Geom $g -StageCount $st -Seed $seed
      $results += ,$res
    }
  }
}

# ---------- summary ----------
Write-Host ""
Write-Host "=== PRODUCTION BATCH SUMMARY ==="
foreach ($r in $results) {
  if ($r.Ok) {
    Write-Host ("OK   {0}  ->  {1}" -f $r.Name, $r.Dir)
  } else {
    Write-Host ("FAIL {0}  ->  {1}" -f $r.Name, $r.Dir)
    Write-Host ("     error log: {0}" -f $r.Err)
  }
}

Write-Host ""
Write-Host ("All outputs live in: {0}" -f $outRoot)
if (Test-Path -LiteralPath $rootErrLog) {
  $len = (Get-Item -LiteralPath $rootErrLog).Length
  if ($len -gt 0) {
    Write-Host ("Consolidated errors:  {0}" -f $rootErrLog)
  } else {
    Write-Host "Consolidated errors:  (no failures)"
  }
} else {
  Write-Host "Consolidated errors:  (file not created)"
}


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:24:01+02:00
# === CUBIST FOOTER STAMP END ===
