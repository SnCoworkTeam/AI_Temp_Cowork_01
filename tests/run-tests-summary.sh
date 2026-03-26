#!/bin/bash
# 测试总结脚本 - 生成测试报告

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

REPORT_FILE="tests/test-report-$(date +%Y%m%d-%H%M%S).txt"

echo "=========================================="
echo "生成测试报告"
echo "=========================================="
echo ""

# 测试结果
declare -A TEST_RESULTS

# 运行测试并记录结果
run_test_and_record() {
    local service=$1
    local test_type=$2
    local test_path=$3
    local container_name="enterprise-ai-${service}"
    
    echo "测试: $service - $test_type"
    
    if ! docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo "  跳过: 容器未运行"
        TEST_RESULTS["${service}_${test_type}"]="SKIPPED"
        return
    fi
    
    # 安装依赖
    docker exec $container_name pip install -q pytest pytest-asyncio pytest-cov pytest-mock httpx 2>/dev/null || true
    
    # 运行测试
    if docker exec -w /app $container_name python3 -m pytest $test_path -q --tb=no 2>&1 | tee -a "$REPORT_FILE"; then
        echo "  ✓ 通过"
        TEST_RESULTS["${service}_${test_type}"]="PASSED"
    else
        echo "  ✗ 失败"
        TEST_RESULTS["${service}_${test_type}"]="FAILED"
    fi
}

# 生成报告
{
    echo "=========================================="
    echo "测试报告 - $(date)"
    echo "=========================================="
    echo ""
    
    echo "--- 单元测试 ---"
    run_test_and_record "workflow-engine" "unit" "tests/unit/"
    run_test_and_record "auth-service" "unit" "tests/unit/"
    run_test_and_record "knowledge-base" "unit" "tests/unit/"
    run_test_and_record "mcp-gateway" "unit" "tests/unit/"
    
    echo ""
    echo "--- 集成测试 ---"
    run_test_and_record "workflow-engine" "integration" "tests/integration/"
    run_test_and_record "auth-service" "integration" "tests/integration/"
    run_test_and_record "knowledge-base" "integration" "tests/integration/"
    
    echo ""
    echo "=========================================="
    echo "测试总结"
    echo "=========================================="
    
    passed=0
    failed=0
    skipped=0
    
    for result in "${TEST_RESULTS[@]}"; do
        case $result in
            PASSED) ((passed++)) ;;
            FAILED) ((failed++)) ;;
            SKIPPED) ((skipped++)) ;;
        esac
    done
    
    echo "通过: $passed"
    echo "失败: $failed"
    echo "跳过: $skipped"
    echo ""
    
} | tee "$REPORT_FILE"

echo ""
echo "报告已保存到: $REPORT_FILE"

