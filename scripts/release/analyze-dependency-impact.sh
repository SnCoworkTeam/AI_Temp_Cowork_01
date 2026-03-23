#!/bin/bash
# 分析依赖变更影响

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

BASE="${1:-origin/main}"
HEAD="${2:-HEAD}"

echo "=========================================="
echo "依赖变更影响分析"
echo "=========================================="
echo "对比范围: $BASE..$HEAD"
echo ""

# 分析requirements.txt变更
echo "## Python依赖变更"
echo ""
for req_file in $(git diff --name-only "$BASE".."$HEAD" | grep "requirements.txt"); do
    echo "**$req_file**:"
    git diff "$BASE".."$HEAD" -- "$req_file" | grep -E "^\+|^-" | grep -v "^+++\|^---" | head -10
    echo ""
done

# 分析package.json变更
echo "## Node.js依赖变更"
echo ""
if git diff --name-only "$BASE".."$HEAD" | grep -q "package.json"; then
    git diff "$BASE".."$HEAD" -- "package.json" | grep -E "^\+|^-" | grep -E "(\"|\')" | head -10
    echo ""
fi

# 检查依赖冲突
echo "## 依赖冲突检查"
echo ""
if [ -f "scripts/dependencies/check-conflicts.sh" ]; then
    ./scripts/dependencies/check-conflicts.sh || echo "检查完成"
fi

echo ""
echo "=========================================="
echo "分析完成"
echo "=========================================="









