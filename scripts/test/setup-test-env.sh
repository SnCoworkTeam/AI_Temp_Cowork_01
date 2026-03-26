#!/bin/bash
# 在测试服务器上设置测试环境

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo -e "${BLUE}🚀 设置企业AI平台测试环境${NC}"
echo "=========================================="
echo ""

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装${NC}"
    exit 1
fi

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose未安装${NC}"
    exit 1
fi

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python3未安装，将使用Docker容器运行测试${NC}"
fi

# 安装测试依赖
echo -e "${BLUE}📦 安装测试依赖...${NC}"
if command -v python3 &> /dev/null; then
    pip3 install --quiet --upgrade pip
    pip3 install --quiet -r tests/requirements.txt || true
    pip3 install --quiet pytest pytest-asyncio pytest-cov pytest-mock httpx || true
    echo -e "${GREEN}✅ 测试依赖已安装${NC}"
else
    echo -e "${YELLOW}⚠️  跳过本地Python依赖安装（将使用Docker）${NC}"
fi

# 检查服务状态
echo ""
echo -e "${BLUE}🔍 检查服务状态...${NC}"
if docker ps --format '{{.Names}}' | grep -q "enterprise-ai-api-gateway"; then
    echo -e "${GREEN}✅ API Gateway运行中${NC}"
else
    echo -e "${YELLOW}⚠️  API Gateway未运行，测试可能需要启动服务${NC}"
fi

if docker ps --format '{{.Names}}' | grep -q "enterprise-ai-postgres"; then
    echo -e "${GREEN}✅ PostgreSQL运行中${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL未运行${NC}"
fi

if docker ps --format '{{.Names}}' | grep -q "enterprise-ai-redis"; then
    echo -e "${GREEN}✅ Redis运行中${NC}"
else
    echo -e "${YELLOW}⚠️  Redis未运行${NC}"
fi

# 创建测试结果目录
mkdir -p test-results
mkdir -p coverage-report

echo ""
echo -e "${GREEN}✅ 测试环境设置完成！${NC}"
echo ""
echo "下一步："
echo "  运行单元测试: ./scripts/test/run-unit-tests.sh"
echo "  运行集成测试: ./scripts/test/run-integration-tests.sh"
echo "  运行端到端测试: ./scripts/test/run-e2e-tests.sh"
echo "  运行所有测试: ./scripts/test/run-all-tests.sh"

