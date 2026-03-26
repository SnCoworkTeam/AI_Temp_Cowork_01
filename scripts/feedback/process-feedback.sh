#!/bin/bash
# 处理反馈队列

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "处理反馈队列"
echo "=========================================="

# 处理用户反馈
echo ""
echo "处理用户反馈..."
python3 << EOF
import json
from pathlib import Path
from datetime import datetime

project_root = Path("$PROJECT_ROOT")
feedback_dir = project_root / "feedback-loop"

# 统计反馈数量
stats = {
    "user_feedback": {
        "feature_requests": {"total": 0, "pending": 0},
        "bug_reports": {"total": 0, "pending": 0},
        "usability_feedback": {"total": 0, "pending": 0}
    },
    "development_feedback": {
        "code_reviews": {"total": 0, "pending": 0},
        "retrospectives": {"total": 0},
        "pain_points": {"total": 0, "pending": 0}
    }
}

# 统计用户反馈
for feedback_type in ["feature-requests", "bug-reports", "usability-feedback"]:
    dir_path = feedback_dir / "user-feedback" / feedback_type
    if dir_path.exists():
        files = list(dir_path.glob("*.md"))
        stats["user_feedback"][feedback_type.replace("-", "_")]["total"] = len(files)
        
        # 统计待处理（简化版，实际应该解析Markdown）
        pending = 0
        for file in files:
            try:
                content = file.read_text(encoding='utf-8')
                if "状态.*待" in content or "status.*pending" in content.lower():
                    pending += 1
            except:
                pass
        stats["user_feedback"][feedback_type.replace("-", "_")]["pending"] = pending

# 统计开发反馈
for feedback_type in ["code-reviews", "retrospectives", "pain-points"]:
    dir_path = feedback_dir / "development-feedback" / feedback_type
    if dir_path.exists():
        files = list(dir_path.glob("*.md"))
        key = feedback_type.replace("-", "_")
        stats["development_feedback"][key]["total"] = len(files)

# 输出统计
print("反馈统计:")
print(json.dumps(stats, indent=2, ensure_ascii=False))
EOF

echo ""
echo "=========================================="
echo "反馈处理完成"
echo "=========================================="









