# LuminaOS平台企业架构数据部署脚本
$ErrorActionPreference = "Stop"

$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LuminaOS平台数据部署到服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. 上传构建脚本
Write-Host "`n[1/4] 上传构建脚本..." -ForegroundColor Yellow
scp -i $APP_SERVER_KEY "scripts/build_complete_luminaos_enterprise_architecture.py" "${APP_SERVER_USER}@${APP_SERVER}:/tmp/build_luminaos_data.py"

# 2. 运行数据库迁移
Write-Host "`n[2/4] 运行数据库迁移..." -ForegroundColor Yellow
ssh -i $APP_SERVER_KEY "${APP_SERVER_USER}@${APP_SERVER}" "cd /opt/enterprise-ai-platform/database && docker compose exec -T metadata-service alembic upgrade 027"

# 3. 运行数据构建脚本
Write-Host "`n[3/4] 运行数据构建脚本..." -ForegroundColor Yellow
ssh -i $APP_SERVER_KEY "${APP_SERVER_USER}@${APP_SERVER}" "cd /opt/enterprise-ai-platform && docker compose exec -T metadata-service python /tmp/build_luminaos_data.py"

# 4. 同步到Neo4j
Write-Host "`n[4/4] 同步数据到Neo4j..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://${APP_SERVER}:8005/api/enterprise-architecture/sync/all" -Method POST -TimeoutSec 300 -ErrorAction Stop
    Write-Host "同步成功: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "API同步失败，请手动触发同步" -ForegroundColor Yellow
}

Write-Host "`nDeploy completed!" -ForegroundColor Green

