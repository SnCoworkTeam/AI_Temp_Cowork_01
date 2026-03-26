#!/bin/bash
# 检查代码健康度告警

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "检查代码健康度告警"
echo "=========================================="

ALERTS=0

# 读取最新指标
python3 << EOF
import json
from datetime import datetime
from pathlib import Path
import sys

project_root = Path("$PROJECT_ROOT")
metrics_dir = project_root / "code-health"

def load_latest(metric_file):
    try:
        with open(metric_file, 'r') as f:
            data = json.load(f)
            if 'history' in data and len(data['history']) > 0:
                return data['history'][-1]
    except:
        pass
    return None

alerts = []

# 检查覆盖率告警
coverage = load_latest(metrics_dir / "quality-metrics/coverage-trends/coverage-history.json")
if coverage:
    cov = coverage.get('overall_coverage', 100)
    if cov < 80:
        alerts.append({
            "level": "high" if cov < 70 else "medium",
            "type": "coverage",
            "message": f"代码覆盖率低于目标: {cov:.2f}% < 80%"
        })

# 检查复杂度告警
complexity = load_latest(metrics_dir / "quality-metrics/complexity-trends/complexity-history.json")
if complexity:
    avg_comp = complexity.get('average_complexity', 0)
    if avg_comp > 10:
        alerts.append({
            "level": "high" if avg_comp > 15 else "medium",
            "type": "complexity",
            "message": f"平均复杂度过高: {avg_comp:.2f} > 10"
        })
    
    max_comp = complexity.get('max_complexity', 0)
    if max_comp > 20:
        alerts.append({
            "level": "critical",
            "type": "complexity",
            "message": f"最大复杂度过高: {max_comp} > 20"
        })

# 检查技术债务告警
debt = load_latest(metrics_dir / "quality-metrics/debt-tracking/debt-history.json")
if debt:
    total_debt = debt.get('total_debt', 0)
    if total_debt > 200:
        alerts.append({
            "level": "high" if total_debt > 300 else "medium",
            "type": "debt",
            "message": f"技术债务过高: {total_debt}点 > 200点"
        })

# 检查构建时间告警
build_time = load_latest(metrics_dir / "performance-metrics/build-times/build-history.json")
if build_time:
    bt = build_time.get('total_build_time_seconds', 0)
    if bt > 600:  # 10分钟
        alerts.append({
            "level": "medium",
            "type": "performance",
            "message": f"构建时间过长: {bt}秒 > 600秒"
        })

# 检查测试时间告警
test_time = load_latest(metrics_dir / "performance-metrics/test-times/test-history.json")
if test_time:
    tt = test_time.get('total_test_time_seconds', 0)
    if tt > 600:  # 10分钟
        alerts.append({
            "level": "medium",
            "type": "performance",
            "message": f"测试时间过长: {tt}秒 > 600秒"
        })

# 输出告警
if alerts:
    print("")
    print("⚠️  发现告警:")
    print("")
    
    critical = [a for a in alerts if a['level'] == 'critical']
    high = [a for a in alerts if a['level'] == 'high']
    medium = [a for a in alerts if a['level'] == 'medium']
    
    if critical:
        print("🔴 Critical:")
        for alert in critical:
            print(f"  - {alert['message']}")
        print("")
    
    if high:
        print("🟠 High:")
        for alert in high:
            print(f"  - {alert['message']}")
        print("")
    
    if medium:
        print("🟡 Medium:")
        for alert in medium:
            print(f"  - {alert['message']}")
        print("")
    
    # 保存告警
    alert_file = metrics_dir / "alerts.json"
    with open(alert_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "alerts": alerts,
            "total": len(alerts)
        }, f, indent=2, ensure_ascii=False)
    
    sys.exit(1)
else:
    print("")
    print("✅ 未发现告警")
    sys.exit(0)
EOF

EXIT_CODE=$?

if [ $EXIT_CODE -eq 1 ]; then
    echo ""
    echo "=========================================="
    echo "发现告警，请及时处理"
    echo "=========================================="
    exit 1
else
    echo ""
    echo "=========================================="
    echo "检查完成，未发现告警"
    echo "=========================================="
    exit 0
fi

