@echo off
REM 上传服务的测试文件到服务器
REM 用法: upload-service-tests.bat <service-name>

if "%1"=="" (
    echo 用法: upload-service-tests.bat ^<service-name^>
    echo.
    echo 可用服务:
    echo   database
    echo   auth-service
    echo   mcp-gateway
    echo   workflow-engine
    echo   knowledge-base
    echo   metadata-service
    exit /b 1
)

set SERVICE=%1

cd /d "%~dp0"

echo ========================================
echo 上传服务: %SERVICE% 的测试文件
echo ========================================
echo.

REM 检查测试文件是否存在
if not exist "%SERVICE%\tests" (
    echo ✗ 错误: %SERVICE%\tests 目录不存在
    exit /b 1
)

REM 上传所有测试文件
echo 上传测试文件...
scp -F remote.ssh -o ConnectTimeout=10 %SERVICE%\tests\*.py enterprise-ai-server:/opt/enterprise-ai-platform/%SERVICE%/tests/

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ 测试文件上传成功！
) else (
    echo.
    echo ✗ 测试文件上传失败，错误码: %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

exit /b 0

