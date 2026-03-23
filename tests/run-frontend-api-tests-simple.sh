#!/bin/bash
# 简化的前端API测试脚本 - 直接在容器中运行

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

echo "=========================================="
echo -e "${CYAN}🧪 前端API功能测试${NC}"
echo "=========================================="
echo ""

# 创建测试报告目录
mkdir -p test-results

# 使用API Gateway容器运行测试
CONTAINER_NAME="enterprise-ai-api-gateway"

if ! sudo docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}错误: 容器 $CONTAINER_NAME 未运行${NC}"
    exit 1
fi

echo -e "${YELLOW}使用容器: $CONTAINER_NAME${NC}"
echo ""

# 安装测试依赖
echo -e "${BLUE}安装测试依赖...${NC}"
sudo docker exec $CONTAINER_NAME python3 -m pip install pytest pytest-asyncio httpx --quiet 2>&1 | grep -v "already satisfied" || true
echo ""

# 运行前端API集成测试
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}运行前端API集成测试${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 复制测试文件和配置文件到容器
sudo docker cp tests/test_frontend_api_integration.py ${CONTAINER_NAME}:/tmp/test_frontend_api_integration.py 2>&1 || true
sudo docker cp tests/pytest.ini ${CONTAINER_NAME}:/tmp/pytest.ini 2>&1 || true

# 运行测试
if sudo docker exec -w /tmp $CONTAINER_NAME python3 -m pytest test_frontend_api_integration.py -v --tb=short -m "integration" --asyncio-mode=auto 2>&1 | tee test-results/frontend-api-test.log; then
    echo -e "${GREEN}✅ 前端API测试通过${NC}"
    exit 0
else
    echo -e "${RED}❌ 前端API测试失败${NC}"
    exit 1
fi

