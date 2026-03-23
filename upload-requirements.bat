@echo off
REM 上传 knowledge-base/requirements.txt 到服务器

echo ========================================
echo 上传 requirements.txt 到服务器
echo ========================================
echo.

REM 查找密钥文件
set KEY_FILE=
if exist "enterprise_ai_platform.pem" (
    set KEY_FILE=enterprise_ai_platform.pem
) else if exist "%USERPROFILE%\.ssh\enterprise_ai_platform.pem" (
    set KEY_FILE=%USERPROFILE%\.ssh\enterprise_ai_platform.pem
) else (
    echo 错误: 未找到密钥文件 enterprise_ai_platform.pem
    pause
    exit /b 1
)

echo 使用密钥文件: %KEY_FILE%
echo 服务器: ubuntu@43.143.139.197
echo 远程路径: /opt/enterprise-ai-platform/knowledge-base/requirements.txt
echo.

REM 上传文件
scp -i "%KEY_FILE%" -o StrictHostKeyChecking=no knowledge-base\requirements.txt ubuntu@43.143.139.197:/opt/enterprise-ai-platform/knowledge-base/requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 上传成功!
    echo ========================================
    echo.
    echo 下一步操作:
    echo   1. SSH 到服务器: ssh -i "%KEY_FILE%" ubuntu@43.143.139.197
    echo   2. 进入目录: cd /opt/enterprise-ai-platform
    echo   3. 重新构建: sudo docker compose up -d --build knowledge-base
    echo.
) else (
    echo.
    echo ========================================
    echo 上传失败!
    echo ========================================
    echo.
)

pause

