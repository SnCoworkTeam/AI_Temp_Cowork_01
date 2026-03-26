# 启动 web-ui 服务的 PowerShell 脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "启动 Web UI 服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker 是否运行
Write-Host "检查 Docker 状态..." -ForegroundColor Yellow
try {
    docker ps > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Docker 正在运行" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "启动 web-ui 服务..." -ForegroundColor Yellow

# 启动 web-ui 服务
docker-compose up -d web-ui

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Web UI 服务启动成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "服务信息:" -ForegroundColor Cyan
    Write-Host "  - 访问地址: http://localhost:3000" -ForegroundColor White
    Write-Host "  - 容器名称: enterprise-ai-web-ui" -ForegroundColor White
    Write-Host ""
    Write-Host "查看日志: docker-compose logs -f web-ui" -ForegroundColor Yellow
    Write-Host "停止服务: docker-compose stop web-ui" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ Web UI 服务启动失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "  1. 网络连接问题，无法拉取 Docker 镜像" -ForegroundColor White
    Write-Host "  2. 需要配置 Docker 镜像加速器" -ForegroundColor White
    Write-Host "  3. Docker Desktop 需要重启以应用镜像加速器配置" -ForegroundColor White
    Write-Host ""
    Write-Host "解决方案:" -ForegroundColor Yellow
    Write-Host "  1. 打开 Docker Desktop" -ForegroundColor White
    Write-Host "  2. 进入 Settings > Docker Engine" -ForegroundColor White
    Write-Host "  3. 添加镜像加速器配置（如果还没有）" -ForegroundColor White
    Write-Host "  4. 点击 Apply & Restart" -ForegroundColor White
    Write-Host "  5. 等待 Docker Desktop 重启完成后，再次运行此脚本" -ForegroundColor White
    exit 1
}


