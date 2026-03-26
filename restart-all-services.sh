#!/bin/bash
# 服务器重启后检查和启动所有服务

echo "=================================================="
echo "检查服务器状态并按顺序启动服务"
echo "=================================================="
echo ""

cd /opt/enterprise-ai-platform

# 等待Docker服务完全启动
echo "1. 等待Docker服务启动..."
sleep 10

# 检查所有容器状态
echo ""
echo "2. 检查当前容器状态:"
sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}' | head -30

# 定义服务启动顺序
# 第一层：基础设施
LAYER1=(
    "enterprise-ai-postgres"
    "enterprise-ai-redis"
    "enterprise-ai-qdrant"
)

# 第二层：核心服务
LAYER2=(
    "enterprise-ai-config-center"
    "enterprise-ai-registry-service"
)

# 第三层：业务服务
LAYER3=(
    "enterprise-ai-auth-service"
    "enterprise-ai-knowledge-base"
    "enterprise-ai-vector-coordinator"
    "enterprise-ai-metadata-service"
    "enterprise-ai-workflow-engine"
    "enterprise-ai-mcp-gateway"
    "enterprise-ai-agent-service"
    "enterprise-ai-api-gateway"
    "enterprise-ai-web-ui"
)

# 第四层：其他服务
LAYER4=(
    "enterprise-ai-sap-metadata-agent"
    "enterprise-ai-memory-service"
    "enterprise-ai-agent-registry"
    "enterprise-ai-agent-orchestrator"
    "enterprise-ai-project-management"
    "enterprise-ai-redis-commander"
    "sap-mcp-web-client"
    "project-redis-prod"
    "project-backend-prod"
    "project-frontend-prod"
)

# 函数：检查并启动服务
check_and_start() {
    local service=$1
    local status=$(sudo docker ps -a --filter "name=^${service}$" --format '{{.Status}}')

    if [[ $status == Up* ]]; then
        echo "  ✓ $service 正在运行"
        return 0
    elif [[ -z $status ]]; then
        echo "  ⚠ $service 不存在"
        return 1
    else
        echo "  ✗ $service 未运行，正在启动..."
        sudo docker start $service
        sleep 3

        # 检查启动是否成功
        status=$(sudo docker ps --filter "name=^${service}$" --format '{{.Status}}')
        if [[ $status == Up* ]]; then
            echo "  ✓ $service 启动成功"
            return 0
        else
            echo "  ✗ $service 启动失败"
            sudo docker logs --tail 20 $service
            return 1
        fi
    fi
}

# 启动第一层：基础设施
echo ""
echo "3. 启动第一层：基础设施服务"
echo "----------------------------------------"
for service in "${LAYER1[@]}"; do
    check_and_start $service
done

echo ""
echo "等待基础设施服务稳定..."
sleep 10

# 启动第二层：核心服务
echo ""
echo "4. 启动第二层：核心服务"
echo "----------------------------------------"
for service in "${LAYER2[@]}"; do
    check_and_start $service
done

echo ""
echo "等待核心服务稳定..."
sleep 10

# 启动第三层：业务服务
echo ""
echo "5. 启动第三层：业务服务"
echo "----------------------------------------"
for service in "${LAYER3[@]}"; do
    check_and_start $service
done

echo ""
echo "等待业务服务稳定..."
sleep 10

# 启动第四层：其他服务
echo ""
echo "6. 启动第四层：其他服务"
echo "----------------------------------------"
for service in "${LAYER4[@]}"; do
    check_and_start $service
done

# 最终检查
echo ""
echo "7. 最终状态检查"
echo "----------------------------------------"
echo ""
echo "运行中的服务:"
sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep "Up"

echo ""
echo "未运行的服务:"
sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}' | grep -v "Up"

echo ""
echo "8. 检查服务健康状态"
echo "----------------------------------------"
sudo docker ps --format 'table {{.Names}}\t{{.Status}}' | grep "healthy\|unhealthy"

echo ""
echo "=================================================="
echo "服务启动检查完成"
echo "=================================================="
