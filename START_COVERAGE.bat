@echo off
chcp 65001 >nul
echo ==========================================
echo 启动测试覆盖率提升系统
echo ==========================================
echo.

REM 清理旧的PowerShell进程
echo [1/3] 清理旧的PowerShell进程...
taskkill /F /IM pwsh.exe 2>nul
taskkill /F /IM powershell.exe 2>nul
timeout /t 2 /nobreak >nul
echo 完成
echo.

REM 切换到项目目录
echo [2/3] 切换到项目目录...
cd /d "%~dp0"
echo 当前目录: %CD%
echo.

REM 启动脚本
echo [3/3] 启动覆盖率提升循环...
echo 注意: 脚本将持续运行直到所有服务达到80%覆盖率
echo.
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\test-coverage\coverage-improvement-loop.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ==========================================
    echo 脚本执行出错，错误代码: %ERRORLEVEL%
    echo ==========================================
    pause
)

