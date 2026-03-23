#!/bin/bash
# 快速回滚（5分钟内）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

TARGET_VERSION="$1"

if [ -z "$TARGET_VERSION" ]; then
    # 获取上一个版本
    TARGET_VERSION=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo "")
    if [ -z "$TARGET_VERSION" ]; then
        echo "错误: 无法确定回滚版本"
        exit 1
    fi
fi

echo "=========================================="
echo "快速回滚到版本: $TARGET_VERSION"
echo "=========================================="

# 确认
read -p "确认回滚到 $TARGET_VERSION? (yes/no): " -r
if [ "$REPLY" != "yes" ]; then
    echo "取消回滚"
    exit 0
fi

# 检出目标版本
echo ""
echo "检出版本: $TARGET_VERSION"
git checkout "$TARGET_VERSION"

# 重新构建
echo ""
echo "重新构建镜像..."
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
echo "回滚完成"
echo "=========================================="









