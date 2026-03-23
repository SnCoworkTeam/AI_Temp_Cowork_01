# 可靠的测试执行脚本
# 使用可靠的SSH执行，避免卡住

param(
    [string]$Service = "workflow-engine",
    [int]$Timeout = 300
)

$ErrorActionPreference = "Continue"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExecScript = Join-Path $ScriptRoot "ssh-exec-reliable.ps1"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Running Tests (Reliable Mode)" -ForegroundColor Cyan
Write-Host "Service: $Service" -ForegroundColor Cyan
Write-Host "Timeout: $Timeout seconds" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$testCommand = "sudo docker exec enterprise-ai-$Service python3 -m pytest /app/tests/unit/ --cov=/app/src --cov-report=term-missing -q 2>&1 | tail -60"

Write-Host "[1/3] Executing tests..." -ForegroundColor Blue

try {
    $output = & powershell -ExecutionPolicy Bypass -File $ExecScript -Command $testCommand -Timeout $Timeout -CleanBeforeExecute
    
    Write-Host "[2/3] Tests completed" -ForegroundColor Green
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
        } else {
            Write-Host ""
            Write-Host "Coverage target achieved!" -ForegroundColor Green
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
    Write-Host "[3/3] Done" -ForegroundColor Green
    
} catch {
    Write-Host "[2/3] Test execution failed" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

