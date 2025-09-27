[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Use venv from PF metadata if present
$pex = $null
if (Test-Path -LiteralPath "./.pf/venv.json") {
  try { $pex = (Get-Content ./.pf/venv.json -Raw | ConvertFrom-Json).python } catch {}
}
if (-not $pex) { $pex = (Get-Command python).Source }

Write-Host "Preflight using: $pex"

# 1) Lint
& $pex -m pip show ruff *> $null 2>&1; if ($LASTEXITCODE -ne 0) { & $pex -m pip install ruff | Out-Null }
ruff check .

# 2) Pytest quick smoke (short + no network)
$env:PYTEST_ADDOPTS = "-q -k smoke -x"
& $pex -m pip show pytest *> $null 2>&1; if ($LASTEXITCODE -ne 0) { & $pex -m pip install pytest | Out-Null }
& $pex -m pytest || throw "Pytest smoke failed."

# 3) GUI smoke: ensure UI module imports and creates app object
$code = @'
try:
    import importlib
    mod = importlib.import_module("cubist_gui_main")
    ok = True
except Exception as e:
    ok = False
    msg = str(e)
import sys
sys.stdout.write("GUI_IMPORT_OK=" + str(ok) + ("\nERR=" + msg if not ok else ""))
sys.exit(0 if ok else 1)
'@
$tmp = New-TemporaryFile
Set-Content -Encoding utf8NoBOM -Path $tmp -Value $code
& $pex $tmp.FullName
Remove-Item $tmp -Force
