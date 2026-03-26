#!/bin/bash
# 创建功能分支

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

FEATURE_NAME="$1"

if [ -z "$FEATURE_NAME" ]; then
    echo "用法: $0 功能名称"
    echo "示例: $0 user-authentication"
    exit 1
fi

# 规范化分支名称（小写，连字符分隔）
FEATURE_NAME=$(echo "$FEATURE_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
BRANCH_NAME="feature/$FEATURE_NAME"

echo "创建功能分支: $BRANCH_NAME"

# 确保在develop分支
git checkout develop
git pull origin develop

# 创建功能分支
git checkout -b "$BRANCH_NAME"
git push -u origin "$BRANCH_NAME"

echo ""
echo "✅ 功能分支创建完成"
echo "分支: $BRANCH_NAME"
echo ""









