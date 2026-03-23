# 阶段一第2周完整测试脚本 - 采购场景图谱构建

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  阶段一第2周完整测试流程" -ForegroundColor Green
Write-Host "  采购场景图谱构建" -ForegroundColor Green
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
    Write-Host "  ✅ postgres 服务已运行" -ForegroundColor Green
}

# ============================================
# 步骤2: 数据采集
# ============================================
Write-Host ""
Write-Host "[步骤2] 数据采集..." -ForegroundColor Cyan
python scripts/collect_procurement_data.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 数据采集失败" -ForegroundColor Red
    exit 1
}

# ============================================
# 步骤3: 向量化
# ============================================
Write-Host ""
Write-Host "[步骤3] 向量化业务活动..." -ForegroundColor Cyan
python scripts/vectorize_procurement_activities.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 向量化失败" -ForegroundColor Red
    exit 1
}

# ============================================
# 步骤4: 图谱构建
# ============================================
Write-Host ""
Write-Host "[步骤4] 构建知识图谱..." -ForegroundColor Cyan
python scripts/build_procurement_graph.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 图谱构建失败" -ForegroundColor Red
    exit 1
}

# ============================================
# 步骤5: 运行测试
# ============================================
Write-Host ""
Write-Host "[步骤5] 运行测试..." -ForegroundColor Cyan
Write-Host ""

python -m pytest tests/test_stage1_week2.py -v --no-cov --tb=short -s

$TEST_EXIT_CODE = $LASTEXITCODE

# ============================================
# 步骤6: 测试结果
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
if ($TEST_EXIT_CODE -eq 0) {
    Write-Host "✅ 所有测试通过！" -ForegroundColor Green
    Write-Host ""
    Write-Host "测试总结:" -ForegroundColor Cyan
    Write-Host "  ✅ 数据完整性测试" -ForegroundColor White
    Write-Host "  ✅ 向量质量测试" -ForegroundColor White
    Write-Host "  ✅ 映射准确性测试" -ForegroundColor White
    Write-Host "  ✅ 图谱结构测试" -ForegroundColor White
    Write-Host ""
    Write-Host "✅ 可以进入第3周！" -ForegroundColor Green
} else {
    Write-Host "❌ 测试失败，请检查错误信息" -ForegroundColor Red
    Write-Host "❌ 不能进入第3周" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Green

exit $TEST_EXIT_CODE





