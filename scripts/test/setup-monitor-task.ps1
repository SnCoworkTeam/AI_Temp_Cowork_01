# 设置Windows定时任务来监控测试报告

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "📅 设置测试报告监控定时任务" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本路径
$ScriptPath = $PSScriptRoot
$MonitorScript = Join-Path $ScriptPath "monitor-test-reports.ps1"

if (-not (Test-Path $MonitorScript)) {
    Write-Host "❌ 监控脚本不存在: $MonitorScript" -ForegroundColor Red
    exit 1
}

# 检查是否已存在任务
$TaskName = "EnterpriseAIPlatform-TestMonitor"
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "⚠️  定时任务已存在: $TaskName" -ForegroundColor Yellow
    $response = Read-Host "是否删除并重新创建? (Y/N)"
    if ($response -eq "Y" -or $response -eq "y") {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ 已删除旧任务" -ForegroundColor Green
    } else {
        Write-Host "取消操作" -ForegroundColor Yellow
        exit 0
    }
}

# 询问配置
Write-Host "`n配置定时任务:" -ForegroundColor Cyan
$interval = Read-Host "检查间隔（分钟，默认30）"
if ([string]::IsNullOrWhiteSpace($interval)) {
    $interval = 30
}

$runTests = Read-Host "是否在检查前自动运行测试? (Y/N，默认N)"
$runTestsFlag = if ($runTests -eq "Y" -or $runTests -eq "y") { "-RunTests" } else { "" }

# 创建任务动作
$Action = New-ScheduledTaskAction -Execute "pwsh.exe" `
    -Argument "-File `"$MonitorScript`" -IntervalMinutes $interval $runTestsFlag" `
    -WorkingDirectory (Split-Path $ScriptPath -Parent -Parent)

# 创建触发器（每30分钟运行一次）
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $interval) -RepetitionDuration (New-TimeSpan -Days 365)

# 创建任务设置
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# 注册任务
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "企业AI平台测试报告监控" | Out-Null
    Write-Host "`n✅ 定时任务已创建: $TaskName" -ForegroundColor Green
    Write-Host "   检查间隔: $interval 分钟" -ForegroundColor Cyan
    Write-Host "   自动运行测试: $($runTests -eq 'Y')" -ForegroundColor Cyan
    Write-Host "`n📋 管理任务命令:" -ForegroundColor Yellow
    Write-Host "   查看任务: Get-ScheduledTask -TaskName `"$TaskName`"" -ForegroundColor Cyan
    Write-Host "   运行任务: Start-ScheduledTask -TaskName `"$TaskName`"" -ForegroundColor Cyan
    Write-Host "   删除任务: Unregister-ScheduledTask -TaskName `"$TaskName`" -Confirm:`$false" -ForegroundColor Cyan
}
catch {
    Write-Host "❌ 创建定时任务失败: $_" -ForegroundColor Red
    exit 1
}

