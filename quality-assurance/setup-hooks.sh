#!/bin/bash
# 安装Git预提交钩子

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
PRE_COMMIT_HOOKS_DIR="$SCRIPT_DIR/pre-commit-hooks"

echo "安装Git预提交钩子..."

# 创建hooks目录
mkdir -p "$HOOKS_DIR"

# 复制预提交钩子脚本
echo "复制预提交钩子脚本..."
cp "$PRE_COMMIT_HOOKS_DIR"/*.py "$HOOKS_DIR/"
chmod +x "$HOOKS_DIR"/*.py

# 创建pre-commit钩子
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Git预提交钩子
# 在提交前运行质量检查

set -e

HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "运行预提交检查..."

# 1. 架构符合性检查
echo "1. 检查架构符合性..."
python3 "$HOOKS_DIR/check-architecture.py" || exit 1

# 2. 代码规范检查
echo "2. 检查代码规范..."
python3 "$HOOKS_DIR/lint-code.py" || exit 1

# 3. 模型验证
echo "3. 验证数据模型..."
python3 "$HOOKS_DIR/validate-models.py" || exit 1

# 4. 快速测试（可选，可以通过环境变量禁用）
if [ "${SKIP_TESTS:-false}" != "true" ]; then
    echo "4. 运行快速测试..."
    python3 "$HOOKS_DIR/run-tests.py" || exit 1
fi

echo "✅ 所有预提交检查通过"
EOF

chmod +x "$HOOKS_DIR/pre-commit"

echo "✅ Git预提交钩子安装完成"
echo ""
echo "钩子将在每次提交时自动运行:"
echo "  - 架构符合性检查"
echo "  - 代码规范检查"
echo "  - 数据模型验证"
echo "  - 快速测试（可通过 SKIP_TESTS=true 禁用）"









