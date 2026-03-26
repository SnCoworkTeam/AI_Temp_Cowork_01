#!/bin/bash
# 部署验证测试脚本

set -e

BASE_URL="${BASE_URL:-http://localhost}"
TIMEOUT=10

echo "=========================================="
echo "部署验证测试"
echo "=========================================="

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数器
PASSED=0
FAILED=0

test_service() {
    local name=$1
    local port=$2
    local endpoint=$3
    
    echo -n "测试 $name (端口 $port)... "
    
    if curl -f -s --max-time $TIMEOUT "${BASE_URL}:${port}${endpoint}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        ((FAILED++))
        return 1
    fi
}

test_api_endpoint() {
    local name=$1
    local port=$2
    local method=$3
    local endpoint=$4
    local data=$5
    
    echo -n "测试 $name API ($method $endpoint)... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s --max-time $TIMEOUT "${BASE_URL}:${port}${endpoint}")
    else
        response=$(curl -s --max-time $TIMEOUT -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${BASE_URL}:${port}${endpoint}")
    fi
    
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        ((FAILED++))
        return 1
    fi
}

echo ""
echo "1. 服务健康检查"
echo "----------------------------------------"

test_service "MCP Gateway" "8001" "/api/health"
test_service "Workflow Engine" "8002" "/api/health"
test_service "Auth Service" "8003" "/api/health"
test_service "Knowledge Base" "8004" "/api/health"
test_service "Web UI" "3000" "/api/health"

echo ""
echo "2. API端点测试"
echo "----------------------------------------"

# MCP Gateway API
test_api_endpoint "MCP Gateway - 工具列表" "8001" "GET" "/api/tools"

# Workflow Engine API
test_api_endpoint "Workflow Engine - 工作流列表" "8002" "GET" "/api/workflows"

# Auth Service API
test_api_endpoint "Auth Service - 健康检查" "8003" "GET" "/api/health"

# Knowledge Base API
test_api_endpoint "Knowledge Base - 文档列表" "8004" "GET" "/api/documents"

echo ""
echo "3. Docker容器状态检查"
echo "----------------------------------------"

containers=(
    "enterprise-ai-mcp-gateway"
    "enterprise-ai-workflow-engine"
    "enterprise-ai-auth-service"
    "enterprise-ai-knowledge-base"
    "enterprise-ai-web-ui"
)

for container in "${containers[@]}"; do
    echo -n "检查容器 $container... "
    if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
        status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "unknown")
        if [ "$status" = "running" ]; then
            echo -e "${GREEN}✅ 运行中${NC}"
            ((PASSED++))
        else
            echo -e "${YELLOW}⚠️  状态: $status${NC}"
            ((FAILED++))
        fi
    else
        echo -e "${RED}❌ 未运行${NC}"
        ((FAILED++))
    fi
done

echo ""
echo "4. 自动化调试系统检查"
echo "----------------------------------------"

# 检查自动化调试系统是否可用
echo -n "检查自动化调试系统... "
debug_response=$(curl -s --max-time $TIMEOUT "${BASE_URL}:8001/api/health" 2>/dev/null || echo "")
if echo "$debug_response" | grep -qi "auto_debug\|auto-debug"; then
    echo -e "${GREEN}✅ 可用${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  未检测到（可能未启用）${NC}"
fi

echo ""
echo "=========================================="
echo "测试结果汇总"
echo "=========================================="
echo -e "${GREEN}通过: $PASSED${NC}"
echo -e "${RED}失败: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}❌ 部分测试失败，请检查服务状态${NC}"
    echo ""
    echo "查看日志: docker-compose logs"
    echo "检查服务: docker-compose ps"
    exit 1
fi

