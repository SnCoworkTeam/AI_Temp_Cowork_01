#!/bin/bash
# 生成代码健康度报告

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_DIR="$PROJECT_ROOT/code-health/reports"

cd "$PROJECT_ROOT"

mkdir -p "$REPORT_DIR"

echo "=========================================="
echo "生成代码健康度报告"
echo "=========================================="

# 生成Markdown报告
python3 << EOF
import json
from datetime import datetime
from pathlib import Path

project_root = Path("$PROJECT_ROOT")
metrics_dir = project_root / "code-health"
report_dir = Path("$REPORT_DIR")

# 读取最新指标
def load_latest_metric(metric_file):
    try:
        with open(metric_file, 'r') as f:
            data = json.load(f)
            if 'history' in data and len(data['history']) > 0:
                return data['history'][-1]
    except:
        pass
    return None

# 生成报告
report_lines = []
report_lines.append("# 代码健康度报告")
report_lines.append("")
report_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report_lines.append("")

# 1. 质量指标
report_lines.append("## 1. 质量指标")
report_lines.append("")

# 覆盖率
coverage = load_latest_metric(metrics_dir / "quality-metrics/coverage-trends/coverage-history.json")
if coverage:
    report_lines.append("### 代码覆盖率")
    report_lines.append(f"- **总体覆盖率**: {coverage.get('overall_coverage', 0):.2f}%")
    report_lines.append(f"- **覆盖行数**: {coverage.get('lines_covered', 0)} / {coverage.get('lines_total', 0)}")
    report_lines.append("")

# 复杂度
complexity = load_latest_metric(metrics_dir / "quality-metrics/complexity-trends/complexity-history.json")
if complexity:
    report_lines.append("### 代码复杂度")
    report_lines.append(f"- **平均复杂度**: {complexity.get('average_complexity', 0):.2f}")
    report_lines.append(f"- **最大复杂度**: {complexity.get('max_complexity', 0)}")
    report_lines.append(f"- **函数数量**: {complexity.get('function_count', 0)}")
    
    complex_funcs = complexity.get('complex_functions', [])
    if complex_funcs:
        report_lines.append("")
        report_lines.append("#### 高复杂度函数（前5）")
        for func in complex_funcs[:5]:
            report_lines.append(f"- `{func['file']}::{func['function']}`: {func['complexity']}")
    report_lines.append("")

# 技术债务
debt = load_latest_metric(metrics_dir / "quality-metrics/debt-tracking/debt-history.json")
if debt:
    report_lines.append("### 技术债务")
    report_lines.append(f"- **总债务**: {debt.get('total_debt', 0)} 点")
    report_lines.append(f"- **TODO/FIXME数量**: {debt.get('todo_count', 0)}")
    report_lines.append("")

# 2. 性能指标
report_lines.append("## 2. 性能指标")
report_lines.append("")

# 构建时间
build_time = load_latest_metric(metrics_dir / "performance-metrics/build-times/build-history.json")
if build_time:
    report_lines.append("### 构建时间")
    report_lines.append(f"- **总构建时间**: {build_time.get('total_build_time_seconds', 0)} 秒")
    report_lines.append("")

# 测试时间
test_time = load_latest_metric(metrics_dir / "performance-metrics/test-times/test-history.json")
if test_time:
    report_lines.append("### 测试时间")
    report_lines.append(f"- **总测试时间**: {test_time.get('total_test_time_seconds', 0)} 秒")
    report_lines.append("")

# 3. 健康度评分
report_lines.append("## 3. 健康度评分")
report_lines.append("")

# 计算健康度评分（简化）
score = 100
if coverage:
    if coverage.get('overall_coverage', 0) < 80:
        score -= 10
if complexity:
    if complexity.get('average_complexity', 0) > 10:
        score -= 10
if debt:
    if debt.get('total_debt', 0) > 200:
        score -= 10

health_level = "优秀" if score >= 90 else "良好" if score >= 80 else "一般" if score >= 70 else "需要改进"

report_lines.append(f"- **综合评分**: {score}/100")
report_lines.append(f"- **健康等级**: {health_level}")
report_lines.append("")

# 4. 改进建议
report_lines.append("## 4. 改进建议")
report_lines.append("")

if coverage and coverage.get('overall_coverage', 0) < 80:
    report_lines.append("- ⚠️ **代码覆盖率不足**: 建议提高测试覆盖率到80%以上")
    report_lines.append("")

if complexity and complexity.get('average_complexity', 0) > 10:
    report_lines.append("- ⚠️ **代码复杂度过高**: 建议重构高复杂度函数")
    report_lines.append("")

if debt and debt.get('total_debt', 0) > 200:
    report_lines.append("- ⚠️ **技术债务累积**: 建议制定债务偿还计划")
    report_lines.append("")

# 保存报告
report_file = report_dir / "health-report.md"
with open(report_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))

print(f"✅ 报告已生成: {report_file}")
EOF

echo ""
echo "=========================================="
echo "报告生成完成"
echo "=========================================="









