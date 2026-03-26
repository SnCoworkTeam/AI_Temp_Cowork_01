# 上传本地修改的代码到服务器并重启服务
# 使用方法: .\upload-and-restart-simple.ps1

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  代码上传和服务重启" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 从 remote.ssh 读取服务器配置
$SSH_CONFIG = Get-Content "remote.ssh" -ErrorAction SilentlyContinue
$SERVER_HOST = ""
$SERVER_USER = ""
$SSH_KEY = ""

foreach ($line in $SSH_CONFIG) {
    if ($line -match 'HostName\s+(.+)') {
        $SERVER_HOST = $matches[1].Trim()
    }
    if ($line -match 'User\s+(.+)') {
        $SERVER_USER = $matches[1].Trim()
    }
    if ($line -match 'IdentityFile\s+(.+)') {
        $SSH_KEY = $matches[1].Trim()
    }
}

# 默认值
if ([string]::IsNullOrEmpty($SERVER_HOST)) {
    $SERVER_HOST = "43.143.139.197"
}
if ([string]::IsNullOrEmpty($SERVER_USER)) {
    $SERVER_USER = "ubuntu"
}
if ([string]::IsNullOrEmpty($SSH_KEY)) {
    $SSH_KEY = "enterprise_ai_platform.pem"
}

# 服务器路径
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "服务器配置:" -ForegroundColor Cyan
Write-Host "  地址: $SERVER_HOST" -ForegroundColor Yellow
Write-Host "  用户: $SERVER_USER" -ForegroundColor Yellow
Write-Host "  SSH密钥: $SSH_KEY" -ForegroundColor Yellow
Write-Host "  路径: $SERVER_PATH" -ForegroundColor Yellow
Write-Host ""

# 检查SSH密钥
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "错误: SSH密钥文件不存在: $SSH_KEY" -ForegroundColor Red
    exit 1
}

# 检查SSH连接
Write-Host "检查SSH连接..." -ForegroundColor Cyan
$sshTest = ssh -i $SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_HOST}" "echo OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: SSH连接失败" -ForegroundColor Red
    Write-Host $sshTest
    exit 1
}
Write-Host "SSH连接成功" -ForegroundColor Green
Write-Host ""

# 获取所有修改的文件
Write-Host "获取修改的文件列表..." -ForegroundColor Cyan
$modifiedFiles = git status --short | Where-Object { $_ -match '^[MADRC]' } | ForEach-Object {
    ($_ -replace '^[MADRC]\s+', '').Trim()
} | Where-Object { 
    $_ -notmatch '\.md$' -and
    $_ -notmatch '\.log$' -and
    $_ -notmatch '__pycache__' -and
    $_ -notmatch '\.pyc$' -and
    $_ -notmatch '^test_' -and
    $_ -notmatch '^check_' -and
    $_ -notmatch '^compare_' -and
    $_ -notmatch '^import_' -and
    $_ -notmatch '^create_' -and
    $_ -notmatch '^link_' -and
    $_ -notmatch '^simple_' -and
    $_ -notmatch '^generate_' -and
    $_ -notmatch '^download_' -and
    $_ -notmatch '^build_' -and
    $_ -notmatch '^test-' -and
    $_ -notmatch '^analyze' -and
    $_ -notmatch '^fix-' -and
    $_ -notmatch '^temp_' -and
    $_ -notmatch '^backup' -and
    $_ -notmatch '^logs/' -and
    $_ -notmatch '^htmlcov/' -and
    $_ -notmatch '^test-reports' -and
    $_ -notmatch '^\.pytest_cache' -and
    $_ -notmatch '^coverage\.json' -and
    $_ -notmatch '^semantic_system_test_report\.json'
}

# 也包含未跟踪但重要的文件
$untrackedFiles = git status --short | Where-Object { $_ -match '^\?\?' } | ForEach-Object {
    ($_ -replace '^\?\?\s+', '').Trim()
} | Where-Object {
    ($_ -match '\.py$' -or $_ -match '\.tsx?$' -or $_ -match '\.jsx?$' -or $_ -match '\.yaml$' -or $_ -match '\.yml$' -or $_ -match '\.json$' -or $_ -match '\.sh$' -or $_ -match '\.ps1$') -and
    $_ -notmatch '^test_' -and
    $_ -notmatch '^check_' -and
    $_ -notmatch '^compare_' -and
    $_ -notmatch '^import_' -and
    $_ -notmatch '^create_' -and
    $_ -notmatch '^link_' -and
    $_ -notmatch '^simple_' -and
    $_ -notmatch '^generate_' -and
    $_ -notmatch '^download_' -and
    $_ -notmatch '^build_' -and
    $_ -notmatch '^test-' -and
    $_ -notmatch '^analyze' -and
    $_ -notmatch '^fix-' -and
    $_ -notmatch '^temp_' -and
    $_ -notmatch '^backup' -and
    $_ -notmatch '\.md$' -and
    $_ -notmatch '\.log$' -and
    $_ -notmatch '__pycache__' -and
    $_ -notmatch '\.pyc$'
}

$allFiles = ($modifiedFiles + $untrackedFiles) | Sort-Object -Unique

if ($allFiles.Count -eq 0) {
    Write-Host "没有找到需要上传的文件，上传所有重要目录" -ForegroundColor Yellow
    $allFiles = @(
        "agent-service",
        "api-gateway",
        "auth-service",
        "dag-orchestrator",
        "knowledge-base",
        "mcp-gateway",
        "metadata-service",
        "registry-service",
        "services",
        "shared_libs",
        "web-ui/src",
        "web-ui/package.json",
        "web-ui/next.config.js",
        "docker-compose.yml"
    )
}

Write-Host "找到 $($allFiles.Count) 个文件/目录需要上传" -ForegroundColor Green
Write-Host ""

# 显示前20个文件
Write-Host "文件列表（前20个）:" -ForegroundColor Cyan
$allFiles | Select-Object -First 20 | ForEach-Object {
    Write-Host "  - $_" -ForegroundColor Gray
}
if ($allFiles.Count -gt 20) {
    Write-Host "  ... 还有 $($allFiles.Count - 20) 个文件" -ForegroundColor Gray
}
Write-Host ""

# 确认上传
Write-Host "是否继续上传? (y/n)" -ForegroundColor Yellow
$confirm = Read-Host
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "已取消" -ForegroundColor Yellow
    exit 0
}

# 上传文件
Write-Host ""
Write-Host "开始上传文件到服务器..." -ForegroundColor Cyan
Write-Host "  目标: ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}" -ForegroundColor Yellow
Write-Host ""

$uploadCount = 0
$failCount = 0

foreach ($file in $allFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "警告: 文件不存在，跳过: $file" -ForegroundColor Yellow
        continue
    }
    
    $remotePath = "$SERVER_PATH/$file"
    $remoteDir = $remotePath -replace '/[^/]+$', ''
    
    # 创建远程目录
    $mkdirCmd = "mkdir -p `"$remoteDir`""
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_HOST}" $mkdirCmd | Out-Null
    
    # 上传文件或目录
    if (Test-Path $file -PathType Container) {
        # 目录
        Write-Host "上传目录: $file" -ForegroundColor Cyan
        scp -i $SSH_KEY -r -o StrictHostKeyChecking=no "$file" "${SERVER_USER}@${SERVER_HOST}:$remoteDir/" 2>&1 | Out-Null
    } else {
        # 文件
        Write-Host "上传文件: $file" -ForegroundColor Cyan
        scp -i $SSH_KEY -o StrictHostKeyChecking=no "$file" "${SERVER_USER}@${SERVER_HOST}:$remotePath" 2>&1 | Out-Null
    }
    
    if ($LASTEXITCODE -eq 0) {
        $uploadCount++
        Write-Host "  成功" -ForegroundColor Green
    } else {
        $failCount++
        Write-Host "  失败" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "上传完成: 成功 $uploadCount 个, 失败 $failCount 个" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })
Write-Host ""

# 重启服务
Write-Host "是否重启服务? (y/n)" -ForegroundColor Yellow
$restart = Read-Host
if ($restart -eq "y" -or $restart -eq "Y") {
    Write-Host ""
    Write-Host "重启服务器上的服务..." -ForegroundColor Cyan
    
    # 确定需要重启的服务
    $servicesToRestart = @()
    
    # 根据修改的文件确定需要重启的服务
    if ($allFiles | Where-Object { $_ -match '^agent-service' }) {
        $servicesToRestart += "agent-service"
    }
    if ($allFiles | Where-Object { $_ -match '^api-gateway' }) {
        $servicesToRestart += "api-gateway"
    }
    if ($allFiles | Where-Object { $_ -match '^auth-service' }) {
        $servicesToRestart += "auth-service"
    }
    if ($allFiles | Where-Object { $_ -match '^dag-orchestrator' }) {
        $servicesToRestart += "dag-orchestrator"
    }
    if ($allFiles | Where-Object { $_ -match '^knowledge-base' }) {
        $servicesToRestart += "knowledge-base"
    }
    if ($allFiles | Where-Object { $_ -match '^mcp-gateway' }) {
        $servicesToRestart += "mcp-gateway"
    }
    if ($allFiles | Where-Object { $_ -match '^metadata-service' }) {
        $servicesToRestart += "metadata-service"
    }
    if ($allFiles | Where-Object { $_ -match '^registry-service' }) {
        $servicesToRestart += "registry-service"
    }
    if ($allFiles | Where-Object { $_ -match '^services/' -or $_ -match '^shared_libs' }) {
        $servicesToRestart += "api-gateway", "agent-service", "workflow-engine"
    }
    if ($allFiles | Where-Object { $_ -match '^web-ui' }) {
        $servicesToRestart += "web-ui"
    }
    if ($allFiles | Where-Object { $_ -match '^docker-compose' }) {
        $servicesToRestart = @("all")
    }
    
    $servicesToRestart = $servicesToRestart | Sort-Object -Unique
    
    if ($servicesToRestart.Count -eq 0) {
        Write-Host "无法确定需要重启的服务，是否重启所有服务? (y/n)" -ForegroundColor Yellow
        $restartAll = Read-Host
        if ($restartAll -eq "y" -or $restartAll -eq "Y") {
            $servicesToRestart = @("all")
        }
    }
    
    if ($servicesToRestart.Count -gt 0) {
        if ($servicesToRestart -contains "all") {
            Write-Host "重启所有服务..." -ForegroundColor Yellow
            $restartCmd = "cd $SERVER_PATH; docker compose down; docker compose up -d"
        } else {
            Write-Host "重启服务: $($servicesToRestart -join ', ')" -ForegroundColor Yellow
            $serviceList = $servicesToRestart -join ' '
            $restartCmd = "cd $SERVER_PATH; docker compose restart $serviceList"
        }
        
        ssh -i $SSH_KEY -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_HOST}" $restartCmd
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "服务重启成功" -ForegroundColor Green
        } else {
            Write-Host "服务重启失败" -ForegroundColor Red
        }
    } else {
        Write-Host "未重启任何服务" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

