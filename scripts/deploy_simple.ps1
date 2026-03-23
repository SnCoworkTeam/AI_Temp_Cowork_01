# 简单部署脚本 - 分步上传
$APP_KEY = ".\enterprise_ai_platform.pem"
$APP_USER = "ubuntu"
$APP_HOST = "43.143.139.197"
$REMOTE = "/opt/enterprise-ai-platform"

Write-Host "开始上传..." -ForegroundColor Green

# 步骤1: 上传neo4j_client.py
Write-Host "`n[1/6] 上传neo4j_client.py" -ForegroundColor Yellow
scp -i $APP_KEY "database\src\core\neo4j_client.py" "${APP_USER}@${APP_HOST}:${REMOTE}/database/src/core/neo4j_client.py"
Write-Host "完成" -ForegroundColor Green

# 步骤2: 上传同步服务
Write-Host "`n[2/6] 上传同步服务" -ForegroundColor Yellow
scp -i $APP_KEY "metadata-service\src\services\enterprise_architecture_sync_service.py" "${APP_USER}@${APP_HOST}:${REMOTE}/metadata-service/src/services/enterprise_architecture_sync_service.py"
Write-Host "完成" -ForegroundColor Green

# 步骤3: 上传同步API
Write-Host "`n[3/6] 上传同步API" -ForegroundColor Yellow
scp -i $APP_KEY "metadata-service\src\api\enterprise_architecture_sync.py" "${APP_USER}@${APP_HOST}:${REMOTE}/metadata-service/src/api/enterprise_architecture_sync.py"
Write-Host "完成" -ForegroundColor Green

# 步骤4: 上传main.py
Write-Host "`n[4/6] 上传main.py" -ForegroundColor Yellow
scp -i $APP_KEY "metadata-service\src\main.py" "${APP_USER}@${APP_HOST}:${REMOTE}/metadata-service/src/main.py"
Write-Host "完成" -ForegroundColor Green

# 步骤5: 上传初始化脚本
Write-Host "`n[5/6] 上传初始化脚本" -ForegroundColor Yellow
scp -i $APP_KEY "scripts\init_enterprise_architecture_data.py" "${APP_USER}@${APP_HOST}:${REMOTE}/scripts/init_enterprise_architecture_data.py"
Write-Host "完成" -ForegroundColor Green

# 步骤6: 上传迁移脚本
Write-Host "`n[6/6] 上传迁移脚本" -ForegroundColor Yellow
scp -i $APP_KEY "scripts\migrate_enterprise_architecture_to_neo4j.py" "${APP_USER}@${APP_HOST}:${REMOTE}/scripts/migrate_enterprise_architecture_to_neo4j.py"
Write-Host "完成" -ForegroundColor Green

Write-Host "`n✅ 所有文件上传完成！" -ForegroundColor Green

