# 提交工作流修复

Write-Host "提交工作流修复..." -ForegroundColor Cyan

git add .github/workflows/deploy.yml
git commit -m "fix: 修复工作流文件 - 移除environment.url中的secrets引用"
git push origin main

Write-Host "修复已提交！" -ForegroundColor Green
Write-Host "现在可以重新触发工作流：" -ForegroundColor Yellow
Write-Host "gh workflow run deploy.yml --field environment=staging" -ForegroundColor Cyan





