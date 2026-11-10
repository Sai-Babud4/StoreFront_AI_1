Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  RetailIQ - One-Click Push to GitHub" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$repoUrl = Read-Host "Enter GitHub Repository URL [Default: https://github.com/Sai-Babud4/Store-IQ.git]"
if ([string]::IsNullOrWhiteSpace($repoUrl)) {
    $repoUrl = "https://github.com/Sai-Babud4/Store-IQ.git"
}

Write-Host "Using repository: $repoUrl" -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/3] Setting remote origin..." -ForegroundColor Green
git remote remove origin 2>$null
git remote add origin $repoUrl

Write-Host "[2/3] Staging all files..." -ForegroundColor Green
git add -A
git commit -m "RetailIQ: Complete production deploy with resilient database and API" 2>$null

Write-Host "[3/3] Pushing to GitHub main branch..." -ForegroundColor Green
git branch -M main
git push -u -f origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host "  SUCCESS! Code pushed to $repoUrl" -ForegroundColor Green
    Write-Host "  Vercel will now automatically build and deploy!" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Push completed or requires authentication in your browser/terminal." -ForegroundColor Yellow
}

