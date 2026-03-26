#!/bin/bash
# 创建紧急修复分支

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# 获取当前版本
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v1.0.0")
CURRENT_VERSION=${CURRENT_VERSION#v}

# 计算下一个补丁版本
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR=${VERSION_PARTS[0]:-1}
MINOR=${VERSION_PARTS[1]:-0}
PATCH=${VERSION_PARTS[2]:-0}
PATCH=$((PATCH + 1))

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
HOTFIX_BRANCH="hotfix/v$NEW_VERSION"

echo "创建紧急修复分支: $HOTFIX_BRANCH"
echo "目标版本: v$NEW_VERSION"

# 确保在main分支
git checkout main
git pull origin main

# 创建hotfix分支
git checkout -b "$HOTFIX_BRANCH"
git push -u origin "$HOTFIX_BRANCH"

echo ""
echo "✅ 紧急修复分支创建完成"
echo "分支: $HOTFIX_BRANCH"
echo "修复后运行: ./scripts/release/merge-release.sh --version $NEW_VERSION"
echo ""









