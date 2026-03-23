# 自动继续测试覆盖率提升脚本
# 检测到停止时自动发送继续执行指令

param(
    [int]$CheckInterval = 300  # 5分钟
)

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)

# 检查是否应该继续执行
function Should-Continue {
    $markerFile = Join-Path $ProjectRoot ".coverage-improvement-active"
    $instructionFile = Join-Path $ProjectRoot "continue-coverage-improvement.txt"
    
    # 检查标记文件是否存在且较新（1小时内）
    if (Test-Path $markerFile) {
        $markerTime = (Get-Item $markerFile).LastWriteTime
        $timeDiff = (Get-Date) - $markerTime
        
        if ($timeDiff.TotalHours -lt 1) {
            return $true
        }
    }
    
    # 检查指令文件
    if (Test-Path $instructionFile) {
        return $true
    }
    
    return $false
}

# 发送继续执行消息（模拟用户输入）
function Send-ContinueMessage {
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "检测到测试覆盖率提升计划已停止" -ForegroundColor Yellow
    Write-Host "自动发送继续执行指令..." -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # 创建指令文件
    $instructionFile = Join-Path $ProjectRoot "continue-coverage-improvement.txt"
    $instruction = @"
继续执行测试覆盖率提升计划，为所有未达到80%覆盖率的服务添加测试，直到所有服务都达到80%覆盖率。
"@
    
    Set-Content -Path $instructionFile -Value $instruction -Force
    
    # 更新标记文件
    $markerFile = Join-Path $ProjectRoot ".coverage-improvement-active"
    Set-Content -Path $markerFile -Value (Get-Date -Format "yyyy-MM-dd HH:mm:ss") -Force
    
    Write-Host "✓ 已发送继续执行指令" -ForegroundColor Green
    Write-Host "指令文件: $instructionFile" -ForegroundColor Gray
    Write-Host ""
    
    # 输出指令内容（可以作为对话框输入）
    Write-Host "--- 对话框输入内容 ---" -ForegroundColor Cyan
    Write-Host $instruction -ForegroundColor White
    Write-Host "--- 结束 ---" -ForegroundColor Cyan
    Write-Host ""
}

# 检查覆盖率状态
function Check-IfNeedsImprovement {
    $checkScript = Join-Path $ScriptRoot "check-coverage-status.py"
    
    if (-not (Test-Path $checkScript)) {
        return $true  # 如果脚本不存在，假设需要改进
    }
    
    try {
        $result = & python $checkScript 2>&1
        $exitCode = $LASTEXITCODE
        
        return $exitCode -ne 0  # 非0表示还有服务未达到80%
    } catch {
        return $true
    }
}

# 主循环
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "测试覆盖率自动继续执行监控" -ForegroundColor Cyan
Write-Host "检查间隔: $CheckInterval 秒 (5分钟)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$iteration = 0

while ($true) {
    $iteration++
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host "[$timestamp] 第 $iteration 次检查..." -ForegroundColor Gray
    
    # 检查是否需要改进
    $needsImprovement = Check-IfNeedsImprovement
    
    if (-not $needsImprovement) {
        Write-Host "✓ 所有服务已达到80%覆盖率！" -ForegroundColor Green
        Write-Host "任务完成，退出监控" -ForegroundColor Green
        break
    }
    
    # 检查是否应该继续执行
    $shouldContinue = Should-Continue
    
    if ($shouldContinue) {
        Write-Host "检测到需要继续执行..." -ForegroundColor Yellow
        
        # 检查是否有正在运行的进程
        $processes = Get-Process | Where-Object {
            $_.ProcessName -like "*python*" -and 
            ($_.CommandLine -like "*improve-coverage*" -or 
             $_.CommandLine -like "*coverage*")
        } -ErrorAction SilentlyContinue
        
        if ($processes.Count -eq 0) {
            Write-Host "未检测到正在运行的进程，发送继续执行指令..." -ForegroundColor Yellow
            Send-ContinueMessage
        } else {
            Write-Host "检测到正在运行的进程，跳过..." -ForegroundColor Green
        }
    }
    
    Write-Host "等待 $CheckInterval 秒..." -ForegroundColor Gray
    Write-Host ""
    
    Start-Sleep -Seconds $CheckInterval
}

