#!/bin/bash
# 检查依赖冲突

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "检查依赖冲突"
echo "=========================================="

CONFLICTS_FILE="$PROJECT_ROOT/dependencies/dependency-graph/dependency-conflicts/conflicts.json"
mkdir -p "$(dirname "$CONFLICTS_FILE")"

# 检查Python依赖冲突
echo ""
echo "检查Python依赖冲突..."
if command -v pip &> /dev/null; then
    SERVICES=("mcp-gateway" "workflow-engine" "auth-service" "knowledge-base")
    
    for service in "${SERVICES[@]}"; do
        if [ -f "$service/requirements.txt" ]; then
            echo ""
            echo "$service:"
            cd "$service"
            pip check 2>&1 || echo "  发现冲突"
            cd "$PROJECT_ROOT"
        fi
    done
fi

# 检查Node.js依赖冲突
echo ""
echo "检查Node.js依赖冲突..."
if [ -f "web-ui/package.json" ] && command -v npm &> /dev/null; then
    cd web-ui
    echo ""
    echo "web-ui:"
    npm ls --depth=0 2>&1 | grep -E "UNMET|extraneous|missing" || echo "  无冲突"
    cd "$PROJECT_ROOT"
fi

# 检查服务间依赖冲突
echo ""
echo "检查服务间依赖冲突..."
if command -v python3 &> /dev/null; then
    python3 "$SCRIPT_DIR/check-service-conflicts.py" || true
fi

echo ""
echo "=========================================="
echo "依赖冲突检查完成"
echo "=========================================="









