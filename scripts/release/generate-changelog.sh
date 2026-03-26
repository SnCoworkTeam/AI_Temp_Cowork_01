#!/bin/bash
# 生成CHANGELOG

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

VERSION="$1"
if [ -z "$VERSION" ]; then
    echo "用法: $0 VERSION"
    exit 1
fi

# 获取上一个标签
PREVIOUS_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$PREVIOUS_TAG" ]; then
    PREVIOUS_TAG=$(git rev-list --max-parents=0 HEAD)
fi

echo "# 版本 $VERSION 发布说明"
echo ""
echo "**发布日期**: $(date +%Y-%m-%d)"
echo ""

# 获取提交记录
echo "## 变更摘要"
echo ""

# 分类提交
FEATURES=$(git log --pretty=format:"- %s" "$PREVIOUS_TAG..HEAD" | grep -E "^-\s*(feat|feature)" || echo "")
FIXES=$(git log --pretty=format:"- %s" "$PREVIOUS_TAG..HEAD" | grep -E "^-\s*fix" || echo "")
DOCS=$(git log --pretty=format:"- %s" "$PREVIOUS_TAG..HEAD" | grep -E "^-\s*docs" || echo "")
REFACTOR=$(git log --pretty=format:"- %s" "$PREVIOUS_TAG..HEAD" | grep -E "^-\s*refactor" || echo "")

if [ -n "$FEATURES" ]; then
    echo "### 新增功能"
    echo "$FEATURES"
    echo ""
fi

if [ -n "$FIXES" ]; then
    echo "### 修复"
    echo "$FIXES"
    echo ""
fi

if [ -n "$REFACTOR" ]; then
    echo "### 重构"
    echo "$REFACTOR"
    echo ""
fi

if [ -n "$DOCS" ]; then
    echo "### 文档"
    echo "$DOCS"
    echo ""
fi

# 统计信息
COMMIT_COUNT=$(git rev-list --count "$PREVIOUS_TAG..HEAD" 2>/dev/null || echo "0")
CONTRIBUTORS=$(git log --pretty=format:"%an" "$PREVIOUS_TAG..HEAD" | sort -u | wc -l)

echo "## 统计信息"
echo ""
echo "- **提交数量**: $COMMIT_COUNT"
echo "- **贡献者**: $CONTRIBUTORS"
echo ""

# 完整提交列表
echo "## 完整变更列表"
echo ""
git log --pretty=format:"- %s (%an, %ar)" "$PREVIOUS_TAG..HEAD"
echo ""









