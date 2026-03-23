@echo off
REM 启动Cursor监控脚本
REM 检测Cursor是否卡住，如果卡住则自动发送继续执行指令

echo ==========================================
echo Cursor任务监控
echo ==========================================
echo.

cd /d "%~dp0"

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 运行监控脚本
python scripts\test-coverage\cursor-monitor.py

pause

