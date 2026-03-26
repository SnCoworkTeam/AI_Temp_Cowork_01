# 上传代码到服务器并重启服务
$ErrorActionPreference = "Continue"

# 服务器配置
$SERVER_HOST = "43.143.139.197"
$SERVER_USER = "ubuntu"
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  代码上传和服务重启" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 检查SSH密钥
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "错误: SSH密钥文件不存在: $SSH_KEY" -ForegroundColor Red
    exit 1
}

# 测试SSH连接
Write-Host "检查SSH连接..." -ForegroundColor Cyan
$testResult = ssh -i $SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_HOST}" "echo OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: SSH连接失败" -ForegroundColor Red
    Write-Host $testResult
    exit 1
}
Write-Host "SSH连接成功" -ForegroundColor Green
Write-Host ""

# 获取修改的文件
Write-Host "获取修改的文件列表..." -ForegroundColor Cyan
$modifiedFiles = @()
git status --short | ForEach-Object {
    if ($_ -match '^[MADRC]\s+(.+)') {
        $file = $matches[1].Trim()
        # 过滤不需要上传的文件
        if ($file -notmatch '\.md$' -and 
            $file -notmatch '\.log$' -and 
            $file -notmatch '__pycache__' -and 
            $file -notmatch '\.pyc$' -and 
            $file -notmatch '^test_' -and 
            $file -notmatch '^check_' -and 
            $file -notmatch '^compare_' -and 
            $file -notmatch '^import_' -and 
            $file -notmatch '^create_' -and 
            $file -notmatch '^link_' -and 
            $file -notmatch '^simple_' -and 
            $file -notmatch '^generate_' -and 
            $file -notmatch '^download_' -and 
            $file -notmatch '^build_' -and 
            $file -notmatch '^test-' -and 
            $file -notmatch '^analyze' -and 
            $file -notmatch '^fix-' -and 
            $file -notmatch '^temp_' -and 
            $file -notmatch '^backup' -and 
            $file -notmatch '^logs/' -and 
            $file -notmatch '^htmlcov/' -and 
            $file -notmatch '^test-reports' -and 
            $file -notmatch '^\.pytest_cache' -and 
            $file -notmatch '^coverage\.json' -and 
            $file -notmatch '^semantic_system_test_report\.json') {
            $modifiedFiles += $file
        }
    }
}

if ($modifiedFiles.Count -eq 0) {
    Write-Host "没有找到需要上传的文件，上传所有重要目录" -ForegroundColor Yellow
    $modifiedFiles = @(
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

Write-Host "找到 $($modifiedFiles.Count) 个文件/目录需要上传" -ForegroundColor Green
Write-Host ""

# 显示前20个文件
Write-Host "文件列表（前20个）:" -ForegroundColor Cyan
$modifiedFiles | Select-Object -First 20 | ForEach-Object {
    Write-Host "  - $_" -ForegroundColor Gray
}
if ($modifiedFiles.Count -gt 20) {
    Write-Host "  ... 还有 $($modifiedFiles.Count - 20) 个文件" -ForegroundColor Gray
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
Write-Host ""

$uploadCount = 0
$failCount = 0

foreach ($file in $modifiedFiles) {
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
        Write-Host "上传目录: $file" -ForegroundColor Cyan
        scp -i $SSH_KEY -r -o StrictHostKeyChecking=no "$file" "${SERVER_USER}@${SERVER_HOST}:$remoteDir/" 2>&1 | Out-Null
    } else {
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
    
    if ($modifiedFiles | Where-Object { $_ -match '^agent-service' }) {
        $servicesToRestart += "agent-service"
    }
    if ($modifiedFiles | Where-Object { $_ -match '^api-gateway' }) {
        $servicesToRestart += "api-gateway"
    }
    if ($modifiedFiles | Where-Object { $_ -match '^auth-service' }) {
        $servicesToRestart += "auth-service"
    }
    if ($modifiedFiles | Where-Object { $_ -match '^dag-orchestrator' }) {
        $servicesToRestart += "dag-orchestrator"
    }
    if ($modifiedFiles | Where-Object { $_ -match '^knowledge-base' }) {
        $servicesToRestart += "knowledge-base"
    }
    if ($modifiedFiles | Where-Object { $_ -match '^mcp-gateway' }) {
        $servicesToRestart += "mcp-gateway"
    }
    if ($modifiedFiles | Where-Object { $_ -match '^metadata-service' }) {
        $servicesToRestart += "metadata-service"
    }
    if ($modifiedFiles | Where-Object { $_ -match '^registry-service' }) {
        $servicesToRestart += "registry-service"
    }
    if ($modifiedFiles | Where-Object { $_ -match '^services/' -or $_ -match '^shared_libs' }) {
        $servicesToRestart += "api-gateway", "agent-service", "workflow-engine"
    }
    if ($modifiedFiles | Where-Object { $_ -match '^web-ui' }) {
        $servicesToRestart += "web-ui"
    }
    if ($modifiedFiles | Where-Object { $_ -match '^docker-compose' }) {
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

