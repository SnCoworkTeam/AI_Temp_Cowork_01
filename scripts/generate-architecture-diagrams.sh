#!/bin/bash
# PlantUML架构图生成脚本（Linux/Mac版本）

OUTPUT_DIR="${1:-docs/images/architecture}"
FORMAT="${2:-png}"
SOURCE_DIR="${3:-docs/architecture-docs}"

echo "=========================================="
echo "PlantUML 架构图生成工具"
echo "=========================================="
echo ""

# 检查PlantUML是否安装
if ! command -v plantuml &> /dev/null; then
    echo "错误: 未找到PlantUML命令"
    echo ""
    echo "请先安装PlantUML:"
    echo "  sudo apt-get install plantuml  # Linux"
    echo "  或"
    echo "  brew install plantuml  # macOS"
    echo ""
    exit 1
fi

echo "✓ PlantUML已安装: $(which plantuml)"
echo ""

# 创建输出目录
mkdir -p "$OUTPUT_DIR"
echo "✓ 输出目录: $OUTPUT_DIR"
echo ""

# 查找所有.puml文件
PUML_FILES=$(find "$SOURCE_DIR" -name "*.puml" -type f)

if [ -z "$PUML_FILES" ]; then
    echo "错误: 未找到.puml文件"
    exit 1
fi

FILE_COUNT=$(echo "$PUML_FILES" | wc -l)
echo "找到 $FILE_COUNT 个PlantUML文件"
echo ""

# 生成图片
echo "开始生成图片..."
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0

# 构建格式参数
FORMAT_FLAG=""
case "$FORMAT" in
    svg)
        FORMAT_FLAG="-tsvg"
        ;;
    pdf)
        FORMAT_FLAG="-tpdf"
        ;;
    *)
        FORMAT_FLAG="-tpng"
        ;;
esac

while IFS= read -r file; do
    if [ -f "$file" ]; then
        filename=$(basename "$file" .puml)
        echo "生成: $(basename "$file") -> $OUTPUT_DIR/$filename.$FORMAT"
        
        if plantuml $FORMAT_FLAG -o "$OUTPUT_DIR" "$file" 2>/dev/null; then
            echo "  ✓ 成功"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo "  ✗ 失败"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    fi
done <<< "$PUML_FILES"

echo ""
echo "=========================================="
echo "生成完成"
echo "=========================================="
echo "成功: $SUCCESS_COUNT"
echo "失败: $FAIL_COUNT"
echo "输出目录: $OUTPUT_DIR"
echo ""




