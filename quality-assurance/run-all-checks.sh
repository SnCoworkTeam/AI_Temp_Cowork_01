#!/bin/bash
# 运行所有质量检查

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "运行完整质量保障检查"
echo "=========================================="

cd "$PROJECT_ROOT"

# 1. 静态代码分析
echo ""
echo "1. 静态代码分析..."
python3 "$SCRIPT_DIR/code-analysis/static-analysis/analyze.py"

# 2. 依赖分析
echo ""
echo "2. 依赖分析..."
python3 "$SCRIPT_DIR/code-analysis/dependency-analysis/analyze.py"

# 3. 复杂度分析
echo ""
echo "3. 复杂度分析..."
python3 "$SCRIPT_DIR/code-analysis/complexity-analysis/analyze.py"

# 4. 安全扫描
echo ""
echo "4. 安全扫描..."
python3 "$SCRIPT_DIR/code-analysis/security-scan/scan.py"

# 5. 运行测试
echo ""
echo "5. 运行测试..."
python3 "$SCRIPT_DIR/testing-strategy/run-all-tests.py"

# 6. 收集覆盖率
echo ""
echo "6. 收集代码覆盖率..."
python3 "$SCRIPT_DIR/quality-metrics/code-coverage/collect.py"

# 7. 质量门禁检查
echo ""
echo "7. 质量门禁检查..."
python3 "$SCRIPT_DIR/quality-metrics/quality-gate.py"

echo ""
echo "=========================================="
echo "所有质量检查完成"
echo "=========================================="









