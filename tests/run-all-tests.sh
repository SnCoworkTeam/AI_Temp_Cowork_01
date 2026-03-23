#!/bin/bash
# 运行所有模块的测试脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

echo "=========================================="
echo -e "${BLUE}企业AI平台 - 完整测试套件${NC}"
echo "=========================================="
echo ""

# 检查pytest是否安装
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}错误: pytest 未安装${NC}"
    echo "请运行: pip install -r tests/requirements.txt"
    exit 1
fi

# 解析参数
TEST_TYPE="${1:-all}"
COVERAGE="${2:-false}"
VERBOSE="${3:-false}"

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

# 测试函数
run_test_suite() {
    local suite_name=$1
    local test_path=$2
    local marker=$3
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}测试: $suite_name${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    if [ ! -d "$test_path" ] && [ ! -f "$test_path" ]; then
        echo -e "${YELLOW}跳过: $test_path 不存在${NC}"
        return
    fi
    
    local cmd="$PYTEST_CMD"
    if [ -n "$marker" ]; then
        cmd="$cmd -m $marker"
    fi
    cmd="$cmd $test_path"
    
    if eval $cmd; then
        echo -e "${GREEN}✓ $suite_name 测试通过${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}✗ $suite_name 测试失败${NC}"
        ((FAILED_TESTS++))
    fi
    echo ""
}

# 根据测试类型运行
case "$TEST_TYPE" in
    unit)
        echo -e "${BLUE}运行单元测试...${NC}"
        echo ""
        
        # 各服务的单元测试
        run_test_suite "MCP Gateway 单元测试" "mcp-gateway/tests/unit" "unit"
        run_test_suite "Workflow Engine 单元测试" "workflow-engine/tests/unit" "unit"
        run_test_suite "Auth Service 单元测试" "auth-service/tests/unit" "unit"
        run_test_suite "Knowledge Base 单元测试" "knowledge-base/tests/unit" "unit"
        run_test_suite "Metadata Service 单元测试" "metadata-service/tests/unit" "unit"
        run_test_suite "架构测试" "tests/test-architecture" "unit"
        ;;
        
    integration)
        echo -e "${BLUE}运行集成测试...${NC}"
        echo ""
        
        # 各服务的集成测试
        run_test_suite "MCP Gateway 集成测试" "mcp-gateway/tests/integration" "integration"
        run_test_suite "Workflow Engine 集成测试" "workflow-engine/tests/integration" "integration"
        run_test_suite "Auth Service 集成测试" "auth-service/tests/integration" "integration"
        run_test_suite "Knowledge Base 集成测试" "knowledge-base/tests/integration" "integration"
        run_test_suite "全局集成测试" "tests/test-integration" "integration"
        ;;
        
    performance)
        echo -e "${BLUE}运行性能测试...${NC}"
        echo ""
        
        run_test_suite "性能测试" "tests/test-performance" "performance"
        ;;
        
    security)
        echo -e "${BLUE}运行安全测试...${NC}"
        echo ""
        
        run_test_suite "安全测试" "tests/test-security" "security"
        ;;
        
    service)
        echo -e "${BLUE}运行服务测试...${NC}"
        echo ""
        
        SERVICE_NAME="${4:-all}"
        
        if [ "$SERVICE_NAME" = "all" ]; then
            run_test_suite "MCP Gateway" "mcp-gateway/tests" ""
            run_test_suite "Workflow Engine" "workflow-engine/tests" ""
            run_test_suite "Auth Service" "auth-service/tests" ""
            run_test_suite "Knowledge Base" "knowledge-base/tests" ""
            run_test_suite "Metadata Service" "metadata-service/tests" ""
        else
            run_test_suite "$SERVICE_NAME" "$SERVICE_NAME/tests" ""
        fi
        ;;
        
    all)
        echo -e "${BLUE}运行所有测试...${NC}"
        echo ""
        
        # 1. 架构测试
        run_test_suite "架构测试" "tests/test-architecture" "unit"
        
        # 2. 单元测试
        echo -e "${YELLOW}--- 单元测试 ---${NC}"
        run_test_suite "MCP Gateway 单元测试" "mcp-gateway/tests/unit" "unit"
        run_test_suite "Workflow Engine 单元测试" "workflow-engine/tests/unit" "unit"
        run_test_suite "Auth Service 单元测试" "auth-service/tests/unit" "unit"
        run_test_suite "Knowledge Base 单元测试" "knowledge-base/tests/unit" "unit"
        run_test_suite "Metadata Service 单元测试" "metadata-service/tests/unit" "unit"
        
        # 3. 集成测试
        echo -e "${YELLOW}--- 集成测试 ---${NC}"
        run_test_suite "MCP Gateway 集成测试" "mcp-gateway/tests/integration" "integration"
        run_test_suite "Workflow Engine 集成测试" "workflow-engine/tests/integration" "integration"
        run_test_suite "Auth Service 集成测试" "auth-service/tests/integration" "integration"
        run_test_suite "Knowledge Base 集成测试" "knowledge-base/tests/integration" "integration"
        run_test_suite "全局集成测试" "tests/test-integration" "integration"
        
        # 4. 安全测试
        echo -e "${YELLOW}--- 安全测试 ---${NC}"
        run_test_suite "安全测试" "tests/test-security" "security"
        
        # 5. 性能测试（可选，通常较慢）
        echo -e "${YELLOW}--- 性能测试（跳过，使用 performance 参数单独运行）---${NC}"
        ;;
        
    *)
        echo "用法: $0 [unit|integration|performance|security|service|all] [coverage] [verbose] [service_name]"
        echo ""
        echo "示例:"
        echo "  $0 all                    # 运行所有测试"
        echo "  $0 unit                   # 只运行单元测试"
        echo "  $0 integration            # 只运行集成测试"
        echo "  $0 service mcp-gateway    # 运行特定服务的所有测试"
        echo "  $0 all true               # 运行所有测试并生成覆盖率报告"
        echo "  $0 all true true          # 运行所有测试，生成覆盖率，详细输出"
        exit 1
        ;;
esac

# 输出测试总结
echo ""
echo "=========================================="
echo -e "${BLUE}测试总结${NC}"
echo "=========================================="
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"
echo -e "${YELLOW}跳过: $SKIPPED_TESTS${NC}"
echo ""

if [ "$COVERAGE" = "true" ]; then
    echo -e "${BLUE}覆盖率报告已生成: htmlcov/index.html${NC}"
    echo ""
fi

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}✗ 有 $FAILED_TESTS 个测试套件失败${NC}"
    exit 1
fi

