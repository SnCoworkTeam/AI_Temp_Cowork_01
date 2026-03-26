# 启动 Workflow Engine 服务 - 简化版本
$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "启动 Workflow Engine 服务" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 设置工作目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# 设置环境变量
$projectRoot = Split-Path -Parent $scriptDir
$env:PYTHONPATH = "$projectRoot;$env:PYTHONPATH"

# 数据库配置（匹配Docker容器配置）
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_USER = "ai_user"
$env:DB_PASSWORD = "ai_password"
$env:DB_NAME = "ai_platform"

# Redis配置
$env:REDIS_HOST = "localhost"
$env:REDIS_PORT = "6379"

Write-Host "配置信息:" -ForegroundColor Yellow
Write-Host "  PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray
Write-Host "  数据库: $env:DB_USER@$env:DB_HOST:$env:DB_PORT/$env:DB_NAME" -ForegroundColor Gray
Write-Host "  Redis: $env:REDIS_HOST:$env:REDIS_PORT" -ForegroundColor Gray
Write-Host ""

# 检查虚拟环境
$venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "❌ 虚拟环境不存在，请先创建虚拟环境" -ForegroundColor Red
    exit 1
}

# 启动服务
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "启动 Workflow Engine..." -ForegroundColor Yellow
Write-Host "服务地址: http://127.0.0.1:8002" -ForegroundColor Cyan
Write-Host "健康检查: http://127.0.0.1:8002/api/health" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

& $venvPython -m uvicorn src.main:app --host 127.0.0.1 --port 8002 --reload

