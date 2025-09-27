param(
	[string]$Remote = $env:GIT_REMOTE,
	[string]$Branch = ""
)

# Usage: .\publish_to_github.ps1 -Remote "git@github.com:org/repo.git"
# If gh CLI is installed it can optionally open a PR after push.

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

if (-not (Test-Path .git)) {
	Write-Host "Initializing git repository..." -ForegroundColor Yellow
	git init
} else {
	Write-Host "Git repository detected." -ForegroundColor Green
}

if (-not $Branch -or $Branch -eq "") {
	$Branch = "smoke-debug-" + (Get-Date -Format "yyyyMMdd_HHmmss")
}

if (-not $Remote -or $Remote -eq "") {
	if (git remote get-url origin 2>$null) {
		$Remote = "origin"
	} else {
		$Remote = Read-Host "Enter git remote URL (ssh or https) or press Enter to abort"
		if (-not $Remote) { Write-Host "No remote provided; aborting." -ForegroundColor Red; exit 2 }
		git remote add origin $Remote
	}
}

Write-Host "Creating branch: $Branch" -ForegroundColor Cyan
git checkout -B $Branch

Write-Host "Staging all changes..." -ForegroundColor Cyan
git add -A

$commitMsg = "chore(smoke): workspace publish for review $(Get-Date -Format 's')"
Write-Host "Committing: $commitMsg" -ForegroundColor Cyan
git commit -m $commitMsg 2>$null
if ($LASTEXITCODE -ne 0) {
	Write-Host "Nothing to commit or commit failed (maybe same content)." -ForegroundColor Yellow
}

Write-Host "Pushing branch to remote: $Remote/$Branch" -ForegroundColor Cyan
git push -u $Remote $Branch

if ($LASTEXITCODE -ne 0) {
	Write-Host "Push failed. Check remote access and network. Remote: $Remote" -ForegroundColor Red
	exit 3
}

# Print handoff checklist and key files for reviewer
Write-Host "`n=== Handoff: branch pushed: $Branch ===" -ForegroundColor Green
Write-Host "Repository root: $RepoRoot"
Write-Host "`nImportant files to inspect:" -ForegroundColor Cyan
$files = @(
	"test_cli.py",
	"cubist_cli.py",
	"svg_export.py",
	"geometry_registry.py",
	"geometry_plugins\*",
	"cubist_core_logic.py",
	"cubist_logger.py",
	"archive_output.py",
	"tools\palette_diff.py",
	"run_svg_smoke.ps1",
	"logs\smoke_transcript_*.log",
	"logs\*_run_*.log"
)
$files | ForEach-Object { Write-Host " - $_" }

# Show local git status porcelain to help reviewer know what's in this push
Write-Host "`nGit status (porcelain):" -ForegroundColor Cyan
git status --porcelain

# Optionally open a PR if gh is available
if (Get-Command gh -ErrorAction SilentlyContinue) {
	$doPr = Read-Host "gh CLI found. Create a PR for this branch? (y/N)"
	if ($doPr -and $doPr.ToLower().StartsWith("y")) {
		# Attempt to open PR against default branch
		gh pr create --head $Branch --fill
		Write-Host "PR creation attempted via gh." -ForegroundColor Green
	}
} else {
	Write-Host "gh CLI not found; to create PR run: gh pr create --head $Branch --fill" -ForegroundColor Yellow
}

Write-Host "`nHandoff complete. Share branch name and repo remote with reviewer." -ForegroundColor Green
