# 启动前端开发服务器

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "启动 Web UI 前端服务" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Node.js
Write-Host "[1/3] 检查Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js版本: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js未安装，请先安装Node.js" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 检查并安装依赖
Write-Host "[2/3] 检查依赖..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "安装依赖..." -ForegroundColor Gray
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 依赖安装失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ 依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "✅ 依赖已存在" -ForegroundColor Green
}
Write-Host ""

# 启动开发服务器
Write-Host "[3/3] 启动开发服务器..." -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "前端服务地址: http://localhost:3000" -ForegroundColor Green
Write-Host "工作流设计器: http://localhost:3000/workflow-designer" -ForegroundColor Green
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

npm run dev

