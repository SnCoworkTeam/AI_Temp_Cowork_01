# 安装测试覆盖率监控定时任务
# 每10分钟检查一次任务状态

param(
    [switch]$Install = $false,
    [switch]$Uninstall = $false,
    [switch]$Status = $false
)

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)

$TaskName = "EnterpriseAI-CoverageTaskMonitor"
$MonitorScript = Join-Path $ScriptRoot "coverage-task-monitor.ps1"
$TaskDescription = "每10分钟检查测试覆盖率提升任务状态，如果卡住则自动恢复"

function Install-Task {
    Write-Host "安装测试覆盖率监控定时任务..." -ForegroundColor Cyan
    
    # 检查脚本是否存在
    if (-not (Test-Path $MonitorScript)) {
        Write-Host "错误: 监控脚本不存在: $MonitorScript" -ForegroundColor Red
        return
    }
    
    # 检查任务是否已存在
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "任务已存在，先删除..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # 创建任务操作
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -File `"$MonitorScript`"" `
        -WorkingDirectory $ProjectRoot
    
    # 创建任务触发器（每10分钟执行一次）
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
        -RepetitionInterval (New-TimeSpan -Minutes 10) `
        -RepetitionDuration (New-TimeSpan -Days 365)
    
    # 创建任务设置
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
    
    # 注册任务
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Description $TaskDescription `
            -User $env:USERNAME `
            -RunLevel Highest | Out-Null
        
        Write-Host "✓ 任务已安装: $TaskName" -ForegroundColor Green
        Write-Host "  描述: $TaskDescription" -ForegroundColor Gray
        Write-Host "  执行间隔: 每10分钟" -ForegroundColor Gray
        Write-Host "  脚本路径: $MonitorScript" -ForegroundColor Gray
    } catch {
        Write-Host "错误: 安装任务失败: $_" -ForegroundColor Red
        Write-Host "提示: 请以管理员身份运行此脚本" -ForegroundColor Yellow
    }
}

function Uninstall-Task {
    Write-Host "卸载测试覆盖率监控定时任务..." -ForegroundColor Cyan
    
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✓ 任务已卸载" -ForegroundColor Green
    } else {
        Write-Host "任务不存在" -ForegroundColor Yellow
    }
}

function Show-Status {
    Write-Host "检查测试覆盖率监控任务状态..." -ForegroundColor Cyan
    
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "任务名称: $TaskName" -ForegroundColor Green
        Write-Host "状态: $($task.State)" -ForegroundColor Green
        Write-Host "描述: $($task.Description)" -ForegroundColor Gray
        
        $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
        Write-Host "上次运行时间: $($taskInfo.LastRunTime)" -ForegroundColor Gray
        Write-Host "下次运行时间: $($taskInfo.NextRunTime)" -ForegroundColor Gray
        Write-Host "上次结果: $($taskInfo.LastTaskResult)" -ForegroundColor Gray
    } else {
        Write-Host "任务不存在" -ForegroundColor Yellow
    }
}

# 主逻辑
if ($Install) {
    Install-Task
} elseif ($Uninstall) {
    Uninstall-Task
} elseif ($Status) {
    Show-Status
} else {
    Write-Host "测试覆盖率监控任务管理" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "用法:" -ForegroundColor Yellow
    Write-Host "  .\install-coverage-monitor.ps1 -Install    # 安装定时任务" -ForegroundColor White
    Write-Host "  .\install-coverage-monitor.ps1 -Uninstall  # 卸载定时任务" -ForegroundColor White
    Write-Host "  .\install-coverage-monitor.ps1 -Status     # 查看任务状态" -ForegroundColor White
}

