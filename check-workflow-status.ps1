# 检查工作流状态

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "检查CI/CD工作流状态" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否已提交修复
Write-Host "检查本地文件状态..." -ForegroundColor Yellow
$status = git status --short .github/workflows/deploy.yml
if ($status) {
    Write-Host "⚠️  工作流文件尚未提交！" -ForegroundColor Red
    Write-Host "请先执行:" -ForegroundColor Yellow
    Write-Host "  git add .github/workflows/deploy.yml" -ForegroundColor Gray
    Write-Host "  git commit -m 'fix: 修复工作流文件'" -ForegroundColor Gray
    Write-Host "  git push origin main" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "✅ 工作流文件已提交" -ForegroundColor Green
}

Write-Host ""
Write-Host "最近的工作流运行:" -ForegroundColor Cyan
gh run list --workflow="deploy.yml" --limit 3

Write-Host ""
Write-Host "获取最新运行ID..." -ForegroundColor Yellow
$runId = gh run list --workflow="deploy.yml" --limit 1 --json databaseId --jq '.[0].databaseId'

if ($runId) {
    Write-Host "最新运行ID: $runId" -ForegroundColor Green
    Write-Host ""
    Write-Host "在浏览器中查看详细日志:" -ForegroundColor Cyan
    Write-Host "https://github.com/PMLiuyubin/enterprise-ai-platform/actions/runs/$runId" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "或使用命令查看:" -ForegroundColor Gray
    Write-Host "gh run view $runId" -ForegroundColor Gray
}





