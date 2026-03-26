# 数据库架构优化部署脚本 (PowerShell版本)
# 用于将本地测试通过的配置部署到服务器

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
Write-Host "数据库架构优化部署脚本" -ForegroundColor Green
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

# 备份PostgreSQL
$backupScript = @"
cd ${ServerPath}
docker-compose exec -T postgres pg_dump -U ai_user ai_platform > /tmp/postgres_backup.sql
echo "PostgreSQL备份完成"
"@

ssh ${ServerUser}@${ServerHost} $backupScript

# 下载备份
scp "${ServerUser}@${ServerHost}:/tmp/postgres_backup.sql" "${BackupDir}/postgres_backup.sql"
Write-Host "✅ 备份完成: ${BackupFile}" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "步骤2: 上传配置文件" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# 上传docker-compose.yml
Write-Host "上传 docker-compose.yml..." -ForegroundColor Yellow
scp docker-compose.yml "${ServerUser}@${ServerHost}:${ServerPath}/docker-compose.yml"

# 上传.env文件（如果存在）
if (Test-Path .env) {
    Write-Host "上传 .env 文件..." -ForegroundColor Yellow
    scp .env "${ServerUser}@${ServerHost}:${ServerPath}/.env"
}

# 上传迁移脚本
Write-Host "上传迁移脚本..." -ForegroundColor Yellow
ssh ${ServerUser}@${ServerHost} "mkdir -p ${ServerPath}/scripts"
scp scripts/migrate_data_to_neo4j.py "${ServerUser}@${ServerHost}:${ServerPath}/scripts/"
scp scripts/migrate_vectors_to_qdrant.py "${ServerUser}@${ServerHost}:${ServerPath}/scripts/"
scp scripts/test_database_migration.py "${ServerUser}@${ServerHost}:${ServerPath}/scripts/"

# 上传Neo4j客户端
Write-Host "上传Neo4j客户端..." -ForegroundColor Yellow
ssh ${ServerUser}@${ServerHost} "mkdir -p ${ServerPath}/database/src/core"
scp database/src/core/neo4j_client.py "${ServerUser}@${ServerHost}:${ServerPath}/database/src/core/"

Write-Host "✅ 文件上传完成" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "步骤3: 安装依赖" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

$installScript = @"
cd ${ServerPath}
Write-Host "安装Neo4j Python驱动..."
docker-compose exec -T metadata-service pip install neo4j==5.14.0
docker-compose exec -T knowledge-base pip install neo4j==5.14.0
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
docker-compose logs --tail=50 neo4j
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
Write-Host "步骤6: 运行测试" -ForegroundColor Green
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
Write-Host "4. 运行测试: python scripts/test_database_migration.py"
Write-Host ""



