@echo off
REM 上传Docker镜像到测试服务器
REM 使用方法: upload-images.bat [service-name]

setlocal

set SERVICE_NAME=%1

echo ========================================
echo 上传Docker镜像到测试服务器
echo ========================================
echo.

if "%SERVICE_NAME%"=="" (
    echo 上传所有服务的镜像...
    powershell -ExecutionPolicy Bypass -File "scripts\deployment\upload-docker-images.ps1"
) else (
    echo 上传服务镜像: %SERVICE_NAME%
    powershell -ExecutionPolicy Bypass -File "scripts\deployment\upload-docker-images.ps1" -ServiceName "%SERVICE_NAME%"
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 上传完成！
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 上传失败！
    echo ========================================
    exit /b 1
)

endlocal

