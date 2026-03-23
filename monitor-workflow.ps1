# 监控工作流运行进度

param(
    [string]$RunId = "19901535278"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "监控CI/CD工作流运行" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "运行ID: $RunId" -ForegroundColor Yellow
Write-Host ""

$maxChecks = 30
$checkCount = 0

while ($checkCount -lt $maxChecks) {
    $checkCount++
    Write-Host "[$checkCount/$maxChecks] 检查运行状态..." -ForegroundColor Yellow
    
    try {
        $runJson = gh run view $RunId --json status,conclusion,displayTitle,jobs
        $runObj = $runJson | ConvertFrom-Json
        
        $statusColor = "Gray"
        if ($runObj.status -eq "completed") { $statusColor = "Green" }
        elseif ($runObj.status -eq "in_progress") { $statusColor = "Yellow" }
        else { $statusColor = "Red" }
        
        Write-Host "状态: $($runObj.status)" -ForegroundColor $statusColor
        
        if ($runObj.conclusion) {
            $conclusionColor = if ($runObj.conclusion -eq "success") { "Green" } else { "Red" }
            Write-Host "结果: $($runObj.conclusion)" -ForegroundColor $conclusionColor
        }
        
        if ($runObj.jobs) {
            Write-Host ""
            Write-Host "Jobs状态:" -ForegroundColor Cyan
            foreach ($job in $runObj.jobs) {
                $icon = "[...]"
                if ($job.status -eq "completed") { $icon = "[OK]" }
                elseif ($job.status -eq "in_progress") { $icon = "[...]" }
                else { $icon = "[X]" }
                Write-Host "  $icon $($job.name): $($job.status)" -ForegroundColor Gray
            }
        }
        
        if ($runObj.status -eq "completed") {
            Write-Host ""
            Write-Host "==========================================" -ForegroundColor Cyan
            if ($runObj.conclusion -eq "success") {
                Write-Host "[SUCCESS] 工作流执行成功！" -ForegroundColor Green
            } else {
                Write-Host "[FAILED] 工作流执行失败" -ForegroundColor Red
                Write-Host "查看详细日志: gh run view $RunId --log" -ForegroundColor Yellow
            }
            break
        }
    }
    catch {
        Write-Host "获取状态失败: $_" -ForegroundColor Red
    }
    
    Write-Host ""
    Start-Sleep -Seconds 10
}

if ($checkCount -ge $maxChecks) {
    Write-Host ""
    Write-Host "[INFO] 已达到最大检查次数" -ForegroundColor Yellow
    Write-Host "在浏览器中查看: https://github.com/PMLiuyubin/enterprise-ai-platform/actions/runs/$RunId" -ForegroundColor Cyan
}
