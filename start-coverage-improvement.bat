@echo off
REM 启动测试覆盖率提升系统

echo ==========================================
echo 测试覆盖率80%自动化提升系统
echo ==========================================
echo.

cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File "start-coverage-improvement.ps1" -InstallMonitor -StartMonitor -StartLoop

pause

