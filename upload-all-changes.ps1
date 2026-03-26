# 上传所有修改的文件到服务器
# 使用 remote.ssh 配置文件中的设置

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传所有修改的文件到服务器" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 从 remote.ssh 读取配置
$SSH_CONFIG = "remote.ssh"
if (-not (Test-Path $SSH_CONFIG)) {
    Write-Host "[错误] 找不到配置文件: $SSH_CONFIG" -ForegroundColor Red
    exit 1
}

# 解析 remote.ssh 配置
$SSH_HOST = "enterprise-ai-server"
$SSH_HOSTNAME = "43.143.139.197"
$SSH_USER = "ubuntu"
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER_PATH = "/opt/enterprise-ai-platform"

# 读取配置文件
$configContent = Get-Content $SSH_CONFIG
foreach ($line in $configContent) {
    if ($line -match "^\s*HostName\s+(.+)$") {
        $SSH_HOSTNAME = $matches[1].Trim()
    }
    elseif ($line -match "^\s*User\s+(.+)$") {
        $SSH_USER = $matches[1].Trim()
    }
    elseif ($line -match "^\s*IdentityFile\s+(.+)$") {
        $SSH_KEY = $matches[1].Trim()
    }
}

# 构建SSH连接字符串
$SERVER = "${SSH_USER}@${SSH_HOSTNAME}"

# 检查密钥文件
if (-not (Test-Path $SSH_KEY)) {
    $SSH_KEY = "$env:USERPROFILE\.ssh\$SSH_KEY"
    if (-not (Test-Path $SSH_KEY)) {
        Write-Host "[错误] 密钥文件未找到: $SSH_KEY" -ForegroundColor Red
        Write-Host "请确保密钥文件在当前目录或 ~/.ssh/ 目录中" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "[配置] 服务器配置:" -ForegroundColor Cyan
Write-Host "  主机: $SSH_HOSTNAME" -ForegroundColor Gray
Write-Host "  用户: $SSH_USER" -ForegroundColor Gray
Write-Host "  密钥: $SSH_KEY" -ForegroundColor Gray
Write-Host "  路径: $SERVER_PATH" -ForegroundColor Gray
Write-Host ""

# 测试SSH连接
Write-Host "[检查] 测试SSH连接..." -ForegroundColor Cyan
$testResult = ssh -i $SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no $SERVER "echo 'SSH连接成功'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] SSH连接失败!" -ForegroundColor Red
    Write-Host $testResult -ForegroundColor Red
    exit 1
}
Write-Host "[OK] SSH连接成功" -ForegroundColor Green
Write-Host ""

# 获取所有修改的文件 - 使用更简单的方法
Write-Host "[准备] 获取修改的文件列表..." -ForegroundColor Cyan

# 禁用 git 分页器
$env:GIT_PAGER = ""
$env:PAGER = ""

# 直接使用 git status --porcelain，这是最可靠的方法
$allModifiedFiles = @()

# 获取已暂存的文件（使用 --no-pager 确保不分页）
$stagedOutput = git --no-pager diff --cached --name-only 2>&1
if ($stagedOutput) {
    $stagedFiles = $stagedOutput | Where-Object { $_ -and $_ -notmatch "warning:" -and $_.Trim() -ne "" }
    if ($stagedFiles) {
        $allModifiedFiles += $stagedFiles
    }
}

# 获取未暂存的文件
$unstagedOutput = git --no-pager diff --name-only 2>&1
if ($unstagedOutput) {
    $unstagedFiles = $unstagedOutput | Where-Object { $_ -and $_ -notmatch "warning:" -and $_.Trim() -ne "" }
    if ($unstagedFiles) {
        $allModifiedFiles += $unstagedFiles
    }
}

# 去重并过滤空值
$allModifiedFiles = $allModifiedFiles | Where-Object { $_ -and $_.Trim() -ne "" } | Sort-Object -Unique

if ($allModifiedFiles.Count -eq 0) {
    Write-Host "[信息] 没有找到修改的文件" -ForegroundColor Yellow
    exit 0
}

Write-Host "[信息] 找到 $($allModifiedFiles.Count) 个修改的文件" -ForegroundColor Green
Write-Host ""

# 显示文件列表（前20个）
Write-Host "修改的文件列表（前20个）:" -ForegroundColor Cyan
$displayCount = [Math]::Min(20, $allModifiedFiles.Count)
for ($i = 0; $i -lt $displayCount; $i++) {
    $file = $allModifiedFiles[$i]
    if (Test-Path $file) {
        $fileInfo = Get-Item $file
        Write-Host "  [OK] $file ($($fileInfo.Length) bytes)" -ForegroundColor Gray
    } else {
        Write-Host "  [WARN] 文件不存在: $file" -ForegroundColor Yellow
    }
}
if ($allModifiedFiles.Count -gt 20) {
    Write-Host "  ... 还有 $($allModifiedFiles.Count - 20) 个文件" -ForegroundColor Gray
}
Write-Host ""

# 确认上传（支持非交互模式）
$nonInteractive = $env:NON_INTERACTIVE -eq "1"
if (-not $nonInteractive) {
    $confirm = Read-Host "是否继续上传所有修改的文件? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "[取消] 用户取消上传" -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "[信息] 非交互模式，自动继续上传" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "[上传] 开始上传文件..." -ForegroundColor Cyan

$successCount = 0
$failCount = 0
$skipCount = 0

foreach ($file in $allModifiedFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "  [跳过] 文件不存在: $file" -ForegroundColor Yellow
        $skipCount++
        continue
    }
    
    # 计算远程路径
    $remoteDir = Split-Path $file -Parent
    $remoteFile = $file
    
    # 确保远程目录存在
    if ($remoteDir -and $remoteDir -ne ".") {
        $remoteDirPath = "$SERVER_PATH/$remoteDir"
        ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p `"$remoteDirPath`"" 2>&1 | Out-Null
    }
    
    # 上传文件
    $remotePath = "$SERVER_PATH/$remoteFile"
    Write-Host "  上传: $file -> $remotePath" -ForegroundColor Gray
    
    $scpResult = scp -i $SSH_KEY -o StrictHostKeyChecking=no "$file" "${SERVER}:${remotePath}" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [OK] 上传成功" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "    [错误] 上传失败: $scpResult" -ForegroundColor Red
        $failCount++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传完成统计" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  成功: $successCount 个文件" -ForegroundColor Green
Write-Host "  失败: $failCount 个文件" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Gray" })
Write-Host "  跳过: $skipCount 个文件" -ForegroundColor $(if ($skipCount -gt 0) { "Yellow" } else { "Gray" })
Write-Host "  总计: $($allModifiedFiles.Count) 个文件" -ForegroundColor Cyan
Write-Host ""

if ($failCount -gt 0) {
    Write-Host "[警告] 有文件上传失败，请检查错误信息" -ForegroundColor Yellow
    exit 1
}

Write-Host "[完成] 所有文件上传成功！" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Cyan
Write-Host "  1. SSH登录服务器: ssh -i $SSH_KEY $SERVER" -ForegroundColor Yellow
Write-Host "  2. 进入项目目录: cd $SERVER_PATH" -ForegroundColor Yellow
Write-Host "  3. 根据需要重启相关服务" -ForegroundColor Yellow
Write-Host ""
