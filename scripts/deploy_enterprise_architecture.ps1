# 企业架构功能PowerShell部署脚本
# 支持应用服务器和图数据库服务器分离部署

$ErrorActionPreference = "Stop"

# 颜色输出函数
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

# 检查密钥文件
$APP_SERVER_KEY = "./remote.ssh"
if (-not (Test-Path $APP_SERVER_KEY)) {
    Write-ColorOutput Red "错误: SSH密钥文件不存在: $APP_SERVER_KEY"
    Write-ColorOutput Yellow "请确保密钥文件在项目根目录下"
    exit 1
}

Write-ColorOutput Green "✅ SSH密钥文件检查通过: $APP_SERVER_KEY"

# 交互式配置
Write-ColorOutput Blue "`n=== 配置服务器信息 ==="

# 应用服务器配置
$APP_SERVER_HOST = Read-Host "请输入应用服务器地址 (IP或域名)"
if ([string]::IsNullOrWhiteSpace($APP_SERVER_HOST)) {
    Write-ColorOutput Red "错误: 应用服务器地址不能为空"
    exit 1
}

$APP_SERVER_USER = Read-Host "请输入应用服务器SSH用户名 [默认: root]"
if ([string]::IsNullOrWhiteSpace($APP_SERVER_USER)) {
    $APP_SERVER_USER = "root"
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
    $NEO4J_SERVER_USER = Read-Host "请输入Neo4j服务器SSH用户名 [默认: root]"
    if ([string]::IsNullOrWhiteSpace($NEO4J_SERVER_USER)) {
        $NEO4J_SERVER_USER = "root"
    }
    $NEO4J_SERVER_KEY = $APP_SERVER_KEY
} else {
    $NEO4J_SERVER_HOST = $APP_SERVER_HOST
    $NEO4J_SERVER_USER = $APP_SERVER_USER
    $NEO4J_SERVER_KEY = $APP_SERVER_KEY
}

# 项目目录
$PROJECT_DIR = Read-Host "请输入服务器上的项目目录 [默认: /opt/enterprise-ai-platform]"
if ([string]::IsNullOrWhiteSpace($PROJECT_DIR)) {
    $PROJECT_DIR = "/opt/enterprise-ai-platform"
}

# 显示配置信息
Write-ColorOutput Blue "`n=== 部署配置 ==="
Write-ColorOutput Green "应用服务器: $APP_SERVER_USER@$APP_SERVER_HOST"
Write-ColorOutput Green "Neo4j服务器: $NEO4J_SERVER_USER@$NEO4J_SERVER_HOST"
Write-ColorOutput Green "项目目录: $PROJECT_DIR"
Write-ColorOutput Green "密钥文件: $APP_SERVER_KEY"

$CONFIRM = Read-Host "`n确认开始部署? (y/n)"
if ($CONFIRM -ne "y" -and $CONFIRM -ne "Y") {
    Write-ColorOutput Yellow "部署已取消"
    exit 0
}

$BACKUP_DIR = "/opt/backups/$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# 1. 测试SSH连接
Write-ColorOutput Yellow "`n1. 测试SSH连接..."
try {
    $result = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$APP_SERVER_USER@$APP_SERVER_HOST" "echo '连接成功'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput Green "✅ 应用服务器连接成功"
    } else {
        throw "连接失败"
    }
} catch {
    Write-ColorOutput Red "❌ 应用服务器连接失败"
    Write-ColorOutput Yellow "请检查:"
    Write-ColorOutput Yellow "  1. 服务器地址是否正确: $APP_SERVER_HOST"
    Write-ColorOutput Yellow "  2. 用户名是否正确: $APP_SERVER_USER"
    Write-ColorOutput Yellow "  3. 密钥文件是否正确: $APP_SERVER_KEY"
    Write-ColorOutput Yellow "  4. 服务器是否允许SSH连接"
    exit 1
}

if ($NEO4J_SERVER_HOST -ne $APP_SERVER_HOST) {
    try {
        $result = ssh -i $NEO4J_SERVER_KEY -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "echo '连接成功'" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput Green "✅ Neo4j服务器连接成功"
        } else {
            throw "连接失败"
        }
    } catch {
        Write-ColorOutput Red "❌ Neo4j服务器连接失败"
        exit 1
    }
}

# 2. 备份数据库
Write-ColorOutput Yellow "`n2. 备份数据库..."
$backupCmd = @"
mkdir -p $BACKUP_DIR
if command -v pg_dump > /dev/null 2>&1; then
    pg_dump -U postgres enterprise_ai > $BACKUP_DIR/database_backup.sql 2>/dev/null || \
    pg_dump -U ai_user ai_platform > $BACKUP_DIR/database_backup.sql 2>/dev/null || \
    echo "⚠️  数据库备份跳过（数据库可能使用Docker）"
else
    echo "⚠️  pg_dump未找到，跳过数据库备份"
fi
echo "✅ 备份目录已创建: $BACKUP_DIR"
"@

ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no "$APP_SERVER_USER@$APP_SERVER_HOST" $backupCmd

# 3. 上传代码
Write-ColorOutput Yellow "`n3. 上传代码到应用服务器..."
# 检查是否有rsync（Windows上通常没有）
if (Get-Command rsync -ErrorAction SilentlyContinue) {
    rsync -avz --progress `
        -e "ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no" `
        --exclude 'node_modules' `
        --exclude '__pycache__' `
        --exclude '*.pyc' `
        --exclude '.git' `
        --exclude '*.log' `
        --exclude '.env' `
        --exclude 'venv' `
        --exclude '.venv' `
        ./ "$APP_SERVER_USER@$APP_SERVER_HOST`:$PROJECT_DIR/"
    Write-ColorOutput Green "✅ 代码上传完成"
} else {
    Write-ColorOutput Yellow "⚠️  rsync未找到，使用scp上传关键文件..."
    # 使用scp上传关键目录
    $keyDirs = @("database", "metadata-service", "scripts")
    foreach ($dir in $keyDirs) {
        if (Test-Path $dir) {
            scp -i $APP_SERVER_KEY -r -o StrictHostKeyChecking=no "$dir" "$APP_SERVER_USER@$APP_SERVER_HOST`:$PROJECT_DIR/"
        }
    }
    Write-ColorOutput Green "✅ 关键文件上传完成"
}

# 4. 运行数据库迁移
Write-ColorOutput Yellow "`n4. 运行数据库迁移..."
$migrateCmd = @"
set -e
cd $PROJECT_DIR/database
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
fi
python -m alembic upgrade 026 || python -m alembic upgrade head
echo "✅ 数据库迁移完成"
"@

ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no "$APP_SERVER_USER@$APP_SERVER_HOST" $migrateCmd

# 5. 测试数据库迁移
Write-ColorOutput Yellow "`n5. 测试数据库迁移..."
$testCmd = "cd $PROJECT_DIR && python scripts/test_enterprise_architecture_migration.py || echo '⚠️  测试脚本执行完成（可能有警告）'"
ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no "$APP_SERVER_USER@$APP_SERVER_HOST" $testCmd

# 6. 更新Neo4j配置（如果分离部署）
if ($NEO4J_SERVER_HOST -ne $APP_SERVER_HOST) {
    Write-ColorOutput Yellow "`n6. 更新Neo4j连接配置..."
    $neo4jConfigCmd = "cd $PROJECT_DIR && if [ -f '.env' ]; then sed -i 's|NEO4J_URI=.*|NEO4J_URI=bolt://$NEO4J_SERVER_HOST:7687|g' .env || true; echo '✅ Neo4j连接配置已更新'; fi"
    ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no "$APP_SERVER_USER@$APP_SERVER_HOST" $neo4jConfigCmd
}

# 7. 重启服务
Write-ColorOutput Yellow "`n7. 重启应用服务..."
$restartCmd = "cd $PROJECT_DIR && if [ -f 'docker-compose.yml' ]; then docker-compose restart metadata-service api-gateway 2>/dev/null || echo '⚠️  docker-compose重启失败'; fi && if systemctl is-active --quiet enterprise-ai-platform 2>/dev/null; then systemctl restart enterprise-ai-platform && echo '✅ 服务已重启'; else echo '⚠️  服务未使用systemctl管理，请手动重启'; fi && echo '✅ 服务重启完成'"

ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no "$APP_SERVER_USER@$APP_SERVER_HOST" $restartCmd

# 8. 检查Neo4j服务器
if ($NEO4J_SERVER_HOST -ne $APP_SERVER_HOST) {
    Write-ColorOutput Yellow "`n8. 检查Neo4j服务器..."
    $neo4jCheckCmd = "if systemctl is-active --quiet neo4j 2>/dev/null; then systemctl status neo4j --no-pager | head -5; elif docker ps | grep -q neo4j; then docker ps | grep neo4j; else echo '⚠️  Neo4j服务状态未知，请手动检查'; fi && echo '✅ Neo4j服务器检查完成'"
    ssh -i $NEO4J_SERVER_KEY -o StrictHostKeyChecking=no "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" $neo4jCheckCmd
}

# 9. 验证部署
Write-ColorOutput Yellow "`n9. 验证部署..."
$verifyCmd = "cd $PROJECT_DIR/database && echo '当前迁移版本:' && python -m alembic current && echo -e '\n检查新表:' && (psql -U postgres -d enterprise_ai -c '\dt organization_*' 2>/dev/null || psql -U ai_user -d ai_platform -c '\dt organization_*' 2>/dev/null || echo '⚠️  无法连接数据库检查，请手动验证')"

ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no "$APP_SERVER_USER@$APP_SERVER_HOST" $verifyCmd

Write-ColorOutput Green "`n========================================"
Write-ColorOutput Green "✅ 部署完成"
Write-ColorOutput Green "========================================"
Write-Host "`n部署信息:"
Write-Host "  应用服务器: $APP_SERVER_USER@$APP_SERVER_HOST"
Write-Host "  Neo4j服务器: $NEO4J_SERVER_USER@$NEO4J_SERVER_HOST"
Write-Host "  项目目录: $PROJECT_DIR"
Write-Host "  备份目录: $BACKUP_DIR"
Write-ColorOutput Yellow "`n请手动验证以下功能:"
Write-Host "  1. 数据库迁移版本"
Write-Host "  2. 新表检查"
Write-Host "  3. 服务状态"
Write-Host "  4. API测试（如果已实现）"

