#!/bin/bash
# 生成代码健康度汇总

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

python3 << EOF
import json
from datetime import datetime
from pathlib import Path

project_root = Path("$PROJECT_ROOT")
metrics_dir = project_root / "code-health"

# 生成JSON汇总
summary = {
    "timestamp": datetime.now().isoformat(),
    "quality_metrics": {},
    "performance_metrics": {},
    "health_score": 0
}

# 读取最新指标
def load_latest(metric_file):
    try:
        with open(metric_file, 'r') as f:
            data = json.load(f)
            if 'history' in data and len(data['history']) > 0:
                return data['history'][-1]
    except:
        pass
    return None

# 质量指标
coverage = load_latest(metrics_dir / "quality-metrics/coverage-trends/coverage-history.json")
if coverage:
    summary["quality_metrics"]["coverage"] = coverage.get("overall_coverage", 0)

complexity = load_latest(metrics_dir / "quality-metrics/complexity-trends/complexity-history.json")
if complexity:
    summary["quality_metrics"]["average_complexity"] = complexity.get("average_complexity", 0)
    summary["quality_metrics"]["max_complexity"] = complexity.get("max_complexity", 0)

debt = load_latest(metrics_dir / "quality-metrics/debt-tracking/debt-history.json")
if debt:
    summary["quality_metrics"]["total_debt"] = debt.get("total_debt", 0)

# 性能指标
build_time = load_latest(metrics_dir / "performance-metrics/build-times/build-history.json")
if build_time:
    summary["performance_metrics"]["build_time_seconds"] = build_time.get("total_build_time_seconds", 0)

test_time = load_latest(metrics_dir / "performance-metrics/test-times/test-history.json")
if test_time:
    summary["performance_metrics"]["test_time_seconds"] = test_time.get("total_test_time_seconds", 0)

# 计算健康评分
score = 100
if coverage and coverage.get('overall_coverage', 0) < 80:
    score -= 10
if complexity and complexity.get('average_complexity', 0) > 10:
    score -= 10
if debt and debt.get('total_debt', 0) > 200:
    score -= 10

summary["health_score"] = score

# 保存汇总
summary_file = metrics_dir / "summary.json"
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print(f"✅ 汇总已生成: {summary_file}")
EOF









