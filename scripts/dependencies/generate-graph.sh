#!/bin/bash
# 生成依赖关系图

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GRAPH_DIR="$PROJECT_ROOT/dependencies/dependency-graph"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "生成依赖关系图"
echo "=========================================="

# 创建目录
mkdir -p "$GRAPH_DIR/service-dependencies"
mkdir -p "$GRAPH_DIR/external-dependencies"

# 生成服务依赖图（使用Python脚本）
if command -v python3 &> /dev/null; then
    echo ""
    echo "生成服务依赖图..."
    python3 "$SCRIPT_DIR/generate-service-graph.py" || echo "Python脚本执行失败"
fi

# 生成Python依赖图
echo ""
echo "生成Python依赖图..."
SERVICES=("mcp-gateway" "workflow-engine" "auth-service" "knowledge-base")

for service in "${SERVICES[@]}"; do
    if [ -f "$service/requirements.txt" ]; then
        echo "处理 $service..."
        # 使用pipdeptree生成依赖树
        if command -v pipdeptree &> /dev/null; then
            cd "$service"
            pipdeptree --json > "$GRAPH_DIR/external-dependencies/${service}-dependencies.json" 2>/dev/null || true
            cd "$PROJECT_ROOT"
        fi
    fi
done

# 生成Node.js依赖图
echo ""
echo "生成Node.js依赖图..."
if [ -f "web-ui/package.json" ]; then
    cd web-ui
    if command -v npm &> /dev/null; then
        npm ls --json > "$GRAPH_DIR/external-dependencies/nodejs-dependencies.json" 2>/dev/null || true
    fi
    cd "$PROJECT_ROOT"
fi

# 生成DOT格式图（如果Graphviz可用）
if command -v dot &> /dev/null && [ -f "$GRAPH_DIR/service-dependencies/graph.json" ]; then
    echo ""
    echo "生成DOT格式图..."
    python3 "$SCRIPT_DIR/generate-dot-graph.py" || echo "DOT图生成失败"
fi

echo ""
echo "=========================================="
echo "依赖关系图生成完成"
echo "保存位置: $GRAPH_DIR"
echo "=========================================="









