#!/bin/bash
# 在测试服务器上运行所有测试

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
echo "=========================================="
echo ""

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# 测试开始时间
START_TIME=$(date +%s)

# 运行测试函数
run_test_suite() {
    local test_type=$1
    local test_path=$2
    local test_name=$3
    
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📋 $test_name${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ ! -d "$test_path" ] && [ ! -f "$test_path" ]; then
        echo -e "${YELLOW}⚠️  跳过: $test_path 不存在${NC}"
        return
    fi
    
    # 运行测试
    local test_output
    if python3 -m pytest "$test_path" \
        -v \
        --tb=short \
        --cov=. \
        --cov-report=html:coverage-report/$test_type \
        --cov-report=term-missing \
        --cov-report=json:coverage-report/$test_type-coverage.json \
        --junit-xml=test-results/$test_type-results.xml \
        -m "not slow" \
        2>&1 | tee test-results/$test_type-output.log; then
        echo ""
        echo -e "${GREEN}✅ $test_name 通过${NC}"
        ((PASSED_TESTS++))
    else
        echo ""
        echo -e "${RED}❌ $test_name 失败${NC}"
        ((FAILED_TESTS++))
    fi
    
    echo ""
}

# 1. 单元测试
run_test_suite "unit" "tests/test-architecture" "单元测试 - 架构测试"

# 2. 集成测试
run_test_suite "integration" "tests/test-integration" "集成测试 - 服务集成"

# 3. 端到端测试
run_test_suite "e2e" "tests/test_e2e_procurement.py" "端到端测试 - 采购场景"
run_test_suite "e2e" "tests/test_complete_real_world.py" "端到端测试 - 真实环境"

# 4. API测试
run_test_suite "api" "tests/test_unified_intent_api.py" "API测试 - 统一意图服务"
run_test_suite "api" "tests/test_collaborative_interface_api.py" "API测试 - 协作接口"

# 5. 语义引擎测试
run_test_suite "semantic" "tests/test_semantic_engine_basic.py" "语义引擎测试 - 基础功能"
run_test_suite "semantic" "tests/test_enterprise_semantic_engine_comprehensive.py" "语义引擎测试 - 综合测试"

# 6. 智能路由测试
run_test_suite "router" "tests/test_enhanced_intelligent_router.py" "智能路由测试 - 增强路由"
run_test_suite "router" "tests/test_enhanced_intelligent_router_simple.py" "智能路由测试 - 简化路由"

# 7. LLM增强测试
run_test_suite "llm" "tests/test_unified_intent_llm_enhancement.py" "LLM增强测试 - 统一意图"

# 计算测试时间
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

# 生成测试报告
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 测试结果汇总${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}✅ 通过: $PASSED_TESTS${NC}"
echo -e "${RED}❌ 失败: $FAILED_TESTS${NC}"
echo -e "${YELLOW}⏭️  跳过: $SKIPPED_TESTS${NC}"
echo ""
echo -e "${BLUE}⏱️  总耗时: ${MINUTES}分${SECONDS}秒${NC}"
echo ""

# 生成HTML报告
if command -v python3 &> /dev/null; then
    python3 << EOF
import json
import os
from datetime import datetime

# 读取所有覆盖率报告
coverage_files = [f for f in os.listdir('coverage-report') if f.endswith('-coverage.json')]
total_coverage = {}

for file in coverage_files:
    try:
        with open(f'coverage-report/{file}', 'r') as f:
            data = json.load(f)
            if 'totals' in data:
                total_coverage[file] = data['totals']['percent_covered']
    except:
        pass

# 生成简单报告
report = f"""
# 测试执行报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 测试统计
- 通过: {os.environ.get('PASSED_TESTS', 0)}
- 失败: {os.environ.get('FAILED_TESTS', 0)}
- 总耗时: {os.environ.get('MINUTES', 0)}分{os.environ.get('SECONDS', 0)}秒

## 代码覆盖率
"""
for file, coverage in total_coverage.items():
    report += f"- {file}: {coverage:.2f}%\n"

with open('test-results/test-report.md', 'w') as f:
    f.write(report)
EOF
fi

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
    echo -e "${RED}❌ 有 $FAILED_TESTS 个测试套件失败${NC}"
    exit 1
fi

