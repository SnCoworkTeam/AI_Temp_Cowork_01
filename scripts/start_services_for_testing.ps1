# PowerShell脚本：启动测试所需的服务

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "启动测试所需的服务" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 检查docker是否运行
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker未运行，请先启动Docker" -ForegroundColor Red
    exit 1
}

# 启动核心服务
Write-Host ""
Write-Host "1. 启动PostgreSQL数据库..." -ForegroundColor Yellow
docker-compose up -d postgres

Write-Host ""
Write-Host "2. 启动Redis（用于缓存）..." -ForegroundColor Yellow
docker-compose up -d redis

Write-Host ""
Write-Host "3. 启动Qdrant向量数据库..." -ForegroundColor Yellow
docker-compose up -d qdrant

Write-Host ""
Write-Host "4. 启动Neo4j图数据库..." -ForegroundColor Yellow
docker-compose up -d neo4j

Write-Host ""
Write-Host "等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查服务状态
Write-Host ""
Write-Host "检查服务状态:" -ForegroundColor Cyan
docker-compose ps postgres redis qdrant neo4j

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "服务启动完成" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "可以运行测试:" -ForegroundColor Yellow
Write-Host "  pytest tests/milestone_integration_test.py -v" -ForegroundColor White

