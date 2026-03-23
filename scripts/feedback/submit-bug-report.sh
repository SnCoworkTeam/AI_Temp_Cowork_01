#!/bin/bash
# 提交缺陷报告

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FEEDBACK_DIR="$PROJECT_ROOT/feedback-loop/user-feedback/bug-reports"

cd "$PROJECT_ROOT"

BUG_DESCRIPTION="$1"

if [ -z "$BUG_DESCRIPTION" ]; then
    echo "用法: $0 \"缺陷描述\""
    echo "示例: $0 \"登录功能无法正常工作\""
    exit 1
fi

# 生成缺陷报告编号
BUG_NUM=$(ls -1 "$FEEDBACK_DIR"/*.md 2>/dev/null | wc -l | xargs)
BUG_NUM=$((BUG_NUM + 1))
BUG_ID=$(printf "BUG-%04d" "$BUG_NUM")

# 创建缺陷报告文件
BUG_FILE="$FEEDBACK_DIR/$BUG_ID.md"

# 从模板创建
TEMPLATE="$FEEDBACK_DIR/template.md"
if [ -f "$TEMPLATE" ]; then
    cp "$TEMPLATE" "$BUG_FILE"
    
    # 替换基本信息
    sed -i.bak "s/BUG-XXXX/$BUG_ID/g" "$BUG_FILE"
    sed -i.bak "s/YYYY-MM-DD/$(date +%Y-%m-%d)/g" "$BUG_FILE"
    sed -i.bak "s/\[简要描述缺陷\]/$BUG_DESCRIPTION/g" "$BUG_FILE"
    rm -f "$BUG_FILE.bak"
else
    # 创建基本文件
    cat > "$BUG_FILE" << EOF
# 缺陷报告: $BUG_DESCRIPTION

**报告编号**: $BUG_ID  
**报告日期**: $(date +%Y-%m-%d)  
**状态**: 待确认  
**严重性**: Medium

## 缺陷概述

### 缺陷标题
$BUG_DESCRIPTION

### 缺陷描述
[详细描述缺陷现象]

## 复现步骤

### 操作步骤
1. [步骤1]
2. [步骤2]
3. [步骤3]

### 预期结果
[描述预期结果]

### 实际结果
[描述实际结果]

EOF
fi

echo "=========================================="
echo "缺陷报告已创建"
echo "=========================================="
echo "编号: $BUG_ID"
echo "文件: $BUG_FILE"
echo ""
echo "请编辑文件填写详细信息"
echo ""









