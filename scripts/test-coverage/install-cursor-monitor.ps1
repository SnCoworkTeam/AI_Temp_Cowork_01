# 安装Cursor监控定时任务
# 每5分钟检查一次Cursor是否卡住，如果卡住则自动发送继续执行指令

param(
    [switch]$Install = $false,
    [switch]$Uninstall = $false,
    [switch]$Status = $false
)

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)

$TaskName = "EnterpriseAI-CursorMonitor"
$MonitorScript = Join-Path $ScriptRoot "cursor-monitor.py"
$TaskDescription = "监控Cursor任务执行，如果卡住则自动发送继续执行指令"

function Install-Task {
    Write-Host "安装Cursor监控定时任务..." -ForegroundColor Cyan
    
    # 检查Python是否可用
    $pythonPath = $null
    $pythonCommands = @("python", "python3", "py")
    
    foreach ($cmd in $pythonCommands) {
        try {
            $result = Get-Command $cmd -ErrorAction SilentlyContinue
            if ($result) {
                $pythonPath = $result.Source
                $pythonVersion = & $cmd --version 2>&1
                Write-Host "找到Python: $pythonVersion" -ForegroundColor Green
                Write-Host "Python路径: $pythonPath" -ForegroundColor Gray
                break
            }
        } catch {
            continue
        }
    }
    
    if (-not $pythonPath) {
        Write-Host "错误: 未找到Python，请先安装Python" -ForegroundColor Red
        Write-Host "提示: 可以尝试安装Python 3.7+或使用py启动器" -ForegroundColor Yellow
        return
    }
    
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
    
    # 创建任务操作（使用找到的Python路径）
    $action = New-ScheduledTaskAction -Execute $pythonPath `
        -Argument "`"$MonitorScript`" --interval 30 --timeout 300" `
        -WorkingDirectory $ProjectRoot
    
    # 创建任务触发器（每5分钟执行一次）
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
        -RepetitionInterval (New-TimeSpan -Minutes 5) `
        -RepetitionDuration (New-TimeSpan -Days 365)
    
    # 创建任务设置
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
    
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
        Write-Host "  执行间隔: 每5分钟" -ForegroundColor Gray
        Write-Host "  脚本路径: $MonitorScript" -ForegroundColor Gray
        Write-Host "  Python路径: $pythonPath" -ForegroundColor Gray
    } catch {
        Write-Host "错误: 安装任务失败: $_" -ForegroundColor Red
        Write-Host "提示: 请以管理员身份运行此脚本" -ForegroundColor Yellow
    }
}

function Uninstall-Task {
    Write-Host "卸载Cursor监控定时任务..." -ForegroundColor Cyan
    
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✓ 任务已卸载" -ForegroundColor Green
    } else {
        Write-Host "任务不存在" -ForegroundColor Yellow
    }
}

function Show-Status {
    Write-Host "检查Cursor监控任务状态..." -ForegroundColor Cyan
    
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
    Write-Host "Cursor监控任务管理" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "用法:" -ForegroundColor Yellow
    Write-Host "  .\install-cursor-monitor.ps1 -Install    # 安装定时任务" -ForegroundColor White
    Write-Host "  .\install-cursor-monitor.ps1 -Uninstall  # 卸载定时任务" -ForegroundColor White
    Write-Host "  .\install-cursor-monitor.ps1 -Status     # 查看任务状态" -ForegroundColor White
    Write-Host ""
    Write-Host "或者直接运行监控脚本:" -ForegroundColor Yellow
    Write-Host "  python scripts\test-coverage\cursor-monitor.py" -ForegroundColor White
}

