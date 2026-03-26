#!/bin/bash
# 分析代码变更影响

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# 获取变更范围
BASE="${1:-origin/main}"
HEAD="${2:-HEAD}"

echo "=========================================="
echo "代码变更影响分析"
echo "=========================================="
echo "对比范围: $BASE..$HEAD"
echo ""

# 统计变更
echo "## 变更统计"
echo ""
CHANGED_FILES=$(git diff --name-only "$BASE".."$HEAD" | wc -l)
echo "- **变更文件数**: $CHANGED_FILES"

LINES_ADDED=$(git diff --numstat "$BASE".."$HEAD" | awk '{sum+=$1} END {print sum}' || echo "0")
LINES_DELETED=$(git diff --numstat "$BASE".."$HEAD" | awk '{sum+=$2} END {print sum}' || echo "0")
echo "- **新增行数**: $LINES_ADDED"
echo "- **删除行数**: $LINES_DELETED"
echo ""

# 分析影响的服务
echo "## 影响的服务"
echo ""
SERVICES=("mcp-gateway" "workflow-engine" "auth-service" "knowledge-base" "web-ui" "shared-libs" "database")

for service in "${SERVICES[@]}"; do
    CHANGED=$(git diff --name-only "$BASE".."$HEAD" | grep -c "^$service/" || echo "0")
    if [ "$CHANGED" -gt 0 ]; then
        echo "- **$service**: $CHANGED 个文件变更"
    fi
done
echo ""

# 分析变更类型
echo "## 变更类型"
echo ""
PYTHON_FILES=$(git diff --name-only "$BASE".."$HEAD" | grep -c "\.py$" || echo "0")
TS_FILES=$(git diff --name-only "$BASE".."$HEAD" | grep -c "\.tsx\?$" || echo "0")
CONFIG_FILES=$(git diff --name-only "$BASE".."$HEAD" | grep -E "(docker-compose|Dockerfile|\.env)" | wc -l || echo "0")

echo "- **Python文件**: $PYTHON_FILES"
echo "- **TypeScript文件**: $TS_FILES"
echo "- **配置文件**: $CONFIG_FILES"
echo ""

# API变更分析
echo "## API变更"
echo ""
API_CHANGES=$(git diff "$BASE".."$HEAD" -- "**/routes/*.py" "**/routes/*.ts" | grep -E "^\+.*@.*\(|^\+.*router\." | wc -l || echo "0")
echo "- **API端点变更**: $API_CHANGES"
echo ""

# 数据库变更分析
echo "## 数据库变更"
echo ""
DB_CHANGES=$(git diff --name-only "$BASE".."$HEAD" | grep -E "(migrations|models)" | wc -l || echo "0")
echo "- **数据库变更文件**: $DB_CHANGES"
echo ""

echo "=========================================="
echo "分析完成"
echo "=========================================="









