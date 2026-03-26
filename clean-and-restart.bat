@echo off
chcp 65001 >nul
echo ========================================
echo Docker 清理和重启服务
echo ========================================
echo.

echo [1/5] 检查 Docker 状态...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)
echo Docker 正在运行
echo.

echo [2/5] 停止所有运行中的容器...
for /f %%i in ('docker ps -q') do (
    docker stop %%i
)
echo 已停止所有容器
echo.

echo [3/5] 清理 Docker 镜像和缓存...
echo 正在清理未使用的容器、网络、镜像和构建缓存...
docker system prune -a -f --volumes=false
echo Docker 清理完成
echo.

echo 清理后的 Docker 磁盘使用情况:
docker system df
echo.

echo [4/5] 重新构建并启动服务...
echo 启动基础服务（PostgreSQL 和 Redis）...
docker compose up -d postgres redis
timeout /t 10 /nobreak >nul

echo 启动其他服务...
docker compose up -d --build
echo 服务启动完成
echo.

echo [5/5] 等待服务启动...
timeout /t 15 /nobreak >nul

echo.
echo ========================================
echo 服务状态
echo ========================================
docker compose ps

echo.
echo ========================================
echo 提示: Docker 数据目录迁移到 E 盘需要在 Docker Desktop 设置中完成
echo   Settings ^> Resources ^> Advanced ^> Disk image location
echo ========================================
echo.
pause

