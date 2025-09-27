# tools/dev_diag.ps1
$ErrorActionPreference = 'Stop'

# Move to repo root
$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

Write-Host "== PATH =="
$code = @'
import sys, os
print("CWD:", os.getcwd())
print("Top of sys.path:", sys.path[:5])
'@
$code | python -

Write-Host "`n== API (cubist_core_logic) =="
$code = @'
import importlib
m = importlib.import_module("cubist_core_logic")
print("EXPORTS:", [n for n in dir(m) if n.startswith("run") or n.endswith("pipeline")])
print("FILE:", m.__file__)
print("HAS_run_cubist:", hasattr(m, "run_cubist"))
'@
$code | python -

Write-Host "`n== grep run_cubist =="
try { git grep -n "run_cubist" } catch { Write-Host "no references or git grep failed" }

Write-Host "`n== pytest (tee to .diag/pytest_last.txt) =="
New-Item -ItemType Directory -Force .diag | Out-Null
python -m pytest tests/ -vv -rA --durations=10 | Tee-Object -FilePath .diag/pytest_last.txt
