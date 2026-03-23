#!/bin/bash
# 检查并修复服务脚本
# 在服务器上执行: bash /opt/enterprise-ai-platform/scripts/deployment/check-and-fix-services.sh

cd /opt/enterprise-ai-platform

echo "=========================================="
echo "服务检查和修复"
echo "=========================================="
echo ""

# 检查需要的服务
REQUIRED_SERVICES=("mcp-gateway" "workflow-engine" "auth-service" "knowledge-base" "web-ui")

echo "1. 检查服务状态:"
for service in "${REQUIRED_SERVICES[@]}"; do
    STATUS=$(sudo docker compose -f docker-compose.prod.yml ps $service 2>/dev/null | grep -v NAME | awk '{print $5}')
    if [ -z "$STATUS" ] || [ "$STATUS" = "Exited" ] || [ "$STATUS" = "Restarting" ]; then
        echo "   ⚠ $service: $STATUS (需要修复)"
    else
        echo "   ✓ $service: $STATUS"
    fi
done
echo ""

echo "2. 检查镜像是否存在:"
for service in "${REQUIRED_SERVICES[@]}"; do
    IMAGE=$(sudo docker images | grep "$service" | head -1)
    if [ -z "$IMAGE" ]; then
        echo "   ⚠ $service: 镜像不存在，需要构建"
    else
        echo "   ✓ $service: 镜像存在"
    fi
done
echo ""

echo "3. 尝试启动所有服务:"
sudo docker compose -f docker-compose.prod.yml up -d 2>&1 | tail -10
echo ""

echo "4. 等待5秒后检查服务状态:"
sleep 5
sudo docker compose -f docker-compose.prod.yml ps
echo ""

echo "5. 检查服务健康状态:"
for service in "${REQUIRED_SERVICES[@]}"; do
    CONTAINER_NAME=$(sudo docker compose -f docker-compose.prod.yml ps $service 2>/dev/null | grep -v NAME | awk '{print $1}')
    if [ ! -z "$CONTAINER_NAME" ]; then
        HEALTH=$(sudo docker inspect $CONTAINER_NAME 2>/dev/null | grep -i health | head -1)
        if [ ! -z "$HEALTH" ]; then
            echo "   $service: 有健康检查配置"
        fi
    fi
done
echo ""

echo "=========================================="
echo "如果服务未启动，查看日志:"
echo "  sudo docker compose -f docker-compose.prod.yml logs [service-name]"
echo "=========================================="

