# 阶段一第5周完整测试脚本 - 统一意图服务完善和API集成

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  阶段一第5周完整测试流程" -ForegroundColor Green
Write-Host "  统一意图服务完善和API集成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 获取脚本所在目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR

Set-Location $PROJECT_ROOT

# ============================================
# 步骤1: 确保Docker服务运行
# ============================================
Write-Host "[步骤1] 检查Docker服务..." -ForegroundColor Cyan

$postgresStatus = docker ps --filter "name=postgres" --format "{{.Status}}" 2>$null
if (-not ($postgresStatus -match "Up")) {
    Write-Host "  启动postgres服务..." -ForegroundColor Yellow
    docker-compose up -d postgres
    Start-Sleep -Seconds 5
} else {
    Write-Host "  [OK] postgres 服务已运行" -ForegroundColor Green
}

# ============================================
# 步骤2: 测试统一意图服务
# ============================================
Write-Host ""
Write-Host "[步骤2] 测试统一意图服务..." -ForegroundColor Cyan
python services/unified_intent_service.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 统一意图服务测试失败" -ForegroundColor Red
    exit 1
}

# ============================================
# 步骤3: 运行测试
# ============================================
Write-Host ""
Write-Host "[步骤3] 运行测试..." -ForegroundColor Cyan
Write-Host ""

python -m pytest tests/test_stage1_week5.py -v --no-cov --tb=short -s

$TEST_EXIT_CODE = $LASTEXITCODE

# ============================================
# 步骤4: 测试结果
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
if ($TEST_EXIT_CODE -eq 0) {
    Write-Host "[OK] 所有测试通过！" -ForegroundColor Green
    Write-Host ""
    Write-Host "测试总结:" -ForegroundColor Cyan
    Write-Host "  [OK] 统一意图服务增强测试" -ForegroundColor White
    Write-Host "  [OK] 能力映射功能测试" -ForegroundColor White
    Write-Host "  [OK] 执行建议功能测试" -ForegroundColor White
    Write-Host "  [OK] API接口测试（可选）" -ForegroundColor White
    Write-Host ""
    Write-Host "[OK] 可以进入第6周！" -ForegroundColor Green
} else {
    Write-Host "[ERROR] 测试失败，请检查错误信息" -ForegroundColor Red
    Write-Host "[ERROR] 不能进入第6周" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Green

exit $TEST_EXIT_CODE




