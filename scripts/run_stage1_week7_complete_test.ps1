# 阶段一第7周完整测试脚本 - 创建前端界面+用户体验增强

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  阶段一第7周完整测试流程" -ForegroundColor Green
Write-Host "  创建前端界面+用户体验增强" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 获取脚本所在目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR

Set-Location $PROJECT_ROOT

# ============================================
# 步骤1: 运行测试
# ============================================
Write-Host "[步骤1] 运行测试..." -ForegroundColor Cyan
Write-Host ""

python -m pytest tests/test_stage1_week7.py -v --no-cov --tb=short -s

$TEST_EXIT_CODE = $LASTEXITCODE

# ============================================
# 步骤2: 测试结果
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
if ($TEST_EXIT_CODE -eq 0) {
    Write-Host "[OK] 所有测试通过！" -ForegroundColor Green
    Write-Host ""
    Write-Host "测试总结:" -ForegroundColor Cyan
    Write-Host "  [OK] 前端组件文件测试" -ForegroundColor White
    Write-Host "  [OK] 组件结构测试" -ForegroundColor White
    Write-Host "  [OK] 用户体验功能测试" -ForegroundColor White
    Write-Host "  [OK] API集成测试" -ForegroundColor White
    Write-Host ""
    Write-Host "[OK] 可以进入第8周！" -ForegroundColor Green
} else {
    Write-Host "[ERROR] 测试失败，请检查错误信息" -ForegroundColor Red
    Write-Host "[ERROR] 不能进入第8周" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Green

exit $TEST_EXIT_CODE





