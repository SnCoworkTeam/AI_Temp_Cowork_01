# 最小化测试版本 - 先验证基本功能
param(
    [int]$LoopInterval = 60  # 测试用1分钟
)

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "测试覆盖率提升循环（测试版）" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "项目根目录: $ProjectRoot" -ForegroundColor Yellow
Write-Host "循环间隔: $LoopInterval 秒" -ForegroundColor Yellow
Write-Host ""

# 初始化进度文件
$progressFile = Join-Path $ProjectRoot ".coverage-progress.json"
if (-not (Test-Path $progressFile)) {
    Write-Host "创建进度文件..." -ForegroundColor Yellow
    $progress = @{
        version = "1.0"
        last_updated = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        target_coverage = 80
        iteration = 0
        start_time = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    }
    $progress | ConvertTo-Json -Depth 10 | Set-Content $progressFile
}

Write-Host "进度文件: $progressFile" -ForegroundColor Green
Write-Host ""

# 简单循环测试
$iteration = 0
$maxIterations = 3  # 只测试3次

while ($iteration -lt $maxIterations) {
    $iteration++
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "第 $iteration 轮循环 ($timestamp)" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # 更新进度
    if (Test-Path $progressFile) {
        $progress = Get-Content $progressFile | ConvertFrom-Json
        $progress.last_updated = $timestamp
        $progress.iteration = $iteration
        $progress | ConvertTo-Json -Depth 10 | Set-Content $progressFile
        Write-Host "进度已更新" -ForegroundColor Green
    }
    
    Write-Host "等待 $LoopInterval 秒..." -ForegroundColor Yellow
    Start-Sleep -Seconds $LoopInterval
    Write-Host ""
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "测试完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

