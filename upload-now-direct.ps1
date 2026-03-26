# 直接上传修改的文件到服务器
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "开始上传文件..." -ForegroundColor Green

# 获取修改的文件（排除文档和测试文件）
$files = git status --short | Where-Object { 
    $_ -match '^[MADRC]' -and 
    $_ -notmatch '\.md$' -and 
    $_ -notmatch 'test_' -and 
    $_ -notmatch 'check_' -and 
    $_ -notmatch 'compare_' -and 
    $_ -notmatch 'import_' -and 
    $_ -notmatch 'create_' -and 
    $_ -notmatch 'link_'
} | ForEach-Object { ($_ -replace '^[MADRC]\s+', '').Trim() }

# 主要修改的目录
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
    "shared_libs",
    "web-ui/src",
    "web-ui/package.json",
    "web-ui/next.config.js"
)

Write-Host "上传主要目录..." -ForegroundColor Cyan
foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        Write-Host "上传: $dir" -ForegroundColor Yellow
        scp -i $SSH_KEY -r -o StrictHostKeyChecking=no "$dir" "${SERVER}:${SERVER_PATH}/" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ 成功" -ForegroundColor Green
        } else {
            Write-Host "  ✗ 失败" -ForegroundColor Red
        }
    }
}

Write-Host "`n上传完成！" -ForegroundColor Green
Write-Host "`n重启服务..." -ForegroundColor Cyan

# 重启相关服务
$restartCmd = "cd $SERVER_PATH && docker compose restart agent-service api-gateway auth-service dag-orchestrator knowledge-base mcp-gateway metadata-service registry-service web-ui"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $restartCmd

Write-Host "`n完成！" -ForegroundColor Green


