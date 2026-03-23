# 检查持续测试系统状态

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "持续测试系统状态检查" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python进程
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcs) {
    Write-Host "[OK] Python进程正在运行" -ForegroundColor Green
    $pythonProcs | ForEach-Object {
        Write-Host "  PID: $($_.Id) | 启动时间: $($_.StartTime)" -ForegroundColor Gray
    }
} else {
    Write-Host "[WARN] 未检测到Python进程" -ForegroundColor Yellow
}

Write-Host ""

# 检查最新工作流运行
Write-Host "最新工作流运行状态:" -ForegroundColor Cyan
$runs = gh run list --workflow=deploy.yml --limit 3 --json databaseId,status,conclusion,createdAt | ConvertFrom-Json

if ($runs) {
    $runs | ForEach-Object {
        $statusColor = switch ($_.status) {
            "completed" { if ($_.conclusion -eq "success") { "Green" } else { "Red" } }
            "in_progress" { "Yellow" }
            default { "Gray" }
        }
        
        $conclusionIcon = switch ($_.conclusion) {
            "success" { "[OK]" }
            "failure" { "[FAIL]" }
            "cancelled" { "[CANCEL]" }
            default { "[...]" }
        }
        
        Write-Host "$conclusionIcon 运行ID: $($_.databaseId) | 状态: $($_.status) | 结果: $($_.conclusion) | 时间: $($_.createdAt)" -ForegroundColor $statusColor
    }
} else {
    Write-Host "[WARN] 未找到运行记录" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "查看详细日志:" -ForegroundColor Cyan
Write-Host "  gh run view {runId} --log" -ForegroundColor Gray
Write-Host ""
Write-Host "查看运行列表:" -ForegroundColor Cyan
Write-Host "  gh run list --workflow=deploy.yml" -ForegroundColor Gray
