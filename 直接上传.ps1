# 直接上传文件到服务器并重启服务
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  开始上传文件到服务器" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 测试SSH连接
Write-Host "测试SSH连接..." -ForegroundColor Cyan
$test = ssh -i $SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no $SERVER "echo OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "SSH连接失败！" -ForegroundColor Red
    Write-Host $test
    exit 1
}
Write-Host "SSH连接成功" -ForegroundColor Green
Write-Host ""

# 要上传的目录列表
$dirs = @(
    "agent-service",
    "api-gateway",
    "auth-service", 
    "dag-orchestrator",
    "knowledge-base",
    "mcp-gateway",
    "metadata-service",
    "registry-service",
    "services",
    "shared_libs"
)

# 上传目录
$count = 0
foreach ($dir in $dirs) {
    $count++
    if (Test-Path $dir) {
        Write-Host "[$count/$($dirs.Count)] 上传 $dir ..." -ForegroundColor Cyan
        scp -i $SSH_KEY -r -o StrictHostKeyChecking=no "$dir" "${SERVER}:${SERVER_PATH}/" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ 成功" -ForegroundColor Green
        } else {
            Write-Host "  ✗ 失败" -ForegroundColor Red
        }
    } else {
        Write-Host "[$count/$($dirs.Count)] 跳过 $dir (不存在)" -ForegroundColor Yellow
    }
}

# 上传web-ui
Write-Host ""
Write-Host "上传 web-ui ..." -ForegroundColor Cyan
if (Test-Path "web-ui/src") {
    scp -i $SSH_KEY -r -o StrictHostKeyChecking=no "web-ui/src" "${SERVER}:${SERVER_PATH}/web-ui/" 2>&1 | Out-Null
    Write-Host "  ✓ web-ui/src 上传成功" -ForegroundColor Green
}
if (Test-Path "web-ui/package.json") {
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/package.json" "${SERVER}:${SERVER_PATH}/web-ui/" 2>&1 | Out-Null
    Write-Host "  ✓ package.json 上传成功" -ForegroundColor Green
}
if (Test-Path "web-ui/next.config.js") {
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/next.config.js" "${SERVER}:${SERVER_PATH}/web-ui/" 2>&1 | Out-Null
    Write-Host "  ✓ next.config.js 上传成功" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  重启服务..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$restartCmd = "cd $SERVER_PATH && docker compose restart agent-service api-gateway auth-service dag-orchestrator knowledge-base mcp-gateway metadata-service registry-service web-ui"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $restartCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  完成！所有服务已重启" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "服务重启可能有问题，请检查" -ForegroundColor Yellow
}

