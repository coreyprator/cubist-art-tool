[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot){ Set-Location -LiteralPath $ProjectRoot }

New-Item -ItemType Directory -Force -Path './.pf' | Out-Null
$cfg = $null; if (Test-Path -LiteralPath './.pf/project.json') { try { $cfg = Get-Content ./.pf/project.json -Raw | ConvertFrom-Json } catch {} }
$cmd = $cfg?.pf?.runui
if ($null -eq $cmd) { $cmd = @{ type = 'python'; args = @('-X','utf8', './cubist_gui_main.py') } }
$manifest = @{ precheck = @('app_selfcheck'); workdir = '.'; env = @{}; command = $cmd } | ConvertTo-Json -Depth 6
$manifest | Set-Content -Encoding utf8NoBOM './.pf/runui.json'
Write-Host 'Wrote ./.pf/runui.json'
