@echo off
REM 启动测试覆盖率监控
REM 每5分钟检查一次，如果停止则自动继续执行

echo ==========================================
echo 启动测试覆盖率监控系统
echo ==========================================
echo.

cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File "scripts\test-coverage\run-continuous-improvement.ps1"

pause

