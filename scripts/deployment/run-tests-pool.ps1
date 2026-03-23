# 使用连接池运行测试
# 所有测试通过同一个持久连接执行

param(
    [string]$Service = "workflow-engine",
    [int]$Timeout = 300
)

$ErrorActionPreference = "Continue"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PoolScript = Join-Path $ScriptRoot "ssh-pool-manager.ps1"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Running Tests (Connection Pool Mode)" -ForegroundColor Cyan
Write-Host "Service: $Service" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 确保连接池已启动
Write-Host "[1/4] Ensuring connection pool is active..." -ForegroundColor Blue
& powershell -ExecutionPolicy Bypass -File $PoolScript -Action start | Out-Null
Start-Sleep -Seconds 1

# 检查状态
$status = & powershell -ExecutionPolicy Bypass -File $PoolScript -Action status
Write-Host $status

# 执行测试
Write-Host "[2/4] Running tests..." -ForegroundColor Blue
$testCommand = "sudo docker exec enterprise-ai-$Service python3 -m pytest /app/tests/unit/ --cov=/app/src --cov-report=term-missing -q 2>&1 | tail -60"

$output = & powershell -ExecutionPolicy Bypass -File $PoolScript -Action execute -Command $testCommand

Write-Host "[3/4] Tests completed" -ForegroundColor Green
Write-Host ""
Write-Host "Test Output:" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host $output
Write-Host "----------------------------------------" -ForegroundColor Gray

# 提取覆盖率
if ($output -match "TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%") {
    $total = $matches[1]
    $missed = $matches[2]
    $coverage = [int]$matches[3]
    
    Write-Host ""
    Write-Host "Coverage: $coverage%" -ForegroundColor $(if ($coverage -ge 80) { "Green" } else { "Yellow" })
    Write-Host "Total: $total lines, Missed: $missed lines" -ForegroundColor Gray
    
    if ($coverage -lt 80) {
        Write-Host ""
        Write-Host "Need to improve coverage to 80%+" -ForegroundColor Yellow
    }
}

# 检查失败的测试
if ($output -match "(\d+)\s+failed") {
    $failedCount = [int]$matches[1]
    if ($failedCount -gt 0) {
        Write-Host ""
        Write-Host "Failed tests: $failedCount" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "[4/4] Done (connection pool remains active)" -ForegroundColor Green

