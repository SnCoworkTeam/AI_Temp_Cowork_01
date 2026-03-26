# Test demo guide - 按照演示指南测试所有功能
$ErrorActionPreference = "Stop"

$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"
$REMOTE_BASE = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Demo Guide - 演示指南测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Change to project root
Set-Location (Split-Path -Parent $PSScriptRoot)

$sshTarget = "${APP_SERVER_USER}@${APP_SERVER}"

Write-Host "`n1. 检查服务状态..." -ForegroundColor Yellow

# 检查服务状态
$services = @("web-ui", "api-gateway", "agent-service", "metadata-service")
foreach ($service in $services) {
    Write-Host "  检查 $service..." -ForegroundColor Gray
    $statusCmd = "cd $REMOTE_BASE; docker compose ps $service --format '{{.Status}}'"
    $status = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $statusCmd 2>&1
    
    if ($status -match "Up|running") {
        Write-Host "    ✅ $service 运行正常" -ForegroundColor Green
    } else {
        Write-Host "    ❌ $service 状态异常: $status" -ForegroundColor Red
    }
}

Write-Host "`n2. 检查数据库连接..." -ForegroundColor Yellow

# 检查PostgreSQL连接
Write-Host "  检查 PostgreSQL..." -ForegroundColor Gray
$pgCmd = "cd $REMOTE_BASE; docker compose exec -T metadata-service python -c 'from src.database import get_db; next(get_db()); print(\\\"OK\\\")' 2>&1"
$pgResult = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $pgCmd 2>&1
if ($pgResult -match "OK") {
    Write-Host "    ✅ PostgreSQL 连接正常" -ForegroundColor Green
} else {
    Write-Host "    ⚠️  PostgreSQL 连接检查: $pgResult" -ForegroundColor Yellow
}

# 检查Neo4j连接
Write-Host "  检查 Neo4j..." -ForegroundColor Gray
$neo4jResult = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "cd $REMOTE_BASE; docker compose exec -T neo4j cypher-shell -u neo4j -p enterprise_ai_neo4j 'RETURN 1 as test' 2>&1 | grep -q '1' && echo 'OK' || echo 'FAIL'"
if ($neo4jResult -match "OK") {
    Write-Host "    ✅ Neo4j 连接正常" -ForegroundColor Green
} else {
    Write-Host "    ⚠️  Neo4j 连接检查: $neo4jResult" -ForegroundColor Yellow
}

Write-Host "`n3. 检查数据完整性..." -ForegroundColor Yellow

# 检查PostgreSQL数据
Write-Host "  检查组织架构数据..." -ForegroundColor Gray
$orgCmd = "cd $REMOTE_BASE; docker compose exec -T metadata-service python -c 'from src.database import get_db; from src.models.organization_models import OrganizationUnit; db = next(get_db()); count = db.query(OrganizationUnit).count(); print(count)' 2>&1"
$orgCount = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $orgCmd 2>&1
if ($orgCount -match "^\d+$" -and [int]$orgCount -gt 0) {
    Write-Host "    ✅ 组织架构数据: $orgCount 条记录" -ForegroundColor Green
} else {
    Write-Host "    ⚠️  组织架构数据: $orgCount" -ForegroundColor Yellow
}

# 检查Neo4j数据
Write-Host "  检查Neo4j节点数量..." -ForegroundColor Gray
$neo4jNodeCount = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "cd $REMOTE_BASE; docker compose exec -T neo4j cypher-shell -u neo4j -p enterprise_ai_neo4j 'MATCH (n) RETURN count(n) as count' 2>&1 | grep -oE '[0-9]+' | head -1"
if ($neo4jNodeCount -match "^\d+$" -and [int]$neo4jNodeCount -gt 0) {
    Write-Host "    ✅ Neo4j 节点: $neo4jNodeCount 个" -ForegroundColor Green
} else {
    Write-Host "    ⚠️  Neo4j 节点: $neo4jNodeCount" -ForegroundColor Yellow
}

Write-Host "`n4. 检查API端点..." -ForegroundColor Yellow

# 检查API Gateway
$apiUrl = "http://${APP_SERVER}:8080/api/health"
try {
    $response = Invoke-WebRequest -Uri $apiUrl -Method GET -TimeoutSec 5 -UseBasicParsing 2>&1
    if ($response.StatusCode -eq 200) {
        Write-Host "    ✅ API Gateway 可访问" -ForegroundColor Green
    }
} catch {
    Write-Host "    ⚠️  API Gateway 检查失败: $_" -ForegroundColor Yellow
}

# 检查企业架构API
$eaUrl = "http://${APP_SERVER}:8080/api/enterprise-architecture/overview"
try {
    $response = Invoke-WebRequest -Uri $eaUrl -Method GET -TimeoutSec 5 -UseBasicParsing 2>&1
    if ($response.StatusCode -eq 200) {
        Write-Host "    ✅ 企业架构API 可访问" -ForegroundColor Green
    }
} catch {
    Write-Host "    ⚠️  企业架构API 检查失败: $_" -ForegroundColor Yellow
}

Write-Host "`n5. 检查前端页面..." -ForegroundColor Yellow

# 检查前端页面
$frontendUrl = "http://${APP_SERVER}:3000"
try {
    $response = Invoke-WebRequest -Uri $frontendUrl -Method GET -TimeoutSec 5 -UseBasicParsing 2>&1
    if ($response.StatusCode -eq 200) {
        Write-Host "    ✅ 前端页面可访问" -ForegroundColor Green
    }
} catch {
    Write-Host "    ⚠️  前端页面检查失败: $_" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "测试完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`n请按照演示指南进行以下测试：" -ForegroundColor Yellow
Write-Host "1. 对话框交互: 查询组织架构、追踪业务流程、影响分析" -ForegroundColor White
Write-Host "2. 前端页面: 访问 /enterprise-architecture 各子页面" -ForegroundColor White
Write-Host "3. 关系图: 访问 /enterprise-architecture/relationships" -ForegroundColor White
Write-Host "`n"

