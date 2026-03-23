# 测试版本 - 简化循环
Write-Host "测试覆盖率提升循环启动" -ForegroundColor Cyan
Write-Host "目标: 所有服务达到80%覆盖率" -ForegroundColor Cyan
Write-Host ""

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)

Write-Host "项目根目录: $ProjectRoot" -ForegroundColor Yellow
Write-Host "脚本目录: $ScriptRoot" -ForegroundColor Yellow
Write-Host ""

# 测试基本功能
Write-Host "[测试] 检查进度文件..." -ForegroundColor Green
$progressFile = Join-Path $ProjectRoot ".coverage-progress.json"
if (Test-Path $progressFile) {
    Write-Host "  进度文件存在" -ForegroundColor Gray
} else {
    Write-Host "  进度文件不存在，将创建" -ForegroundColor Yellow
}

Write-Host "[测试] 检查SSH配置..." -ForegroundColor Green
$configFile = Join-Path $ProjectRoot "remote.ssh"
if (Test-Path $configFile) {
    Write-Host "  SSH配置文件存在" -ForegroundColor Gray
} else {
    Write-Host "  SSH配置文件不存在" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "测试完成！脚本可以正常运行。" -ForegroundColor Green
Write-Host "现在可以启动完整版本了。" -ForegroundColor Cyan

