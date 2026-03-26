@echo off
chcp 65001 >nul
echo ========================================
echo   代码上传和服务重启
echo ========================================
echo.

set SSH_KEY=enterprise_ai_platform.pem
set SERVER=ubuntu@43.143.139.197
set SERVER_PATH=/opt/enterprise-ai-platform

echo 开始上传文件...
echo.

echo [1/10] 上传 agent-service...
scp -i %SSH_KEY% -r -o StrictHostKeyChecking=no agent-service %SERVER%:%SERVER_PATH%/
if %errorlevel% equ 0 (echo   ✓ 成功) else (echo   ✗ 失败)

echo [2/10] 上传 api-gateway...
scp -i %SSH_KEY% -r -o StrictHostKeyChecking=no api-gateway %SERVER%:%SERVER_PATH%/
if %errorlevel% equ 0 (echo   ✓ 成功) else (echo   ✗ 失败)

echo [3/10] 上传 auth-service...
scp -i %SSH_KEY% -r -o StrictHostKeyChecking=no auth-service %SERVER%:%SERVER_PATH%/
if %errorlevel% equ 0 (echo   ✓ 成功) else (echo   ✗ 失败)

echo [4/10] 上传 dag-orchestrator...
scp -i %SSH_KEY% -r -o StrictHostKeyChecking=no dag-orchestrator %SERVER%:%SERVER_PATH%/
if %errorlevel% equ 0 (echo   ✓ 成功) else (echo   ✗ 失败)

echo [5/10] 上传 knowledge-base...
scp -i %SSH_KEY% -r -o StrictHostKeyChecking=no knowledge-base %SERVER%:%SERVER_PATH%/
if %errorlevel% equ 0 (echo   ✓ 成功) else (echo   ✗ 失败)

echo [6/10] 上传 mcp-gateway...
scp -i %SSH_KEY% -r -o StrictHostKeyChecking=no mcp-gateway %SERVER%:%SERVER_PATH%/
if %errorlevel% equ 0 (echo   ✓ 成功) else (echo   ✗ 失败)

echo [7/10] 上传 metadata-service...
scp -i %SSH_KEY% -r -o StrictHostKeyChecking=no metadata-service %SERVER%:%SERVER_PATH%/
if %errorlevel% equ 0 (echo   ✓ 成功) else (echo   ✗ 失败)

echo [8/10] 上传 registry-service...
scp -i %SSH_KEY% -r -o StrictHostKeyChecking=no registry-service %SERVER%:%SERVER_PATH%/
if %errorlevel% equ 0 (echo   ✓ 成功) else (echo   ✗ 失败)

echo [9/10] 上传 services...
scp -i %SSH_KEY% -r -o StrictHostKeyChecking=no services %SERVER%:%SERVER_PATH%/
if %errorlevel% equ 0 (echo   ✓ 成功) else (echo   ✗ 失败)

echo [10/10] 上传 shared_libs...
scp -i %SSH_KEY% -r -o StrictHostKeyChecking=no shared_libs %SERVER%:%SERVER_PATH%/
if %errorlevel% equ 0 (echo   ✓ 成功) else (echo   ✗ 失败)

echo.
echo 上传 web-ui...
scp -i %SSH_KEY% -r -o StrictHostKeyChecking=no web-ui\src %SERVER%:%SERVER_PATH%/web-ui/
scp -i %SSH_KEY% -o StrictHostKeyChecking=no web-ui\package.json %SERVER%:%SERVER_PATH%/web-ui/
scp -i %SSH_KEY% -o StrictHostKeyChecking=no web-ui\next.config.js %SERVER%:%SERVER_PATH%/web-ui/

echo.
echo ========================================
echo   重启服务...
echo ========================================
echo.

ssh -i %SSH_KEY% -o StrictHostKeyChecking=no %SERVER% "cd %SERVER_PATH% && docker compose restart agent-service api-gateway auth-service dag-orchestrator knowledge-base mcp-gateway metadata-service registry-service web-ui"

echo.
echo ========================================
echo   完成！
echo ========================================
echo.
pause


