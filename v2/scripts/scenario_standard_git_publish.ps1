[CmdletBinding()]
param([string]$ProjectRoot,[string]$Message)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot){ Set-Location -LiteralPath $ProjectRoot }

$git = (Get-Command git -ErrorAction SilentlyContinue)?.Source; if (-not $git) { throw 'git is not on PATH.' }
if (-not (Test-Path -LiteralPath '.git')) { & $git init | Out-Null }
& $git add -A
$pending = & $git status --porcelain
if ($pending) {
  if (-not $Message) { $Message = 'PF publish ' + (Get-Date -Format s) }
  & $git commit -m $Message
  try { & $git push --set-upstream origin (git rev-parse --abbrev-ref HEAD) 2>$null | Out-Null } catch { Write-Host 'Push skipped or failed (no remote?)' }
  $ok = $true
  $sha = (& $git rev-parse --short HEAD).Trim()
} else { $ok = $true; $sha = (& $git rev-parse --short HEAD 2>$null) }

# Journal
New-Item -ItemType Directory -Force -Path './.pf/journal' | Out-Null
$jn = './.pf/journal/publish_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.json'
(@{ ok=$ok; project=(Get-Location).Path; commit=$sha; message=$Message } | ConvertTo-Json) | Set-Content -Encoding utf8NoBOM $jn
Write-Host ('Wrote journal: ' + $jn)
Write-Host '[standard_git_publish] OK'
