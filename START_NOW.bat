@echo off
echo ==========================================
echo 启动测试覆盖率提升系统
echo ==========================================
echo.
echo 如果脚本卡住，按 Ctrl+C 中断
echo.
cd /d "%~dp0"
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\test-coverage\coverage-improvement-loop.ps1"
pause

