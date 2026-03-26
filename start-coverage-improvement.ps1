# 启动测试覆盖率提升系统
# 持续运行直到所有服务达到80%覆盖率

param(
    [switch]$InstallMonitor = $false,
    [switch]$StartMonitor = $false,
    [switch]$StartLoop = $false
)

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "测试覆盖率80%自动化提升系统" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

if ($InstallMonitor) {
    # 安装监控定时任务
    Write-Host "安装监控定时任务..." -ForegroundColor Yellow
    & "$ScriptRoot\scripts\test-coverage\install-coverage-monitor.ps1" -Install
    Write-Host ""
    Write-Host "✓ 监控定时任务已安装（每10分钟检查一次）" -ForegroundColor Green
}

if ($StartMonitor) {
    # 启动监控（后台运行）
    Write-Host "启动任务监控..." -ForegroundColor Yellow
    $monitorScript = Join-Path $ScriptRoot "scripts\test-coverage\coverage-task-monitor.ps1"
    Start-Process -FilePath "powershell.exe" `
        -ArgumentList "-ExecutionPolicy Bypass -File `"$monitorScript`"" `
        -WindowStyle Hidden
    Write-Host "✓ 监控已启动（后台运行）" -ForegroundColor Green
}

if ($StartLoop) {
    # 启动主循环
    Write-Host "启动覆盖率提升主循环..." -ForegroundColor Yellow
    Write-Host "注意: 此进程将持续运行直到所有服务达到80%覆盖率" -ForegroundColor Cyan
    Write-Host ""
    
    $loopScript = Join-Path $ScriptRoot "scripts\test-coverage\coverage-improvement-loop.ps1"
    
    # 检查脚本是否存在
    if (-not (Test-Path $loopScript)) {
        Write-Host "错误: 主循环脚本不存在: $loopScript" -ForegroundColor Red
        exit 1
    }
    
    # 直接在当前进程运行，避免后台进程问题
    & powershell.exe -ExecutionPolicy Bypass -NoProfile -File $loopScript
}

if (-not $InstallMonitor -and -not $StartMonitor -and -not $StartLoop) {
    Write-Host "用法:" -ForegroundColor Yellow
    Write-Host "  .\start-coverage-improvement.ps1 -InstallMonitor  # 安装监控定时任务" -ForegroundColor White
    Write-Host "  .\start-coverage-improvement.ps1 -StartMonitor      # 启动监控（后台）" -ForegroundColor White
    Write-Host "  .\start-coverage-improvement.ps1 -StartLoop         # 启动主循环" -ForegroundColor White
    Write-Host ""
    Write-Host "推荐流程:" -ForegroundColor Cyan
    Write-Host "  1. .\start-coverage-improvement.ps1 -InstallMonitor" -ForegroundColor White
    Write-Host "  2. .\start-coverage-improvement.ps1 -StartMonitor" -ForegroundColor White
    Write-Host "  3. .\start-coverage-improvement.ps1 -StartLoop" -ForegroundColor White
}

