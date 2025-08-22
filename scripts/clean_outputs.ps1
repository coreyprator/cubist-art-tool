# This script is a PowerShell script, not a Python script.
# To run it, use PowerShell, not python:
#   powershell -ExecutionPolicy Bypass -File scripts\clean_outputs.ps1
# or from PowerShell prompt:
#   .\scripts\clean_outputs.ps1

param(
    [string]$Root = "output",
    [switch]$DryRun
)

if (-not (Test-Path $Root)) {
    Write-Host "No '$Root' folder found."
    exit 0
}

$grandTotal = 0

Get-ChildItem -Path $Root -Directory | ForEach-Object {
    $size = (Get-ChildItem -Path $_.FullName -Recurse -File -ErrorAction SilentlyContinue |
                Measure-Object -Property Length -Sum).Sum
    $sizeMB = "{0:N2}" -f ($size / 1MB)
    $grandTotal += $size

    if ($DryRun) {
        Write-Host "[dry-run] Would remove $($_.FullName) ($sizeMB MB)"
    }
    else {
        Write-Host "Removing $($_.FullName) ($sizeMB MB)..."
        Remove-Item -Recurse -Force -LiteralPath $_.FullName
    }
}

$grandTotalMB = "{0:N2}" -f ($grandTotal / 1MB)
Write-Host "Grand total size of deleted items: $grandTotalMB MB ($grandTotal bytes)"
