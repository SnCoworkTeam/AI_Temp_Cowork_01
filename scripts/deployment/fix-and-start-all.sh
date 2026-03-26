#!/bin/bash
# 修复并启动所有服务

set -e

cd /opt/enterprise-ai-platform

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "修复并启动所有服务"
echo "==========================================${NC}"

# 1. 修复.env文件
echo -e "${BLUE}[1/5] 修复.env文件...${NC}"
sudo rm -f .env
if [ -f env.example ]; then
    sudo cp env.example .env
    sudo chown ubuntu:ubuntu .env
    echo -e "${GREEN}✅ .env文件已修复${NC}"
else
    echo -e "${RED}❌ env.example不存在${NC}"
    exit 1
fi

# 2. 启动Redis（从docker-compose.yml）
echo -e "${BLUE}[2/5] 启动Redis服务...${NC}"
if ! sudo docker compose ps redis 2>/dev/null | grep -q "Up"; then
    sudo docker compose up -d redis
    echo "等待Redis就绪..."
    sleep 5
    echo -e "${GREEN}✅ Redis已启动${NC}"
else
    echo -e "${GREEN}✅ Redis已在运行${NC}"
fi

# 3. 启动MCP Gateway
echo -e "${BLUE}[3/5] 启动MCP Gateway...${NC}"
sudo docker compose up -d --build mcp-gateway
sleep 5
if sudo docker compose ps mcp-gateway | grep -q "Up"; then
    echo -e "${GREEN}✅ MCP Gateway已启动${NC}"
else
    echo -e "${RED}❌ MCP Gateway启动失败${NC}"
    sudo docker compose logs --tail=20 mcp-gateway
fi

# 4. 启动其他服务
echo -e "${BLUE}[4/5] 启动其他服务...${NC}"
services=("auth-service" "knowledge-base" "workflow-engine" "web-ui")
for svc in "${services[@]}"; do
    echo "启动 $svc..."
    sudo docker compose up -d --build $svc
    sleep 3
    if sudo docker compose ps $svc | grep -q "Up"; then
        echo -e "${GREEN}✅ $svc 已启动${NC}"
    else
        echo -e "${YELLOW}⚠️  $svc 启动中或失败，查看日志:${NC}"
        sudo docker compose logs --tail=10 $svc
    fi
done

# 5. 检查所有服务状态
echo -e "${BLUE}[5/5] 检查服务状态...${NC}"
echo ""
sudo docker compose ps

echo ""
echo -e "${BLUE}=========================================="
echo "服务统计"
echo "==========================================${NC}"

expected_services=("redis" "mcp-gateway" "workflow-engine" "auth-service" "knowledge-base" "web-ui")
running=0
stopped=0

for svc in "${expected_services[@]}"; do
    if sudo docker compose ps $svc 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}✅ $svc - 运行中${NC}"
        running=$((running + 1))
    else
        echo -e "${RED}❌ $svc - 未运行${NC}"
        stopped=$((stopped + 1))
    fi
done

echo ""
echo -e "运行中: ${GREEN}$running${NC} / ${#expected_services[@]}"
echo -e "未运行: ${RED}$stopped${NC} / ${#expected_services[@]}"

if [ $stopped -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}未运行的服务日志:${NC}"
    for svc in "${expected_services[@]}"; do
        if ! sudo docker compose ps $svc 2>/dev/null | grep -q "Up"; then
            echo -e "${YELLOW}--- $svc 日志 ---${NC}"
            sudo docker compose logs --tail=15 $svc 2>&1 | tail -10
            echo ""
        fi
    done
fi

