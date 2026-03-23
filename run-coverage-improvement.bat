@echo off
REM 运行测试覆盖率提升主程序
REM 使用命令直接执行，不使用PowerShell脚本

cd /d "%~dp0"

echo ========================================
echo 测试覆盖率80%%目标提升程序
echo ========================================
echo.

REM 运行Python脚本
REM 尝试使用py命令（Windows Python Launcher）
py scripts\test-coverage\coverage-improvement-main.py %*
if %ERRORLEVEL% NEQ 0 (
    REM 如果py失败，尝试python3
    python3 scripts\test-coverage\coverage-improvement-main.py %*
    if %ERRORLEVEL% NEQ 0 (
        REM 如果python3失败，尝试python
        python scripts\test-coverage\coverage-improvement-main.py %*
    )
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 所有服务已达到目标覆盖率！
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 部分服务未达到目标覆盖率，请查看结果
    echo ========================================
)

pause

