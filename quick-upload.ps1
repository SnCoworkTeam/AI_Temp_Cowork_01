$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

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

foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        Write-Host "上传 $dir ..." -ForegroundColor Cyan
        & scp -i $SSH_KEY -r -o StrictHostKeyChecking=no "$dir" "${SERVER}:${SERVER_PATH}/"
    }
}

Write-Host "上传web-ui..." -ForegroundColor Cyan
if (Test-Path "web-ui/src") {
    & scp -i $SSH_KEY -r -o StrictHostKeyChecking=no "web-ui/src" "${SERVER}:${SERVER_PATH}/web-ui/"
}
if (Test-Path "web-ui/package.json") {
    & scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/package.json" "${SERVER}:${SERVER_PATH}/web-ui/"
}
if (Test-Path "web-ui/next.config.js") {
    & scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/next.config.js" "${SERVER}:${SERVER_PATH}/web-ui/"
}

Write-Host "`n重启服务..." -ForegroundColor Yellow
$cmd = "cd $SERVER_PATH && docker compose restart agent-service api-gateway auth-service dag-orchestrator knowledge-base mcp-gateway metadata-service registry-service web-ui"
& ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $cmd

Write-Host "`n完成！" -ForegroundColor Green


