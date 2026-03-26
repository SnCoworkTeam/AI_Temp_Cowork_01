# PowerShell脚本 - 扫描所有依赖的安全漏洞

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ReportsDir = Join-Path $ProjectRoot "dependencies\security-scan\reports"

Write-Host "=========================================="
Write-Host "依赖安全扫描"
Write-Host "=========================================="

# 创建报告目录
New-Item -ItemType Directory -Force -Path $ReportsDir | Out-Null

# 扫描Python依赖
Write-Host ""
Write-Host "扫描Python依赖..."
if (Get-Command pip-audit -ErrorAction SilentlyContinue) {
    pip-audit --format json --output "$ReportsDir\python-audit.json"
    pip-audit --format table
} else {
    Write-Host "⚠️  pip-audit未安装，跳过Python扫描"
}

# 扫描Node.js依赖
Write-Host ""
Write-Host "扫描Node.js依赖..."
$PackageJson = Join-Path $ProjectRoot "web-ui\package.json"
if (Test-Path $PackageJson) {
    Push-Location (Join-Path $ProjectRoot "web-ui")
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        npm audit --json | Out-File "$ReportsDir\npm-audit.json" -Encoding UTF8
        npm audit
    }
    Pop-Location
} else {
    Write-Host "⚠️  未找到package.json"
}

Write-Host ""
Write-Host "=========================================="
Write-Host "扫描完成"
Write-Host "报告保存在: $ReportsDir"
Write-Host "=========================================="









