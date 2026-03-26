#!/bin/bash
# 验证生产环境

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

PROD_URL="${PROD_URL:-https://api.example.com}"

echo "验证生产环境: $PROD_URL"

# 检查服务健康状态
SERVICES=(
    "$PROD_URL/api/health"
)

FAILED=0

for url in "${SERVICES[@]}"; do
    echo ""
    echo "检查: $url"
    if curl -f -s "$url" > /dev/null; then
        echo "  ✅ 健康检查通过"
    else
        echo "  ❌ 健康检查失败"
        FAILED=$((FAILED + 1))
    fi
done

# 检查核心功能
echo ""
echo "检查核心功能..."

# 可以添加更多功能检查
# curl -f -s "$PROD_URL/api/tools" > /dev/null || FAILED=$((FAILED + 1))

if [ $FAILED -gt 0 ]; then
    echo ""
    echo "错误: $FAILED 个检查失败"
    exit 1
fi

echo ""
echo "✅ 所有检查通过"









