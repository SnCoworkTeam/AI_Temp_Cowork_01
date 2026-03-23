@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==========================================
echo 启动测试覆盖率提升循环
echo ==========================================
echo.

REM 检查PowerShell是否可用
where pwsh >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo 使用 pwsh...
    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\test-coverage\coverage-improvement-loop.ps1"
) else (
    echo 使用 powershell...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\test-coverage\coverage-improvement-loop.ps1"
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 错误: 脚本执行失败，错误代码: %ERRORLEVEL%
    pause
)

