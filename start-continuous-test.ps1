# 启动持续测试系统

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "启动持续测试系统" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "系统将持续运行直到所有21个服务测试通过" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 可以手动停止" -ForegroundColor Gray
Write-Host ""

# 检查GitHub CLI
$ghCheck = gh --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ GitHub CLI未安装或未配置" -ForegroundColor Red
    exit 1
}

# 运行持续测试脚本
python scripts\cicd\continuous-test-until-pass.py





