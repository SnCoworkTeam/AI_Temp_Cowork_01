#!/bin/bash
# 认证服务测试运行脚本

echo "=========================================="
echo "Auth Service Test Suite"
echo "=========================================="
echo ""

# 检查是否在auth-service目录
if [ ! -f "requirements.txt" ]; then
    echo "Error: This script should be run from auth-service directory"
    exit 1
fi

# 检查pytest是否安装
if ! python -c "import pytest" 2>/dev/null; then
    echo "Installing test dependencies..."
    pip install pytest pytest-asyncio pytest-cov pytest-mock faker -q
fi

echo "Running tests with coverage..."
echo ""

# 运行测试并生成覆盖率报告
pytest tests/ \
    --cov=src \
    --cov-report=html \
    --cov-report=term \
    --cov-report=xml \
    -v \
    --tb=short \
    2>&1 | tee test_output.log

TEST_EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed (exit code: $TEST_EXIT_CODE)"
fi

echo ""
echo "Coverage report generated:"
echo "  - HTML: htmlcov/index.html"
echo "  - XML: coverage.xml"
echo "  - Terminal output above"
echo ""

exit $TEST_EXIT_CODE
