# 强制提交修复

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "强制提交工作流修复" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查文件状态
Write-Host "[1/5] 检查文件状态..." -ForegroundColor Yellow
git status .github/workflows/deploy.yml

Write-Host ""
Write-Host "[2/5] 查看文件差异..." -ForegroundColor Yellow
git diff .github/workflows/deploy.yml | Select-Object -First 20

Write-Host ""
Write-Host "[3/5] 强制添加到暂存区..." -ForegroundColor Yellow
git add -f .github/workflows/deploy.yml

Write-Host ""
Write-Host "[4/5] 提交更改..." -ForegroundColor Yellow
git commit -m "fix: 修复工作流文件 - 移除environment.url中的secrets引用" --allow-empty

Write-Host ""
Write-Host "[5/5] 推送到远程..." -ForegroundColor Yellow
git push origin main

Write-Host ""
Write-Host "✅ 修复已强制提交并推送！" -ForegroundColor Green
Write-Host ""
Write-Host "等待5秒后重新触发工作流..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "重新触发工作流..." -ForegroundColor Cyan
gh workflow run deploy.yml --field environment=staging

Write-Host ""
Write-Host "✅ 完成！" -ForegroundColor Green





