[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot){ Set-Location -LiteralPath $ProjectRoot }

function _GetPy { (Get-Command py -ErrorAction SilentlyContinue)?.Source ?? (Get-Command python -ErrorAction SilentlyContinue)?.Source ?? 'python' }

# Prefer manifest if present
$manifest = './.pf/runui.json'
if (Test-Path -LiteralPath $manifest) {
  $m = Get-Content $manifest -Raw | ConvertFrom-Json
  $wd = if ($m.workdir) { (Resolve-Path $m.workdir).Path } else { (Get-Location).Path }
  $cmd = $m.command
  switch ($cmd.type) {
    'python' { Start-Process -FilePath (_GetPy) -ArgumentList (@($cmd.args) -join ' ') -WorkingDirectory $wd | Out-Null }
    'exec'   { Start-Process -FilePath $cmd.exec[0] -ArgumentList ((@($cmd.exec) | Select-Object -Skip 1) -join ' ') -WorkingDirectory $wd | Out-Null }
    default  { throw "Unsupported runui command.type: $($cmd.type)" }
  }
  Write-Host 'Run UI (manifest): started.'; return
}

# Auto-detect if no manifest
$cand = @()
if (Test-Path -LiteralPath './cubist_gui_main.py') { $cand += [pscustomobject]@{ score=90; kind='python'; args=@('-X','utf8','./cubist_gui_main.py') } }
elseif (Test-Path -LiteralPath './app.py')       { $cand += [pscustomobject]@{ score=80; kind='python'; args=@('-X','utf8','./app.py') } }
if (Test-Path -LiteralPath './package.json') { try { $pkg = Get-Content ./package.json -Raw | ConvertFrom-Json; if ($pkg.scripts.start) { $cand += [pscustomobject]@{ score=70; kind='exec'; exec=@('npm','run','start') } elseif ($pkg.scripts.dev) { $cand += [pscustomobject]@{ score=65; kind='exec'; exec=@('npm','run','dev') } } } catch {} }
$csproj = Get-ChildItem -Filter *.csproj -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($csproj) { $cand += [pscustomobject]@{ score=60; kind='exec'; exec=@('dotnet','run','--project', $csproj.FullName) } }
if (-not $cand) { throw 'No entry point found. Create .pf/runui.json or add an app.py/cubist_gui_main.py.' }
$choice = $cand | Sort-Object score -Descending | Select-Object -First 1
switch ($choice.kind) {
  'python' { Start-Process -FilePath (_GetPy) -ArgumentList ($choice.args -join ' ') -WorkingDirectory (Get-Location).Path | Out-Null }
  'exec'   { Start-Process -FilePath $choice.exec[0] -ArgumentList (($choice.exec | Select-Object -Skip 1) -join ' ') -WorkingDirectory (Get-Location).Path | Out-Null }
}
Write-Host 'Run UI (auto-detect): started.'
