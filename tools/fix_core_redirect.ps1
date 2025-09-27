[CmdletBinding()]
param([string]$FilePath = "cubist_core_logic.py")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $FilePath)) { Write-Error "Not found: $FilePath"; exit 1 }
$text = Get-Content -Raw -Encoding UTF8 $FilePath

# Drop any old redirect we added earlier
$text = [regex]::Replace($text, '(?ms)^# --- Legacy attribute redirect .*? ^# --- End legacy redirect\s*', '')

# Append a redirect that *doesn't* import anything until the function is called
$redirect = @"
# --- Legacy attribute redirect (v2.3.7.5)
def __getattr__(name):
    if name == "run_cubist":
        # Late-resolve at call time to avoid circular imports.
        def _run_cubist(*args, **kwargs):
            try:
                fn = globals().get("run_pipeline", None)
                if fn is None:
                    from cubist_api import run_cubist as _rc  # import facade only when needed
                    return _rc(*args, **kwargs)
                return fn(*args, **kwargs)
            except Exception as e:
                raise RuntimeError(f"run_cubist shim failed: {e}")
        return _run_cubist
    raise AttributeError(name)
# --- End legacy redirect
"@

Set-Content -Encoding UTF8 $FilePath ($text.TrimEnd() + "`r`n`r`n" + $redirect)
Write-Host "Updated $FilePath"
