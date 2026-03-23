# 服务器部署脚本
# 在服务器上执行：拉取代码、部署Docker、执行数据迁移

$SERVER_IP = "43.143.139.197"
$SERVER_USER = "ubuntu"
$SERVER_DIR = "/opt/enterprise-ai-platform"
$SSH_KEY = "E:\enterprise-ai-platform\Jenkins.pem"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "服务器部署脚本" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. 拉取最新代码
Write-Host "1. 拉取最新代码..." -ForegroundColor Yellow
$sshCommand = @"
cd $SERVER_DIR
echo "当前目录: \$(pwd)"
echo "当前Git提交: \$(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
echo ""
echo "📥 拉取最新代码..."
git fetch origin main
git reset --hard origin/main
echo "✅ 代码已更新到最新版本: \$(git rev-parse --short HEAD)"
"@

ssh -i $SSH_KEY -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} $sshCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ 拉取代码失败" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ 代码拉取成功" -ForegroundColor Green

# 2. 停止旧服务
Write-Host "`n2. 停止旧服务..." -ForegroundColor Yellow
$sshCommand = @"
cd $SERVER_DIR
echo "🛑 停止旧服务..."
docker compose down --timeout 30 || true
echo "✅ 旧服务已停止"
"@

ssh -i $SSH_KEY -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} $sshCommand

# 3. 构建新镜像
Write-Host "`n3. 构建新镜像..." -ForegroundColor Yellow
$sshCommand = @"
cd $SERVER_DIR
echo "🔨 构建新镜像..."
docker compose build --parallel project-management api-gateway 2>&1 | tail -20
echo "✅ 镜像构建完成"
"@

ssh -i $SSH_KEY -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} $sshCommand

# 4. 执行数据库迁移
Write-Host "`n4. 执行数据库迁移..." -ForegroundColor Yellow
$sshCommand = @"
cd $SERVER_DIR
echo "📊 执行数据库迁移..."
docker compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  project-management sh -c 'cd /database/src/migrations && python -m alembic upgrade head' 2>&1

if [ \$? -eq 0 ]; then
    echo "✅ 数据库迁移成功完成！"
else
    echo "❌ 数据库迁移失败"
    exit 1
fi
"@

ssh -i $SSH_KEY -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} $sshCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ 数据库迁移失败" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ 数据库迁移成功" -ForegroundColor Green

# 5. 启动服务
Write-Host "`n5. 启动服务..." -ForegroundColor Yellow
$sshCommand = @"
cd $SERVER_DIR
echo "🚀 启动服务..."
docker compose up -d project-management api-gateway
echo "✅ 服务已启动"
echo ""
echo "⏳ 等待服务就绪..."
sleep 30
echo ""
echo "📊 服务状态:"
docker compose ps project-management api-gateway
"@

ssh -i $SSH_KEY -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} $sshCommand

# 6. 健康检查
Write-Host "`n6. 健康检查..." -ForegroundColor Yellow
$sshCommand = @"
echo "🏥 检查服务健康状态..."
MAX_RETRIES=10
RETRY_COUNT=0
HEALTH_CHECK_PASSED=false

while [ \$RETRY_COUNT -lt \$MAX_RETRIES ]; do
    if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ API Gateway健康检查通过"
        HEALTH_CHECK_PASSED=true
        break
    fi
    RETRY_COUNT=\$((RETRY_COUNT + 1))
    echo "   等待中... (\$RETRY_COUNT/\$MAX_RETRIES)"
    sleep 5
done

if [ "\$HEALTH_CHECK_PASSED" != "true" ]; then
    echo "❌ API Gateway健康检查失败"
    exit 1
fi

if curl -f -s http://localhost:8016/api/health > /dev/null 2>&1; then
    echo "✅ Project Management健康检查通过"
else
    echo "⚠️  Project Management健康检查失败（可能还在启动中）"
fi
"@

ssh -i $SSH_KEY -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} $sshCommand

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
Write-Host "API Gateway: http://${SERVER_IP}:8080" -ForegroundColor White
Write-Host "Project Management: http://${SERVER_IP}:8016" -ForegroundColor White


