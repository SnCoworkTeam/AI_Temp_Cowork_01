# 检查所有服务的测试覆盖率
# 在本地运行，检查每个服务的覆盖率

$ErrorActionPreference = "Continue"

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
    
    $servicePath = Join-Path $PSScriptRoot $service
    if (-not (Test-Path $servicePath)) {
        Write-Host "  [SKIP] Service directory not found" -ForegroundColor Yellow
        continue
    }
    
    $testPath = Join-Path $servicePath "tests"
    if (-not (Test-Path $testPath)) {
        Write-Host "  [SKIP] Tests directory not found" -ForegroundColor Yellow
        $results += [PSCustomObject]@{
            Service = $service
            Coverage = 0
            Total = 0
            Missed = 0
            Passed = 0
            Failed = 0
            Status = "NO_TESTS"
        }
        continue
    }
    
    Push-Location $servicePath
    
    try {
        # 运行测试并获取覆盖率
        $output = & python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=json -q 2>&1
        
        # 查找覆盖率JSON文件
        $coverageJsonPath = Join-Path $servicePath ".coverage.json"
        if (Test-Path $coverageJsonPath) {
            $coverageData = Get-Content $coverageJsonPath | ConvertFrom-Json
            $total = $coverageData.totals.num_statements
            $covered = $coverageData.totals.covered_lines
            $missed = $total - $covered
            $coverage = if ($total -gt 0) { [math]::Round(($covered / $total) * 100, 2) } else { 0 }
        } else {
            # 从输出中提取覆盖率
            $coverageMatch = $output | Select-String -Pattern "TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%" | Select-Object -First 1
            if ($coverageMatch) {
                $total = [int]$coverageMatch.Matches.Groups[1].Value
                $missed = [int]$coverageMatch.Matches.Groups[2].Value
                $coverage = [int]$coverageMatch.Matches.Groups[3].Value
            } else {
                $total = 0
                $missed = 0
                $coverage = 0
            }
        }
        
        # 提取测试结果
        $passedMatch = $output | Select-String -Pattern "(\d+)\s+passed" | Select-Object -First 1
        $failedMatch = $output | Select-String -Pattern "(\d+)\s+failed" | Select-Object -First 1
        
        $passed = if ($passedMatch) { [int]$passedMatch.Matches.Groups[1].Value } else { 0 }
        $failed = if ($failedMatch) { [int]$failedMatch.Matches.Groups[1].Value } else { 0 }
        
        $status = if ($coverage -ge 80) { "OK" } else { "NEEDS_IMPROVEMENT" }
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
            Status = $status
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
    } finally {
        Pop-Location
    }
    
    Write-Host ""
}

# 汇总
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$validResults = $results | Where-Object { $_.Status -ne "ERROR" -and $_.Status -ne "NO_TESTS" }
if ($validResults.Count -gt 0) {
    $avgCoverage = ($validResults | Measure-Object -Property Coverage -Average).Average
    $servicesAtTarget = ($validResults | Where-Object { $_.Coverage -ge 80 }).Count
    $totalServices = $validResults.Count
    
    Write-Host "Average Coverage: $([math]::Round($avgCoverage, 2))%" -ForegroundColor $(if ($avgCoverage -ge 80) { "Green" } else { "Yellow" })
    Write-Host "Services at 80%+: $servicesAtTarget/$totalServices" -ForegroundColor $(if ($servicesAtTarget -eq $totalServices) { "Green" } else { "Yellow" })
    Write-Host ""
    
    # 详细表格
    $results | Format-Table -AutoSize
    
    # 需要改进的服务
    $needsImprovement = $validResults | Where-Object { $_.Coverage -lt 80 }
    if ($needsImprovement) {
        Write-Host "Services needing improvement:" -ForegroundColor Yellow
        $needsImprovement | ForEach-Object {
            $gap = 80 - $_.Coverage
            Write-Host "  - $($_.Service): $($_.Coverage)% (need +$gap%)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "All services have reached 80% coverage!" -ForegroundColor Green
    }
} else {
    Write-Host "No valid coverage data found" -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan

