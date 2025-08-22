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
