#!/bin/bash

# Docker 服务连接诊断脚本

echo "🔍 检查 Docker 服务连接状态..."
echo ""

# 检查 API Gateway
echo "1. 检查 API Gateway (http://localhost:8080)"
if curl -s -f http://localhost:8080/health > /dev/null 2>&1; then
    echo "   ✅ API Gateway 可访问"
else
    echo "   ❌ API Gateway 不可访问"
fi

# 检查 agent-service
echo "2. 检查 agent-service (http://localhost:8010)"
if curl -s -f http://localhost:8010/api/v1/health > /dev/null 2>&1; then
    echo "   ✅ agent-service 可访问"
else
    echo "   ❌ agent-service 不可访问"
fi

# 检查 mcp-gateway
echo "3. 检查 mcp-gateway (http://localhost:8001)"
if curl -s -f http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "   ✅ mcp-gateway 可访问"
else
    echo "   ❌ mcp-gateway 不可访问"
fi

# 检查 knowledge-base
echo "4. 检查 knowledge-base (http://localhost:8004)"
if curl -s -f http://localhost:8004/health > /dev/null 2>&1; then
    echo "   ✅ knowledge-base 可访问"
else
    echo "   ❌ knowledge-base 不可访问"
fi

echo ""
echo "📋 检查 Docker 容器状态..."
docker ps --filter "name=enterprise-ai" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔗 检查 Docker 网络..."
docker network inspect enterprise-ai-platform_enterprise-ai-network 2>/dev/null | grep -A 5 "Containers" || echo "   网络未找到或无法访问"

echo ""
echo "💡 如果服务不可访问，请检查："
echo "   1. 所有服务是否都在运行: docker-compose ps"
echo "   2. 服务日志是否有错误: docker-compose logs agent-service"
echo "   3. Docker 网络是否正确: docker network ls"
echo "   4. 服务之间的连接: docker exec enterprise-ai-agent-service ping -c 2 mcp-gateway"
















