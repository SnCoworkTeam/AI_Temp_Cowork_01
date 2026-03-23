#!/bin/bash
# 运行集成测试

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "🔗 运行集成测试..."
python3 -m pytest tests/test-integration/ -v --tb=short -m "integration" "$@"

