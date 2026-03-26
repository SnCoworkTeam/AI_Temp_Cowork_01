# 在原生PowerShell中运行覆盖率提升循环
# 避免Cursor终端环境问题

$ErrorActionPreference = "Continue"

# 获取脚本目录
if ($PSScriptRoot) {
    $ScriptPath = Join-Path $PSScriptRoot "scripts\test-coverage\coverage-improvement-loop.ps1"
} else {
    $ScriptPath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "scripts\test-coverage\coverage-improvement-loop.ps1"
}

if (-not (Test-Path $ScriptPath)) {
    Write-Host "错误: 找不到脚本文件: $ScriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "启动测试覆盖率提升循环" -ForegroundColor Cyan
Write-Host "脚本路径: $ScriptPath" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 在原生PowerShell中执行，添加超时保护
try {
    $job = Start-Job -ScriptBlock {
        param($script)
        & pwsh -ExecutionPolicy Bypass -File $script
    } -ArgumentList $ScriptPath
    
    # 等待最多5分钟，如果卡住就停止
    $result = Wait-Job $job -Timeout 300
    
    if ($result) {
        $output = Receive-Job $job
        Remove-Job $job -ErrorAction SilentlyContinue
        Write-Host $output
    } else {
        Write-Host "警告: 脚本执行超时（5分钟），可能卡住了" -ForegroundColor Yellow
        Stop-Job $job -ErrorAction SilentlyContinue
        Remove-Job $job -ErrorAction SilentlyContinue
        Write-Host "已停止卡住的脚本" -ForegroundColor Yellow
    }
} catch {
    Write-Host "执行出错: $_" -ForegroundColor Red
    exit 1
}
