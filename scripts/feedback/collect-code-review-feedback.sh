#!/bin/bash
# 收集代码审查反馈

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FEEDBACK_DIR="$PROJECT_ROOT/feedback-loop/development-feedback/code-reviews"

cd "$PROJECT_ROOT"

PR_NUMBER="$1"
REVIEWER="$2"

if [ -z "$PR_NUMBER" ] || [ -z "$REVIEWER" ]; then
    echo "用法: $0 PR编号 审查人"
    echo "示例: $0 123 张三"
    exit 1
fi

# 生成审查编号
REVIEW_NUM=$(ls -1 "$FEEDBACK_DIR"/*.md 2>/dev/null | wc -l | xargs)
REVIEW_NUM=$((REVIEW_NUM + 1))
REVIEW_ID=$(printf "REVIEW-%04d" "$REVIEW_NUM")

# 创建审查文件
REVIEW_FILE="$FEEDBACK_DIR/$REVIEW_ID.md"

# 从模板创建
TEMPLATE="$FEEDBACK_DIR/template.md"
if [ -f "$TEMPLATE" ]; then
    cp "$TEMPLATE" "$REVIEW_FILE"
    
    # 替换基本信息
    sed -i.bak "s/REVIEW-XXXX/$REVIEW_ID/g" "$REVIEW_FILE"
    sed -i.bak "s/YYYY-MM-DD/$(date +%Y-%m-%d)/g" "$REVIEW_FILE"
    sed -i.bak "s/\[姓名\]/$REVIEWER/g" "$REVIEW_FILE"
    sed -i.bak "s/#XXXX/#$PR_NUMBER/g" "$REVIEW_FILE"
    rm -f "$REVIEW_FILE.bak"
else
    # 创建基本文件
    cat > "$REVIEW_FILE" << EOF
# 代码审查反馈

**审查编号**: $REVIEW_ID  
**审查日期**: $(date +%Y-%m-%d)  
**审查人**: $REVIEWER  
**PR编号**: #$PR_NUMBER  
**状态**: 待审查

## 审查概述

### 代码变更
- **文件数量**: [待填写]
- **代码行数**: [待填写]

## 代码质量反馈

[填写审查反馈]

EOF
fi

echo "=========================================="
echo "代码审查反馈已创建"
echo "=========================================="
echo "编号: $REVIEW_ID"
echo "文件: $REVIEW_FILE"
echo ""
echo "请编辑文件填写审查反馈"
echo ""









