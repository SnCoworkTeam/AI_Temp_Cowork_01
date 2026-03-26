#!/bin/bash
# 部署到生产环境

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "部署到生产环境"
echo "=========================================="

# 确认
read -p "⚠️  确认部署到生产环境? (yes/no): " -r
if [ "$REPLY" != "yes" ]; then
    echo "取消部署"
    exit 0
fi

# 检查是否有生产配置文件
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "警告: 未找到docker-compose.prod.yml，使用docker-compose.yml"
    COMPOSE_FILE="docker-compose.yml"
else
    COMPOSE_FILE="docker-compose.prod.yml"
fi

# 备份
echo ""
echo "备份数据库..."
./scripts/backup/backup-postgres.sh || echo "警告: 数据库备份失败"

echo ""
echo "备份Redis..."
./scripts/backup/backup-redis.sh || echo "警告: Redis备份失败"

# 构建镜像
echo ""
echo "构建生产镜像..."
docker-compose -f "$COMPOSE_FILE" build

# 获取当前版本
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "unknown")
echo "部署版本: $CURRENT_VERSION"

# 部署（使用蓝绿部署或滚动更新）
echo ""
echo "部署服务..."
docker-compose -f "$COMPOSE_FILE" up -d --no-deps --build

# 运行数据库迁移
echo ""
echo "运行数据库迁移..."
docker-compose -f "$COMPOSE_FILE" exec -T mcp-gateway alembic upgrade head || {
    echo "错误: 数据库迁移失败，开始回滚..."
    ./scripts/release/rollback-fast.sh "$CURRENT_VERSION"
    exit 1
}

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 15

# 健康检查
echo ""
echo "健康检查..."
./scripts/release/verify-production.sh || {
    echo "错误: 健康检查失败，开始回滚..."
    ./scripts/release/rollback-fast.sh "$CURRENT_VERSION"
    exit 1
}

echo ""
echo "=========================================="
echo "生产部署完成"
echo "=========================================="
echo ""
echo "版本: $CURRENT_VERSION"
echo "部署时间: $(date)"
echo ""









