#!/bin/bash
# 完整回滚（包括数据库）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

TARGET_VERSION="$1"

if [ -z "$TARGET_VERSION" ]; then
    TARGET_VERSION=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo "")
    if [ -z "$TARGET_VERSION" ]; then
        echo "错误: 无法确定回滚版本"
        exit 1
    fi
fi

echo "=========================================="
echo "完整回滚到版本: $TARGET_VERSION"
echo "=========================================="

# 评估回滚影响
echo ""
echo "评估回滚影响..."
./scripts/release/assess-rollback.sh "$TARGET_VERSION"

# 确认
read -p "确认执行完整回滚? (yes/no): " -r
if [ "$REPLY" != "yes" ]; then
    echo "取消回滚"
    exit 0
fi

# 备份当前状态
echo ""
echo "备份当前状态..."
./scripts/backup/backup-postgres.sh || echo "警告: 数据库备份失败"
./scripts/backup/backup-redis.sh || echo "警告: Redis备份失败"

# 代码回滚
echo ""
echo "回滚代码..."
git checkout "$TARGET_VERSION"

# 数据库回滚（如果有迁移）
echo ""
echo "检查数据库迁移..."
DB_MIGRATIONS=$(git diff --name-only "$TARGET_VERSION"..HEAD | grep -E "migrations" | wc -l || echo "0")
if [ "$DB_MIGRATIONS" -gt 0 ]; then
    echo "发现数据库迁移，需要回滚..."
    read -p "是否回滚数据库迁移? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 回滚到目标版本的迁移
        docker-compose exec mcp-gateway alembic downgrade -1 || echo "警告: 数据库回滚失败"
    fi
fi

# 重新构建
echo ""
echo "重新构建..."
docker-compose -f docker-compose.prod.yml build

# 重新部署
echo ""
echo "重新部署..."
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 15

# 验证
echo ""
echo "验证回滚..."
./scripts/release/verify-production.sh

echo ""
echo "=========================================="
echo "完整回滚完成"
echo "=========================================="









