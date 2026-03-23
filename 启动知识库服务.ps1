# 启动本地docker知识库服务
# 用于测试文档上传处理

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "启动知识库Docker服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查docker是否运行
Write-Host "1. 检查Docker状态..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "   ✓ Docker已安装: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Docker未安装或未运行" -ForegroundColor Red
    exit 1
}

# 检查docker-compose
Write-Host "`n2. 检查docker-compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker compose version
    Write-Host "   ✓ docker-compose可用" -ForegroundColor Green
} catch {
    Write-Host "   ✗ docker-compose不可用" -ForegroundColor Red
    exit 1
}

# 检查依赖服务（postgres和redis）
Write-Host "`n3. 检查依赖服务（PostgreSQL和Redis）..." -ForegroundColor Yellow

$postgresRunning = docker compose ps postgres --format "{{.State}}" 2>$null
if ($postgresRunning -eq "running") {
    Write-Host "   ✓ PostgreSQL正在运行" -ForegroundColor Green
} else {
    Write-Host "   ⚠ PostgreSQL未运行，正在启动..." -ForegroundColor Yellow
    docker compose up -d postgres
    Write-Host "   等待PostgreSQL就绪..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

$redisRunning = docker compose ps redis --format "{{.State}}" 2>$null
if ($redisRunning -eq "running") {
    Write-Host "   ✓ Redis正在运行" -ForegroundColor Green
} else {
    Write-Host "   ⚠ Redis未运行，正在启动..." -ForegroundColor Yellow
    docker compose up -d redis
    Write-Host "   等待Redis就绪..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# 启动知识库服务
Write-Host "`n4. 启动知识库服务..." -ForegroundColor Yellow
Write-Host "   正在构建并启动..." -ForegroundColor Gray

docker compose up -d --build knowledge-base

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ✗ 启动失败" -ForegroundColor Red
    exit 1
}

Write-Host "   ✓ 知识库服务已启动" -ForegroundColor Green

# 等待服务就绪
Write-Host "`n5. 等待服务就绪（最多60秒）..." -ForegroundColor Yellow
$maxWait = 60
$waited = 0
$checkInterval = 3
$isReady = $false

while ($waited -lt $maxWait) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8004/api/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "   ✓ 服务已就绪！" -ForegroundColor Green
            $isReady = $true
            break
        }
    } catch {
        # 服务还未就绪，继续等待
    }
    
    Write-Host "   等待中... ($waited/$maxWait秒)" -ForegroundColor Gray
    Start-Sleep -Seconds $checkInterval
    $waited += $checkInterval
}

if (-not $isReady) {
    Write-Host "   ⚠ 服务启动超时，但容器可能仍在启动中" -ForegroundColor Yellow
    Write-Host "   请检查日志: docker logs enterprise-ai-knowledge-base --tail 50" -ForegroundColor Yellow
}

# 显示服务状态
Write-Host "`n6. 服务状态:" -ForegroundColor Yellow
docker compose ps knowledge-base

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "启动完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "服务地址: http://localhost:8004" -ForegroundColor Green
Write-Host "查看日志: docker logs -f enterprise-ai-knowledge-base" -ForegroundColor Green
Write-Host ""
