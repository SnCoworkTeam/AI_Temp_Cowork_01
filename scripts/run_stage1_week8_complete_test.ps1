# 阶段一第8周完整测试脚本 - 多场景验证+性能监控

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  阶段一第8周完整测试流程" -ForegroundColor Green
Write-Host "  多场景验证+性能监控" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 获取脚本所在目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR

Set-Location $PROJECT_ROOT

# ============================================
# 步骤1: 确保基础服务运行
# ============================================
Write-Host "[步骤1] 检查基础服务..." -ForegroundColor Cyan

$postgresStatus = docker ps --filter "name=postgres" --format "{{.Status}}" 2>$null
if (-not ($postgresStatus -match "Up")) {
    Write-Host "  启动postgres服务..." -ForegroundColor Yellow
    docker-compose up -d postgres
    Start-Sleep -Seconds 10
} else {
    Write-Host "  [OK] postgres 服务已运行" -ForegroundColor Green
}

# ============================================
# 步骤2: 运行数据库迁移
# ============================================
Write-Host ""
Write-Host "[步骤2] 运行数据库迁移..." -ForegroundColor Cyan
cd database
python -m alembic upgrade head 2>&1 | Out-Null
cd ..
Write-Host "  [OK] 数据库迁移完成" -ForegroundColor Green

# ============================================
# 步骤3: 测试性能监控服务
# ============================================
Write-Host ""
Write-Host "[步骤3] 测试性能监控服务..." -ForegroundColor Cyan
python services/performance_monitor.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 性能监控服务测试失败" -ForegroundColor Red
    exit 1
}

# ============================================
# 步骤4: 运行场景测试
# ============================================
Write-Host ""
Write-Host "[步骤4] 运行场景测试..." -ForegroundColor Cyan
Write-Host ""

python -m pytest tests/test_stage1_week8_scenarios.py -v --no-cov --tb=short -s

$TEST_EXIT_CODE = $LASTEXITCODE

# ============================================
# 步骤5: 测试结果
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
if ($TEST_EXIT_CODE -eq 0) {
    Write-Host "[OK] 所有测试通过！" -ForegroundColor Green
    Write-Host ""
    Write-Host "测试总结:" -ForegroundColor Cyan
    Write-Host "  [OK] 性能监控服务测试" -ForegroundColor White
    Write-Host "  [OK] 标准订单场景测试" -ForegroundColor White
    Write-Host "  [OK] 查询订单场景测试" -ForegroundColor White
    Write-Host "  [OK] 复杂流程场景测试" -ForegroundColor White
    Write-Host "  [OK] 性能指标测试" -ForegroundColor White
    Write-Host "  [OK] 端到端性能测试" -ForegroundColor White
    Write-Host ""
    Write-Host "[OK] 可以进入第9周！" -ForegroundColor Green
} else {
    Write-Host "[ERROR] 测试失败，请检查错误信息" -ForegroundColor Red
    Write-Host "[ERROR] 不能进入第9周" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Green

exit $TEST_EXIT_CODE





