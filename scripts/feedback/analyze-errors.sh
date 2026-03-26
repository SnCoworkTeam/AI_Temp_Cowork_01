#!/bin/bash
# 分析错误日志

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FEEDBACK_DIR="$PROJECT_ROOT/feedback-loop/system-feedback/error-analytics"

cd "$PROJECT_ROOT"

mkdir -p "$FEEDBACK_DIR"

echo "=========================================="
echo "分析错误日志"
echo "=========================================="

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 分析错误日志（简化版）
python3 << EOF
import json
from datetime import datetime
from pathlib import Path
import subprocess

project_root = Path("$PROJECT_ROOT")
feedback_dir = Path("$FEEDBACK_DIR")

# 简化的错误分析
# 实际应该从日志系统或监控系统获取

error_analysis = {
    "timestamp": "$TIMESTAMP",
    "error_summary": {
        "total_errors": 0,
        "errors_by_type": {},
        "errors_by_service": {},
        "top_errors": []
    },
    "trends": {
        "error_rate": "stable",
        "error_trend": "stable"
    },
    "recommendations": []
}

# 检查日志文件（如果存在）
log_files = list(project_root.glob("**/*.log"))
if log_files:
    # 简单的错误统计（实际应该使用专业的日志分析工具）
    error_count = 0
    for log_file in log_files[:5]:  # 只检查前5个日志文件
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if any(keyword in line.lower() for keyword in ['error', 'exception', 'failed']):
                        error_count += 1
        except:
            pass
    
    error_analysis["error_summary"]["total_errors"] = error_count

# 生成建议
if error_analysis["error_summary"]["total_errors"] > 100:
    error_analysis["recommendations"].append({
        "type": "error_rate",
        "priority": "high",
        "message": "错误数量较高，建议深入分析错误原因"
    })

# 保存分析
analysis_file = feedback_dir / f"error-analysis-{datetime.now().strftime('%Y%m%d')}.json"
with open(analysis_file, 'w', encoding='utf-8') as f:
    json.dump(error_analysis, f, indent=2, ensure_ascii=False)

print(f"✅ 错误分析完成")
print(f"分析文件: {analysis_file}")
print(f"错误总数: {error_analysis['error_summary']['total_errors']}")
print(f"建议数量: {len(error_analysis['recommendations'])}")
EOF

echo ""
echo "=========================================="
echo "错误分析完成"
echo "=========================================="









