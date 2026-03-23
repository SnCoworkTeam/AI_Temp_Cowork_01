# 使用交互式SSH会话运行测试

param(
    [string]$Service = "workflow-engine"
)

$ErrorActionPreference = "Continue"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SessionScript = Join-Path $ScriptRoot "ssh-interactive-session.ps1"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Running Tests (Interactive Session Mode)" -ForegroundColor Cyan
Write-Host "Service: $Service" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 确保会话已启动
Write-Host "[1/4] Ensuring SSH interactive session..." -ForegroundColor Blue
& powershell -ExecutionPolicy Bypass -File $SessionScript -Action start | Out-Null
Start-Sleep -Seconds 2

# 检查状态
$status = & powershell -ExecutionPolicy Bypass -File $SessionScript -Action status
Write-Host $status

# 执行测试
Write-Host "[2/4] Running tests..." -ForegroundColor Blue
$testCommand = "sudo docker exec enterprise-ai-$Service python3 -m pytest /app/tests/unit/ --cov=/app/src --cov-report=term-missing -q 2>&1 | tail -60"

$output = & powershell -ExecutionPolicy Bypass -File $SessionScript -Action execute -Command $testCommand

Write-Host "[3/4] Tests completed" -ForegroundColor Green
Write-Host ""
Write-Host "Test Output:" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host $output
Write-Host "----------------------------------------" -ForegroundColor Gray

# 提取覆盖率
$coverageMatch = $output | Select-String -Pattern "TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%" | Select-Object -First 1
if ($coverageMatch) {
    $total = $coverageMatch.Matches.Groups[1].Value
    $missed = $coverageMatch.Matches.Groups[2].Value
    $coverage = [int]$coverageMatch.Matches.Groups[3].Value
    
    Write-Host ""
    Write-Host "Coverage: $coverage%" -ForegroundColor $(if ($coverage -ge 80) { "Green" } else { "Yellow" })
    Write-Host "Total: $total lines, Missed: $missed lines" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[4/4] Done" -ForegroundColor Green
Write-Host ""
Write-Host "Note: SSH interactive session window remains open." -ForegroundColor Gray
Write-Host "You can minimize it, but keep it running for faster connections." -ForegroundColor Gray

