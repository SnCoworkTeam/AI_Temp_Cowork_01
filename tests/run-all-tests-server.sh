#!/bin/bash
# 在服务器上运行所有测试的脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo -e "${BLUE}在服务器上运行所有测试${NC}"
echo "=========================================="
echo ""

# 检查pytest
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}安装pytest...${NC}"
    pip3 install pytest pytest-asyncio pytest-cov pytest-mock httpx --quiet
fi

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
run_test_suite() {
    local service=$1
    local test_path=$2
    local test_type=$3
    
    echo -e "${BLUE}测试: $service - $test_type${NC}"
    
    if [ ! -d "$test_path" ] && [ ! -f "$test_path" ]; then
        echo -e "${YELLOW}跳过: $test_path 不存在${NC}"
        return
    fi
    
    # 在Docker容器中运行测试（如果服务运行中）
    container_name="enterprise-ai-${service}"
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo "  在容器中运行测试..."
        if docker exec $container_name python3 -m pytest $test_path -v --tb=short 2>&1; then
            echo -e "${GREEN}✓ $service - $test_type 通过${NC}"
            ((PASSED_TESTS++))
        else
            echo -e "${RED}✗ $service - $test_type 失败${NC}"
            ((FAILED_TESTS++))
        fi
    else
        # 在主机上运行测试
        echo "  在主机上运行测试..."
        if python3 -m pytest $test_path -v --tb=short 2>&1; then
            echo -e "${GREEN}✓ $service - $test_type 通过${NC}"
            ((PASSED_TESTS++))
        else
            echo -e "${RED}✗ $service - $test_type 失败${NC}"
            ((FAILED_TESTS++))
        fi
    fi
    echo ""
}

# 运行所有测试
echo -e "${BLUE}--- 单元测试 ---${NC}"
run_test_suite "metadata-service" "metadata-service/tests/unit" "unit"
run_test_suite "database" "database/tests/unit" "unit"
run_test_suite "workflow-engine" "workflow-engine/tests/unit" "unit"
run_test_suite "auth-service" "auth-service/tests/unit" "unit"
run_test_suite "knowledge-base" "knowledge-base/tests/unit" "unit"
run_test_suite "mcp-gateway" "mcp-gateway/tests/unit" "unit"

echo -e "${BLUE}--- 集成测试 ---${NC}"
run_test_suite "metadata-service" "metadata-service/tests/integration" "integration"
run_test_suite "database" "database/tests/integration" "integration"
run_test_suite "workflow-engine" "workflow-engine/tests/integration" "integration"
run_test_suite "auth-service" "auth-service/tests/integration" "integration"
run_test_suite "knowledge-base" "knowledge-base/tests/integration" "integration"
run_test_suite "mcp-gateway" "mcp-gateway/tests/integration" "integration"

# 输出总结
echo ""
echo "=========================================="
echo -e "${BLUE}测试总结${NC}"
echo "=========================================="
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}✗ 有 $FAILED_TESTS 个测试套件失败${NC}"
    exit 1
fi

