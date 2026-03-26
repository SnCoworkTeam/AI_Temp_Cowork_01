@echo off
chcp 65001 >nul
echo ========================================
echo 上传修改的文件到服务器
echo ========================================
echo.

REM 读取 remote.ssh 配置
set SERVER_IP=43.143.139.197
set SERVER_USER=ubuntu
set KEY_FILE=
set REMOTE_PATH=/opt/enterprise-ai-platform

if exist "remote.ssh" (
    echo 读取配置文件: remote.ssh
    for /f "tokens=2" %%a in ('findstr /c:"HostName" remote.ssh') do set SERVER_IP=%%a
    for /f "tokens=2" %%a in ('findstr /c:"User" remote.ssh') do set SERVER_USER=%%a
    for /f "tokens=2" %%a in ('findstr /c:"IdentityFile" remote.ssh') do set KEY_FILE=%%a
    set KEY_FILE=%KEY_FILE:"=%
)

REM 查找密钥文件
if "%KEY_FILE%"=="" set KEY_FILE=enterprise_ai_platform.pem
if not exist "%KEY_FILE%" (
    if exist "%USERPROFILE%\.ssh\enterprise_ai_platform.pem" (
        set KEY_FILE=%USERPROFILE%\.ssh\enterprise_ai_platform.pem
    ) else (
        echo 错误: 未找到密钥文件
        pause
        exit /b 1
    )
)

echo 服务器: %SERVER_USER%@%SERVER_IP%
echo 密钥文件: %KEY_FILE%
echo 远程路径: %REMOTE_PATH%
echo.

REM 上传 knowledge-base/requirements.txt（最重要的修复文件）
echo [1/1] 上传 knowledge-base/requirements.txt...
scp -i "%KEY_FILE%" -o StrictHostKeyChecking=no knowledge-base\requirements.txt %SERVER_USER%@%SERVER_IP%:%REMOTE_PATH%/knowledge-base/requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo [OK] knowledge-base/requirements.txt 上传成功
) else (
    echo [FAIL] knowledge-base/requirements.txt 上传失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 上传完成!
echo ========================================
echo.
echo 下一步操作:
echo   1. SSH 连接: ssh -i "%KEY_FILE%" %SERVER_USER%@%SERVER_IP%
echo   2. 进入目录: cd %REMOTE_PATH%
echo   3. 重新构建: sudo docker compose up -d --build knowledge-base
echo.
pause

