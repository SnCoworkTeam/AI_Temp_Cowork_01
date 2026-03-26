$ErrorActionPreference = "Continue"
Write-Host "启动 Web UI..." -ForegroundColor Cyan
cd "E:\enterprise-ai-platform\web-ui"
if (Test-Path "node_modules") {
    Write-Host "依赖已安装，启动开发服务器..." -ForegroundColor Green
    npm run dev
} else {
    Write-Host "依赖未安装，正在安装..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -eq 0) {
        Write-Host "依赖安装完成，启动开发服务器..." -ForegroundColor Green
        npm run dev
    } else {
        Write-Host "依赖安装失败，请检查错误信息" -ForegroundColor Red
        pause
    }
}
