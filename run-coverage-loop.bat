@echo off
cd /d "%~dp0"
echo 启动测试覆盖率提升循环...
echo.
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "scripts\test-coverage\coverage-improvement-loop.ps1"
pause

