#!/bin/bash
# 发布前检查

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "发布前检查"
echo "=========================================="

ERRORS=0

# 检查1: Git状态
echo ""
echo "检查1: Git状态..."
if ! git diff-index --quiet HEAD --; then
    echo "  ❌ 有未提交的更改"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✅ Git状态正常"
fi

# 检查2: 测试通过
echo ""
echo "检查2: 测试..."
if command -v pytest &> /dev/null; then
    if pytest tests/ -q; then
        echo "  ✅ 测试通过"
    else
        echo "  ❌ 测试失败"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  ⚠️  pytest未安装，跳过测试"
fi

# 检查3: 安全扫描
echo ""
echo "检查3: 安全扫描..."
if [ -f "scripts/dependencies/scan-all.sh" ]; then
    ./scripts/dependencies/scan-all.sh > /dev/null 2>&1 || {
        echo "  ⚠️  安全扫描发现问题（非阻塞）"
    }
    echo "  ✅ 安全扫描完成"
else
    echo "  ⚠️  安全扫描脚本不存在"
fi

# 检查4: 依赖检查
echo ""
echo "检查4: 依赖检查..."
if [ -f "scripts/dependencies/check-conflicts.sh" ]; then
    ./scripts/dependencies/check-conflicts.sh > /dev/null 2>&1 || {
        echo "  ⚠️  发现依赖冲突（非阻塞）"
    }
    echo "  ✅ 依赖检查完成"
fi

# 检查5: 文档检查
echo ""
echo "检查5: 文档..."
if [ -f "scripts/docs/check-documentation.py" ]; then
    python3 scripts/docs/check-documentation.py > /dev/null 2>&1 || {
        echo "  ⚠️  文档检查发现问题（非阻塞）"
    }
    echo "  ✅ 文档检查完成"
fi

# 总结
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ 所有检查通过，可以发布"
    exit 0
else
    echo "❌ 发现 $ERRORS 个错误，请修复后重试"
    exit 1
fi









