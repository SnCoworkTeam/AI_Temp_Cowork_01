#!/bin/bash
# 合并发布分支到main和develop

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# 解析参数
VERSION=""
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        *)
            echo "用法: $0 --version VERSION [--skip-tests]"
            exit 1
            ;;
    esac
done

if [ -z "$VERSION" ]; then
    echo "错误: 必须提供版本号"
    echo "用法: $0 --version VERSION"
    exit 1
fi

RELEASE_BRANCH="release/v$VERSION"
TAG="v$VERSION"

echo "=========================================="
echo "合并发布分支: $RELEASE_BRANCH"
echo "=========================================="

# 检查release分支是否存在
if ! git show-ref --verify --quiet "refs/heads/$RELEASE_BRANCH" && ! git show-ref --verify --quiet "refs/remotes/origin/$RELEASE_BRANCH"; then
    echo "错误: release分支不存在: $RELEASE_BRANCH"
    exit 1
fi

# 运行测试（除非跳过）
if [ "$SKIP_TESTS" = false ]; then
    echo ""
    echo "运行测试..."
    pytest tests/ || {
        echo "错误: 测试失败，请修复后重试"
        exit 1
    }
fi

# 合并到main
echo ""
echo "合并到main分支..."
git checkout main
git pull origin main

# 合并release分支
git merge --no-ff "$RELEASE_BRANCH" -m "chore: 合并发布版本 v$VERSION"

# 创建标签
echo ""
echo "创建标签: $TAG"
git tag -a "$TAG" -m "Release version $VERSION"

# 推送到远程
echo ""
echo "推送到远程..."
git push origin main
git push origin "$TAG"

# 合并到develop
echo ""
echo "合并到develop分支..."
git checkout develop
git pull origin develop
git merge --no-ff "$RELEASE_BRANCH" -m "chore: 合并发布版本 v$VERSION到develop"
git push origin develop

# 删除release分支
echo ""
echo "删除release分支..."
git branch -d "$RELEASE_BRANCH"
git push origin --delete "$RELEASE_BRANCH"

echo ""
echo "=========================================="
echo "发布合并完成"
echo "=========================================="
echo ""
echo "版本: $TAG"
echo "标签已创建并推送"
echo "发布分支已删除"
echo ""









