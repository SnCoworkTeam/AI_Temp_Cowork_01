# 启动测试覆盖率监控服务
# 创建Windows定时任务，每5分钟检查一次

param(
    [switch]$Install = $false,
    [switch]$Uninstall = $false,
    [switch]$Start = $false
)

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)

$TaskName = "EnterpriseAI-TestCoverageMonitor"
$MonitorScript = Join-Path $ScriptRoot "auto-continue-coverage.ps1"
$TaskDescription = "每5分钟检查测试覆盖率提升计划，如果停止则自动继续执行"

function Install-Task {
    Write-Host "安装测试覆盖率监控任务..." -ForegroundColor Cyan
    
    # 检查任务是否已存在
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "任务已存在，先删除..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # 创建任务操作
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -File `"$MonitorScript`""
    
    # 创建任务触发器（每5分钟执行一次）
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)
    
    # 创建任务设置
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false
    
    # 注册任务
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
    Write-Host "  执行间隔: 每5分钟" -ForegroundColor Gray
    Write-Host "  脚本路径: $MonitorScript" -ForegroundColor Gray
}

function Uninstall-Task {
    Write-Host "卸载测试覆盖率监控任务..." -ForegroundColor Cyan
    
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✓ 任务已卸载" -ForegroundColor Green
    } else {
        Write-Host "任务不存在" -ForegroundColor Yellow
    }
}

function Start-Task {
    Write-Host "启动测试覆盖率监控..." -ForegroundColor Cyan
    
    # 检查任务是否存在
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $existingTask) {
        Write-Host "任务不存在，先安装..." -ForegroundColor Yellow
        Install-Task
    }
    
    # 启动任务
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "✓ 监控已启动" -ForegroundColor Green
    
    # 显示任务状态
    $task = Get-ScheduledTask -TaskName $TaskName
    Write-Host "任务状态: $($task.State)" -ForegroundColor Gray
}

# 主逻辑
if ($Install) {
    Install-Task
} elseif ($Uninstall) {
    Uninstall-Task
} elseif ($Start) {
    Start-Task
} else {
    Write-Host "用法:" -ForegroundColor Cyan
    Write-Host "  .\start-coverage-monitor.ps1 -Install    # 安装定时任务" -ForegroundColor White
    Write-Host "  .\start-coverage-monitor.ps1 -Uninstall  # 卸载定时任务" -ForegroundColor White
    Write-Host "  .\start-coverage-monitor.ps1 -Start      # 启动监控" -ForegroundColor White
    Write-Host ""
    Write-Host "或者直接运行监控脚本:" -ForegroundColor Cyan
    Write-Host "  .\auto-continue-coverage.ps1" -ForegroundColor White
}

