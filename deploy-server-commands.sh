#!/bin/bash
# 服务器部署命令脚本
# 在服务器上执行：拉取代码、部署Docker、执行数据迁移

set -e

SERVER_DIR="/opt/enterprise-ai-platform"

echo "========================================"
echo "服务器部署脚本"
echo "========================================"
echo ""

# 1. 拉取最新代码
echo "[1/6] 拉取最新代码..."
cd $SERVER_DIR
echo "当前目录: $(pwd)"
echo "当前Git提交: $(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
echo ""
echo "📥 拉取最新代码..."
git fetch origin main
git reset --hard origin/main
echo "✅ 代码已更新到最新版本: $(git rev-parse --short HEAD)"
echo ""

# 2. 停止旧服务
echo "[2/6] 停止旧服务..."
cd $SERVER_DIR
echo "🛑 停止旧服务..."
docker compose down --timeout 30 || true
echo "✅ 旧服务已停止"
echo ""

# 3. 构建新镜像
echo "[3/6] 构建新镜像..."
cd $SERVER_DIR
echo "🔨 构建新镜像（project-management 和 api-gateway）..."
docker compose build --parallel project-management api-gateway 2>&1 | tail -30
echo "✅ 镜像构建完成"
echo ""

# 4. 执行数据库迁移
echo "[4/6] 执行数据库迁移..."
cd $SERVER_DIR
echo "📊 执行数据库迁移..."
docker compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  project-management sh -c 'cd /database/src/migrations && python -m alembic upgrade head' 2>&1

if [ $? -eq 0 ]; then
    echo "✅ 数据库迁移成功完成！"
else
    echo "❌ 数据库迁移失败"
    exit 1
fi
echo ""

# 5. 启动服务
echo "[5/6] 启动服务..."
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
echo ""

# 6. 健康检查
echo "[6/6] 健康检查..."
MAX_RETRIES=10
RETRY_COUNT=0
HEALTH_CHECK_PASSED=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ API Gateway健康检查通过"
        HEALTH_CHECK_PASSED=true
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   等待中... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

if [ "$HEALTH_CHECK_PASSED" != "true" ]; then
    echo "❌ API Gateway健康检查失败"
    exit 1
fi

if curl -f -s http://localhost:8016/api/health > /dev/null 2>&1; then
    echo "✅ Project Management健康检查通过"
else
    echo "⚠️  Project Management健康检查失败（可能还在启动中）"
fi

echo ""
echo "========================================"
echo "部署完成！"
echo "========================================"
echo ""
echo "API Gateway: http://43.143.139.197:8080"
echo "Project Management: http://43.143.139.197:8016"
echo ""
echo "当前Git提交: $(git rev-parse --short HEAD)"


