@echo off
REM 构建完成后执行此脚本，将镜像导出到此文件夹

echo ==========================================
echo 导出镜像到 FTP 上传文件夹
echo ==========================================
echo.

cd /d "%~dp0"
cd ..

echo [1] 验证镜像存在...
docker images enterprise-ai-opencode-local-web:latest
if errorlevel 1 (
    echo [ERROR] 镜像不存在，请先完成构建！
    pause
    exit /b 1
)
echo.

echo [2] 检查构建标记...
docker run --rm enterprise-ai-opencode-local-web:latest cat /app-web/build.txt
echo.

echo [3] 导出镜像（约 600MB，需要几分钟）...
cd ftp-upload-package
docker save -o enterprise-ai-opencode-local-web.tar enterprise-ai-opencode-local-web:latest
if errorlevel 1 (
    echo [ERROR] 导出失败！
    pause
    exit /b 1
)
echo.

echo [OK] 镜像已导出到：
cd
dir enterprise-ai-opencode-local-web.tar
echo.

echo ==========================================
echo 准备就绪！
echo ==========================================
echo.
echo FTP 上传文件夹：%cd%
echo.
echo 包含文件：
dir /b
echo.
echo 下一步：
echo 1. 将整个 ftp-upload-package 文件夹通过 FTP 上传到服务器
echo 2. 在服务器上执行：bash deploy-on-server.sh
echo.
pause
