# 上传所有代码到43服务器
# 使用方法: .\scripts\upload-all-to-server-43.ps1

$ErrorActionPreference = "Continue"

$SERVER_HOST = "43.143.139.197"
$SERVER_USER = "ubuntu"
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "上传代码到43服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "服务器: $SERVER_USER@$SERVER_HOST" -ForegroundColor Yellow
Write-Host "路径: $SERVER_PATH" -ForegroundColor Yellow
Write-Host ""

# 检查SSH密钥
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "[错误] SSH密钥文件不存在: $SSH_KEY" -ForegroundColor Red
    exit 1
}

# 测试SSH连接
Write-Host "[1/4] 检查SSH连接..." -ForegroundColor Yellow
$testResult = ssh -i $SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_HOST}" "echo OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] SSH连接失败" -ForegroundColor Red
    Write-Host $testResult
    exit 1
}
Write-Host "[OK] SSH连接成功" -ForegroundColor Green
Write-Host ""

# 检查本地Git状态
Write-Host "[2/4] 检查本地Git状态..." -ForegroundColor Yellow
$localCommit = git log -1 --oneline
Write-Host "本地最新提交: $localCommit" -ForegroundColor Green
Write-Host ""

# 方式1: 使用Git Pull（推荐，如果服务器有Git仓库）
Write-Host "[3/4] 尝试在服务器上使用Git Pull..." -ForegroundColor Yellow
$gitPullCmd = 'cd ' + $SERVER_PATH + ' && git fetch origin && git pull origin main 2>&1'
$pullResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_HOST}" $gitPullCmd

if ($LASTEXITCODE -eq 0 -and $pullResult -notmatch "error|fatal|conflict") {
    Write-Host "[OK] Git Pull成功" -ForegroundColor Green
    Write-Host $pullResult
    Write-Host ""
    
    # 验证服务器上的提交
    Write-Host "[4/4] 验证服务器代码..." -ForegroundColor Yellow
    $serverCommitCmd = 'cd ' + $SERVER_PATH + ' && git log -1 --oneline'
    $serverCommit = ssh -i $SSH_KEY -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_HOST}" $serverCommitCmd
    Write-Host "服务器最新提交: $serverCommit" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "上传完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "[警告] Git Pull失败或需要手动处理" -ForegroundColor Yellow
    Write-Host $pullResult
    Write-Host ""
    Write-Host "将使用SCP方式上传代码..." -ForegroundColor Yellow
    Write-Host ""
}

# 方式2: 使用SCP上传关键目录
Write-Host "[3/4] 使用SCP上传代码..." -ForegroundColor Yellow

# 需要上传的目录
$uploadDirs = @(
    "metadata-service",
    "sap-metadata-agent",
    "shared_libs",
    "knowledge-base/src/models/document_metadata.py",
    "agent-service",
    "api-gateway",
    "auth-service",
    "dag-orchestrator",
    "mcp-gateway",
    "registry-service",
    "services",
    "database/src/migrations",
    "docker-compose.yml"
)

$uploadCount = 0
$failCount = 0

foreach ($dir in $uploadDirs) {
    if (-not (Test-Path $dir)) {
        Write-Host "  [跳过] 文件/目录不存在: $dir" -ForegroundColor Gray
        continue
    }
    
    $remotePath = "$SERVER_PATH/$dir"
    $remoteDir = Split-Path $remotePath -Parent
    
    # 创建远程目录
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_HOST}" "mkdir -p `"$remoteDir`"" | Out-Null
    
    # 上传文件或目录
    if (Test-Path $dir -PathType Container) {
        Write-Host "  [上传] 目录: $dir" -ForegroundColor Cyan
        scp -i $SSH_KEY -r -o StrictHostKeyChecking=no "$dir" "${SERVER_USER}@${SERVER_HOST}:$remoteDir/" 2>&1 | Out-Null
    } else {
        Write-Host "  [上传] 文件: $dir" -ForegroundColor Cyan
        scp -i $SSH_KEY -o StrictHostKeyChecking=no "$dir" "${SERVER_USER}@${SERVER_HOST}:$remotePath" 2>&1 | Out-Null
    }
    
    if ($LASTEXITCODE -eq 0) {
        $uploadCount++
        Write-Host "    [OK] 成功" -ForegroundColor Green
    } else {
        $failCount++
        Write-Host "    [失败]" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "[4/4] 上传完成: 成功 $uploadCount 个, 失败 $failCount 个" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })

# 验证服务器上的提交
Write-Host ""
Write-Host "验证服务器代码..." -ForegroundColor Yellow
$verifyCmd = 'cd ' + $SERVER_PATH + ' && git log -1 --oneline 2>&1'
$serverCommit = ssh -i $SSH_KEY -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_HOST}" $verifyCmd
Write-Host "服务器最新提交: $serverCommit" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示: 如果需要重启服务，请运行:" -ForegroundColor Yellow
$restartCmd = 'cd ' + $SERVER_PATH + ' && docker compose restart'
Write-Host "  ssh -i $SSH_KEY ${SERVER_USER}@${SERVER_HOST} `"$restartCmd`"" -ForegroundColor Cyan
Write-Host ""




