# Docker 清理和重启脚本
# 清理 Docker 镜像和缓存，然后重新启动服务

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker 清理和重启服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker 是否运行
Write-Host "[1/5] 检查 Docker 状态..." -ForegroundColor Yellow
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Docker 正在运行" -ForegroundColor Green
} else {
    Write-Host "Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
    exit 1
}

# 停止所有运行中的容器
Write-Host ""
Write-Host "[2/5] 停止所有运行中的容器..." -ForegroundColor Yellow
$containers = docker ps -q
if ($containers) {
    docker stop $containers
    Write-Host "已停止所有容器" -ForegroundColor Green
} else {
    Write-Host "没有运行中的容器" -ForegroundColor Gray
}

# 清理 Docker 系统（镜像、容器、缓存等）
Write-Host ""
Write-Host "[3/5] 清理 Docker 镜像和缓存..." -ForegroundColor Yellow
Write-Host "正在清理未使用的容器、网络、镜像和构建缓存..." -ForegroundColor Gray

# 清理未使用的资源（不包括卷，以保留数据）
docker system prune -a -f --volumes=false

Write-Host "Docker 清理完成" -ForegroundColor Green

# 显示清理后的磁盘空间
Write-Host ""
Write-Host "清理后的 Docker 磁盘使用情况:" -ForegroundColor Cyan
docker system df

# 重新构建并启动服务
Write-Host ""
Write-Host "[4/5] 重新构建并启动服务..." -ForegroundColor Yellow

# 先启动基础服务（数据库和 Redis）
Write-Host "启动基础服务（PostgreSQL 和 Redis）..." -ForegroundColor Gray
docker compose up -d postgres redis

# 等待基础服务就绪
Write-Host "等待基础服务就绪..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# 启动其他服务
Write-Host "启动其他服务..." -ForegroundColor Gray
docker compose up -d --build

Write-Host "服务启动完成" -ForegroundColor Green

# 等待服务启动
Write-Host ""
Write-Host "[5/5] 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 显示服务状态
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "服务状态" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
docker compose ps

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "服务统计" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$services = @("postgres", "redis", "registry-service", "api-gateway", "config-center", "mcp-gateway", "workflow-engine", "web-ui", "auth-service", "knowledge-base", "metadata-service", "chat-service", "joyagent-adapter")

$running = 0
$stopped = 0

foreach ($svc in $services) {
    $statusOutput = docker compose ps $svc 2>&1 | Select-String "Up"
    if ($statusOutput) {
        Write-Host "$svc - 运行中" -ForegroundColor Green
        $running++
    } else {
        Write-Host "$svc - 未运行" -ForegroundColor Red
        $stopped++
        Write-Host "  查看日志: docker compose logs --tail=10 $svc" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "运行中: $running / $($services.Count)" -ForegroundColor Cyan
if ($stopped -eq 0) {
    Write-Host "未运行: $stopped / $($services.Count)" -ForegroundColor Green
} else {
    Write-Host "未运行: $stopped / $($services.Count)" -ForegroundColor Yellow
}

if ($stopped -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "所有服务已成功启动！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "部分服务未启动，请检查日志" -ForegroundColor Yellow
    Write-Host "使用以下命令查看日志:" -ForegroundColor Gray
    Write-Host "  docker compose logs [服务名]" -ForegroundColor Gray
}

Write-Host ""
Write-Host "提示: Docker 数据目录迁移到 E 盘需要在 Docker Desktop 设置中完成" -ForegroundColor Cyan
Write-Host "  Settings > Resources > Advanced > Disk image location" -ForegroundColor Gray
