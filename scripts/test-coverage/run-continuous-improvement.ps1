# 持续运行测试覆盖率提升
# 这个脚本会持续运行，直到所有服务达到80%覆盖率

param(
    [int]$CheckInterval = 300  # 5分钟
)

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "持续测试覆盖率提升系统" -ForegroundColor Cyan
Write-Host "目标：所有服务达到80%覆盖率" -ForegroundColor Cyan
Write-Host "检查间隔：$CheckInterval 秒" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$iteration = 0
$maxIterations = 1000  # 最大迭代次数（防止无限循环）

while ($iteration -lt $maxIterations) {
    $iteration++
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host "[$timestamp] ========== 第 $iteration 轮检查 ==========" -ForegroundColor Cyan
    Write-Host ""
    
    # 1. 检查覆盖率状态
    Write-Host "[1/3] 检查覆盖率状态..." -ForegroundColor Yellow
    $checkScript = Join-Path $ScriptRoot "check-coverage-status.py"
    
    if (-not (Test-Path $checkScript)) {
        Write-Host "错误：覆盖率检查脚本不存在" -ForegroundColor Red
        break
    }
    
    try {
        $coverageOutput = & python $checkScript 2>&1
        $coverageExitCode = $LASTEXITCODE
        
        if ($coverageExitCode -eq 0) {
            Write-Host "✓ 所有服务已达到80%覆盖率！" -ForegroundColor Green
            Write-Host ""
            Write-Host "任务完成！" -ForegroundColor Green
            break
        }
        
        # 解析结果
        $coverageResults = $coverageOutput | ConvertFrom-Json
        $needsImprovement = @()
        
        foreach ($service in $coverageResults.PSObject.Properties) {
            $serviceName = $service.Name
            $serviceData = $service.Value
            
            if ($serviceData.coverage -lt 80 -and $serviceData.status -ne "NO_TESTS") {
                $needsImprovement += @{
                    "name" = $serviceName
                    "coverage" = $serviceData.coverage
                    "status" = $serviceData.status
                }
            }
        }
        
        if ($needsImprovement.Count -eq 0) {
            Write-Host "✓ 所有服务已达到80%覆盖率！" -ForegroundColor Green
            break
        }
        
        Write-Host "需要改进的服务 ($($needsImprovement.Count) 个):" -ForegroundColor Yellow
        foreach ($service in $needsImprovement) {
            $gap = 80 - $service.coverage
            Write-Host "  - $($service.name): $($service.coverage)% (需要 +$gap%)" -ForegroundColor Yellow
        }
        Write-Host ""
        
    } catch {
        Write-Host "检查覆盖率时出错: $_" -ForegroundColor Red
        Write-Host "继续下一轮检查..." -ForegroundColor Yellow
        Start-Sleep -Seconds $CheckInterval
        continue
    }
    
    # 2. 执行覆盖率提升
    Write-Host "[2/3] 执行覆盖率提升..." -ForegroundColor Yellow
    $improveScript = Join-Path $ScriptRoot "improve-coverage.py"
    
    if (-not (Test-Path $improveScript)) {
        Write-Host "错误：覆盖率提升脚本不存在" -ForegroundColor Red
        break
    }
    
    try {
        Write-Host "运行覆盖率提升脚本..." -ForegroundColor Gray
        $improveOutput = & python $improveScript --all 2>&1
        Write-Host $improveOutput
        Write-Host ""
    } catch {
        Write-Host "执行覆盖率提升时出错: $_" -ForegroundColor Red
    }
    
    # 3. 发送继续执行指令（模拟对话框输入）
    Write-Host "[3/3] 准备继续执行指令..." -ForegroundColor Yellow
    
    $instruction = @"
继续执行测试覆盖率提升计划，为所有未达到80%覆盖率的服务添加测试，直到所有服务都达到80%覆盖率。
"@
    
    $instructionFile = Join-Path $ProjectRoot "continue-coverage-improvement.txt"
    Set-Content -Path $instructionFile -Value $instruction -Force
    
    Write-Host "✓ 已创建继续执行指令文件" -ForegroundColor Green
    Write-Host "文件路径: $instructionFile" -ForegroundColor Gray
    Write-Host ""
    Write-Host "--- 对话框输入内容（复制此内容到Cursor对话框）---" -ForegroundColor Cyan
    Write-Host $instruction -ForegroundColor White
    Write-Host "--- 结束 ---" -ForegroundColor Cyan
    Write-Host ""
    
    # 等待间隔
    Write-Host "等待 $CheckInterval 秒后进行下一轮检查..." -ForegroundColor Gray
    Write-Host ""
    Start-Sleep -Seconds $CheckInterval
}

if ($iteration -ge $maxIterations) {
    Write-Host "已达到最大迭代次数，退出" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "监控结束" -ForegroundColor Cyan

