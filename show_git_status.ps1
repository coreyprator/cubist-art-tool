# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: show_git_status.ps1
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:29+02:00
# === CUBIST STAMP END ===
# Show local and remote commit status for this repo

git status
Write-Host "`n--- Last 3 commits on current branch ---" -ForegroundColor Cyan
git log -3 --oneline --decorate --graph

Write-Host "`n--- Remote branches ---" -ForegroundColor Cyan
git branch -r

Write-Host "`n--- Unpushed commits (if any) ---" -ForegroundColor Cyan
git log --branches --not --remotes --oneline

Write-Host "`n--- Tags ---" -ForegroundColor Cyan
git tag --sort=-creatordate | Select-Object -First 10

# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:29+02:00
# === CUBIST FOOTER STAMP END ===
