# 执行部署任务脚本
# 从智能体工作目录读取任务文件并执行

param(
    [string]$TaskFile,
    [string]$Workdir = ".\deployment-agent\workdir"
)

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "执行部署智能体任务" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 如果没有指定任务文件，查找最新的任务文件
if (-not $TaskFile) {
    $taskFiles = Get-ChildItem -Path $Workdir -Filter "*.json" | 
        Where-Object { $_.Name -like "*task*.json" } | 
        Sort-Object LastWriteTime -Descending
    
    if ($taskFiles.Count -eq 0) {
        Write-Host "未找到任务文件" -ForegroundColor Red
        exit 1
    }
    
    $TaskFile = $taskFiles[0].FullName
    Write-Host "使用最新任务文件: $TaskFile" -ForegroundColor Yellow
}

if (-not (Test-Path $TaskFile)) {
    Write-Host "任务文件不存在: $TaskFile" -ForegroundColor Red
    exit 1
}

# 读取任务文件
$task = Get-Content $TaskFile | ConvertFrom-Json

Write-Host "任务类型: $($task.type)" -ForegroundColor Cyan
Write-Host "脚本: $($task.script)" -ForegroundColor Cyan
Write-Host "服务: $($task.services -join ', ')" -ForegroundColor Cyan
Write-Host ""

# 执行命令
Write-Host "执行命令..." -ForegroundColor Yellow
Write-Host "$($task.command)" -ForegroundColor Gray
Write-Host ""

# 切换到项目根目录
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Push-Location $ProjectRoot

try {
    # 执行PowerShell命令
    Invoke-Expression $task.command
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 任务执行成功" -ForegroundColor Green
    } else {
        Write-Host "❌ 任务执行失败 (退出码: $LASTEXITCODE)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ 执行错误: $_" -ForegroundColor Red
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "任务完成" -ForegroundColor Cyan




