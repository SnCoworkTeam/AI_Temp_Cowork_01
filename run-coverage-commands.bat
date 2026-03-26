@echo off
REM 测试覆盖率80%%目标 - 直接命令执行
REM 不使用脚本，直接用命令执行

cd /d "%~dp0"

REM 创建覆盖率报告目录
if not exist ".coverage-reports" mkdir .coverage-reports

echo ========================================
echo 测试覆盖率80%%目标提升 - 直接命令执行
echo ========================================
echo.

REM 服务列表
set SERVICES=database auth-service mcp-gateway workflow-engine knowledge-base metadata-service

REM 对每个服务执行
for %%s in (%SERVICES%) do (
    echo.
    echo ========================================
    echo 处理服务: %%s
    echo ========================================
    echo.
    
    REM 步骤1: 运行测试
    echo [步骤1] 运行测试...
    ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "sudo docker exec enterprise-ai-%%s python3 -m pytest /app/tests --cov=/app/src --cov-report=json:/tmp/coverage.json --cov-report=term-missing 2>&1"
    
    if %%s==database (
        ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "sudo docker exec enterprise-ai-postgres python3 -m pytest /database/tests --cov=/database/src --cov-report=json:/tmp/coverage.json --cov-report=term-missing 2>&1"
    )
    
    REM 检查命令是否成功
    if %ERRORLEVEL% NEQ 0 (
        echo 警告: 测试命令执行失败，错误码: %ERRORLEVEL%
        echo 继续处理下一个服务...
        continue
    )
    
    REM 步骤2: 下载覆盖率报告
    echo.
    echo [步骤2] 下载覆盖率报告...
    scp -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server:/tmp/coverage.json .coverage-reports\%%s-coverage.json
    
    if %ERRORLEVEL% NEQ 0 (
        echo 警告: 下载覆盖率报告失败，错误码: %ERRORLEVEL%
        echo 继续处理下一个服务...
        continue
    )
    
    REM 步骤3: 检查覆盖率
    echo.
    echo [步骤3] 检查覆盖率...
    py -c "import json; data=json.load(open('.coverage-reports\\%%s-coverage.json')); print(f\"当前覆盖率: {data['totals']['percent_covered']:.2f}%%\"); exit(0 if data['totals']['percent_covered'] >= 80.0 else 1)" 2>nul
    
    if %ERRORLEVEL% EQU 0 (
        echo ✓ %%s 已达到80%%覆盖率！
    ) else (
        echo ✗ %%s 未达到80%%覆盖率，需要添加测试
        echo.
        echo 提示: 运行以下命令生成测试文件:
        echo   py scripts\test-coverage\improve-coverage.py --service %%s
        echo.
        echo 然后上传测试文件:
        echo   scp -F remote.ssh -o ConnectTimeout=10 %%s\tests\*.py enterprise-ai-server:/opt/enterprise-ai-platform/%%s/tests/
    )
    
    echo.
    echo 按任意键继续下一个服务...
    pause >nul
)

echo.
echo ========================================
echo 所有服务处理完成
echo ========================================
echo.
echo 覆盖率报告保存在: .coverage-reports\
echo.

pause

