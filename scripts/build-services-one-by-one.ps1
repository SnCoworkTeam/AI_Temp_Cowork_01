# 逐个构建 docker-compose 中的服务，某个失败即停止并报告
# 用法: .\scripts\build-services-one-by-one.ps1
# 跳过因网络无法拉取镜像的服务（如 web-ui 需 node:20-alpine）:
#   $env:SKIP_SERVICES="web-ui"; .\scripts\build-services-one-by-one.ps1
# 或先配置 Docker 镜像加速 / 在能访问外网时: docker pull node:20-alpine 后再运行本脚本

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path "$root\docker-compose.yml")) { $root = $PWD }
Set-Location $root

# 可选：跳过某些服务（如 Docker Hub 不可达时跳过 web-ui）
$skipList = @()
if ($env:SKIP_SERVICES) { $skipList = $env:SKIP_SERVICES -split "," | ForEach-Object { $_.Trim() } }

# 需要构建的服务（不含 sap-mcp-server，其有 profile 且目录为空）
$allServices = @(
    "registry-service",
    "api-gateway",
    "config-center",
    "mcp-gateway",
    "workflow-engine",
    "web-ui",
    "auth-service",
    "knowledge-base",
    "metadata-service",
    "chat-service",
    "dag-orchestrator",
    "agent-service",
    "agent-orchestrator",
    "agent-registry",
    "memory-service",
    "sap-metadata-agent",
    "project-management",
    "vector-coordinator-service",
    "deployment-agent",
    "joyagent-adapter"
)
$services = $allServices | Where-Object { $_ -notin $skipList }
if ($skipList.Count -gt 0) { Write-Host "Skipping: $($skipList -join ', ')" -ForegroundColor Yellow }

$built = @()
$failed = $null

foreach ($name in $services) {
    Write-Host "`n========== Building: $name ==========" -ForegroundColor Cyan
    & docker compose build $name
    if ($LASTEXITCODE -ne 0) {
        $failed = $name
        Write-Host "`n*** BUILD FAILED: $name ***" -ForegroundColor Red
        break
    }
    $built += $name
    Write-Host "OK: $name" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
if ($failed) {
    Write-Host "Stopped at failed service: $failed" -ForegroundColor Red
    Write-Host "Successfully built: $($built.Count) - $($built -join ', ')" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "All $($built.Count) services built successfully." -ForegroundColor Green
    exit 0
}
