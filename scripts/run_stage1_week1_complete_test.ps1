# 阶段一第1周完整测试脚本 - 启动服务并测试直到通过

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  阶段一第1周完整测试流程" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 获取脚本所在目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR

Set-Location $PROJECT_ROOT

# ============================================
# 步骤1: 启动Docker服务
# ============================================
Write-Host "[步骤1] 启动Docker服务..." -ForegroundColor Cyan

# 检查Docker是否运行
try {
    docker ps | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker未运行，请先启动Docker Desktop" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Docker未运行，请先启动Docker Desktop" -ForegroundColor Red
    exit 1
}

# 启动postgres服务
Write-Host "  启动postgres服务..." -ForegroundColor Yellow
docker-compose up -d postgres

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker服务启动失败" -ForegroundColor Red
    exit 1
}

# ============================================
# 步骤2: 等待服务就绪
# ============================================
Write-Host ""
Write-Host "[步骤2] 等待postgres服务就绪..." -ForegroundColor Cyan

$maxRetries = 30
$retryInterval = 2
$serviceReady = $false

for ($i = 1; $i -le $maxRetries; $i++) {
    $status = docker ps --filter "name=postgres" --format "{{.Status}}" 2>$null
    if ($status -match "Up") {
        Write-Host "  ✅ postgres 服务已启动" -ForegroundColor Green
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
Write-Host "  等待数据库完全就绪..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 测试数据库连接
Write-Host "  测试数据库连接..." -ForegroundColor Yellow
$connectionTest = docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT 1;" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ⚠️  数据库连接测试失败，继续尝试..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# ============================================
# 步骤3: 执行数据库迁移
# ============================================
Write-Host ""
Write-Host "[步骤3] 执行数据库迁移..." -ForegroundColor Cyan

Set-Location "$PROJECT_ROOT\database"

# 检查当前迁移版本
Write-Host "  检查当前迁移版本..." -ForegroundColor Yellow
$currentVersion = python -m alembic current 2>&1
Write-Host "  $currentVersion" -ForegroundColor Gray

# 执行迁移
Write-Host "  执行迁移到最新版本..." -ForegroundColor Yellow
python -m alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 数据库迁移失败" -ForegroundColor Red
    Write-Host "  错误信息:" -ForegroundColor Yellow
    Write-Host $currentVersion -ForegroundColor Red
    Set-Location $PROJECT_ROOT
    exit 1
}

Write-Host "  ✅ 数据库迁移成功" -ForegroundColor Green

Set-Location $PROJECT_ROOT

# ============================================
# 步骤4: 运行测试
# ============================================
Write-Host ""
Write-Host "[步骤4] 运行测试..." -ForegroundColor Cyan
Write-Host ""

# 运行测试
python -m pytest tests/test_stage1_week1_with_docker.py -v --no-cov --tb=short

$TEST_EXIT_CODE = $LASTEXITCODE

# ============================================
# 步骤5: 测试结果
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
if ($TEST_EXIT_CODE -eq 0) {
    Write-Host "✅ 所有测试通过！" -ForegroundColor Green
    Write-Host ""
    Write-Host "测试总结:" -ForegroundColor Cyan
    Write-Host "  ✅ 数据模型导入测试" -ForegroundColor White
    Write-Host "  ✅ 数据库迁移测试" -ForegroundColor White
    Write-Host "  ✅ 表结构验证测试" -ForegroundColor White
    Write-Host "  ✅ 索引验证测试" -ForegroundColor White
    Write-Host "  ✅ CRUD操作测试" -ForegroundColor White
    Write-Host "  ✅ 向量更新检查测试" -ForegroundColor White
    Write-Host ""
    Write-Host "✅ 可以进入第2周！" -ForegroundColor Green
} else {
    Write-Host "❌ 测试失败，请检查错误信息" -ForegroundColor Red
    Write-Host "❌ 不能进入第2周" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Green

exit $TEST_EXIT_CODE





