#!/bin/bash

# SAP OData 智能体元数据构建脚本
# 重启服务并触发元数据构建

set -e

echo "============================================================"
echo "SAP OData 智能体元数据构建"
echo "============================================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 重启 agent-service
echo -e "\n${YELLOW}[步骤 1/3] 重启 Agent Service...${NC}"
docker-compose restart agent-service || docker-compose up -d agent-service

echo "等待服务启动..."
sleep 10

# 2. 检查服务健康
echo -e "\n${YELLOW}[步骤 2/3] 检查服务健康状态...${NC}"

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -f http://localhost:8010/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Agent Service 已就绪${NC}"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "   等待中... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Agent Service 未就绪，请检查服务状态${NC}"
    exit 1
fi

# 3. 运行元数据构建脚本
echo -e "\n${YELLOW}[步骤 3/3] 触发元数据构建...${NC}"

if [ -f "build_sap_odata_agent_metadata.py" ]; then
    python build_sap_odata_agent_metadata.py
else
    echo -e "${RED}❌ 未找到构建脚本: build_sap_odata_agent_metadata.py${NC}"
    exit 1
fi

echo -e "\n${GREEN}============================================================"
echo "✅ 完成！"
echo "============================================================${NC}"

