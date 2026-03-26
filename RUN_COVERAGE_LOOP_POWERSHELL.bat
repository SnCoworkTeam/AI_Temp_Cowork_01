@echo off
REM 在原生PowerShell中运行覆盖率提升循环
REM 避免Cursor终端环境问题

cd /d "%~dp0"

echo ==========================================
echo 启动测试覆盖率提升循环
echo ==========================================
echo.

pwsh -ExecutionPolicy Bypass -File "%~dp0scripts\test-coverage\coverage-improvement-loop.ps1"

pause

