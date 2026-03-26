#!/bin/bash
# 文档生成脚本（简化版）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "生成所有文档..."
python3 "$SCRIPT_DIR/generate-all.py"

echo "检查文档完整性..."
python3 "$SCRIPT_DIR/check-documentation.py"

echo "文档生成完成！"









