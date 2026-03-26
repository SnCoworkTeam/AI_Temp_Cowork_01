# 启动 Auth Service

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "启动 Auth Service" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 激活虚拟环境
Write-Host "[1/4] 激活虚拟环境..." -ForegroundColor Yellow
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "❌ 虚拟环境不存在，正在创建..." -ForegroundColor Red
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 虚拟环境创建失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ 虚拟环境创建成功" -ForegroundColor Green
}

& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 虚拟环境激活失败" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green
Write-Host ""

# 2. 安装依赖
Write-Host "[2/4] 检查并安装依赖..." -ForegroundColor Yellow
if (-not (Test-Path "venv\Lib\site-packages\fastapi")) {
    Write-Host "正在安装依赖包..." -ForegroundColor Gray
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 依赖安装失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ 依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "✅ 依赖已安装" -ForegroundColor Green
}
Write-Host ""

# 3. 设置环境变量
Write-Host "[3/4] 设置环境变量..." -ForegroundColor Yellow
$projectRoot = Split-Path -Parent $PSScriptRoot
# 将项目根目录添加到PYTHONPATH，这样Python可以找到shared_libs包
$env:PYTHONPATH = "$projectRoot;$env:PYTHONPATH"

# 数据库配置（连接Docker中的PostgreSQL）
# 注意：这些配置必须与docker-compose.yml中的数据库配置一致
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_USER = "ai_user"
$env:DB_PASSWORD = "ai_password"
$env:DB_NAME = "ai_platform"

# Redis配置（连接Docker中的Redis）
$env:REDIS_HOST = "localhost"
$env:REDIS_PORT = "6379"
$env:REDIS_DB = "0"

Write-Host "配置信息:" -ForegroundColor Gray
Write-Host "  PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray
Write-Host "  数据库: $env:DB_USER@$env:DB_HOST:$env:DB_PORT/$env:DB_NAME" -ForegroundColor Gray
Write-Host "  Redis: $env:REDIS_HOST:$env:REDIS_PORT" -ForegroundColor Gray
Write-Host "✅ 环境变量已设置" -ForegroundColor Green
Write-Host ""

# 4. 启动服务
Write-Host "[4/4] 启动 Auth Service..." -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "服务地址: http://127.0.0.1:8003" -ForegroundColor Cyan
Write-Host "健康检查: http://127.0.0.1:8003/health" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

python -m uvicorn src.main:app --host 127.0.0.1 --port 8003 --reload

