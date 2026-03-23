#!/bin/bash
# 交互式更新依赖

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "依赖更新工具"
echo "=========================================="

# 检查可更新依赖
echo ""
echo "检查可更新依赖..."
./scripts/dependencies/check-updates.sh

echo ""
read -p "是否继续更新依赖? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消更新"
    exit 0
fi

# 更新Python依赖
echo ""
echo "更新Python依赖..."
read -p "更新Python依赖? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SERVICES=("mcp-gateway" "workflow-engine" "auth-service" "knowledge-base")
    
    for service in "${SERVICES[@]}"; do
        if [ -f "$service/requirements.txt" ]; then
            echo ""
            echo "更新 $service..."
            cd "$service"
            
            # 备份requirements.txt
            cp requirements.txt requirements.txt.backup
            
            # 更新依赖（仅安全补丁）
            if command -v pip-audit &> /dev/null; then
                pip-audit --fix --only-fix || true
            fi
            
            cd "$PROJECT_ROOT"
        fi
    done
fi

# 更新Node.js依赖
echo ""
echo "更新Node.js依赖..."
read -p "更新Node.js依赖? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "web-ui/package.json" ]; then
        cd web-ui
        
        # 备份package.json
        cp package.json package.json.backup
        
        # 更新依赖（交互式）
        if command -v npx &> /dev/null; then
            npx npm-check-updates -i || true
            npm install
        fi
        
        cd "$PROJECT_ROOT"
    fi
fi

# 运行测试
echo ""
echo "运行测试验证更新..."
read -p "运行测试? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Python测试
    if command -v pytest &> /dev/null; then
        pytest tests/ || echo "测试失败，请检查"
    fi
    
    # Node.js测试
    if [ -f "web-ui/package.json" ]; then
        cd web-ui
        npm test || echo "测试失败，请检查"
        cd "$PROJECT_ROOT"
    fi
fi

# 重新扫描安全漏洞
echo ""
echo "重新扫描安全漏洞..."
./scripts/dependencies/scan-all.sh

echo ""
echo "=========================================="
echo "依赖更新完成"
echo "=========================================="
echo ""
echo "提示:"
echo "  1. 检查备份文件 (*.backup)"
echo "  2. 运行完整测试"
echo "  3. 提交更新到版本控制"









