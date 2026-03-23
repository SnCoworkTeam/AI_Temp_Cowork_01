#!/bin/bash
# 确保所有服务都启动并运行

set -e

cd /opt/enterprise-ai-platform

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "确保所有服务启动"
echo "==========================================${NC}"

# 1. 修复.env
echo -e "${BLUE}[1/6] 修复.env文件...${NC}"
sudo rm -f .env
sudo cp env.example .env
sudo chown ubuntu:ubuntu .env
echo -e "${GREEN}✅ .env已修复${NC}"

# 2. 启动Redis
echo -e "${BLUE}[2/6] 启动Redis...${NC}"
sudo docker compose up -d redis
sleep 3
echo -e "${GREEN}✅ Redis已启动${NC}"

# 3. 启动MCP Gateway
echo -e "${BLUE}[3/6] 启动MCP Gateway...${NC}"
sudo docker compose up -d --build mcp-gateway
sleep 5
echo -e "${GREEN}✅ MCP Gateway已启动${NC}"

# 4. 启动Auth Service和Knowledge Base
echo -e "${BLUE}[4/6] 启动Auth Service和Knowledge Base...${NC}"
sudo docker compose up -d --build auth-service knowledge-base
sleep 5
echo -e "${GREEN}✅ Auth Service和Knowledge Base已启动${NC}"

# 5. 启动Workflow Engine
echo -e "${BLUE}[5/6] 启动Workflow Engine...${NC}"
sudo docker compose up -d --build workflow-engine
sleep 5
echo -e "${GREEN}✅ Workflow Engine已启动${NC}"

# 6. 启动Web UI
echo -e "${BLUE}[6/6] 启动Web UI...${NC}"
sudo docker compose up -d --build web-ui
sleep 10
echo -e "${GREEN}✅ Web UI已启动${NC}"

# 检查状态
echo ""
echo -e "${BLUE}=========================================="
echo "服务状态"
echo "==========================================${NC}"
sudo docker compose ps

echo ""
echo -e "${BLUE}=========================================="
echo "服务统计"
echo "==========================================${NC}"

services=("redis" "mcp-gateway" "workflow-engine" "auth-service" "knowledge-base" "web-ui")
running=0
stopped=0

for svc in "${services[@]}"; do
    if sudo docker compose ps $svc 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}✅ $svc - 运行中${NC}"
        running=$((running + 1))
    else
        echo -e "${RED}❌ $svc - 未运行${NC}"
        stopped=$((stopped + 1))
        echo "查看日志:"
        sudo docker compose logs --tail=15 $svc 2>&1 | tail -10
    fi
done

echo ""
echo -e "运行中: ${GREEN}$running${NC} / ${#services[@]}"
echo -e "未运行: ${RED}$stopped${NC} / ${#services[@]}"

if [ $stopped -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✅ 所有服务已启动！"
    echo "==========================================${NC}"
    echo ""
    echo "服务地址:"
    echo "  - MCP Gateway:      http://43.143.139.197:8001"
    echo "  - Workflow Engine:   http://43.143.139.197:8002"
    echo "  - Auth Service:      http://43.143.139.197:8003"
    echo "  - Knowledge Base:    http://43.143.139.197:8004"
    echo "  - Web UI:            http://43.143.139.197:3000"
else
    echo ""
    echo -e "${YELLOW}⚠️  部分服务未运行，请检查日志${NC}"
fi

