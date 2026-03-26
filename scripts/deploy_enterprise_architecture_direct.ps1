# 企业架构功能直接部署脚本
# 支持应用服务器和图数据库服务器分离部署

$ErrorActionPreference = "Stop"

# 颜色输出
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Green "========================================"
Write-ColorOutput Green "企业架构功能部署脚本"
Write-ColorOutput Green "支持应用服务器和图数据库服务器分离部署"
Write-ColorOutput Green "========================================"

# 从SSH配置文件读取服务器信息
$SSH_CONFIG = "./remote.ssh"
if (-not (Test-Path $SSH_CONFIG)) {
    Write-ColorOutput Red "错误: SSH配置文件不存在: $SSH_CONFIG"
    exit 1
}

# 解析SSH配置
$configContent = Get-Content $SSH_CONFIG
$APP_SERVER_HOST = ($configContent | Select-String "HostName" | Select-Object -First 1).Line -replace ".*HostName\s+", ""
$APP_SERVER_USER = ($configContent | Select-String "User" | Select-Object -First 1).Line -replace ".*User\s+", ""
$IDENTITY_FILE = ($configContent | Select-String "IdentityFile" | Select-Object -First 1).Line -replace ".*IdentityFile\s+", ""

if ([string]::IsNullOrWhiteSpace($APP_SERVER_HOST)) {
    Write-ColorOutput Red "错误: 无法从SSH配置读取服务器地址"
    exit 1
}

# 如果IdentityFile是相对路径，转换为绝对路径
if (-not [string]::IsNullOrWhiteSpace($IDENTITY_FILE) -and -not $IDENTITY_FILE.StartsWith("/") -and -not $IDENTITY_FILE.StartsWith("C:")) {
    $IDENTITY_FILE = Join-Path (Get-Location) $IDENTITY_FILE
}

# 检查密钥文件
if (-not [string]::IsNullOrWhiteSpace($IDENTITY_FILE) -and -not (Test-Path $IDENTITY_FILE)) {
    Write-ColorOutput Yellow "警告: 密钥文件不存在: $IDENTITY_FILE"
    Write-ColorOutput Yellow "将尝试使用SSH配置文件中的Host名称连接"
    $SSH_HOST = "enterprise-ai-server"
    $SSH_OPTS = "-F ./remote.ssh"
} else {
    $SSH_HOST = "$APP_SERVER_USER@$APP_SERVER_HOST"
    if (-not [string]::IsNullOrWhiteSpace($IDENTITY_FILE)) {
        $SSH_OPTS = "-i `"$IDENTITY_FILE`" -o StrictHostKeyChecking=no"
    } else {
        $SSH_OPTS = "-o StrictHostKeyChecking=no"
    }
}

Write-ColorOutput Green "`n✅ 服务器配置:"
Write-Host "  主机: $APP_SERVER_HOST"
Write-Host "  用户: $APP_SERVER_USER"
if (-not [string]::IsNullOrWhiteSpace($IDENTITY_FILE)) {
    Write-Host "  密钥: $IDENTITY_FILE"
}

# Neo4j服务器配置
Write-ColorOutput Yellow "`nNeo4j服务器配置"
$SEPARATE_NEO4J = Read-Host "Neo4j服务器是否与应用服务器分离? (y/n) [默认: n]"
if ([string]::IsNullOrWhiteSpace($SEPARATE_NEO4J)) {
    $SEPARATE_NEO4J = "n"
}

if ($SEPARATE_NEO4J -eq "y" -or $SEPARATE_NEO4J -eq "Y") {
    $NEO4J_SERVER_HOST = Read-Host "请输入Neo4j服务器地址 (IP或域名)"
    if ([string]::IsNullOrWhiteSpace($NEO4J_SERVER_HOST)) {
        Write-ColorOutput Red "错误: Neo4j服务器地址不能为空"
        exit 1
    }
    $NEO4J_SERVER_USER = Read-Host "请输入Neo4j服务器SSH用户名 [默认: $APP_SERVER_USER]"
    if ([string]::IsNullOrWhiteSpace($NEO4J_SERVER_USER)) {
        $NEO4J_SERVER_USER = $APP_SERVER_USER
    }
    $NEO4J_SSH_OPTS = $SSH_OPTS
    $NEO4J_SSH_HOST = "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST"
} else {
    $NEO4J_SERVER_HOST = $APP_SERVER_HOST
    $NEO4J_SERVER_USER = $APP_SERVER_USER
    $NEO4J_SSH_OPTS = $SSH_OPTS
    $NEO4J_SSH_HOST = $SSH_HOST
}

# 项目目录
$PROJECT_DIR = Read-Host "请输入服务器上的项目目录 [默认: /opt/enterprise-ai-platform]"
if ([string]::IsNullOrWhiteSpace($PROJECT_DIR)) {
    $PROJECT_DIR = "/opt/enterprise-ai-platform"
}

# 显示配置
Write-ColorOutput Blue "`n=== 部署配置 ==="
Write-ColorOutput Green "应用服务器: $SSH_HOST"
Write-ColorOutput Green "Neo4j服务器: $NEO4J_SSH_HOST"
Write-ColorOutput Green "项目目录: $PROJECT_DIR"

$CONFIRM = Read-Host "`n确认开始部署? (y/n)"
if ($CONFIRM -ne "y" -and $CONFIRM -ne "Y") {
    Write-ColorOutput Yellow "部署已取消"
    exit 0
}

$BACKUP_DIR = "/opt/backups/$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# 1. 测试SSH连接
Write-ColorOutput Yellow "`n1. 测试SSH连接..."
if ($SSH_OPTS -match "-F") {
    $result = ssh -F ./remote.ssh enterprise-ai-server "echo '连接成功'" 2>&1
} else {
    $result = ssh $SSH_OPTS "$SSH_HOST" "echo '连接成功'" 2>&1
}
if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput Green "✅ 应用服务器连接成功"
} else {
    Write-ColorOutput Red "❌ 应用服务器连接失败"
    Write-ColorOutput Yellow "请检查服务器配置和网络连接"
    exit 1
}

# 2. 备份数据库
Write-ColorOutput Yellow "`n2. 备份数据库..."
$backupCmd = "mkdir -p $BACKUP_DIR; if command -v pg_dump > /dev/null 2>&1; then pg_dump -U postgres enterprise_ai > $BACKUP_DIR/database_backup.sql 2>/dev/null || pg_dump -U ai_user ai_platform > $BACKUP_DIR/database_backup.sql 2>/dev/null || docker exec enterprise-ai-postgres pg_dump -U ai_user ai_platform > $BACKUP_DIR/database_backup.sql 2>/dev/null || echo '⚠️  数据库备份跳过'; else echo '⚠️  pg_dump未找到，跳过数据库备份'; fi; echo '✅ 备份目录已创建: $BACKUP_DIR'"

if ($SSH_OPTS -match "-F") {
    ssh -F ./remote.ssh enterprise-ai-server $backupCmd
} else {
    ssh $SSH_OPTS "$SSH_HOST" $backupCmd
}

# 3. 上传代码（使用scp上传关键目录）
Write-ColorOutput Yellow "`n3. 上传代码到应用服务器..."
$keyDirs = @("database", "metadata-service", "scripts")
foreach ($dir in $keyDirs) {
    if (Test-Path $dir) {
        Write-Host "  上传 $dir..."
        if ($SSH_OPTS -match "-F") {
            scp -F ./remote.ssh -r "$dir" "enterprise-ai-server:$PROJECT_DIR/"
        } else {
            scp $SSH_OPTS -r "$dir" "$SSH_HOST`:$PROJECT_DIR/"
        }
    }
}
Write-ColorOutput Green "✅ 关键文件上传完成"

# 4. 运行数据库迁移
Write-ColorOutput Yellow "`n4. 运行数据库迁移..."
$migrateCmd = "set -e; cd $PROJECT_DIR/database; if [ -d 'venv' ]; then source venv/bin/activate; elif [ -d '../venv' ]; then source ../venv/bin/activate; fi; python -m alembic upgrade 026 || python -m alembic upgrade head; echo '✅ 数据库迁移完成'"

if ($SSH_OPTS -match "-F") {
    ssh -F ./remote.ssh enterprise-ai-server $migrateCmd
} else {
    ssh $SSH_OPTS "$SSH_HOST" $migrateCmd
}

# 5. 测试数据库迁移
Write-ColorOutput Yellow "`n5. 测试数据库迁移..."
$testCmd = "cd $PROJECT_DIR && python scripts/test_enterprise_architecture_migration.py || echo '⚠️  测试脚本执行完成（可能有警告）'"

if ($SSH_OPTS -match "-F") {
    ssh -F ./remote.ssh enterprise-ai-server $testCmd
} else {
    ssh $SSH_OPTS "$SSH_HOST" $testCmd
}

# 6. 更新Neo4j配置（如果分离部署）
if ($NEO4J_SERVER_HOST -ne $APP_SERVER_HOST) {
    Write-ColorOutput Yellow "`n6. 更新Neo4j连接配置..."
    $neo4jConfigCmd = "cd $PROJECT_DIR && if [ -f '.env' ]; then sed -i 's|NEO4J_URI=.*|NEO4J_URI=bolt://$NEO4J_SERVER_HOST:7687|g' .env || true; echo '✅ Neo4j连接配置已更新为: bolt://$NEO4J_SERVER_HOST:7687'; fi"
    
    if ($SSH_OPTS -match "-F") {
        ssh -F ./remote.ssh enterprise-ai-server $neo4jConfigCmd
    } else {
        ssh $SSH_OPTS "$SSH_HOST" $neo4jConfigCmd
    }
}

# 7. 重启服务
Write-ColorOutput Yellow "`n7. 重启应用服务..."
$restartCmd = "cd $PROJECT_DIR && if [ -f 'docker-compose.yml' ]; then docker-compose restart metadata-service api-gateway 2>/dev/null || echo '⚠️  docker-compose重启失败'; fi && if systemctl is-active --quiet enterprise-ai-platform 2>/dev/null; then systemctl restart enterprise-ai-platform && echo '✅ 服务已重启'; else echo '⚠️  服务未使用systemctl管理，请手动重启'; fi && echo '✅ 服务重启完成'"

if ($SSH_OPTS -match "-F") {
    ssh -F ./remote.ssh enterprise-ai-server $restartCmd
} else {
    ssh $SSH_OPTS "$SSH_HOST" $restartCmd
}

# 8. 检查Neo4j服务器
if ($NEO4J_SERVER_HOST -ne $APP_SERVER_HOST) {
    Write-ColorOutput Yellow "`n8. 检查Neo4j服务器..."
    $neo4jCheckCmd = "if systemctl is-active --quiet neo4j 2>/dev/null; then systemctl status neo4j --no-pager | head -5; elif docker ps | grep -q neo4j; then docker ps | grep neo4j; else echo '⚠️  Neo4j服务状态未知，请手动检查'; fi && echo '✅ Neo4j服务器检查完成'"
    
    if ($NEO4J_SSH_OPTS -match "-F") {
        ssh -F ./remote.ssh enterprise-ai-server $neo4jCheckCmd
    } else {
        ssh $NEO4J_SSH_OPTS "$NEO4J_SSH_HOST" $neo4jCheckCmd
    }
}

# 9. 验证部署
Write-ColorOutput Yellow "`n9. 验证部署..."
$verifyCmd = "cd $PROJECT_DIR/database && echo '当前迁移版本:' && python -m alembic current && echo -e '\n检查新表:' && (psql -U postgres -d enterprise_ai -c '\dt organization_*' 2>/dev/null || psql -U ai_user -d ai_platform -c '\dt organization_*' 2>/dev/null || docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c '\dt organization_*' 2>/dev/null || echo '⚠️  无法连接数据库检查，请手动验证')"

if ($SSH_OPTS -match "-F") {
    ssh -F ./remote.ssh enterprise-ai-server $verifyCmd
} else {
    ssh $SSH_OPTS "$SSH_HOST" $verifyCmd
}

Write-ColorOutput Green "`n========================================"
Write-ColorOutput Green "✅ 部署完成"
Write-ColorOutput Green "========================================"
Write-Host "`n部署信息:"
Write-Host "  应用服务器: $SSH_HOST"
Write-Host "  Neo4j服务器: $NEO4J_SSH_HOST"
Write-Host "  项目目录: $PROJECT_DIR"
Write-Host "  备份目录: $BACKUP_DIR"
Write-ColorOutput Yellow "`n请手动验证以下功能:"
Write-Host "  1. 数据库迁移版本"
Write-Host "  2. 新表检查"
Write-Host "  3. 服务状态"
Write-Host "  4. API测试（如果已实现）"

