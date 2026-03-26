#!/bin/bash
# 前端功能重点测试脚本
# 包括：单元测试、集成测试、端到端测试

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
NC='\033[0m'

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

echo "=========================================="
echo -e "${CYAN}🧪 企业AI平台 - 前端功能重点测试${NC}"
echo "=========================================="
echo ""

# 跳过主机上的pytest检查，直接在容器中运行
echo -e "${YELLOW}注意: 测试将在Docker容器中运行，使用容器内的pytest${NC}"

# 创建测试报告目录
mkdir -p test-results coverage-report

# 测试函数
run_test_suite() {
    local name=$1
    local path=$2
    local marker=$3
    local output_prefix=$4
    local container_name=$5
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}📋 $name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local cmd="pytest $path -v --tb=short"
    if [ -n "$marker" ]; then
        cmd="$cmd -m \"$marker\""
    fi
    cmd="$cmd --cov=. --cov-report=html:coverage-report/$output_prefix --cov-report=term-missing --junit-xml=test-results/$output_prefix-results.xml"
    
    # 优先在容器中运行，如果没有容器则在主机上运行
    if [ -n "$container_name" ] && docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo "执行命令: docker exec $container_name $cmd"
        # 确保容器中有pytest
        docker exec $container_name python3 -m pip install pytest pytest-asyncio pytest-cov pytest-mock httpx --quiet 2>&1 | grep -v "already satisfied" || true
        if docker exec $container_name bash -c "$cmd" 2>&1 | tee test-results/$output_prefix-output.log; then
            echo -e "${GREEN}✅ $name 通过${NC}"
            ((PASSED_TESTS++))
        else
            echo -e "${RED}❌ $name 失败${NC}"
            ((FAILED_TESTS++))
        fi
    else
        # 在主机上运行（如果pytest可用）
        if command -v pytest &> /dev/null; then
            echo "执行命令: $cmd"
            if bash -c "$cmd" 2>&1 | tee test-results/$output_prefix-output.log; then
                echo -e "${GREEN}✅ $name 通过${NC}"
                ((PASSED_TESTS++))
            else
                echo -e "${RED}❌ $name 失败${NC}"
                ((FAILED_TESTS++))
            fi
        else
            echo -e "${YELLOW}⚠️  跳过 $name (容器未运行且主机无pytest)${NC}"
            ((SKIPPED_TESTS++))
        fi
    fi
    ((TOTAL_TESTS++))
}

START_TIME=$(date +%s)

echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${CYAN}📦 第一阶段：单元测试${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"

# 架构测试
run_test_suite "单元测试 - 架构验证" "tests/test-architecture" "unit" "unit-architecture"

# 业务活动模型测试
run_test_suite "单元测试 - 业务活动模型" "tests/test_business_activity_model_comprehensive.py" "unit" "unit-business-activity"

# 语义引擎基础测试
run_test_suite "单元测试 - 语义引擎基础" "tests/test_semantic_engine_basic.py" "unit" "unit-semantic-basic"

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${CYAN}🔗 第二阶段：集成测试${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"

# API集成测试
run_test_suite "集成测试 - API集成" "tests/test-integration/test_api_integration.py" "integration" "integration-api" "enterprise-ai-api-gateway"

# 数据库集成测试
run_test_suite "集成测试 - 数据库集成" "tests/test-integration/test_database_integration.py" "integration" "integration-database"

# 统一意图API测试
run_test_suite "集成测试 - 统一意图API" "tests/test_unified_intent_api.py" "integration" "integration-unified-intent" "enterprise-ai-api-gateway"

# 协作接口API测试
run_test_suite "集成测试 - 协作接口API" "tests/test_collaborative_interface_api.py" "integration" "integration-collaborative" "enterprise-ai-api-gateway"

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${CYAN}🚀 第三阶段：端到端测试（前端功能重点）${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"

# 采购场景E2E测试
run_test_suite "端到端测试 - 采购场景" "tests/test_e2e_procurement.py" "e2e" "e2e-procurement"

# 真实环境E2E测试
run_test_suite "端到端测试 - 真实环境" "tests/test_complete_real_world.py" "e2e" "e2e-real-world"

# LLM增强E2E测试
run_test_suite "端到端测试 - LLM增强" "tests/test_unified_intent_llm_enhancement.py" "e2e" "e2e-llm-enhancement"

# 智能路由E2E测试
run_test_suite "端到端测试 - 智能路由" "tests/test_enhanced_intelligent_router.py" "e2e" "e2e-intelligent-router"

# 语义引擎E2E测试
run_test_suite "端到端测试 - 语义引擎" "tests/test_enterprise_semantic_engine_comprehensive.py" "e2e" "e2e-semantic-engine"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}📊 测试执行完成${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}⏱️  总耗时: $((DURATION / 60))分$((DURATION % 60))秒${NC}"
echo ""
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"
echo -e "${YELLOW}总计: $TOTAL_TESTS${NC}"
echo ""
echo -e "${CYAN}📄 测试报告位置:${NC}"
echo -e "  - HTML覆盖率报告: coverage-report/"
echo -e "  - JUnit XML报告: test-results/*-results.xml"
echo -e "  - 测试日志: test-results/*-output.log"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}❌ 有 $FAILED_TESTS 个测试失败${NC}"
    exit 1
fi

