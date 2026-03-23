#!/bin/bash
# 收集迭代回顾

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FEEDBACK_DIR="$PROJECT_ROOT/feedback-loop/development-feedback/retrospectives"

cd "$PROJECT_ROOT"

ITERATION_START="$1"
ITERATION_END="$2"

if [ -z "$ITERATION_START" ] || [ -z "$ITERATION_END" ]; then
    echo "用法: $0 迭代开始日期 迭代结束日期"
    echo "示例: $0 2024-01-01 2024-01-14"
    exit 1
fi

# 生成回顾编号
RETRO_NUM=$(ls -1 "$FEEDBACK_DIR"/*.md 2>/dev/null | wc -l | xargs)
RETRO_NUM=$((RETRO_NUM + 1))
RETRO_ID=$(printf "RETRO-%04d" "$RETRO_NUM")

# 创建回顾文件
RETRO_FILE="$FEEDBACK_DIR/$RETRO_ID.md"

# 从模板创建
TEMPLATE="$FEEDBACK_DIR/template.md"
if [ -f "$TEMPLATE" ]; then
    cp "$TEMPLATE" "$RETRO_FILE"
    
    # 替换基本信息
    sed -i.bak "s/RETRO-XXXX/$RETRO_ID/g" "$RETRO_FILE"
    sed -i.bak "s/YYYY-MM-DD 至 YYYY-MM-DD/$ITERATION_START 至 $ITERATION_END/g" "$RETRO_FILE"
    sed -i.bak "s/日期: YYYY-MM-DD/日期: $(date +%Y-%m-%d)/g" "$RETRO_FILE"
    rm -f "$RETRO_FILE.bak"
else
    # 创建基本文件
    cat > "$RETRO_FILE" << EOF
# 迭代回顾

**回顾编号**: $RETRO_ID  
**迭代周期**: $ITERATION_START 至 $ITERATION_END  
**日期**: $(date +%Y-%m-%d)

## 迭代概述

### 迭代目标
[描述迭代目标]

## 做得好的

1. [经验1]
2. [经验2]

## 需要改进

1. [问题1]
2. [问题2]

## 行动计划

- [ ] [任务1]

EOF
fi

echo "=========================================="
echo "迭代回顾已创建"
echo "=========================================="
echo "编号: $RETRO_ID"
echo "文件: $RETRO_FILE"
echo ""
echo "请编辑文件填写回顾内容"
echo ""









