#!/bin/bash
# 收集所有代码健康度指标

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "收集代码健康度指标"
echo "=========================================="

# 收集质量指标
echo ""
echo "收集质量指标..."
./scripts/code-health/collect-quality-metrics.sh

# 收集性能指标
echo ""
echo "收集性能指标..."
./scripts/code-health/collect-performance-metrics.sh

# 生成汇总报告
echo ""
echo "生成汇总报告..."
./scripts/code-health/generate-summary.sh

echo ""
echo "=========================================="
echo "指标收集完成"
echo "=========================================="









