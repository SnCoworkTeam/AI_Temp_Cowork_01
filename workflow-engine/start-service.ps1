# 启动 Workflow Engine 服务
# 此脚本会启动数据库服务（如果Docker可用）并启动workflow-engine

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "启动 Workflow Engine 服务" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查并启动Docker服务
Write-Host "[1/4] 检查Docker服务..." -ForegroundColor Yellow
try {
    docker ps > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker已运行" -ForegroundColor Green
        Write-Host "启动数据库服务..." -ForegroundColor Gray
        cd ..
        docker-compose -f docker-compose.db.yml up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 数据库服务已启动" -ForegroundColor Green
            Start-Sleep -Seconds 3
        } else {
            Write-Host "⚠️  数据库服务启动失败，继续启动workflow-engine" -ForegroundColor Yellow
        }
        cd workflow-engine
    } else {
        Write-Host "⚠️  Docker未运行，跳过数据库服务启动" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Docker未安装或未运行，跳过数据库服务启动" -ForegroundColor Yellow
}
Write-Host ""

# 2. 激活虚拟环境
Write-Host "[2/4] 激活虚拟环境..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 虚拟环境激活失败" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green
Write-Host ""

# 3. 设置环境变量
Write-Host "[3/4] 设置环境变量..." -ForegroundColor Yellow
$projectRoot = Split-Path -Parent $PSScriptRoot
# 将项目根目录添加到PYTHONPATH，这样Python可以找到shared_libs包
$env:PYTHONPATH = "$projectRoot;$env:PYTHONPATH"
$env:REDIS_HOST = "localhost"
# 数据库配置（匹配Docker容器配置）
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_USER = "ai_user"
$env:DB_PASSWORD = "ai_password"
$env:DB_NAME = "ai_platform"

Write-Host "PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray
Write-Host "✅ 环境变量已设置" -ForegroundColor Green
Write-Host ""

# 4. 启动服务
Write-Host "[4/4] 启动 Workflow Engine..." -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "服务地址: http://127.0.0.1:8002" -ForegroundColor Cyan
Write-Host "健康检查: http://127.0.0.1:8002/api/health" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

python -m uvicorn src.main:app --host 127.0.0.1 --port 8002

