#!/bin/bash
# 完整发布流程

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# 解析参数
VERSION=""
RELEASE_TYPE="minor"
SKIP_TESTS=false
SKIP_STAGING=false

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
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-staging)
            SKIP_STAGING=true
            shift
            ;;
        *)
            echo "用法: $0 [--version VERSION] [--type TYPE] [--skip-tests] [--skip-staging]"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "发布流程"
echo "=========================================="

# 步骤1: 创建发布
echo ""
echo "步骤1: 创建发布版本..."
./scripts/release/create-release.sh --version "$VERSION" --type "$RELEASE_TYPE"

# 步骤2: 运行测试
if [ "$SKIP_TESTS" = false ]; then
    echo ""
    echo "步骤2: 运行测试..."
    pytest tests/ || {
        echo "错误: 测试失败"
        exit 1
    }
fi

# 步骤3: 预发布部署（可选）
if [ "$SKIP_STAGING" = false ]; then
    echo ""
    echo "步骤3: 预发布部署..."
    read -p "是否部署到预发布环境? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./scripts/release/deploy-staging.sh || {
            echo "警告: 预发布部署失败，但继续"
        }
    fi
fi

# 步骤4: 合并发布
echo ""
echo "步骤4: 合并发布..."
read -p "是否合并到main并创建标签? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -z "$VERSION" ]; then
        # 从release分支获取版本
        RELEASE_BRANCH=$(git branch -r | grep "release/v" | tail -1 | sed 's/origin\///' | xargs)
        if [ -n "$RELEASE_BRANCH" ]; then
            VERSION=$(echo "$RELEASE_BRANCH" | sed 's/release\/v//')
        fi
    fi
    
    if [ -n "$VERSION" ]; then
        ./scripts/release/merge-release.sh --version "$VERSION"
    else
        echo "错误: 无法确定版本号"
        exit 1
    fi
fi

# 步骤5: 生产部署（可选）
echo ""
echo "步骤5: 生产部署..."
read -p "是否部署到生产环境? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./scripts/release/deploy-production.sh || {
        echo "错误: 生产部署失败"
        exit 1
    }
fi

echo ""
echo "=========================================="
echo "发布流程完成"
echo "=========================================="









