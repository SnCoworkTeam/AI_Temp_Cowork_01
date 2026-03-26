#!/bin/bash
# 评估回滚影响

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

CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "HEAD")

echo "=========================================="
echo "回滚影响评估"
echo "=========================================="
echo "当前版本: $CURRENT_VERSION"
echo "目标版本: $TARGET_VERSION"
echo ""

# 分析变更范围
echo "## 变更范围"
echo ""
CHANGED_FILES=$(git diff --name-only "$TARGET_VERSION".."$CURRENT_VERSION" | wc -l)
echo "- **变更文件数**: $CHANGED_FILES"

LINES_ADDED=$(git diff --numstat "$TARGET_VERSION".."$CURRENT_VERSION" | awk '{sum+=$1} END {print sum}' || echo "0")
LINES_DELETED=$(git diff --numstat "$TARGET_VERSION".."$CURRENT_VERSION" | awk '{sum+=$2} END {print sum}' || echo "0")
echo "- **将回滚的代码行数**: +$LINES_ADDED / -$LINES_DELETED"
echo ""

# 分析数据库变更
echo "## 数据库变更"
echo ""
DB_MIGRATIONS=$(git diff --name-only "$TARGET_VERSION".."$CURRENT_VERSION" | grep -E "migrations" | wc -l || echo "0")
if [ "$DB_MIGRATIONS" -gt 0 ]; then
    echo "- **数据库迁移文件**: $DB_MIGRATIONS 个"
    echo "  ⚠️  需要回滚数据库迁移"
else
    echo "- **数据库迁移**: 无"
fi
echo ""

# 分析API变更
echo "## API变更"
echo ""
API_CHANGES=$(git diff "$TARGET_VERSION".."$CURRENT_VERSION" -- "**/routes/*.py" | grep -E "^\+.*@.*\(|^\+.*router\." | wc -l || echo "0")
if [ "$API_CHANGES" -gt 0 ]; then
    echo "- **API端点变更**: $API_CHANGES 个"
    echo "  ⚠️  可能影响API兼容性"
else
    echo "- **API变更**: 无"
fi
echo ""

# 分析依赖变更
echo "## 依赖变更"
echo ""
DEP_CHANGES=$(git diff --name-only "$TARGET_VERSION".."$CURRENT_VERSION" | grep -E "(requirements.txt|package.json)" | wc -l || echo "0")
if [ "$DEP_CHANGES" -gt 0 ]; then
    echo "- **依赖变更**: 有"
    echo "  ⚠️  需要检查依赖兼容性"
else
    echo "- **依赖变更**: 无"
fi
echo ""

# 回滚风险评估
echo "## 回滚风险评估"
echo ""
if [ "$DB_MIGRATIONS" -gt 0 ]; then
    echo "⚠️  **高风险**: 包含数据库迁移，需要谨慎处理"
elif [ "$API_CHANGES" -gt 0 ]; then
    echo "⚠️  **中风险**: 包含API变更，可能影响客户端"
else
    echo "✅ **低风险**: 主要是代码变更，回滚相对安全"
fi

echo ""
echo "=========================================="
echo "评估完成"
echo "=========================================="









