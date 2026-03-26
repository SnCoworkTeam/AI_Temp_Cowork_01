@echo off
REM 快速上传 knowledge-base 修改的文件到服务器
REM 使用方法: quick-upload.bat

echo ========================================
echo 上传文件到服务器
echo ========================================
echo.

set SERVER_IP=43.143.139.197
set SERVER_USER=ubuntu
set REMOTE_PATH=/opt/enterprise-ai-platform
set KEY_FILE=enterprise_ai_platform.pem

if not exist "%KEY_FILE%" (
    if exist "%USERPROFILE%\.ssh\%KEY_FILE%" (
        set KEY_FILE=%USERPROFILE%\.ssh\%KEY_FILE%
    ) else (
        echo 错误: 未找到密钥文件
        pause
        exit /b 1
    )
)

echo 服务器: %SERVER_USER%@%SERVER_IP%
echo 远程路径: %REMOTE_PATH%
echo.

REM 上传文件
echo 上传 knowledge-base/src/core/embedding_manager.py...
scp -i "%KEY_FILE%" -o StrictHostKeyChecking=no knowledge-base\src\core\embedding_manager.py %SERVER_USER%@%SERVER_IP%:%REMOTE_PATH%/knowledge-base/src/core/embedding_manager.py

echo 上传 knowledge-base/src/core/vector_store.py...
scp -i "%KEY_FILE%" -o StrictHostKeyChecking=no knowledge-base\src\core\vector_store.py %SERVER_USER%@%SERVER_IP%:%REMOTE_PATH%/knowledge-base/src/core/vector_store.py

echo 上传 knowledge-base/DEPENDENCY_FIX.md...
scp -i "%KEY_FILE%" -o StrictHostKeyChecking=no knowledge-base\DEPENDENCY_FIX.md %SERVER_USER%@%SERVER_IP%:%REMOTE_PATH%/knowledge-base/DEPENDENCY_FIX.md

echo.
echo ========================================
echo 上传完成！
echo ========================================
echo.
echo 在服务器上重启服务:
echo   ssh -i "%KEY_FILE%" %SERVER_USER%@%SERVER_IP% "cd %REMOTE_PATH% && sudo docker compose restart knowledge-base"
echo.

pause

