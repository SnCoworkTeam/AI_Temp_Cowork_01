# mypy 环境设置脚本
# 注意：目录已重命名为 project_management，不再需要符号链接

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "mypy 环境设置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查目录是否存在
if (-not (Test-Path "project_management")) {
    Write-Host "❌ 错误: project_management 目录不存在" -ForegroundColor Red
    Write-Host "请确保目录已重命名为 project_management" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ 目录检查通过: project_management" -ForegroundColor Green

Write-Host ""
Write-Host "设置 PYTHONPATH..." -ForegroundColor Yellow
$env:PYTHONPATH = "project_management\src"
Write-Host "✅ PYTHONPATH = $env:PYTHONPATH" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ 环境设置完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "现在可以运行 mypy:" -ForegroundColor Cyan
Write-Host "  mypy --config-file mypy.ini project_management\src\routes\project_plans.py" -ForegroundColor White
Write-Host ""
Write-Host "或者检查整个目录:" -ForegroundColor Cyan
Write-Host "  mypy --config-file mypy.ini project_management\src\routes\" -ForegroundColor White
Write-Host ""
Write-Host "生成 HTML 报告:" -ForegroundColor Cyan
Write-Host "  mypy --config-file mypy.ini project_management\src\routes\ --html-report mypy-report" -ForegroundColor White
Write-Host ""
