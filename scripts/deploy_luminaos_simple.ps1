# 简化版部署脚本
$APP_SERVER = "43.143.139.197"
$KEY = ".\enterprise_ai_platform.pem"

Write-Host "Step 1: Upload script..." -ForegroundColor Yellow
scp -i $KEY -o ConnectTimeout=10 "scripts/build_complete_luminaos_enterprise_architecture.py" "ubuntu@${APP_SERVER}:/tmp/build_luminaos_data.py"

Write-Host "Step 2: Run migration..." -ForegroundColor Yellow
ssh -i $KEY -o ConnectTimeout=10 "ubuntu@${APP_SERVER}" "cd /opt/enterprise-ai-platform/database && timeout 60 docker compose exec -T metadata-service alembic upgrade 027" 2>&1

Write-Host "Step 3: Build data..." -ForegroundColor Yellow
ssh -i $KEY -o ConnectTimeout=10 "ubuntu@${APP_SERVER}" "cd /opt/enterprise-ai-platform && timeout 300 docker compose exec -T metadata-service python /tmp/build_luminaos_data.py" 2>&1

Write-Host "Step 4: Sync to Neo4j..." -ForegroundColor Yellow
$result = Invoke-WebRequest -Uri "http://${APP_SERVER}:8005/api/enterprise-architecture/sync/all" -Method POST -TimeoutSec 300 -ErrorAction SilentlyContinue
if ($result) { Write-Host "Sync OK: $($result.StatusCode)" -ForegroundColor Green } else { Write-Host "Sync failed, check manually" -ForegroundColor Yellow }

Write-Host "Done!" -ForegroundColor Green

