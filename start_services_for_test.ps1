# PowerShell脚本：启动测试所需的服务

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "启动统一意图识别MVP测试所需服务" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 检查Docker是否运行
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker未运行，请先启动Docker" -ForegroundColor Red
    exit 1
}

# 启动基础服务（数据库、Redis）
Write-Host ""
Write-Host "1. 启动基础服务（PostgreSQL、Redis）..." -ForegroundColor Yellow
docker-compose up -d postgres redis

# 等待数据库就绪
Write-Host ""
Write-Host "2. 等待数据库就绪..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 启动agent-service
Write-Host ""
Write-Host "3. 启动agent-service..." -ForegroundColor Yellow
docker-compose up -d agent-service

# 等待服务启动
Write-Host ""
Write-Host "4. 等待agent-service启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查服务状态
Write-Host ""
Write-Host "5. 检查服务状态..." -ForegroundColor Yellow
docker-compose ps agent-service

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "服务启动完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "agent-service地址: http://localhost:8010" -ForegroundColor Cyan
Write-Host "API文档: http://localhost:8010/docs" -ForegroundColor Cyan
Write-Host "统一意图MVP端点: http://localhost:8010/api/v1/unified/process" -ForegroundColor Cyan
Write-Host ""
Write-Host "查看日志: docker-compose logs -f agent-service" -ForegroundColor Yellow
Write-Host "停止服务: docker-compose stop agent-service" -ForegroundColor Yellow
Write-Host ""




