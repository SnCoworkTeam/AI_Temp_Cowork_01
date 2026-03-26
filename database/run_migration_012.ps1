# 运行迁移 012 - 添加 workflow_metadata 列
# 注意：数据库在Docker容器中，通过localhost:5432访问
$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "运行数据库迁移 012" -ForegroundColor Cyan
Write-Host "添加 workflow_metadata 列" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Docker容器是否运行
Write-Host "检查Docker数据库容器..." -ForegroundColor Yellow
$containerStatus = docker ps --filter "name=enterprise-ai-postgres" --format "{{.Status}}"
if (-not $containerStatus) {
    Write-Host "❌ Docker数据库容器未运行！" -ForegroundColor Red
    Write-Host "   请先启动数据库: docker-compose -f docker-compose.db.yml up -d" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ 数据库容器运行中: $containerStatus" -ForegroundColor Green
Write-Host ""

# 设置工作目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# 设置环境变量
$projectRoot = Split-Path -Parent $scriptDir
$env:PYTHONPATH = "$projectRoot;$env:PYTHONPATH"

# 数据库配置（连接到Docker中的数据库）
$env:DB_HOST = "localhost"  # Docker端口映射到localhost
$env:DB_PORT = "5432"
$env:DB_USER = "ai_user"
$env:DB_PASSWORD = "ai_password"
$env:DB_NAME = "ai_platform"

Write-Host "配置信息:" -ForegroundColor Yellow
Write-Host "  数据库: $env:DB_USER@$env:DB_HOST:$env:DB_PORT/$env:DB_NAME" -ForegroundColor Gray
Write-Host ""

# 检查虚拟环境
$venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "❌ 虚拟环境不存在，请先创建虚拟环境" -ForegroundColor Red
    exit 1
}

# 运行迁移
Write-Host "运行迁移..." -ForegroundColor Yellow
& $venvPython -m alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 迁移完成！" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ 迁移失败" -ForegroundColor Red
    exit 1
}

