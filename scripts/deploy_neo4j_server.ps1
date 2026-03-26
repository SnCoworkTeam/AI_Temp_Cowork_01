# Neo4j图数据库服务器部署脚本

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
Write-ColorOutput Green "Neo4j图数据库服务器部署脚本"
Write-ColorOutput Green "========================================"

# 检查Neo4j密钥文件
$NEO4J_KEY = "./Neo4j.pem"
if (-not (Test-Path $NEO4J_KEY)) {
    Write-ColorOutput Yellow "警告: Neo4j密钥文件不存在: $NEO4J_KEY"
    Write-ColorOutput Yellow "将使用应用服务器配置"
    $NEO4J_KEY = "./enterprise_ai_platform.pem"
}

# 配置Neo4j服务器
Write-ColorOutput Blue "`n=== 配置Neo4j服务器信息 ==="
$NEO4J_SERVER_HOST = Read-Host "请输入Neo4j服务器地址 (IP或域名)"
if ([string]::IsNullOrWhiteSpace($NEO4J_SERVER_HOST)) {
    Write-ColorOutput Red "错误: Neo4j服务器地址不能为空"
    exit 1
}

$NEO4J_SERVER_USER = Read-Host "请输入Neo4j服务器SSH用户名 [默认: ubuntu]"
if ([string]::IsNullOrWhiteSpace($NEO4J_SERVER_USER)) {
    $NEO4J_SERVER_USER = "ubuntu"
}

$NEO4J_PROJECT_DIR = Read-Host "请输入Neo4j服务器上的项目目录 [默认: /opt/neo4j-enterprise-ai]"
if ([string]::IsNullOrWhiteSpace($NEO4J_PROJECT_DIR)) {
    $NEO4J_PROJECT_DIR = "/opt/neo4j-enterprise-ai"
}

# 显示配置
Write-ColorOutput Blue "`n=== 部署配置 ==="
Write-ColorOutput Green "Neo4j服务器: $NEO4J_SERVER_USER@$NEO4J_SERVER_HOST"
Write-ColorOutput Green "项目目录: $NEO4J_PROJECT_DIR"
Write-ColorOutput Green "密钥文件: $NEO4J_KEY"

$CONFIRM = Read-Host "`n确认开始部署Neo4j服务器? (y/n)"
if ($CONFIRM -ne "y" -and $CONFIRM -ne "Y") {
    Write-ColorOutput Yellow "部署已取消"
    exit 0
}

# 1. 测试SSH连接
Write-ColorOutput Yellow "`n1. 测试SSH连接..."
$SSH_OPTS = "-i `"$NEO4J_KEY`" -o StrictHostKeyChecking=no"
$SSH_HOST = "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST"

$result = ssh $SSH_OPTS "$SSH_HOST" "echo '连接成功'" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput Green "✅ Neo4j服务器连接成功"
} else {
    Write-ColorOutput Red "❌ Neo4j服务器连接失败"
    Write-ColorOutput Yellow "请检查服务器配置和网络连接"
    exit 1
}

# 2. 检查Docker和Docker Compose
Write-ColorOutput Yellow "`n2. 检查Docker环境..."
$dockerCheck = ssh $SSH_OPTS "$SSH_HOST" "command -v docker > /dev/null 2>&1 && docker --version && command -v docker-compose > /dev/null 2>&1 && docker-compose --version || echo 'Docker未安装'"
Write-Host $dockerCheck

# 3. 创建项目目录
Write-ColorOutput Yellow "`n3. 创建项目目录..."
ssh $SSH_OPTS "$SSH_HOST" "mkdir -p $NEO4J_PROJECT_DIR && echo '✅ 项目目录已创建: $NEO4J_PROJECT_DIR'"

# 4. 上传Neo4j配置文件
Write-ColorOutput Yellow "`n4. 上传Neo4j配置文件..."
$neo4jFiles = @(
    "docker-compose.neo4j-standalone.yml",
    "neo4j-docker-compose.yml"
)

foreach ($file in $neo4jFiles) {
    if (Test-Path $file) {
        Write-Host "  上传 $file..."
        scp $SSH_OPTS "$file" "$SSH_HOST`:$NEO4J_PROJECT_DIR/"
    }
}

# 上传docker-compose.yml（如果存在）
if (Test-Path "docker-compose.yml") {
    Write-Host "  上传 docker-compose.yml..."
    scp $SSH_OPTS "docker-compose.yml" "$SSH_HOST`:$NEO4J_PROJECT_DIR/"
}

# 5. 创建.env文件（如果不存在）
Write-ColorOutput Yellow "`n5. 配置Neo4j环境变量..."
$envContent = @"
# Neo4j配置
NEO4J_PASSWORD=${NEO4J_PASSWORD:-neo4j_password}
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
NEO4J_HTTPS_PORT=7473
"@

$envFile = [System.IO.Path]::GetTempFileName()
$envContent | Out-File -FilePath $envFile -Encoding UTF8
scp $SSH_OPTS $envFile "$SSH_HOST`:$NEO4J_PROJECT_DIR/.env"
Remove-Item $envFile

Write-ColorOutput Green "✅ 环境变量文件已创建"

# 6. 停止现有Neo4j服务（如果存在）
Write-ColorOutput Yellow "`n6. 停止现有Neo4j服务..."
ssh $SSH_OPTS "$SSH_HOST" @"
cd $NEO4J_PROJECT_DIR
if [ -f 'docker-compose.neo4j-standalone.yml' ]; then
    docker-compose -f docker-compose.neo4j-standalone.yml down 2>/dev/null || echo '没有运行中的Neo4j服务'
elif [ -f 'neo4j-docker-compose.yml' ]; then
    docker-compose -f neo4j-docker-compose.yml down 2>/dev/null || echo '没有运行中的Neo4j服务'
else
    docker stop enterprise-ai-neo4j-standalone 2>/dev/null || echo '没有运行中的Neo4j容器'
fi
echo '✅ 现有服务已停止'
"@

# 7. 启动Neo4j服务
Write-ColorOutput Yellow "`n7. 启动Neo4j服务..."
ssh $SSH_OPTS "$SSH_HOST" @"
cd $NEO4J_PROJECT_DIR
if [ -f 'docker-compose.neo4j-standalone.yml' ]; then
    docker-compose -f docker-compose.neo4j-standalone.yml up -d
    echo '✅ Neo4j服务已启动 (使用 docker-compose.neo4j-standalone.yml)'
elif [ -f 'neo4j-docker-compose.yml' ]; then
    docker-compose -f neo4j-docker-compose.yml up -d
    echo '✅ Neo4j服务已启动 (使用 neo4j-docker-compose.yml)'
else
    echo '❌ 未找到Neo4j配置文件'
    exit 1
fi
"@

# 8. 等待服务启动
Write-ColorOutput Yellow "`n8. 等待Neo4j服务启动..."
Start-Sleep -Seconds 10

# 9. 检查Neo4j服务状态
Write-ColorOutput Yellow "`n9. 检查Neo4j服务状态..."
ssh $SSH_OPTS "$SSH_HOST" @"
cd $NEO4J_PROJECT_DIR
echo 'Docker容器状态:'
docker ps | grep neo4j || echo '未找到Neo4j容器'

echo -e '\nNeo4j服务健康检查:'
docker exec enterprise-ai-neo4j-standalone cypher-shell -u neo4j -p `${NEO4J_PASSWORD:-neo4j_password} 'RETURN 1' 2>/dev/null && echo '✅ Neo4j服务运行正常' || echo '⚠️  Neo4j服务可能还在启动中，请稍后检查'

echo -e '\nNeo4j端口监听:'
netstat -tlnp | grep -E '7474|7687' || ss -tlnp | grep -E '7474|7687' || echo '端口检查完成'
"@

# 10. 显示连接信息
Write-ColorOutput Green "`n========================================"
Write-ColorOutput Green "✅ Neo4j服务器部署完成"
Write-ColorOutput Green "========================================"
Write-Host "`nNeo4j连接信息:"
Write-Host "  HTTP Web界面: http://$NEO4J_SERVER_HOST`:7474"
Write-Host "  Bolt连接: bolt://$NEO4J_SERVER_HOST`:7687"
Write-Host "  用户名: neo4j"
Write-Host "  密码: (请查看服务器上的 .env 文件)"
Write-Host "`n项目目录: $NEO4J_PROJECT_DIR"
Write-ColorOutput Yellow "`n请手动验证以下功能:"
Write-Host "  1. 访问Web界面: http://$NEO4J_SERVER_HOST`:7474"
Write-Host "  2. 测试Bolt连接: bolt://$NEO4J_SERVER_HOST`:7687"
Write-Host "  3. 检查服务日志: ssh到服务器执行 'docker logs enterprise-ai-neo4j-standalone'"

