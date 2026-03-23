#!/bin/bash
# 启动所有服务的脚本
# 确保所有服务都能正常启动

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "启动所有服务"
echo "==========================================${NC}"

# 检查.env文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env文件不存在，从env.example创建...${NC}"
    if [ -f env.example ]; then
        cp env.example .env
        echo -e "${GREEN}✅ .env文件已创建${NC}"
    else
        echo -e "${RED}❌ env.example文件不存在${NC}"
        exit 1
    fi
fi

# 步骤1: 启动数据库服务（如果使用docker-compose.db.yml）
if [ -f docker-compose.db.yml ]; then
    echo -e "${BLUE}[1/3] 启动数据库服务...${NC}"
    docker compose -f docker-compose.db.yml up -d
    echo "等待数据库服务就绪..."
    sleep 5
    echo -e "${GREEN}✅ 数据库服务已启动${NC}"
fi

# 步骤2: 确保Redis服务运行（如果不在db compose中）
if ! docker compose ps redis 2>/dev/null | grep -q "Up"; then
    echo -e "${BLUE}[2/3] 启动Redis服务...${NC}"
    docker compose up -d redis
    echo "等待Redis就绪..."
    sleep 3
    echo -e "${GREEN}✅ Redis服务已启动${NC}"
fi

# 步骤3: 按顺序启动应用服务
echo -e "${BLUE}[3/3] 启动应用服务...${NC}"

# 3.1 启动MCP Gateway（基础服务）
echo "启动 MCP Gateway..."
docker compose up -d --build mcp-gateway
echo "等待MCP Gateway就绪..."
sleep 5

# 3.2 启动Auth Service
echo "启动 Auth Service..."
docker compose up -d --build auth-service
sleep 3

# 3.3 启动Knowledge Base
echo "启动 Knowledge Base..."
docker compose up -d --build knowledge-base
sleep 3

# 3.4 启动Workflow Engine（依赖MCP Gateway）
echo "启动 Workflow Engine..."
docker compose up -d --build workflow-engine
sleep 3

# 3.5 启动Web UI（最后启动，依赖所有后端服务）
echo "启动 Web UI..."
docker compose up -d --build web-ui
sleep 5

# 检查所有服务状态
echo ""
echo -e "${BLUE}=========================================="
echo "服务状态检查"
echo "==========================================${NC}"

docker compose ps

# 健康检查
echo ""
echo -e "${BLUE}健康检查...${NC}"

services=(
    "8001:MCP Gateway:/api/health"
    "8002:Workflow Engine:/api/health"
    "8003:Auth Service:/health"
    "8004:Knowledge Base:/api/health"
    "3000:Web UI:/api/health"
)

all_healthy=true
for service_info in "${services[@]}"; do
    IFS=':' read -r port name path <<< "$service_info"
    http_code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://localhost:${port}${path}" 2>/dev/null || echo "000")
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✅ $name (端口 $port) - 健康${NC}"
    else
        echo -e "${RED}❌ $name (端口 $port) - 未响应 (HTTP $http_code)${NC}"
        all_healthy=false
    fi
done

echo ""
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}=========================================="
    echo "✅ 所有服务已启动并运行正常！"
    echo "==========================================${NC}"
    echo ""
    echo "服务地址:"
    echo "  - MCP Gateway:      http://localhost:8001"
    echo "  - Workflow Engine:   http://localhost:8002"
    echo "  - Auth Service:      http://localhost:8003"
    echo "  - Knowledge Base:    http://localhost:8004"
    echo "  - Web UI:            http://localhost:3000"
else
    echo -e "${YELLOW}⚠️  部分服务可能未正常运行${NC}"
    echo "查看日志: docker compose logs -f"
fi

