# zhgj 分支 19 个业务服务健康检查（不含 postgres/redis/qdrant/neo4j/redis-commander 等基础服务）
# 用法: .\scripts\zhgj-19-services-check.ps1

$root = if (Test-Path "docker-compose.yml") { $PWD } else { Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
Set-Location $root

$zhgj19 = @(
    "registry-service", "api-gateway", "config-center", "mcp-gateway", "workflow-engine",
    "web-ui", "auth-service", "knowledge-base", "metadata-service", "chat-service",
    "dag-orchestrator", "agent-service", "agent-orchestrator", "agent-registry",
    "memory-service", "sap-metadata-agent", "project-management", "vector-coordinator-service",
    "deployment-agent"
)

$out = docker compose ps -a --format "{{.Service}}|{{.Status}}" 2>$null
$status = @{}
foreach ($line in ($out -split "`n")) {
    if ($line -match "^([^|]+)\|(.+)$") { $status[$matches[1].Trim()] = $matches[2].Trim() }
}

$ok = 0
$bad = @()
foreach ($s in $zhgj19) {
    $st = $status[$s]
    if ($st -match "healthy|Up \d") { $ok++; Write-Host "[OK]  $s" -ForegroundColor Green }
    else { Write-Host "[--]  $s  $st" -ForegroundColor Yellow; $bad += $s }
}

Write-Host "`nzhgj 19 服务: $ok 个正常, $($bad.Count) 个异常" -ForegroundColor Cyan
if ($bad.Count -gt 0) { Write-Host "异常: $($bad -join ', ')" -ForegroundColor Yellow; exit 1 }
exit 0
