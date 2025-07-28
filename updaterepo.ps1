# updaterepo.ps1
param(
    [string]$Message = "Update repo"
)

Write-Host "Staging all changes..."
git add .

Write-Host "Committing with message: $Message"
git commit -m "$Message"

Write-Host "Pushing to origin/main..."
git push origin main

Write-Host "✅ Repo updated!"
