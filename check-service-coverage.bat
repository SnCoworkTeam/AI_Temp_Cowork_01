@echo off
REM 检查单个服务的测试覆盖率
REM 用法: check-service-coverage.bat <service-name>

if "%1"=="" (
    echo 用法: check-service-coverage.bat ^<service-name^>
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

REM 创建覆盖率报告目录
if not exist ".coverage-reports" mkdir .coverage-reports

echo ========================================
echo 检查服务: %SERVICE% 的测试覆盖率
echo ========================================
echo.

REM 确定容器名称和路径
if "%SERVICE%"=="database" (
    set CONTAINER=enterprise-ai-postgres
    set TEST_PATH=/database/tests
    set COV_PATH=/database/src
) else (
    set CONTAINER=enterprise-ai-%SERVICE%
    set TEST_PATH=/app/tests
    set COV_PATH=/app/src
)

REM 步骤1: 运行测试
echo [步骤1] 运行测试...
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "sudo docker exec %CONTAINER% python3 -m pytest %TEST_PATH% --cov=%COV_PATH% --cov-report=json:/tmp/coverage.json --cov-report=term-missing 2>&1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ✗ 测试执行失败，错误码: %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

REM 步骤2: 下载覆盖率报告
echo.
echo [步骤2] 下载覆盖率报告...
scp -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server:/tmp/coverage.json .coverage-reports\%SERVICE%-coverage.json

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ✗ 下载覆盖率报告失败，错误码: %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

REM 步骤3: 显示覆盖率
echo.
echo [步骤3] 覆盖率结果:
py -c "import json; data=json.load(open('.coverage-reports\\%SERVICE%-coverage.json')); cov=data['totals']['percent_covered']; print(f\"当前覆盖率: {cov:.2f}%%\"); print(f\"目标覆盖率: 80.00%%\"); print(f\"状态: {'✓ 达标' if cov >= 80.0 else '✗ 未达标'}\"); exit(0 if cov >= 80.0 else 1)"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ %SERVICE% 已达到80%%覆盖率！
) else (
    echo.
    echo ✗ %SERVICE% 未达到80%%覆盖率
    echo.
    echo 建议运行以下命令生成测试文件:
    echo   py scripts\test-coverage\improve-coverage.py --service %SERVICE%
)

exit /b %ERRORLEVEL%

