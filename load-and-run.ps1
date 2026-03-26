# 在内网服务器上加载 OpenCode 镜像并启动（本文件夹内执行）
# 用法: .\load-and-run.ps1
# 请先配置 .env 中的 OPENCODE_WORKSPACE

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path "enterprise-ai-opencode.tar")) {
    Write-Host "ERROR: enterprise-ai-opencode.tar not found" -ForegroundColor Red
    exit 1
}
Write-Host "Loading OpenCode image..."
docker load -i enterprise-ai-opencode.tar

if (-not (Test-Path ".env")) {
    Write-Host "WARN: .env not found. Copy .env.example to .env and set OPENCODE_WORKSPACE." -ForegroundColor Yellow
    Write-Host "Example: OPENCODE_WORKSPACE=/opt/enterprise-ai-platform"
    exit 1
}

Write-Host "Starting OpenCode..."
docker compose -f docker-compose.opencode.yml --env-file .env up -d
Write-Host "Done. Check: docker compose -f docker-compose.opencode.yml ps"
