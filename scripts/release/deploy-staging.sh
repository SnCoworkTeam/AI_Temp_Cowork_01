#!/bin/bash
# 部署到预发布环境

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "部署到预发布环境"
echo "=========================================="

# 检查是否有staging配置文件
if [ ! -f "docker-compose.staging.yml" ]; then
    echo "警告: 未找到docker-compose.staging.yml，使用docker-compose.yml"
    COMPOSE_FILE="docker-compose.yml"
else
    COMPOSE_FILE="docker-compose.staging.yml"
fi

# 构建镜像
echo ""
echo "构建Docker镜像..."
docker-compose -f "$COMPOSE_FILE" build

# 停止旧服务
echo ""
echo "停止旧服务..."
docker-compose -f "$COMPOSE_FILE" down

# 启动服务
echo ""
echo "启动服务..."
docker-compose -f "$COMPOSE_FILE" up -d

# 运行数据库迁移
echo ""
echo "运行数据库迁移..."
docker-compose -f "$COMPOSE_FILE" exec -T mcp-gateway alembic upgrade head || echo "警告: 数据库迁移失败"

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 10

# 健康检查
echo ""
echo "健康检查..."
./scripts/release/verify-staging.sh

echo ""
echo "=========================================="
echo "预发布部署完成"
echo "=========================================="









