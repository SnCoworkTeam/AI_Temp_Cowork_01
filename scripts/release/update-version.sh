#!/bin/bash
# 更新版本号

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

VERSION="$1"

if [ -z "$VERSION" ]; then
    echo "用法: $0 VERSION"
    echo "示例: $0 1.0.0"
    exit 1
fi

echo "更新版本号到: $VERSION"

# 更新Python服务的版本文件
for service in mcp-gateway workflow-engine auth-service knowledge-base shared-libs database; do
    VERSION_FILE="$service/src/__version__.py"
    if [ ! -f "$VERSION_FILE" ]; then
        # 创建版本文件
        mkdir -p "$service/src"
        echo "__version__ = \"$VERSION\"" > "$VERSION_FILE"
        echo "创建: $VERSION_FILE"
    else
        # 更新版本文件
        sed -i.bak "s/__version__ = .*/__version__ = \"$VERSION\"/" "$VERSION_FILE"
        rm -f "$VERSION_FILE.bak"
        echo "更新: $VERSION_FILE"
    fi
done

# 更新package.json
if [ -f "web-ui/package.json" ]; then
    if command -v jq &> /dev/null; then
        jq ".version = \"$VERSION\"" web-ui/package.json > web-ui/package.json.tmp
        mv web-ui/package.json.tmp web-ui/package.json
        echo "更新: web-ui/package.json"
    else
        # 使用sed更新（简单方式）
        sed -i.bak "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" web-ui/package.json
        rm -f web-ui/package.json.bak
        echo "更新: web-ui/package.json"
    fi
fi

# 更新docker-compose.yml中的版本标签（可选）
if [ -f "docker-compose.yml" ]; then
    # 这里可以添加更新docker-compose版本标签的逻辑
    echo "跳过docker-compose.yml版本更新（需要手动更新）"
fi

echo ""
echo "✅ 版本号更新完成"









