@echo off
echo ========================================
echo Docker 简单诊断
echo ========================================
echo.

echo [1] 检查Docker是否运行...
docker --version
if %errorlevel% neq 0 (
    echo Docker未安装或未在PATH中
    pause
    exit /b 1
)

echo.
echo [2] 测试Docker连接...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker API无法连接，请检查Docker Desktop是否运行
    pause
    exit /b 1
)

echo.
echo [3] 尝试拉取基础镜像（测试网络）...
docker pull python:3.11-slim

echo.
echo [4] 检查镜像是否拉取成功...
docker images python:3.11-slim

echo.
echo ========================================
echo 诊断完成
echo ========================================
pause






