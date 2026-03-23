#!/bin/bash
# 清理已合并的分支

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "清理已合并的分支"
echo "=========================================="

# 确保在main分支
git checkout main
git pull origin main

# 清理本地已合并分支
echo ""
echo "清理本地分支..."
for branch in $(git branch --merged | grep -v "\*\|main\|develop"); do
    echo "  删除: $branch"
    read -p "  确认删除? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git branch -d "$branch" || git branch -D "$branch"
    fi
done

# 清理远程已合并分支
echo ""
echo "清理远程分支..."
for branch in $(git branch -r --merged origin/main | grep -v "origin/main\|origin/develop" | sed 's/origin\///'); do
    echo "  删除远程分支: $branch"
    read -p "  确认删除? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push origin --delete "$branch"
    fi
done

echo ""
echo "=========================================="
echo "分支清理完成"
echo "=========================================="









