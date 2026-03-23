# 阶段一第1周测试脚本（带Docker服务自动启动）- PowerShell版本

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  阶段一第1周测试 - Docker服务自动启动" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 获取脚本所在目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR

Set-Location $PROJECT_ROOT

# 1. 启动Docker服务
Write-Host "🚀 启动Docker服务..." -ForegroundColor Cyan
docker-compose up -d postgres

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker服务启动失败" -ForegroundColor Red
    exit 1
}

# 2. 等待服务就绪
Write-Host "⏳ 等待postgres服务就绪..." -ForegroundColor Yellow
$maxRetries = 30
$retryInterval = 2
$serviceReady = $false

for ($i = 1; $i -le $maxRetries; $i++) {
    $status = docker ps --filter "name=postgres" --format "{{.Status}}" 2>$null
    if ($status -match "Up") {
        Write-Host "✅ postgres 服务已启动" -ForegroundColor Green
        $serviceReady = $true
        break
    }
    if ($i -lt $maxRetries) {
        Write-Host "  等待中... ($i/$maxRetries)" -ForegroundColor Gray
        Start-Sleep -Seconds $retryInterval
    }
}

if (-not $serviceReady) {
    Write-Host "❌ postgres 服务启动超时" -ForegroundColor Red
    exit 1
}

# 额外等待数据库完全就绪
Write-Host "⏳ 等待数据库完全就绪..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 3. 执行数据库迁移
Write-Host ""
Write-Host "📦 执行数据库迁移..." -ForegroundColor Cyan
Set-Location "$PROJECT_ROOT\database"
alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 数据库迁移失败" -ForegroundColor Red
    Set-Location $PROJECT_ROOT
    exit 1
}

Set-Location $PROJECT_ROOT

# 4. 运行测试
Write-Host ""
Write-Host "🧪 运行测试..." -ForegroundColor Cyan
python -m pytest tests/test_stage1_week1_with_docker.py -v --tb=short -s

$TEST_EXIT_CODE = $LASTEXITCODE

# 5. 测试结果
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
if ($TEST_EXIT_CODE -eq 0) {
    Write-Host "✅ 所有测试通过！" -ForegroundColor Green
    Write-Host "✅ 可以进入第2周" -ForegroundColor Green
} else {
    Write-Host "❌ 测试失败，请检查错误信息" -ForegroundColor Red
    Write-Host "❌ 不能进入第2周" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Green

exit $TEST_EXIT_CODE





