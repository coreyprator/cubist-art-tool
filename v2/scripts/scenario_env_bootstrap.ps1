[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot){ Set-Location -LiteralPath $ProjectRoot }

# Load PF config if present
$cfgPath = Join-Path (Get-Location) '.pf/project.json'
$cfg = $null
if (Test-Path -LiteralPath $cfgPath) { try { $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json } catch {} }
$ver  = $cfg?.pf?.python?.version; if (-not $ver) { $ver = '3.12' }
$repo = Split-Path -Leaf (Get-Location)
$venv = $cfg?.pf?.python?.venv_path; if (-not $venv) { $venv = "C:/venvs/${repo}-${ver}" }

# Ensure parent dir exists
$venvParent = Split-Path -Parent $venv
if ($venvParent -and -not (Test-Path -LiteralPath $venvParent)) { New-Item -ItemType Directory -Path $venvParent | Out-Null }

# Create venv with py launcher if available
$py = (Get-Command py -ErrorAction SilentlyContinue)?.Source
if ($py) { & $py ("-" + $ver) -m venv $venv } else { & (Get-Command python).Source -m venv $venv }

$pex = Join-Path $venv 'Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pex)) { throw "venv python not found: $pex" }
& $pex -m pip install -U pip
if (Test-Path -LiteralPath './requirements.txt') { & $pex -m pip install -r ./requirements.txt }

# Persist for tools
$meta = @{ venv_path = $venv; python = (Get-Item $pex).FullName; version = $ver } | ConvertTo-Json
New-Item -ItemType Directory -Force -Path './.pf' | Out-Null
$meta | Set-Content -Encoding utf8NoBOM './.pf/venv.json'
Write-Host ("Env bootstrap: ready -> " + $venv)
