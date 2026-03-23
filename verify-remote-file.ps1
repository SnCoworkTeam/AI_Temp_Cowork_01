# 验证远程文件是否已修复

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "验证远程工作流文件" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 方法1: 检查本地文件
Write-Host "[1/3] 检查本地文件..." -ForegroundColor Yellow
$localCheck = Select-String -Path ".github/workflows/deploy.yml" -Pattern "url.*SERVER_URL|secrets\.SERVER_URL"
if ($localCheck) {
    Write-Host "❌ 本地文件仍有问题" -ForegroundColor Red
    $localCheck
} else {
    Write-Host "✅ 本地文件已修复" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/3] 检查远程文件（通过git）..." -ForegroundColor Yellow
try {
    # 先fetch
    git fetch origin main --quiet
    
    # 检查远程文件
    $remoteCheck = git show origin/main:.github/workflows/deploy.yml | Select-String -Pattern "url.*SERVER_URL|secrets\.SERVER_URL"
    if ($remoteCheck) {
        Write-Host "❌ 远程文件仍有问题" -ForegroundColor Red
        Write-Host "需要推送修复..." -ForegroundColor Yellow
        $remoteCheck
    } else {
        Write-Host "✅ 远程文件已修复" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  无法检查远程文件: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[3/3] 检查最近的提交..." -ForegroundColor Yellow
git log --oneline -5 -- .github/workflows/deploy.yml

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "建议操作" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "如果远程文件仍有问题，执行:" -ForegroundColor Yellow
Write-Host "  git add .github/workflows/deploy.yml" -ForegroundColor Gray
Write-Host "  git commit -m 'fix: 移除environment.url'" -ForegroundColor Gray
Write-Host "  git push origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "然后在浏览器中验证:" -ForegroundColor Yellow
Write-Host "  https://github.com/PMLiuyubin/enterprise-ai-platform/blob/main/.github/workflows/deploy.yml" -ForegroundColor Cyan





