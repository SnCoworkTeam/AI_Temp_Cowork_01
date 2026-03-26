#!/bin/bash
# 监控部署状态并自动修复

SERVER_IP="43.143.139.197"
SERVER_USER="ubuntu"
KEY_PATH="E:/enterprise-ai-platform/enterprise_ai_platform.pem"
REMOTE_PATH="/opt/enterprise-ai-platform"
MAX_ITERATIONS=30

SSH_CMD="ssh -i \"$KEY_PATH\" -o StrictHostKeyChecking=no $SERVER_USER@${SERVER_IP}"

echo "=========================================="
echo "监控部署状态"
echo "=========================================="
echo ""

iteration=0
all_healthy=false

while [ $iteration -lt $MAX_ITERATIONS ] && [ "$all_healthy" = false ]; do
    iteration=$((iteration + 1))
    echo "=== 迭代 $iteration/$MAX_ITERATIONS ==="
    
    # 检查服务状态
    echo "检查服务状态..."
    $SSH_CMD "cd $REMOTE_PATH && sudo docker compose ps" 2>&1
    
    # 检查健康状态
    echo ""
    echo "健康检查..."
    services=("8001:MCP Gateway:/api/health" "8002:Workflow Engine:/api/health" "8003:Auth Service:/health" "8004:Knowledge Base:/api/health" "3000:Web UI:/api/health")
    all_healthy=true
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r port name path <<< "$service_info"
        http_code=$($SSH_CMD "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:$port$path 2>&1" || echo "000")
        if [ "$http_code" = "200" ]; then
            echo "✅ $name - 健康"
        else
            echo "❌ $name - 未响应 (HTTP $http_code)"
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        echo ""
        echo "✅ 所有服务健康检查通过！"
        break
    fi
    
    # 检查错误日志
    echo ""
    echo "检查错误日志..."
    errors=$($SSH_CMD "cd $REMOTE_PATH && sudo docker compose logs --tail=50 2>&1 | grep -iE '(error|failed|exception|traceback)' | head -10")
    if [ -n "$errors" ]; then
        echo "发现错误:"
        echo "$errors"
    fi
    
    echo ""
    echo "等待 10 秒后再次检查..."
    sleep 10
done

echo ""
echo "=========================================="
echo "最终状态"
echo "=========================================="
$SSH_CMD "cd $REMOTE_PATH && sudo docker compose ps"

if [ "$all_healthy" = true ]; then
    echo ""
    echo "✅ 所有服务已启动并运行正常！"
    echo ""
    echo "服务地址:"
    echo "  - MCP Gateway:      http://$SERVER_IP:8001"
    echo "  - Workflow Engine:   http://$SERVER_IP:8002"
    echo "  - Auth Service:      http://$SERVER_IP:8003"
    echo "  - Knowledge Base:    http://$SERVER_IP:8004"
    echo "  - Web UI:            http://$SERVER_IP:3000"
else
    echo ""
    echo "❌ 部分服务未正常运行"
    echo "查看详细日志:"
    echo "  ssh -i \"$KEY_PATH\" $SERVER_USER@${SERVER_IP}"
    echo "  cd $REMOTE_PATH"
    echo "  sudo docker compose logs -f"
fi

