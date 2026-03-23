#!/bin/bash
# 扫描Python依赖的安全漏洞

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Python依赖安全扫描"
echo "=========================================="

# 检查工具是否安装
if ! command -v pip-audit &> /dev/null; then
    echo "安装pip-audit..."
    pip install pip-audit
fi

if ! command -v safety &> /dev/null; then
    echo "安装safety..."
    pip install safety
fi

# 扫描所有Python服务
SERVICES=("mcp-gateway" "workflow-engine" "auth-service" "knowledge-base" "shared-libs" "database")

for service in "${SERVICES[@]}"; do
    if [ -f "$service/requirements.txt" ]; then
        echo ""
        echo "扫描 $service..."
        echo "----------------------------------------"
        
        # 使用pip-audit扫描
        if [ -f "$service/requirements.txt" ]; then
            pip-audit -r "$service/requirements.txt" --format table || true
        fi
        
        # 使用safety扫描
        if [ -f "$service/requirements.txt" ]; then
            safety check -r "$service/requirements.txt" || true
        fi
    fi
done

echo ""
echo "=========================================="
echo "Python依赖扫描完成"
echo "=========================================="









