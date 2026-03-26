#!/bin/bash
# SAP元数据语义分析构建脚本 (Bash)
# 用于快速启动语义分析构建

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 默认参数
BATCH_SIZE=50
ASSETS_OFFSET=0
ENTITIES_OFFSET=0
RESUME=false
NO_RESUME=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --assets-offset)
            ASSETS_OFFSET="$2"
            shift 2
            ;;
        --entities-offset)
            ENTITIES_OFFSET="$2"
            shift 2
            ;;
        --resume)
            RESUME=true
            shift
            ;;
        --no-resume)
            NO_RESUME=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}SAP元数据语义分析构建${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 检查Python环境
echo -e "${YELLOW}检查Python环境...${NC}"
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python未安装或不在PATH中${NC}"
    exit 1
fi

PYTHON_CMD=$(command -v python3 || command -v python)
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"
echo ""

# 检查服务连接
echo -e "${YELLOW}检查服务连接...${NC}"

# 检查元数据服务
METADATA_URL=${METADATA_SERVICE_URL:-http://localhost:8005}
echo -e "  元数据服务: ${METADATA_URL}"

if curl -s -f --max-time 5 "${METADATA_URL}/health" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ 元数据服务连接正常${NC}"
else
    echo -e "  ${YELLOW}⚠️  元数据服务连接失败${NC}"
    echo -e "     请确保元数据服务正在运行"
fi

# 检查知识库服务
KB_URL=${KNOWLEDGE_BASE_URL:-http://localhost:8004}
echo -e "  知识库服务: ${KB_URL}"

if curl -s -f --max-time 5 "${KB_URL}/api/health" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ 知识库服务连接正常${NC}"
else
    echo -e "  ${YELLOW}⚠️  知识库服务连接失败${NC}"
    echo -e "     请确保知识库服务正在运行"
    echo ""
    read -p "是否继续? (Y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# 构建参数
ARGS=()
if [ -n "$BATCH_SIZE" ]; then
    ARGS+=("--batch-size" "$BATCH_SIZE")
fi
if [ -n "$ASSETS_OFFSET" ]; then
    ARGS+=("--assets-offset" "$ASSETS_OFFSET")
fi
if [ -n "$ENTITIES_OFFSET" ]; then
    ARGS+=("--entities-offset" "$ENTITIES_OFFSET")
fi
if [ "$RESUME" = true ]; then
    ARGS+=("--resume")
fi
if [ "$NO_RESUME" = true ]; then
    ARGS+=("--no-resume")
fi

# 显示构建参数
echo -e "${YELLOW}构建参数:${NC}"
echo -e "  批次大小: ${BATCH_SIZE}"
echo -e "  数据资产偏移: ${ASSETS_OFFSET}"
echo -e "  业务实体偏移: ${ENTITIES_OFFSET}"
if [ "$RESUME" = true ]; then
    echo -e "  从进度文件恢复: 是"
fi
echo ""

# 执行构建
echo -e "${CYAN}开始构建...${NC}"
echo ""

$PYTHON_CMD build_semantic_analysis.py "${ARGS[@]}"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 构建完成${NC}"
else
    echo -e "${RED}❌ 构建失败 (退出码: $EXIT_CODE)${NC}"
    echo ""
    echo -e "${YELLOW}提示:${NC}"
    echo -e "  - 检查服务是否正常运行"
    echo -e "  - 查看错误日志"
    echo -e "  - 使用 --resume 参数继续构建"
fi

exit $EXIT_CODE

