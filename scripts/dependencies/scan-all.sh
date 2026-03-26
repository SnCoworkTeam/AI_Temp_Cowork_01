#!/bin/bash
# 扫描所有依赖的安全漏洞

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORTS_DIR="$PROJECT_ROOT/dependencies/security-scan/reports"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "依赖安全扫描"
echo "=========================================="

# 创建报告目录
mkdir -p "$REPORTS_DIR"

# 扫描Python依赖
echo ""
echo "扫描Python依赖..."
if command -v pip-audit &> /dev/null; then
    pip-audit --format json --output "$REPORTS_DIR/python-audit.json" || true
    pip-audit --format table || true
else
    echo "⚠️  pip-audit未安装，跳过Python扫描"
fi

# 扫描Node.js依赖
echo ""
echo "扫描Node.js依赖..."
if [ -f "web-ui/package.json" ]; then
    cd web-ui
    if command -v npm &> /dev/null; then
        npm audit --json > "$REPORTS_DIR/npm-audit.json" || true
        npm audit || true
    fi
    cd "$PROJECT_ROOT"
else
    echo "⚠️  未找到package.json"
fi

# 扫描Docker镜像
echo ""
echo "扫描Docker镜像..."
if command -v trivy &> /dev/null; then
    # 扫描Dockerfile
    trivy config --config "$PROJECT_ROOT/dependencies/security-scan/trivy-config.yaml" . || true
    
    # 扫描镜像（如果已构建）
    if docker images | grep -q "mcp-gateway"; then
        trivy image mcp-gateway:latest || true
    fi
else
    echo "⚠️  trivy未安装，跳过Docker扫描"
fi

# 使用Snyk扫描（如果配置）
echo ""
echo "扫描Snyk..."
if command -v snyk &> /dev/null && [ -n "$SNYK_TOKEN" ]; then
    snyk test --json-file-output="$REPORTS_DIR/snyk-report.json" || true
    snyk test || true
else
    echo "⚠️  Snyk未配置，跳过Snyk扫描"
fi

echo ""
echo "=========================================="
echo "扫描完成"
echo "报告保存在: $REPORTS_DIR"
echo "=========================================="









