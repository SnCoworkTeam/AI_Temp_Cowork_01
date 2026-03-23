# 快速查看工作流状态

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "CI/CD 工作流状态" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 获取最新运行
Write-Host "获取最新运行..." -ForegroundColor Yellow
$runs = gh run list --workflow="deploy.yml" --limit 1 --json databaseId,status,conclusion,displayTitle,createdAt,url

if ($runs) {
    $run = $runs | ConvertFrom-Json
    Write-Host "运行ID: $($run.databaseId)" -ForegroundColor Green
    Write-Host "状态: $($run.status)" -ForegroundColor $(if ($run.status -eq "completed") { "Green" } elseif ($run.status -eq "in_progress") { "Yellow" } else { "Red" })
    
    if ($run.conclusion) {
        Write-Host "结果: $($run.conclusion)" -ForegroundColor $(if ($run.conclusion -eq "success") { "Green" } else { "Red" })
    }
    
    Write-Host "创建时间: $($run.createdAt)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "在浏览器中查看:" -ForegroundColor Cyan
    Write-Host $run.url -ForegroundColor Yellow
    Write-Host ""
    Write-Host "查看详细日志:" -ForegroundColor Cyan
    Write-Host "gh run view $($run.databaseId)" -ForegroundColor Gray
    Write-Host "gh run watch $($run.databaseId)" -ForegroundColor Gray
} else {
    Write-Host "未找到运行记录" -ForegroundColor Red
}





