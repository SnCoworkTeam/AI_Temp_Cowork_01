# 启动测试覆盖率监控（主入口）
# 每5分钟检查一次，如果停止则自动继续执行

param(
    [switch]$InstallTask = $false,
    [switch]$RunOnce = $false
)

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "测试覆盖率自动提升系统" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

if ($InstallTask) {
    # 安装Windows定时任务
    Write-Host "安装Windows定时任务..." -ForegroundColor Yellow
    & "$ScriptRoot\scripts\test-coverage\start-coverage-monitor.ps1" -Install
    & "$ScriptRoot\scripts\test-coverage\start-coverage-monitor.ps1" -Start
    Write-Host ""
    Write-Host "✓ 定时任务已安装并启动" -ForegroundColor Green
    Write-Host "任务将每5分钟自动检查一次" -ForegroundColor Gray
} else {
    # 直接运行持续改进脚本
    Write-Host "启动持续改进监控..." -ForegroundColor Yellow
    Write-Host ""
    
    if ($RunOnce) {
        & "$ScriptRoot\scripts\test-coverage\auto-continue-coverage.ps1"
    } else {
        & "$ScriptRoot\scripts\test-coverage\run-continuous-improvement.ps1"
    }
}

Write-Host ""
Write-Host "提示：当检测到停止时，系统会自动输出继续执行的指令" -ForegroundColor Cyan
Write-Host "你可以复制该指令内容到Cursor对话框，让AI继续执行" -ForegroundColor Cyan

