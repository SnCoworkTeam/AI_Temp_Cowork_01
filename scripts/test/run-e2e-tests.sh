#!/bin/bash
# 运行端到端测试

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "🌐 运行端到端测试..."
python3 -m pytest \
    tests/test_e2e_procurement.py \
    tests/test_complete_real_world.py \
    -v \
    --tb=short \
    --timeout=300 \
    "$@"

