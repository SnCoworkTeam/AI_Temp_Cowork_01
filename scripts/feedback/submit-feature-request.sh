#!/bin/bash
# 提交功能请求

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FEEDBACK_DIR="$PROJECT_ROOT/feedback-loop/user-feedback/feature-requests"

cd "$PROJECT_ROOT"

FEATURE_DESCRIPTION="$1"

if [ -z "$FEATURE_DESCRIPTION" ]; then
    echo "用法: $0 \"功能描述\""
    echo "示例: $0 \"添加用户权限管理功能\""
    exit 1
fi

# 生成功能请求编号
FEATURE_NUM=$(ls -1 "$FEEDBACK_DIR"/*.md 2>/dev/null | wc -l | xargs)
FEATURE_NUM=$((FEATURE_NUM + 1))
FEATURE_ID=$(printf "FEATURE-%04d" "$FEATURE_NUM")

# 创建功能请求文件
FEATURE_FILE="$FEEDBACK_DIR/$FEATURE_ID.md"

# 从模板创建
TEMPLATE="$FEEDBACK_DIR/template.md"
if [ -f "$TEMPLATE" ]; then
    cp "$TEMPLATE" "$FEATURE_FILE"
    
    # 替换基本信息
    sed -i.bak "s/FEATURE-XXXX/$FEATURE_ID/g" "$FEATURE_FILE"
    sed -i.bak "s/YYYY-MM-DD/$(date +%Y-%m-%d)/g" "$FEATURE_FILE"
    sed -i.bak "s/\[简要描述功能\]/$FEATURE_DESCRIPTION/g" "$FEATURE_FILE"
    rm -f "$FEATURE_FILE.bak"
else
    # 创建基本文件
    cat > "$FEATURE_FILE" << EOF
# 功能请求: $FEATURE_DESCRIPTION

**请求编号**: $FEATURE_ID  
**提交日期**: $(date +%Y-%m-%d)  
**状态**: 待评估

## 功能概述

### 功能标题
$FEATURE_DESCRIPTION

### 功能描述
[详细描述功能需求]

## 业务价值

### 解决的问题
[描述这个功能解决什么问题]

## 功能需求

### 核心功能
1. [功能1]
2. [功能2]

EOF
fi

echo "=========================================="
echo "功能请求已创建"
echo "=========================================="
echo "编号: $FEATURE_ID"
echo "文件: $FEATURE_FILE"
echo ""
echo "请编辑文件填写详细信息"
echo ""









