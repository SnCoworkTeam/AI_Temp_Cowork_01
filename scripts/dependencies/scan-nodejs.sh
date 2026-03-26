#!/bin/bash
# 扫描Node.js依赖的安全漏洞

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Node.js依赖安全扫描"
echo "=========================================="

if [ ! -f "web-ui/package.json" ]; then
    echo "未找到package.json"
    exit 1
fi

cd web-ui

# 检查npm是否安装
if ! command -v npm &> /dev/null; then
    echo "错误: npm未安装"
    exit 1
fi

# 安装依赖（如果未安装）
if [ ! -d "node_modules" ]; then
    echo "安装依赖..."
    npm install
fi

# 运行npm audit
echo ""
echo "运行npm audit..."
npm audit --json > ../dependencies/security-scan/reports/npm-audit.json || true
npm audit || true

# 使用npm-check-updates检查可更新依赖
if command -v npx &> /dev/null; then
    echo ""
    echo "检查可更新依赖..."
    npx npm-check-updates || true
fi

echo ""
echo "=========================================="
echo "Node.js依赖扫描完成"
echo "=========================================="









