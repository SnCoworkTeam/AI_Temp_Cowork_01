#!/bin/bash
# 检查可更新的依赖

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "检查依赖更新"
echo "=========================================="

# 检查Python依赖更新
echo ""
echo "检查Python依赖更新..."
if command -v pip-audit &> /dev/null; then
    SERVICES=("mcp-gateway" "workflow-engine" "auth-service" "knowledge-base")
    
    for service in "${SERVICES[@]}"; do
        if [ -f "$service/requirements.txt" ]; then
            echo ""
            echo "$service:"
            pip-audit --desc "$service/requirements.txt" | grep -E "UPDATE|UPGRADE" || echo "  无更新"
        fi
    done
else
    echo "⚠️  pip-audit未安装"
fi

# 检查Node.js依赖更新
echo ""
echo "检查Node.js依赖更新..."
if [ -f "web-ui/package.json" ] && command -v npx &> /dev/null; then
    cd web-ui
    echo ""
    echo "web-ui:"
    npx npm-check-updates || true
    cd "$PROJECT_ROOT"
fi

# 使用pip list检查已安装包的版本
echo ""
echo "检查已安装Python包版本..."
if command -v pip &> /dev/null; then
    pip list --outdated || true
fi

echo ""
echo "=========================================="
echo "依赖更新检查完成"
echo "=========================================="
echo ""
echo "提示: 更新依赖前请运行测试确保兼容性"
echo "      ./scripts/dependencies/update-dependencies.sh"









