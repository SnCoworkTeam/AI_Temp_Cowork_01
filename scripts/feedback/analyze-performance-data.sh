#!/bin/bash
# 分析性能数据

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FEEDBACK_DIR="$PROJECT_ROOT/feedback-loop/system-feedback/performance-data"

cd "$PROJECT_ROOT"

mkdir -p "$FEEDBACK_DIR"

echo "=========================================="
echo "分析性能数据"
echo "=========================================="

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 分析性能数据
python3 << EOF
import json
from datetime import datetime
from pathlib import Path

project_root = Path("$PROJECT_ROOT")
metrics_dir = project_root / "code-health/performance-metrics"
feedback_dir = Path("$FEEDBACK_DIR")

# 读取性能指标
def load_latest(metric_file):
    try:
        with open(metric_file, 'r') as f:
            data = json.load(f)
            if 'history' in data and len(data['history']) > 0:
                return data['history'][-1]
    except:
        pass
    return None

# 收集性能数据
performance_data = {
    "timestamp": "$TIMESTAMP",
    "build_time": {},
    "test_time": {},
    "startup_time": {},
    "memory_usage": {}
}

# 构建时间
build_time = load_latest(metrics_dir / "build-times/build-history.json")
if build_time:
    performance_data["build_time"] = {
        "total_seconds": build_time.get("total_build_time_seconds", 0),
        "status": "good" if build_time.get("total_build_time_seconds", 0) < 600 else "warning"
    }

# 测试时间
test_time = load_latest(metrics_dir / "performance-metrics/test-times/test-history.json")
if test_time:
    performance_data["test_time"] = {
        "total_seconds": test_time.get("total_test_time_seconds", 0),
        "status": "good" if test_time.get("total_test_time_seconds", 0) < 600 else "warning"
    }

# 生成分析报告
analysis = {
    "timestamp": "$TIMESTAMP",
    "summary": {
        "build_time_status": performance_data["build_time"].get("status", "unknown"),
        "test_time_status": performance_data["test_time"].get("status", "unknown")
    },
    "recommendations": []
}

# 生成建议
if performance_data["build_time"].get("total_seconds", 0) > 600:
    analysis["recommendations"].append({
        "type": "build_time",
        "priority": "medium",
        "message": "构建时间超过10分钟，建议优化构建流程"
    })

if performance_data["test_time"].get("total_seconds", 0) > 600:
    analysis["recommendations"].append({
        "type": "test_time",
        "priority": "medium",
        "message": "测试时间超过10分钟，建议优化测试套件"
    })

# 保存数据
data_file = feedback_dir / f"performance-analysis-{datetime.now().strftime('%Y%m%d')}.json"
with open(data_file, 'w', encoding='utf-8') as f:
    json.dump({
        "performance_data": performance_data,
        "analysis": analysis
    }, f, indent=2, ensure_ascii=False)

print(f"✅ 性能数据分析完成")
print(f"数据文件: {data_file}")
print(f"建议数量: {len(analysis['recommendations'])}")
EOF

echo ""
echo "=========================================="
echo "性能数据分析完成"
echo "=========================================="









