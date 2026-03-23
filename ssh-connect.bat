@echo off
REM 直接使用 remote.ssh 配置连接服务器
REM 使用方法: ssh-connect.bat

echo ========================================
echo 连接企业AI平台服务器
echo ========================================
echo.

REM 读取 remote.ssh 配置
for /f "tokens=2" %%a in ('findstr /C:"HostName" remote.ssh 2^>nul') do set SERVER_IP=%%a
for /f "tokens=2" %%a in ('findstr /C:"User" remote.ssh 2^>nul') do set SERVER_USER=%%a

if "%SERVER_IP%"=="" (
    echo 错误: 无法从 remote.ssh 读取服务器IP
    pause
    exit /b 1
)

if "%SERVER_USER%"=="" (
    set SERVER_USER=ubuntu
)

echo 服务器: %SERVER_USER%@%SERVER_IP%
echo 密钥: enterprise_ai_platform.pem
echo.
echo 正在连接...
echo.

REM 检查密钥文件
if not exist "enterprise_ai_platform.pem" (
    if exist "%USERPROFILE%\.ssh\enterprise_ai_platform.pem" (
        set KEY_FILE=%USERPROFILE%\.ssh\enterprise_ai_platform.pem
    ) else (
        echo 错误: 未找到密钥文件 enterprise_ai_platform.pem
        pause
        exit /b 1
    )
) else (
    set KEY_FILE=enterprise_ai_platform.pem
)

REM 执行 SSH 连接
ssh -i "%KEY_FILE%" -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_IP%

