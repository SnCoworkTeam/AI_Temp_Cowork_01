# 查看CI/CD工作流状态（非交互式）

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "CI/CD 工作流状态" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 获取最新的运行ID
Write-Host "获取最新的部署工作流运行..." -ForegroundColor Yellow
$runs = gh run list --workflow="deploy.yml" --limit 1 --json databaseId,status,conclusion,displayTitle,createdAt --jq '.[0]'

if ($runs) {
    $run = $runs | ConvertFrom-Json
    Write-Host "运行ID: $($run.databaseId)" -ForegroundColor Green
    Write-Host "状态: $($run.status)" -ForegroundColor $(if ($run.status -eq "completed") { "Green" } else { "Yellow" })
    Write-Host "结果: $($run.conclusion)" -ForegroundColor $(if ($run.conclusion -eq "success") { "Green" } else { "Red" })
    Write-Host "标题: $($run.displayTitle)" -ForegroundColor Gray
    Write-Host "创建时间: $($run.createdAt)" -ForegroundColor Gray
    Write-Host ""
    
    # 查看详细日志
    Write-Host "查看详细日志..." -ForegroundColor Yellow
    Write-Host "在浏览器中打开: https://github.com/PMLiuyubin/enterprise-ai-platform/actions/runs/$($run.databaseId)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "或使用命令查看日志:" -ForegroundColor Yellow
    Write-Host "gh run view $($run.databaseId) --log" -ForegroundColor Gray
} else {
    Write-Host "未找到运行记录" -ForegroundColor Red
}

Write-Host ""
Write-Host "所有最近的运行:" -ForegroundColor Cyan
gh run list --workflow="deploy.yml" --limit 5





