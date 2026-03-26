#!/bin/bash
# 创建缺陷修复分支

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

BUG_DESCRIPTION="$1"

if [ -z "$BUG_DESCRIPTION" ]; then
    echo "用法: $0 问题描述"
    echo "示例: $0 fix-api-timeout"
    exit 1
fi

# 规范化分支名称
BUG_DESCRIPTION=$(echo "$BUG_DESCRIPTION" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
BRANCH_NAME="bugfix/$BUG_DESCRIPTION"

echo "创建缺陷修复分支: $BRANCH_NAME"

# 确保在develop分支
git checkout develop
git pull origin develop

# 创建bugfix分支
git checkout -b "$BRANCH_NAME"
git push -u origin "$BRANCH_NAME"

echo ""
echo "✅ 缺陷修复分支创建完成"
echo "分支: $BRANCH_NAME"
echo ""









