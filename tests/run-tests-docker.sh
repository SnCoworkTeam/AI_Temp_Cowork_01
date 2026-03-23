#!/bin/bash
# 在Docker容器中运行测试

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
echo -e "${BLUE}在Docker容器中运行测试${NC}"
echo "=========================================="
echo ""

# 检查Docker服务
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    exit 1
fi

# 测试函数
run_test_in_container() {
    local service=$1
    local test_path=$2
    local container_name="enterprise-ai-${service}"
    
    echo -e "${BLUE}测试: $service${NC}"
    
    # 检查容器是否存在
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo -e "${YELLOW}跳过: 容器 $container_name 不存在${NC}"
        return
    fi
    
    # 检查容器是否运行
    if ! docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo -e "${YELLOW}启动容器: $container_name${NC}"
        docker start $container_name
        sleep 3
    fi
    
    # 在容器中安装测试依赖（如果需要）
    echo "安装测试依赖..."
    docker exec $container_name pip install pytest pytest-asyncio pytest-cov pytest-mock httpx fakeredis 2>&1 | tail -5
    
    # 运行测试
    echo "运行测试..."
    if docker exec -w /app $container_name python3 -m pytest $test_path -v --tb=short 2>&1; then
        echo -e "${GREEN}✓ $service 测试通过${NC}"
    else
        echo -e "${RED}✗ $service 测试失败${NC}"
    fi
    echo ""
}

# 运行各服务的测试
echo -e "${BLUE}--- 单元测试 ---${NC}"
run_test_in_container "workflow-engine" "tests/unit/"
run_test_in_container "auth-service" "tests/unit/"
run_test_in_container "knowledge-base" "tests/unit/"

echo -e "${BLUE}--- 集成测试 ---${NC}"
run_test_in_container "workflow-engine" "tests/integration/"
run_test_in_container "auth-service" "tests/integration/"
run_test_in_container "knowledge-base" "tests/integration/"

echo -e "${GREEN}测试完成${NC}"

