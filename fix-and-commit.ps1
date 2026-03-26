# 正确的提交顺序

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "提交工作流修复" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 添加文件到暂存区
Write-Host "[1/3] 添加文件到暂存区..." -ForegroundColor Yellow
git add .github/workflows/deploy.yml

# 步骤2: 提交
Write-Host "[2/3] 提交更改..." -ForegroundColor Yellow
git commit -m "fix: 修复工作流文件 - 移除environment.url中的secrets引用"

# 步骤3: 推送
Write-Host "[3/3] 推送到远程..." -ForegroundColor Yellow
git push origin main

Write-Host ""
Write-Host "✅ 修复已提交并推送！" -ForegroundColor Green
Write-Host ""
Write-Host "等待几秒后重新触发工作流..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "重新触发工作流..." -ForegroundColor Cyan
gh workflow run deploy.yml --field environment=staging

Write-Host ""
Write-Host "✅ 工作流已重新触发！" -ForegroundColor Green
Write-Host "查看状态: gh run list --workflow='deploy.yml' --limit 3" -ForegroundColor Gray





