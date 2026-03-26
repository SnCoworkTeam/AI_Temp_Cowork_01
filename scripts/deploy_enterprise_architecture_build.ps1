# 企业架构数据构建和部署脚本
# 部署到应用服务器和图数据库服务器

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "🚀 企业架构数据构建和部署" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 服务器配置
$APP_SERVER_HOST = "43.143.139.197"
$APP_SERVER_USER = "ubuntu"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_PATH = "/opt/enterprise-ai-platform"

$NEO4J_SERVER_HOST = "43.143.90.179"
$NEO4J_SERVER_USER = "ubuntu"
$NEO4J_SERVER_KEY = ".\Neo4j.pem"
$NEO4J_SERVER_PATH = "/opt/enterprise-ai-platform"

# 检查密钥文件
if (-not (Test-Path $APP_SERVER_KEY)) {
    Write-Host "❌ 应用服务器密钥文件不存在: $APP_SERVER_KEY" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $NEO4J_SERVER_KEY)) {
    Write-Host "❌ Neo4j服务器密钥文件不存在: $NEO4J_SERVER_KEY" -ForegroundColor Red
    exit 1
}

Write-Host "`n服务器配置:" -ForegroundColor Cyan
Write-Host "  应用服务器: $APP_SERVER_USER@$APP_SERVER_HOST"
Write-Host "  Neo4j服务器: $NEO4J_SERVER_USER@$NEO4J_SERVER_HOST"

# 1. 上传数据同步服务
Write-Host "`n1. 上传数据同步服务..." -ForegroundColor Yellow
$syncServiceFile = "metadata-service\src\services\enterprise_architecture_sync_service.py"
scp -i $APP_SERVER_KEY "$syncServiceFile" "${APP_SERVER_USER}@${APP_SERVER_HOST}:${APP_SERVER_PATH}/metadata-service/src/services/enterprise_architecture_sync_service.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 数据同步服务上传成功" -ForegroundColor Green
} else {
    Write-Host "❌ 数据同步服务上传失败" -ForegroundColor Red
    exit 1
}

# 2. 上传同步API
Write-Host "`n2. 上传同步API..." -ForegroundColor Yellow
$syncApiFile = "metadata-service\src\api\enterprise_architecture_sync.py"
scp -i $APP_SERVER_KEY "$syncApiFile" "${APP_SERVER_USER}@${APP_SERVER_HOST}:${APP_SERVER_PATH}/metadata-service/src/api/enterprise_architecture_sync.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 同步API上传成功" -ForegroundColor Green
} else {
    Write-Host "❌ 同步API上传失败" -ForegroundColor Red
    exit 1
}

# 3. 上传Neo4j客户端更新
Write-Host "`n3. 上传Neo4j客户端更新..." -ForegroundColor Yellow
$neo4jClientFile = "database\src\core\neo4j_client.py"
scp -i $APP_SERVER_KEY "$neo4jClientFile" "${APP_SERVER_USER}@${APP_SERVER_HOST}:${APP_SERVER_PATH}/database/src/core/neo4j_client.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Neo4j客户端上传成功" -ForegroundColor Green
} else {
    Write-Host "❌ Neo4j客户端上传失败" -ForegroundColor Red
    exit 1
}

# 4. 上传初始化脚本
Write-Host "`n4. 上传初始化脚本..." -ForegroundColor Yellow
$initScriptFile = "scripts\init_enterprise_architecture_data.py"
scp -i $APP_SERVER_KEY "$initScriptFile" "${APP_SERVER_USER}@${APP_SERVER_HOST}:${APP_SERVER_PATH}/scripts/init_enterprise_architecture_data.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 初始化脚本上传成功" -ForegroundColor Green
} else {
    Write-Host "❌ 初始化脚本上传失败" -ForegroundColor Red
    exit 1
}

# 5. 上传迁移脚本
Write-Host "`n5. 上传迁移脚本..." -ForegroundColor Yellow
$migrateScriptFile = "scripts\migrate_enterprise_architecture_to_neo4j.py"
scp -i $APP_SERVER_KEY "$migrateScriptFile" "${APP_SERVER_USER}@${APP_SERVER_HOST}:${APP_SERVER_PATH}/scripts/migrate_enterprise_architecture_to_neo4j.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 迁移脚本上传成功" -ForegroundColor Green
} else {
    Write-Host "❌ 迁移脚本上传失败" -ForegroundColor Red
    exit 1
}

# 6. 更新main.py注册同步API
Write-Host "`n6. 更新main.py注册同步API..." -ForegroundColor Yellow
$mainPyFile = "metadata-service\src\main.py"
scp -i $APP_SERVER_KEY "$mainPyFile" "${APP_SERVER_USER}@${APP_SERVER_HOST}:${APP_SERVER_PATH}/metadata-service/src/main.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ main.py更新成功" -ForegroundColor Green
} else {
    Write-Host "❌ main.py更新失败" -ForegroundColor Red
    exit 1
}

# 7. 重启metadata-service
Write-Host "`n7. 重启metadata-service..." -ForegroundColor Yellow
$restartCmd = "cd $APP_SERVER_PATH && docker compose restart metadata-service"
ssh -i $APP_SERVER_KEY "$APP_SERVER_USER@$APP_SERVER_HOST" $restartCmd
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ metadata-service重启成功" -ForegroundColor Green
} else {
    Write-Host "❌ metadata-service重启失败" -ForegroundColor Red
    exit 1
}

# 8. 等待服务启动
Write-Host "`n8. 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 9. 检查服务状态
Write-Host "`n9. 检查服务状态..." -ForegroundColor Yellow
$statusCmd = "cd $APP_SERVER_PATH && docker compose ps metadata-service"
ssh -i $APP_SERVER_KEY "$APP_SERVER_USER@$APP_SERVER_HOST" $statusCmd

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ 企业架构数据构建部署完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host "`n下一步操作:" -ForegroundColor Cyan
Write-Host "  1. 初始化数据: 运行 init_enterprise_architecture_data.py" -ForegroundColor White
Write-Host "  2. 迁移数据: 运行 migrate_enterprise_architecture_to_neo4j.py" -ForegroundColor White
Write-Host "  3. 或通过API: POST /api/enterprise-architecture/sync/all" -ForegroundColor White

