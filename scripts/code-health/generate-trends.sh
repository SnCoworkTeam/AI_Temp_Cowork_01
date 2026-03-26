#!/bin/bash
# 生成趋势分析

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "生成趋势分析"
echo "=========================================="

python3 << EOF
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

project_root = Path("$PROJECT_ROOT")
metrics_dir = project_root / "code-health"
trends_dir = project_root / "code-health/trends"

trends_dir.mkdir(parents=True, exist_ok=True)

def load_history(metric_file):
    try:
        with open(metric_file, 'r') as f:
            data = json.load(f)
            return data.get('history', [])
    except:
        return []

# 生成覆盖率趋势
coverage_history = load_history(metrics_dir / "quality-metrics/coverage-trends/coverage-history.json")
if coverage_history:
    trend_data = {
        "metric": "coverage",
        "data_points": len(coverage_history),
        "trend": "stable",
        "latest": coverage_history[-1].get('overall_coverage', 0),
        "first": coverage_history[0].get('overall_coverage', 0) if coverage_history else 0,
        "history": coverage_history
    }
    
    # 计算趋势
    if len(coverage_history) >= 2:
        latest = coverage_history[-1].get('overall_coverage', 0)
        previous = coverage_history[-2].get('overall_coverage', 0)
        if latest > previous + 1:
            trend_data["trend"] = "improving"
        elif latest < previous - 1:
            trend_data["trend"] = "declining"
    
    with open(trends_dir / "coverage-trend.json", 'w', encoding='utf-8') as f:
        json.dump(trend_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 覆盖率趋势: {trend_data['trend']} ({trend_data['latest']:.2f}%)")

# 生成复杂度趋势
complexity_history = load_history(metrics_dir / "quality-metrics/complexity-trends/complexity-history.json")
if complexity_history:
    trend_data = {
        "metric": "complexity",
        "data_points": len(complexity_history),
        "trend": "stable",
        "latest": complexity_history[-1].get('average_complexity', 0),
        "first": complexity_history[0].get('average_complexity', 0) if complexity_history else 0,
        "history": complexity_history
    }
    
    if len(complexity_history) >= 2:
        latest = complexity_history[-1].get('average_complexity', 0)
        previous = complexity_history[-2].get('average_complexity', 0)
        if latest < previous - 0.5:
            trend_data["trend"] = "improving"
        elif latest > previous + 0.5:
            trend_data["trend"] = "declining"
    
    with open(trends_dir / "complexity-trend.json", 'w', encoding='utf-8') as f:
        json.dump(trend_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 复杂度趋势: {trend_data['trend']} (平均={trend_data['latest']:.2f})")

# 生成技术债务趋势
debt_history = load_history(metrics_dir / "quality-metrics/debt-tracking/debt-history.json")
if debt_history:
    trend_data = {
        "metric": "debt",
        "data_points": len(debt_history),
        "trend": "stable",
        "latest": debt_history[-1].get('total_debt', 0),
        "first": debt_history[0].get('total_debt', 0) if debt_history else 0,
        "history": debt_history
    }
    
    if len(debt_history) >= 2:
        latest = debt_history[-1].get('total_debt', 0)
        previous = debt_history[-2].get('total_debt', 0)
        if latest < previous - 10:
            trend_data["trend"] = "improving"
        elif latest > previous + 10:
            trend_data["trend"] = "declining"
    
    with open(trends_dir / "debt-trend.json", 'w', encoding='utf-8') as f:
        json.dump(trend_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 技术债务趋势: {trend_data['trend']} ({trend_data['latest']}点)")

# 生成构建时间趋势
build_history = load_history(metrics_dir / "performance-metrics/build-times/build-history.json")
if build_history:
    trend_data = {
        "metric": "build_time",
        "data_points": len(build_history),
        "trend": "stable",
        "latest": build_history[-1].get('total_build_time_seconds', 0),
        "first": build_history[0].get('total_build_time_seconds', 0) if build_history else 0,
        "history": build_history
    }
    
    if len(build_history) >= 2:
        latest = build_history[-1].get('total_build_time_seconds', 0)
        previous = build_history[-2].get('total_build_time_seconds', 0)
        if latest < previous - 10:
            trend_data["trend"] = "improving"
        elif latest > previous + 10:
            trend_data["trend"] = "declining"
    
    with open(trends_dir / "build-time-trend.json", 'w', encoding='utf-8') as f:
        json.dump(trend_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 构建时间趋势: {trend_data['trend']} ({trend_data['latest']}秒)")

print("")
print("==========================================")
print("趋势分析完成")
print("==========================================")
EOF









