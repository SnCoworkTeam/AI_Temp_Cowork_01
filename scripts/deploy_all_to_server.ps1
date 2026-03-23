# 完整部署脚本 (PowerShell版本)：同步代码和数据到服务器并启动服务

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerHost,
    
    [Parameter(Mandatory=$false)]
    [string]$ServerUser = "root",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerPath = "/opt/enterprise-ai-platform",
    
    [Parameter(Mandatory=$false)]
    [string]$BackupDir = "./backups"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "完整部署脚本 - 同步代码和数据到服务器" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Write-Host "部署配置:" -ForegroundColor Yellow
Write-Host "  服务器: ${ServerUser}@${ServerHost}"
Write-Host "  部署路径: ${ServerPath}"
Write-Host ""

# 确认部署
$confirm = Read-Host "确认部署到服务器? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "部署已取消" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "步骤1: 备份服务器数据" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# 创建备份目录
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$BackupFile = "${BackupDir}/backup-$(Get-Date -Format 'yyyyMMdd-HHmmss').tar.gz"

Write-Host "创建服务器数据备份..." -ForegroundColor Yellow

$backupScript = @"
cd ${ServerPath}
docker-compose exec -T postgres pg_dump -U ai_user ai_platform > /tmp/postgres_backup.sql 2>/dev/null || echo "PostgreSQL备份跳过"
echo "备份完成"
"@

ssh ${ServerUser}@${ServerHost} $backupScript

# 下载备份
scp "${ServerUser}@${ServerHost}:/tmp/postgres_backup.sql" "${BackupDir}/postgres_backup.sql" 2>$null
Write-Host "✅ 备份完成" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "步骤2: 同步代码文件" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# 同步docker-compose.yml
Write-Host "同步 docker-compose.yml..." -ForegroundColor Yellow
scp docker-compose.yml "${ServerUser}@${ServerHost}:${ServerPath}/docker-compose.yml"

# 同步.env文件
if (Test-Path .env) {
    Write-Host "同步 .env 文件..." -ForegroundColor Yellow
    scp .env "${ServerUser}@${ServerHost}:${ServerPath}/.env"
}

# 同步数据库代码
Write-Host "同步数据库代码..." -ForegroundColor Yellow
ssh ${ServerUser}@${ServerHost} "mkdir -p ${ServerPath}/database/src/core"
scp database/src/core/neo4j_client.py "${ServerUser}@${ServerHost}:${ServerPath}/database/src/core/"

# 同步迁移脚本
Write-Host "同步迁移脚本..." -ForegroundColor Yellow
ssh ${ServerUser}@${ServerHost} "mkdir -p ${ServerPath}/scripts"
scp scripts/migrate_data_to_neo4j.py "${ServerUser}@${ServerHost}:${ServerPath}/scripts/"
scp scripts/migrate_vectors_to_qdrant.py "${ServerUser}@${ServerHost}:${ServerPath}/scripts/"
scp scripts/test_database_migration.py "${ServerUser}@${ServerHost}:${ServerPath}/scripts/"

# 同步API Gateway代码
Write-Host "同步API Gateway代码..." -ForegroundColor Yellow
ssh ${ServerUser}@${ServerHost} "mkdir -p ${ServerPath}/api-gateway/src/routes"
scp api-gateway/src/routes/neo4j_graph.py "${ServerUser}@${ServerHost}:${ServerPath}/api-gateway/src/routes/"

# 同步Metadata Service代码
Write-Host "同步Metadata Service代码..." -ForegroundColor Yellow
ssh ${ServerUser}@${ServerHost} "mkdir -p ${ServerPath}/metadata-service/src/api"
scp metadata-service/src/api/neo4j_api.py "${ServerUser}@${ServerHost}:${ServerPath}/metadata-service/src/api/"

# 同步前端代码
Write-Host "同步前端代码..." -ForegroundColor Yellow
ssh ${ServerUser}@${ServerHost} "mkdir -p ${ServerPath}/web-ui/src/services"
ssh ${ServerUser}@${ServerHost} "mkdir -p ${ServerPath}/web-ui/src/app/neo4j-graph"
scp web-ui/src/services/neo4jGraphService.ts "${ServerUser}@${ServerHost}:${ServerPath}/web-ui/src/services/"
scp web-ui/src/app/neo4j-graph/page.tsx "${ServerUser}@${ServerHost}:${ServerPath}/web-ui/src/app/neo4j-graph/"

# 更新main.py文件
Write-Host "更新服务主文件..." -ForegroundColor Yellow
$updateScript = @"
cd ${ServerPath}

# 更新api-gateway main.py
if ! grep -q "neo4j_graph" api-gateway/src/main.py; then
    sed -i 's/from \.routes import unified_search, knowledge_graph_monitor, nl_query, assistant, intelligent_monitoring, knowledge_graph, analytics, enterprise_architecture/from .routes import unified_search, knowledge_graph_monitor, nl_query, assistant, intelligent_monitoring, knowledge_graph, analytics, enterprise_architecture, neo4j_graph/' api-gateway/src/main.py
    sed -i '/app.include_router(enterprise_architecture.router)/a app.include_router(neo4j_graph.router)' api-gateway/src/main.py
fi

# 更新metadata-service main.py
if ! grep -q "neo4j_api" metadata-service/src/main.py; then
    sed -i 's/from .api import knowledge_graph, document_entity_linker, knowledge_graph_visualization/from .api import knowledge_graph, document_entity_linker, knowledge_graph_visualization, neo4j_api/' metadata-service/src/main.py
    sed -i '/app.include_router(knowledge_graph_visualization.router/a app.include_router(neo4j_api.router, tags=["Neo4j"])  # 路由已有prefix="/api/neo4j"' metadata-service/src/main.py
fi
"@

ssh ${ServerUser}@${ServerHost} $updateScript

Write-Host "✅ 代码同步完成" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "步骤3: 安装依赖" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

$installScript = @"
cd ${ServerPath}
Write-Host "安装Neo4j Python驱动..."
docker-compose exec -T metadata-service pip install neo4j==5.14.0
docker-compose exec -T api-gateway pip install neo4j==5.14.0
Write-Host "✅ 依赖安装完成"
"@

ssh ${ServerUser}@${ServerHost} $installScript

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "步骤4: 启动Neo4j服务" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

$startScript = @"
cd ${ServerPath}
Write-Host "启动Neo4j服务..."
docker-compose up -d neo4j

Write-Host "等待Neo4j启动..."
Start-Sleep -Seconds 30

Write-Host "检查Neo4j状态..."
docker-compose ps neo4j
docker-compose logs --tail=20 neo4j
"@

ssh ${ServerUser}@${ServerHost} $startScript

Write-Host "✅ Neo4j服务启动完成" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "步骤5: 运行数据迁移" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

Write-Host "⚠️  注意: 数据迁移可能需要较长时间，请耐心等待" -ForegroundColor Yellow
$confirmMigration = Read-Host "继续执行数据迁移? (yes/no)"

if ($confirmMigration -eq "yes") {
    $migrationScript = @"
cd ${ServerPath}

Write-Host "运行知识图谱数据迁移..."
docker-compose exec -T metadata-service python /app/scripts/migrate_data_to_neo4j.py

Write-Host "运行向量数据迁移..."
docker-compose exec -T metadata-service python /app/scripts/migrate_vectors_to_qdrant.py --qdrant-url http://qdrant:6333

Write-Host "✅ 数据迁移完成"
"@
    
    ssh ${ServerUser}@${ServerHost} $migrationScript
} else {
    Write-Host "跳过数据迁移，稍后手动执行" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "步骤6: 重启相关服务" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

$restartScript = @"
cd ${ServerPath}
Write-Host "重启API Gateway..."
docker-compose restart api-gateway

Write-Host "重启Metadata Service..."
docker-compose restart metadata-service

Write-Host "等待服务启动..."
Start-Sleep -Seconds 10

Write-Host "检查服务状态..."
docker-compose ps api-gateway metadata-service neo4j
"@

ssh ${ServerUser}@${ServerHost} $restartScript

Write-Host "✅ 服务重启完成" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "步骤7: 运行测试" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

$testScript = @"
cd ${ServerPath}
Write-Host "运行迁移测试..."
docker-compose exec -T metadata-service python /app/scripts/test_database_migration.py
"@

ssh ${ServerUser}@${ServerHost} $testScript

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "部署完成" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "1. 检查Neo4j Browser: http://${ServerHost}:7474"
Write-Host "2. 检查服务状态: docker-compose ps"
Write-Host "3. 查看日志: docker-compose logs neo4j"
Write-Host "4. 访问前端页面: http://${ServerHost}:3000/neo4j-graph"
Write-Host ""



