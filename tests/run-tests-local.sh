#!/bin/bash
# 本地测试运行脚本（Bash）
# 用于在本地环境运行测试并检查覆盖率

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 解析参数
TEST_TYPE="${1:-all}"
COVERAGE="${2:-false}"
VERBOSE="${3:-false}"

echo "=========================================="
echo -e "${CYAN}本地测试运行${NC}"
echo "=========================================="
echo ""

# 检查pytest是否安装
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}安装pytest...${NC}"
    pip install pytest pytest-asyncio pytest-cov pytest-mock httpx
fi

# 构建pytest命令
PYTEST_CMD="pytest"

if [ "$VERBOSE" = "true" ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
else
    PYTEST_CMD="$PYTEST_CMD -q"
fi

if [ "$COVERAGE" = "true" ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=html --cov-report=term-missing --cov-report=json"
fi

# 根据测试类型运行
case "$TEST_TYPE" in
    unit)
        echo -e "${BLUE}运行单元测试...${NC}"
        $PYTEST_CMD -m unit
        ;;
    integration)
        echo -e "${BLUE}运行集成测试...${NC}"
        $PYTEST_CMD -m integration
        ;;
    metadata-service|database|workflow-engine|auth-service|knowledge-base|mcp-gateway)
        echo -e "${BLUE}运行${TEST_TYPE}测试...${NC}"
        $PYTEST_CMD "${TEST_TYPE}/tests"
        ;;
    all)
        echo -e "${BLUE}运行所有测试...${NC}"
        
        services=("metadata-service" "database" "workflow-engine" "auth-service" "knowledge-base" "mcp-gateway")
        failed_services=()
        
        for service in "${services[@]}"; do
            echo ""
            echo "------------------------------------------"
            echo -e "${YELLOW}测试: $service${NC}"
            echo "------------------------------------------"
            
            if $PYTEST_CMD "${service}/tests"; then
                echo -e "${GREEN}✓ $service 测试通过${NC}"
            else
                echo -e "${RED}✗ $service 测试失败${NC}"
                failed_services+=("$service")
            fi
        done
        
        echo ""
        echo "=========================================="
        echo -e "${CYAN}测试总结${NC}"
        echo "=========================================="
        
        if [ ${#failed_services[@]} -eq 0 ]; then
            echo -e "${GREEN}✓ 所有服务测试通过！${NC}"
        else
            echo -e "${RED}✗ 以下服务测试失败:${NC}"
            for service in "${failed_services[@]}"; do
                echo -e "  ${RED}- $service${NC}"
            done
        fi
        
        if [ "$COVERAGE" = "true" ]; then
            echo ""
            echo -e "${CYAN}覆盖率报告已生成: htmlcov/index.html${NC}"
        fi
        
        exit 0
        ;;
    *)
        echo "用法: $0 [all|unit|integration|service-name] [coverage] [verbose]"
        echo ""
        echo "示例:"
        echo "  $0 all                    # 运行所有测试"
        echo "  $0 unit                    # 运行单元测试"
        echo "  $0 metadata-service        # 运行metadata-service测试"
        echo "  $0 all true                # 运行所有测试并生成覆盖率报告"
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ 测试通过！${NC}"
    
    if [ "$COVERAGE" = "true" ]; then
        echo ""
        echo -e "${CYAN}覆盖率报告已生成: htmlcov/index.html${NC}"
    fi
else
    echo ""
    echo -e "${RED}✗ 测试失败${NC}"
    echo ""
    echo -e "${YELLOW}提示:${NC}"
    echo "1. 检查错误信息"
    echo "2. 验证导入路径是否正确"
    echo "3. 检查依赖是否安装"
    echo "4. 查看测试运行指南: docs/development-docs/TEST_RUNNING_GUIDE.md"
fi


