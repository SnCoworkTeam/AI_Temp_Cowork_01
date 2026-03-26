# 检查所有服务的测试覆盖率

param(
    [switch]$Detailed = $false
)

$ErrorActionPreference = "Continue"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SessionScript = Join-Path $ScriptRoot "ssh-session-manager.ps1"

$services = @(
    "workflow-engine",
    "database",
    "metadata-service",
    "auth-service",
    "knowledge-base",
    "mcp-gateway"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Checking Test Coverage for All Services" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$results = @()

foreach ($service in $services) {
    Write-Host "Checking $service..." -ForegroundColor Blue
    
    $testCommand = "sudo docker exec enterprise-ai-$service python3 -m pytest /app/tests/ --cov=/app/src --cov-report=term-missing -q 2>&1 | tail -20"
    
    try {
        $output = & powershell -ExecutionPolicy Bypass -File $SessionScript -Action execute -Command $testCommand
        
        # 提取覆盖率
        $coverageMatch = $output | Select-String -Pattern "TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%" | Select-Object -First 1
        $passedMatch = $output | Select-String -Pattern "(\d+)\s+passed" | Select-Object -First 1
        $failedMatch = $output | Select-String -Pattern "(\d+)\s+failed" | Select-Object -First 1
        
        $coverage = 0
        $total = 0
        $missed = 0
        $passed = 0
        $failed = 0
        
        if ($coverageMatch) {
            $total = $coverageMatch.Matches.Groups[1].Value
            $missed = $coverageMatch.Matches.Groups[2].Value
            $coverage = [int]$coverageMatch.Matches.Groups[3].Value
        }
        
        if ($passedMatch) {
            $passed = [int]$passedMatch.Matches.Groups[1].Value
        }
        
        if ($failedMatch) {
            $failed = [int]$failedMatch.Matches.Groups[1].Value
        }
        
        $status = if ($coverage -ge 80) { "OK" } else { "FAIL" }
        $color = if ($coverage -ge 80) { "Green" } else { "Yellow" }
        
        $statusSymbol = if ($coverage -ge 80) { "[OK]" } else { "[FAIL]" }
        Write-Host "  $statusSymbol Coverage: $coverage% | Passed: $passed | Failed: $failed" -ForegroundColor $color
        
        $results += [PSCustomObject]@{
            Service = $service
            Coverage = $coverage
            Total = $total
            Missed = $missed
            Passed = $passed
            Failed = $failed
            Status = if ($coverage -ge 80) { "OK" } else { "NEEDS_IMPROVEMENT" }
        }
        
        if ($Detailed) {
            Write-Host "  Details: Total=$total, Missed=$missed" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  [ERROR] Error checking $service : $_" -ForegroundColor Red
        $results += [PSCustomObject]@{
            Service = $service
            Coverage = 0
            Total = 0
            Missed = 0
            Passed = 0
            Failed = 0
            Status = "ERROR"
        }
    }
    
    Write-Host ""
}

# 汇总
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$avgCoverage = ($results | Where-Object { $_.Status -ne "ERROR" } | Measure-Object -Property Coverage -Average).Average
$servicesAtTarget = ($results | Where-Object { $_.Coverage -ge 80 }).Count
$totalServices = ($results | Where-Object { $_.Status -ne "ERROR" }).Count

Write-Host "Average Coverage: $([math]::Round($avgCoverage, 2))%" -ForegroundColor $(if ($avgCoverage -ge 80) { "Green" } else { "Yellow" })
Write-Host "Services at 80%+: $servicesAtTarget/$totalServices" -ForegroundColor $(if ($servicesAtTarget -eq $totalServices) { "Green" } else { "Yellow" })
Write-Host ""

# 详细表格
$results | Format-Table -AutoSize

# 需要改进的服务
$needsImprovement = $results | Where-Object { $_.Coverage -lt 80 -and $_.Status -ne "ERROR" }
if ($needsImprovement) {
    Write-Host "Services needing improvement:" -ForegroundColor Yellow
    $needsImprovement | ForEach-Object {
        $gap = 80 - $_.Coverage
        Write-Host "  - $($_.Service): $($_.Coverage)% (need +$gap%)" -ForegroundColor Yellow
    }
}

