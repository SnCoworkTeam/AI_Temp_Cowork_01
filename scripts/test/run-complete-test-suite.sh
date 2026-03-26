#!/bin/bash
# 完整测试套件 - 包括单元测试、集成测试、端到端测试

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

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# 测试开始时间
START_TIME=$(date +%s)

# 运行测试函数
run_test_category() {
    local category=$1
    local test_path=$2
    local description=$3
    local markers=${4:-""}
    
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📋 $description${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ ! -d "$test_path" ] && [ ! -f "$test_path" ]; then
        echo -e "${YELLOW}⚠️  跳过: $test_path 不存在${NC}"
        return
    fi
    
    # 构建pytest命令
    local pytest_cmd="python3 -m pytest $test_path -v --tb=short"
    
    # 添加标记
    if [ -n "$markers" ]; then
        pytest_cmd="$pytest_cmd -m \"$markers\""
    fi
    
    # 添加覆盖率
    pytest_cmd="$pytest_cmd --cov=. --cov-report=html:coverage-report/$category --cov-report=term-missing"
    
    # 添加JUnit XML报告
    pytest_cmd="$pytest_cmd --junit-xml=test-results/$category-results.xml"
    
    # 运行测试
    local exit_code=0
    
    echo -e "${YELLOW}执行命令: $pytest_cmd${NC}"
    echo ""
    
    # 直接执行pytest命令，不使用eval
    python3 -m pytest "$test_path" \
        -v \
        --tb=short \
        --cov=. \
        --cov-report=html:coverage-report/$category \
        --cov-report=term-missing \
        --junit-xml=test-results/$category-results.xml \
        ${markers:+-m "$markers"} \
        > "test-results/$category-output.log" 2>&1 || exit_code=$?
    
    # 统计结果
    local passed=$(grep -c "PASSED" "test-results/$category-output.log" 2>/dev/null || echo "0")
    local failed=$(grep -c "FAILED" "test-results/$category-output.log" 2>/dev/null || echo "0")
    local skipped=$(grep -c "SKIPPED" "test-results/$category-output.log" 2>/dev/null || echo "0")
    
    TOTAL_TESTS=$((TOTAL_TESTS + passed + failed + skipped))
    PASSED_TESTS=$((PASSED_TESTS + passed))
    FAILED_TESTS=$((FAILED_TESTS + failed))
    SKIPPED_TESTS=$((SKIPPED_TESTS + skipped))
    
    if [ $exit_code -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ $description 通过 (通过: $passed, 跳过: $skipped)${NC}"
    else
        echo ""
        echo -e "${RED}❌ $description 失败 (失败: $failed)${NC}"
        echo -e "${YELLOW}查看详细日志: test-results/$category-output.log${NC}"
    fi
    
    echo ""
}

# ==================== 1. 单元测试 ====================
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}📦 第一阶段：单元测试${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

# 架构测试
run_test_category "unit-architecture" "tests/test-architecture" "单元测试 - 架构验证" "unit"

# 业务活动模型测试
run_test_category "unit-business-model" "tests/test_business_activity_model_comprehensive.py" "单元测试 - 业务活动模型" "unit"

# 语义引擎基础测试
run_test_category "unit-semantic-basic" "tests/test_semantic_engine_basic.py" "单元测试 - 语义引擎基础" "unit"

# ==================== 2. 集成测试 ====================
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔗 第二阶段：集成测试${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

# API集成测试
run_test_category "integration-api" "tests/test-integration/test_api_integration.py" "集成测试 - API集成" "integration"

# 数据库集成测试
run_test_category "integration-database" "tests/test-integration/test_database_integration.py" "集成测试 - 数据库集成" "integration"

# 外部服务集成测试
run_test_category "integration-external" "tests/test-integration/test_external_services.py" "集成测试 - 外部服务" "integration"

# 统一意图API测试
run_test_category "integration-unified-intent" "tests/test_unified_intent_api.py" "集成测试 - 统一意图API" "integration"

# 协作接口API测试
run_test_category "integration-collaborative" "tests/test_collaborative_interface_api.py" "集成测试 - 协作接口API" "integration"

# ==================== 3. 端到端测试 ====================
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}🌐 第三阶段：端到端测试${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

# 采购场景E2E测试
run_test_category "e2e-procurement" "tests/test_e2e_procurement.py" "端到端测试 - 采购场景" "e2e"

# 真实环境完整测试
run_test_category "e2e-real-world" "tests/test_complete_real_world.py" "端到端测试 - 真实环境" "e2e"

# 企业语义引擎综合测试
run_test_category "e2e-semantic-engine" "tests/test_enterprise_semantic_engine_comprehensive.py" "端到端测试 - 企业语义引擎" "e2e"

# 智能路由测试
run_test_category "e2e-intelligent-router" "tests/test_enhanced_intelligent_router.py" "端到端测试 - 智能路由" "e2e"

# LLM增强测试
run_test_category "e2e-llm-enhancement" "tests/test_unified_intent_llm_enhancement.py" "端到端测试 - LLM增强" "e2e"

# ==================== 4. 性能测试（可选）====================
if [ "${RUN_PERFORMANCE_TESTS:-false}" = "true" ]; then
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo -e "${BLUE}⚡ 第四阶段：性能测试${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    
    run_test_category "performance" "tests/test-performance" "性能测试" "performance"
fi

# 计算测试时间
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

# ==================== 生成测试报告 ====================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 测试结果汇总${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}✅ 通过: $PASSED_TESTS${NC}"
echo -e "${RED}❌ 失败: $FAILED_TESTS${NC}"
echo -e "${YELLOW}⏭️  跳过: $SKIPPED_TESTS${NC}"
echo -e "${BLUE}📊 总计: $TOTAL_TESTS${NC}"
echo ""
echo -e "${BLUE}⏱️  总耗时: ${MINUTES}分${SECONDS}秒${NC}"
echo ""

# 生成Markdown报告
cat > test-results/test-report.md << EOF
# 完整测试套件执行报告

生成时间: $(date '+%Y-%m-%d %H:%M:%S')

## 测试统计

- **总计**: $TOTAL_TESTS
- **通过**: $PASSED_TESTS
- **失败**: $FAILED_TESTS
- **跳过**: $SKIPPED_TESTS
- **总耗时**: ${MINUTES}分${SECONDS}秒

## 测试分类

### 单元测试
- 架构验证
- 业务活动模型
- 语义引擎基础

### 集成测试
- API集成
- 数据库集成
- 外部服务集成
- 统一意图API
- 协作接口API

### 端到端测试
- 采购场景
- 真实环境
- 企业语义引擎
- 智能路由
- LLM增强

## 报告位置

- HTML覆盖率报告: \`coverage-report/\`
- JUnit XML报告: \`test-results/*-results.xml\`
- 测试日志: \`test-results/*-output.log\`
- 本报告: \`test-results/test-report.md\`

EOF

# 输出报告位置
echo -e "${BLUE}📄 测试报告位置:${NC}"
echo "  - HTML覆盖率报告: coverage-report/"
echo "  - JUnit XML报告: test-results/*-results.xml"
echo "  - 测试日志: test-results/*-output.log"
echo "  - Markdown报告: test-results/test-report.md"
echo ""

# 返回退出码
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}❌ 有 $FAILED_TESTS 个测试失败${NC}"
    exit 1
fi

