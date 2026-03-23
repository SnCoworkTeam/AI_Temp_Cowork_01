@echo off
REM 一键部署到测试服务器的便捷脚本
REM 使用方法: deploy-to-test.bat [service-name]

setlocal

set SERVICE_NAME=%1

echo ========================================
echo 部署到测试服务器
echo ========================================
echo.

if "%SERVICE_NAME%"=="" (
    echo 部署所有服务...
    powershell -ExecutionPolicy Bypass -File "scripts\deployment\deploy-test-server.ps1"
) else (
    echo 部署服务: %SERVICE_NAME%
    powershell -ExecutionPolicy Bypass -File "scripts\deployment\deploy-test-server.ps1" -ServiceName "%SERVICE_NAME%"
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 部署完成！
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 部署失败！
    echo ========================================
    exit /b 1
)

endlocal

