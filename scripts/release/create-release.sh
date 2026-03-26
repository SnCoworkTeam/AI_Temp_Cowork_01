#!/bin/bash
# 创建发布版本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# 解析参数
VERSION=""
RELEASE_TYPE=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --type)
            RELEASE_TYPE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 如果没有提供版本，自动生成
if [ -z "$VERSION" ]; then
    # 获取当前版本
    CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
    CURRENT_VERSION=${CURRENT_VERSION#v}
    
    # 解析版本号
    IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
    MAJOR=${VERSION_PARTS[0]:-0}
    MINOR=${VERSION_PARTS[1]:-0}
    PATCH=${VERSION_PARTS[2]:-0}
    
    # 根据类型递增版本
    if [ "$RELEASE_TYPE" == "major" ]; then
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
    elif [ "$RELEASE_TYPE" == "minor" ]; then
        MINOR=$((MINOR + 1))
        PATCH=0
    else
        PATCH=$((PATCH + 1))
    fi
    
    VERSION="$MAJOR.$MINOR.$PATCH"
fi

echo "=========================================="
echo "创建发布版本: v$VERSION"
echo "=========================================="

if [ "$DRY_RUN" = true ]; then
    echo "⚠️  这是试运行，不会实际创建发布"
fi

# 检查当前分支
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "develop" ]; then
    echo "警告: 当前不在develop分支，是否继续? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# 确保develop是最新的
echo ""
echo "更新develop分支..."
git checkout develop
git pull origin develop

# 创建release分支
RELEASE_BRANCH="release/v$VERSION"
echo ""
echo "创建release分支: $RELEASE_BRANCH"

if [ "$DRY_RUN" = false ]; then
    git checkout -b "$RELEASE_BRANCH"
    git push -u origin "$RELEASE_BRANCH"
else
    echo "  [试运行] 将创建分支: $RELEASE_BRANCH"
fi

# 更新版本号
echo ""
echo "更新版本号..."
if [ "$DRY_RUN" = false ]; then
    # 更新Python服务的版本文件
    for service in mcp-gateway workflow-engine auth-service knowledge-base; do
        if [ -f "$service/src/__version__.py" ]; then
            echo "__version__ = \"$VERSION\"" > "$service/src/__version__.py"
        fi
    done
    
    # 更新package.json（如果存在）
    if [ -f "web-ui/package.json" ]; then
        # 使用sed或jq更新版本
        if command -v jq &> /dev/null; then
            jq ".version = \"$VERSION\"" web-ui/package.json > web-ui/package.json.tmp
            mv web-ui/package.json.tmp web-ui/package.json
        fi
    fi
else
    echo "  [试运行] 将更新版本号为: $VERSION"
fi

# 生成CHANGELOG
echo ""
echo "生成CHANGELOG..."
if [ "$DRY_RUN" = false ]; then
    ./scripts/release/generate-changelog.sh "$VERSION" > "release-management/release-notes/v$VERSION.md"
else
    echo "  [试运行] 将生成CHANGELOG"
fi

# 提交变更
echo ""
echo "提交变更..."
if [ "$DRY_RUN" = false ]; then
    git add .
    git commit -m "chore: 准备发布版本 v$VERSION"
    git push origin "$RELEASE_BRANCH"
else
    echo "  [试运行] 将提交变更"
fi

echo ""
echo "=========================================="
echo "发布版本创建完成"
echo "=========================================="
echo ""
echo "下一步:"
echo "  1. 在release分支进行测试"
echo "  2. 修复发现的问题"
echo "  3. 运行: ./scripts/release/merge-release.sh v$VERSION"
echo ""









