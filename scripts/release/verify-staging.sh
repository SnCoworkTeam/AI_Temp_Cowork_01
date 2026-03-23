#!/bin/bash
# 验证预发布环境

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

STAGING_URL="${STAGING_URL:-http://localhost:8000}"

echo "验证预发布环境: $STAGING_URL"

# 检查服务健康状态
SERVICES=(
    "$STAGING_URL/api/health"
    "$STAGING_URL:8001/api/health"
    "$STAGING_URL:8002/api/health"
    "$STAGING_URL:8004/api/health"
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

if [ $FAILED -gt 0 ]; then
    echo ""
    echo "错误: $FAILED 个服务健康检查失败"
    exit 1
fi

echo ""
echo "✅ 所有服务健康检查通过"









