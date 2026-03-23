#!/bin/bash
# 运行测试脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "运行测试套件"
echo "=========================================="

# 解析参数
TEST_TYPE="${1:-all}"
COVERAGE="${2:-true}"

case "$TEST_TYPE" in
    unit)
        echo "运行单元测试..."
        if [ "$COVERAGE" = "true" ]; then
            pytest -m unit --cov=. --cov-report=html --cov-report=term
        else
            pytest -m unit
        fi
        ;;
    integration)
        echo "运行集成测试..."
        pytest -m integration -v
        ;;
    performance)
        echo "运行性能测试..."
        pytest -m performance -v
        ;;
    security)
        echo "运行安全测试..."
        pytest -m security -v
        ;;
    all)
        echo "运行所有测试..."
        if [ "$COVERAGE" = "true" ]; then
            pytest --cov=. --cov-report=html --cov-report=term --cov-report=json
        else
            pytest
        fi
        ;;
    *)
        echo "用法: $0 [unit|integration|performance|security|all] [coverage]"
        exit 1
        ;;
esac

echo "=========================================="
echo "测试完成"
echo "=========================================="









