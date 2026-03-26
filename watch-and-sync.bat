@echo off
REM 启动文件监控和自动同步（热加载）
REM 使用方法: watch-and-sync.bat [service-name]

setlocal

set SERVICE_NAME=%1

echo ========================================
echo 文件监控和自动同步（热加载）
echo ========================================
echo.
echo 按 Ctrl+C 停止监控
echo.

if "%SERVICE_NAME%"=="" (
    echo 监控所有服务...
    powershell -ExecutionPolicy Bypass -File "scripts\deployment\watch-and-sync.ps1"
) else (
    echo 监控服务: %SERVICE_NAME%
    powershell -ExecutionPolicy Bypass -File "scripts\deployment\watch-and-sync.ps1" -ServiceName "%SERVICE_NAME%" -AutoRestart
)

endlocal

