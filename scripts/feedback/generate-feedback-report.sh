#!/bin/bash
# 生成反馈报告

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_DIR="$PROJECT_ROOT/feedback-loop/reports"

cd "$PROJECT_ROOT"

mkdir -p "$REPORT_DIR"

echo "=========================================="
echo "生成反馈报告"
echo "=========================================="

python3 << EOF
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

project_root = Path("$PROJECT_ROOT")
feedback_dir = project_root / "feedback-loop"
report_dir = Path("$REPORT_DIR")

# 生成报告
report_lines = []
report_lines.append("# 反馈和持续改进报告")
report_lines.append("")
report_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report_lines.append("")

# 统计反馈
stats = defaultdict(int)

# 用户反馈统计
for feedback_type in ["feature-requests", "bug-reports", "usability-feedback"]:
    dir_path = feedback_dir / "user-feedback" / feedback_type
    if dir_path.exists():
        count = len(list(dir_path.glob("*.md")))
        stats[feedback_type] = count

# 开发反馈统计
for feedback_type in ["code-reviews", "retrospectives", "pain-points", "improvement-ideas"]:
    dir_path = feedback_dir / "development-feedback" / feedback_type
    if dir_path.exists():
        count = len(list(dir_path.glob("*.md")))
        stats[feedback_type] = count

# 生成报告内容
report_lines.append("## 反馈统计")
report_lines.append("")

report_lines.append("### 用户反馈")
report_lines.append(f"- **功能请求**: {stats['feature-requests']} 个")
report_lines.append(f"- **缺陷报告**: {stats['bug-reports']} 个")
report_lines.append(f"- **可用性反馈**: {stats['usability-feedback']} 个")
report_lines.append("")

report_lines.append("### 开发反馈")
report_lines.append(f"- **代码审查**: {stats['code-reviews']} 次")
report_lines.append(f"- **迭代回顾**: {stats['retrospectives']} 次")
report_lines.append(f"- **痛点收集**: {stats['pain-points']} 个")
report_lines.append(f"- **改进建议**: {stats['improvement-ideas']} 个")
report_lines.append("")

report_lines.append("## 改进建议")
report_lines.append("")
report_lines.append("基于反馈分析，建议关注以下方面：")
report_lines.append("")
report_lines.append("- 及时处理用户反馈")
report_lines.append("- 跟踪改进实施效果")
report_lines.append("- 持续优化开发流程")
report_lines.append("")

# 保存报告
report_file = report_dir / f"feedback-report-{datetime.now().strftime('%Y%m%d')}.md"
with open(report_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))

print(f"✅ 反馈报告已生成: {report_file}")
EOF

echo ""
echo "=========================================="
echo "报告生成完成"
echo "=========================================="









