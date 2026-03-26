# 阶段一第6周完整测试脚本 - 创建协同界面API

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  阶段一第6周完整测试流程" -ForegroundColor Green
Write-Host "  创建协同界面API" -ForegroundColor Green
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
# 步骤2: 运行测试
# ============================================
Write-Host ""
Write-Host "[步骤2] 运行测试..." -ForegroundColor Cyan
Write-Host ""

python -m pytest tests/test_stage1_week6.py -v --no-cov --tb=short -s

$TEST_EXIT_CODE = $LASTEXITCODE

# ============================================
# 步骤3: 测试结果
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
if ($TEST_EXIT_CODE -eq 0) {
    Write-Host "[OK] 所有测试通过！" -ForegroundColor Green
    Write-Host ""
    Write-Host "测试总结:" -ForegroundColor Cyan
    Write-Host "  [OK] 协同界面API功能测试" -ForegroundColor White
    Write-Host "  [OK] 意图理解工作流测试" -ForegroundColor White
    Write-Host "  [OK] 组装执行计划测试" -ForegroundColor White
    Write-Host "  [OK] 参数验证测试" -ForegroundColor White
    Write-Host "  [OK] 端到端工作流测试" -ForegroundColor White
    Write-Host ""
    Write-Host "[OK] 可以进入第7周！" -ForegroundColor Green
} else {
    Write-Host "[ERROR] 测试失败，请检查错误信息" -ForegroundColor Red
    Write-Host "[ERROR] 不能进入第7周" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Green

exit $TEST_EXIT_CODE





