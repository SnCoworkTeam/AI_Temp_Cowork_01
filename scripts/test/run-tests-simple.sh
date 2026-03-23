#!/bin/bash
# 简化版测试执行脚本 - 直接在服务器上运行所有测试

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo "=========================================="
echo -e "${BLUE}🧪 企业AI平台 - 完整测试套件${NC}"
echo -e "${BLUE}包括：单元测试、集成测试、端到端测试${NC}"
echo "=========================================="
echo ""

# 创建测试结果目录
mkdir -p test-results
mkdir -p coverage-report

# 测试开始时间
START_TIME=$(date +%s)

# 运行测试并统计结果
run_pytest() {
    local test_path=$1
    local category=$2
    local description=$3
    
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📋 $description${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ ! -d "$test_path" ] && [ ! -f "$test_path" ]; then
        echo -e "${YELLOW}⚠️  跳过: $test_path 不存在${NC}"
        return 0
    fi
    
    # 运行pytest
    if python3 -m pytest "$test_path" \
        -v \
        --tb=short \
        --cov=. \
        --cov-report=html:coverage-report/$category \
        --cov-report=term-missing \
        --junit-xml=test-results/$category-results.xml \
        2>&1 | tee test-results/$category-output.log; then
        echo ""
        echo -e "${GREEN}✅ $description 通过${NC}"
        return 0
    else
        echo ""
        echo -e "${RED}❌ $description 失败${NC}"
        return 1
    fi
}

# ==================== 1. 单元测试 ====================
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}📦 第一阶段：单元测试${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

run_pytest "tests/test-architecture" "unit-architecture" "单元测试 - 架构验证"
run_pytest "tests/test_business_activity_model_comprehensive.py" "unit-business-model" "单元测试 - 业务活动模型"
run_pytest "tests/test_semantic_engine_basic.py" "unit-semantic-basic" "单元测试 - 语义引擎基础"

# ==================== 2. 集成测试 ====================
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔗 第二阶段：集成测试${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

run_pytest "tests/test-integration" "integration" "集成测试 - 服务集成"
run_pytest "tests/test_unified_intent_api.py" "integration-unified-intent" "集成测试 - 统一意图API"
run_pytest "tests/test_collaborative_interface_api.py" "integration-collaborative" "集成测试 - 协作接口API"

# ==================== 3. 端到端测试 ====================
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}🌐 第三阶段：端到端测试${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

run_pytest "tests/test_e2e_procurement.py" "e2e-procurement" "端到端测试 - 采购场景"
run_pytest "tests/test_complete_real_world.py" "e2e-real-world" "端到端测试 - 真实环境"
run_pytest "tests/test_enterprise_semantic_engine_comprehensive.py" "e2e-semantic-engine" "端到端测试 - 企业语义引擎"
run_pytest "tests/test_enhanced_intelligent_router.py" "e2e-intelligent-router" "端到端测试 - 智能路由"
run_pytest "tests/test_unified_intent_llm_enhancement.py" "e2e-llm-enhancement" "端到端测试 - LLM增强"

# 计算测试时间
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

# 生成测试报告
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 测试执行完成${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}⏱️  总耗时: ${MINUTES}分${SECONDS}秒${NC}"
echo ""
echo -e "${BLUE}📄 测试报告位置:${NC}"
echo "  - HTML覆盖率报告: coverage-report/"
echo "  - JUnit XML报告: test-results/*-results.xml"
echo "  - 测试日志: test-results/*-output.log"
echo ""

echo -e "${GREEN}✅ 测试执行完成！请查看报告了解详细结果。${NC}"

