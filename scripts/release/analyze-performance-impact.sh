#!/bin/bash
# 分析性能影响（简化版）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

BASE="${1:-origin/main}"
HEAD="${2:-HEAD}"

echo "=========================================="
echo "性能影响分析"
echo "=========================================="
echo "对比范围: $BASE..$HEAD"
echo ""

# 检查性能相关变更
echo "## 性能相关变更"
echo ""

# 检查数据库查询变更
DB_QUERY_CHANGES=$(git diff "$BASE".."$HEAD" | grep -cE "(query|select|insert|update|delete)" || echo "0")
echo "- **数据库查询变更**: $DB_QUERY_CHANGES 处"

# 检查缓存相关变更
CACHE_CHANGES=$(git diff "$BASE".."$HEAD" | grep -cE "(cache|redis|memcached)" || echo "0")
echo "- **缓存相关变更**: $CACHE_CHANGES 处"

# 检查异步操作变更
ASYNC_CHANGES=$(git diff "$BASE".."$HEAD" | grep -cE "(async|await|asyncio)" || echo "0")
echo "- **异步操作变更**: $ASYNC_CHANGES 处"

# 检查循环和递归
LOOP_CHANGES=$(git diff "$BASE".."$HEAD" | grep -cE "(for|while|recursive)" || echo "0")
echo "- **循环/递归变更**: $LOOP_CHANGES 处"

echo ""
echo "=========================================="
echo "分析完成"
echo ""
echo "注意: 这是简化分析，实际性能影响需要通过测试验证"
echo "=========================================="









