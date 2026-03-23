# 调试版本 - 找出卡住的原因
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "调试模式：测试覆盖率循环" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)

Write-Host "[1] 检查基本路径..." -ForegroundColor Yellow
Write-Host "  脚本目录: $ScriptRoot" -ForegroundColor Gray
Write-Host "  项目根目录: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

Write-Host "[2] 检查SSH会话管理器..." -ForegroundColor Yellow
$SessionScript = Join-Path (Split-Path $ScriptRoot -Parent) "deployment\ssh-session-manager.ps1"
if (Test-Path $SessionScript) {
    Write-Host "  ✓ SSH会话管理器存在" -ForegroundColor Green
} else {
    Write-Host "  ✗ SSH会话管理器不存在: $SessionScript" -ForegroundColor Red
}
Write-Host ""

Write-Host "[3] 测试Start-Job（带超时）..." -ForegroundColor Yellow
try {
    $testJob = Start-Job -ScriptBlock { Start-Sleep -Seconds 2; Write-Output "Job完成" }
    Write-Host "  作业已启动，等待结果（最多5秒）..." -ForegroundColor Gray
    
    $result = Wait-Job $testJob -Timeout 5
    if ($result) {
        $output = Receive-Job $testJob
        Write-Host "  ✓ Job测试成功: $output" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Job超时" -ForegroundColor Red
        Stop-Job $testJob -ErrorAction SilentlyContinue
    }
    Remove-Job $testJob -Force -ErrorAction SilentlyContinue
} catch {
    Write-Host "  ✗ Job测试失败: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "[4] 测试SSH连接（如果配置存在）..." -ForegroundColor Yellow
$ConfigPath = Join-Path $ProjectRoot "remote.ssh"
if (Test-Path $ConfigPath) {
    Write-Host "  SSH配置文件存在，测试连接（最多10秒）..." -ForegroundColor Gray
    try {
        $sshJob = Start-Job -ScriptBlock {
            param($config)
            ssh -F $config -O check enterprise-ai-server 2>&1
        } -ArgumentList $ConfigPath
        
        $sshResult = Wait-Job $sshJob -Timeout 10
        if ($sshResult) {
            $sshOutput = Receive-Job $sshJob
            Write-Host "  SSH检查结果: $sshOutput" -ForegroundColor Gray
        } else {
            Write-Host "  ⚠ SSH检查超时（可能连接不上）" -ForegroundColor Yellow
            Stop-Job $sshJob -ErrorAction SilentlyContinue
        }
        Remove-Job $sshJob -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Host "  ✗ SSH测试失败: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  SSH配置文件不存在，跳过" -ForegroundColor Gray
}
Write-Host ""

Write-Host "[5] 检查Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python可用: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python不可用" -ForegroundColor Red
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "调试完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "如果脚本卡住，可能的原因：" -ForegroundColor Yellow
Write-Host "  1. SSH连接超时（没有设置超时）" -ForegroundColor White
Write-Host "  2. Start-Job没有超时控制" -ForegroundColor White
Write-Host "  3. 某些命令在等待输入" -ForegroundColor White
Write-Host "  4. 网络连接问题" -ForegroundColor White

