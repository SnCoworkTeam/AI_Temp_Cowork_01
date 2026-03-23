# 使用安全SSH执行运行测试

param(
    [string]$Service = "workflow-engine"
)

$ErrorActionPreference = "Continue"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExecScript = Join-Path $ScriptRoot "ssh-exec-safe.ps1"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Running Tests (Safe Mode)" -ForegroundColor Cyan
Write-Host "Service: $Service" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$testCommand = "sudo docker exec enterprise-ai-$Service python3 -m pytest /app/tests/unit/ --cov=/app/src --cov-report=term-missing -q 2>&1 | tail -60"

Write-Host "[1/3] Running tests..." -ForegroundColor Blue

$output = & powershell -ExecutionPolicy Bypass -File $ExecScript -Command $testCommand -Timeout 300

Write-Host "[2/3] Tests completed" -ForegroundColor Green
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
    
    if ($coverage -lt 80) {
        Write-Host ""
        Write-Host "Need to improve coverage to 80%+" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[3/3] Done" -ForegroundColor Green
