@echo off
chcp 65001 >nul
echo ========================================
echo   代码上传和服务重启
echo ========================================
echo.

REM 从 remote.ssh 读取配置
set SERVER_HOST=43.143.139.197
set SERVER_USER=ubuntu
set SSH_KEY=enterprise_ai_platform.pem
set SERVER_PATH=/opt/enterprise-ai-platform

echo 服务器配置:
echo   地址: %SERVER_HOST%
echo   用户: %SERVER_USER%
echo   SSH密钥: %SSH_KEY%
echo   路径: %SERVER_PATH%
echo.

REM 检查SSH密钥
if not exist "%SSH_KEY%" (
    echo 错误: SSH密钥文件不存在: %SSH_KEY%
    exit /b 1
)

REM 检查SSH连接
echo 检查SSH连接...
ssh -i %SSH_KEY% -o ConnectTimeout=5 -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_HOST% "echo OK" >nul 2>&1
if errorlevel 1 (
    echo 错误: SSH连接失败
    exit /b 1
)
echo SSH连接成功
echo.

REM 获取修改的文件列表（使用PowerShell）
echo 获取修改的文件列表...
powershell -Command "$files = git status --short | Where-Object { $_ -match '^[MADRC]' } | ForEach-Object { ($_ -replace '^[MADRC]\s+', '').Trim() } | Where-Object { $_ -notmatch '\.md$' -and $_ -notmatch '\.log$' -and $_ -notmatch '__pycache__' -and $_ -notmatch '\.pyc$' -and $_ -notmatch '^test_' -and $_ -notmatch '^check_' -and $_ -notmatch '^compare_' -and $_ -notmatch '^import_' -and $_ -notmatch '^create_' -and $_ -notmatch '^link_' -and $_ -notmatch '^simple_' -and $_ -notmatch '^generate_' -and $_ -notmatch '^download_' -and $_ -notmatch '^build_' -and $_ -notmatch '^test-' -and $_ -notmatch '^analyze' -and $_ -notmatch '^fix-' -and $_ -notmatch '^temp_' -and $_ -notmatch '^backup' -and $_ -notmatch '^logs/' -and $_ -notmatch '^htmlcov/' -and $_ -notmatch '^test-reports' -and $_ -notmatch '^\.pytest_cache' -and $_ -notmatch '^coverage\.json' -and $_ -notmatch '^semantic_system_test_report\.json'; $files | Out-File -FilePath files-to-upload.txt -Encoding UTF8; Write-Host \"找到 $($files.Count) 个文件\""

if not exist files-to-upload.txt (
    echo 没有找到需要上传的文件
    echo 是否上传所有重要目录? (y/n)
    set /p uploadAll=
    if /i not "%uploadAll%"=="y" (
        echo 已取消
        exit /b 0
    )
    echo agent-service> files-to-upload.txt
    echo api-gateway>> files-to-upload.txt
    echo auth-service>> files-to-upload.txt
    echo dag-orchestrator>> files-to-upload.txt
    echo knowledge-base>> files-to-upload.txt
    echo mcp-gateway>> files-to-upload.txt
    echo metadata-service>> files-to-upload.txt
    echo registry-service>> files-to-upload.txt
    echo services>> files-to-upload.txt
    echo shared_libs>> files-to-upload.txt
    echo web-ui/src>> files-to-upload.txt
    echo web-ui/package.json>> files-to-upload.txt
    echo web-ui/next.config.js>> files-to-upload.txt
    echo docker-compose.yml>> files-to-upload.txt
)

echo.
echo 文件列表:
type files-to-upload.txt | more
echo.
echo 是否继续上传? (y/n)
set /p confirm=
if /i not "%confirm%"=="y" (
    echo 已取消
    del files-to-upload.txt
    exit /b 0
)

echo.
echo 开始上传文件到服务器...
echo.

REM 上传文件
set uploadCount=0
set failCount=0
for /f "usebackq delims=" %%f in ("files-to-upload.txt") do (
    if exist "%%f" (
        echo 上传: %%f
        REM 创建远程目录
        for %%p in ("%%f") do set "remoteDir=%%~dpf"
        set "remoteDir=%remoteDir:~0,-1%"
        set "remoteDir=%remoteDir:\=/%"
        ssh -i %SSH_KEY% -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_HOST% "mkdir -p %SERVER_PATH%/%remoteDir%" >nul 2>&1
        
        REM 上传文件
        if exist "%%f\" (
            REM 是目录
            scp -i %SSH_KEY% -r -o StrictHostKeyChecking=no "%%f" %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/%%~dpf >nul 2>&1
        ) else (
            REM 是文件
            scp -i %SSH_KEY% -o StrictHostKeyChecking=no "%%f" %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/%%f >nul 2>&1
        )
        
        if errorlevel 1 (
            echo   失败
            set /a failCount+=1
        ) else (
            echo   成功
            set /a uploadCount+=1
        )
    ) else (
        echo 警告: 文件不存在，跳过: %%f
    )
)

echo.
echo 上传完成: 成功 %uploadCount% 个, 失败 %failCount% 个
echo.

REM 重启服务
echo 是否重启服务? (y/n)
set /p restart=
if /i "%restart%"=="y" (
    echo.
    echo 重启服务器上的服务...
    ssh -i %SSH_KEY% -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_HOST% "cd %SERVER_PATH% && docker compose restart"
    if errorlevel 1 (
        echo 服务重启失败
    ) else (
        echo 服务重启成功
    )
)

del files-to-upload.txt
echo.
echo ========================================
echo   完成！
echo ========================================
echo.

