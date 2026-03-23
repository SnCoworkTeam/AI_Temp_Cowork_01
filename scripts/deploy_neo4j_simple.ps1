# Neo4j图数据库服务器部署脚本（简化版）

Write-Host "========================================" -ForegroundColor Green
Write-Host "Neo4j图数据库服务器部署" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 配置Neo4j服务器
Write-Host "`n配置Neo4j服务器信息:" -ForegroundColor Yellow
$NEO4J_SERVER_HOST = Read-Host "请输入Neo4j服务器地址 (IP或域名)"
if ([string]::IsNullOrWhiteSpace($NEO4J_SERVER_HOST)) {
    Write-Host "错误: Neo4j服务器地址不能为空" -ForegroundColor Red
    exit 1
}

$NEO4J_SERVER_USER = Read-Host "请输入Neo4j服务器SSH用户名 [默认: ubuntu]"
if ([string]::IsNullOrWhiteSpace($NEO4J_SERVER_USER)) {
    $NEO4J_SERVER_USER = "ubuntu"
}

# 检查密钥文件
$NEO4J_KEY = "./Neo4j.pem"
if (-not (Test-Path $NEO4J_KEY)) {
    Write-Host "警告: Neo4j密钥文件不存在，使用应用服务器密钥" -ForegroundColor Yellow
    $NEO4J_KEY = "./enterprise_ai_platform.pem"
}

if (-not (Test-Path $NEO4J_KEY)) {
    Write-Host "错误: 密钥文件不存在: $NEO4J_KEY" -ForegroundColor Red
    exit 1
}

$NEO4J_PROJECT_DIR = Read-Host "请输入Neo4j服务器上的项目目录 [默认: /opt/neo4j-enterprise-ai]"
if ([string]::IsNullOrWhiteSpace($NEO4J_PROJECT_DIR)) {
    $NEO4J_PROJECT_DIR = "/opt/neo4j-enterprise-ai"
}

Write-Host "`n部署配置:" -ForegroundColor Blue
Write-Host "  Neo4j服务器: $NEO4J_SERVER_USER@$NEO4J_SERVER_HOST"
Write-Host "  项目目录: $NEO4J_PROJECT_DIR"
Write-Host "  密钥文件: $NEO4J_KEY"

$CONFIRM = Read-Host "`n确认开始部署? (y/n)"
if ($CONFIRM -ne "y" -and $CONFIRM -ne "Y") {
    Write-Host "部署已取消" -ForegroundColor Yellow
    exit 0
}

# 1. 测试SSH连接
Write-Host "`n1. 测试SSH连接..." -ForegroundColor Yellow
$SSH_CMD = "ssh -i `"$NEO4J_KEY`" -o StrictHostKeyChecking=no $NEO4J_SERVER_USER@$NEO4J_SERVER_HOST"
$result = & ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "echo '连接成功'" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Neo4j服务器连接成功" -ForegroundColor Green
} else {
    Write-Host "❌ Neo4j服务器连接失败" -ForegroundColor Red
    Write-Host "请检查服务器配置和网络连接" -ForegroundColor Yellow
    exit 1
}

# 2. 检查Docker
Write-Host "`n2. 检查Docker环境..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "docker --version && docker-compose --version"

# 3. 创建项目目录
Write-Host "`n3. 创建项目目录..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "mkdir -p $NEO4J_PROJECT_DIR && echo '✅ 项目目录已创建: $NEO4J_PROJECT_DIR'"

# 4. 上传Neo4j配置文件
Write-Host "`n4. 上传Neo4j配置文件..." -ForegroundColor Yellow
if (Test-Path "docker-compose.neo4j-standalone.yml") {
    Write-Host "  上传 docker-compose.neo4j-standalone.yml..."
    scp -i $NEO4J_KEY -o StrictHostKeyChecking=no "docker-compose.neo4j-standalone.yml" "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST`:$NEO4J_PROJECT_DIR/"
}

if (Test-Path "neo4j-docker-compose.yml") {
    Write-Host "  上传 neo4j-docker-compose.yml..."
    scp -i $NEO4J_KEY -o StrictHostKeyChecking=no "neo4j-docker-compose.yml" "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST`:$NEO4J_PROJECT_DIR/"
}

# 5. 创建.env文件
Write-Host "`n5. 配置Neo4j环境变量..." -ForegroundColor Yellow
$NEO4J_PASSWORD = Read-Host "请输入Neo4j密码 [默认: neo4j_password]"
if ([string]::IsNullOrWhiteSpace($NEO4J_PASSWORD)) {
    $NEO4J_PASSWORD = "neo4j_password"
}

$envContent = @"
NEO4J_PASSWORD=$NEO4J_PASSWORD
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
NEO4J_HTTPS_PORT=7473
"@

$envFile = [System.IO.Path]::GetTempFileName()
$envContent | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline
scp -i $NEO4J_KEY -o StrictHostKeyChecking=no $envFile "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST`:$NEO4J_PROJECT_DIR/.env"
Remove-Item $envFile
Write-Host "✅ 环境变量文件已创建" -ForegroundColor Green

# 6. 停止现有Neo4j服务
Write-Host "`n6. 停止现有Neo4j服务..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "cd $NEO4J_PROJECT_DIR && if [ -f 'docker-compose.neo4j-standalone.yml' ]; then docker-compose -f docker-compose.neo4j-standalone.yml down 2>/dev/null || echo '没有运行中的Neo4j服务'; elif [ -f 'neo4j-docker-compose.yml' ]; then docker-compose -f neo4j-docker-compose.yml down 2>/dev/null || echo '没有运行中的Neo4j服务'; else docker stop enterprise-ai-neo4j-standalone 2>/dev/null || echo '没有运行中的Neo4j容器'; fi; echo '✅ 现有服务已停止'"

# 7. 启动Neo4j服务
Write-Host "`n7. 启动Neo4j服务..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "cd $NEO4J_PROJECT_DIR && if [ -f 'docker-compose.neo4j-standalone.yml' ]; then docker-compose -f docker-compose.neo4j-standalone.yml up -d && echo '✅ Neo4j服务已启动'; elif [ -f 'neo4j-docker-compose.yml' ]; then docker-compose -f neo4j-docker-compose.yml up -d && echo '✅ Neo4j服务已启动'; else echo '❌ 未找到Neo4j配置文件'; exit 1; fi"

# 8. 等待服务启动
Write-Host "`n8. 等待Neo4j服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 9. 检查Neo4j服务状态
Write-Host "`n9. 检查Neo4j服务状态..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "cd $NEO4J_PROJECT_DIR && echo 'Docker容器状态:' && docker ps | grep neo4j && echo '' && echo 'Neo4j端口监听:' && (netstat -tlnp 2>/dev/null | grep -E '7474|7687' || ss -tlnp 2>/dev/null | grep -E '7474|7687' || echo '端口检查完成')"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ Neo4j服务器部署完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nNeo4j连接信息:" -ForegroundColor Cyan
Write-Host "  HTTP Web界面: http://$NEO4J_SERVER_HOST`:7474"
Write-Host "  Bolt连接: bolt://$NEO4J_SERVER_HOST`:7687"
Write-Host "  用户名: neo4j"
Write-Host "  密码: $NEO4J_PASSWORD"
Write-Host "`n项目目录: $NEO4J_PROJECT_DIR"
Write-Host "`n请手动验证:" -ForegroundColor Yellow
Write-Host "  1. 访问Web界面: http://$NEO4J_SERVER_HOST`:7474"
Write-Host "  2. 测试Bolt连接: bolt://$NEO4J_SERVER_HOST`:7687"
Write-Host "  3. 检查服务日志: docker logs enterprise-ai-neo4j-standalone"

