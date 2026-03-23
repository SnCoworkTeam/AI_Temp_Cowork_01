#!/bin/bash
# 在服务器上直接执行的启动脚本

cd /opt/enterprise-ai-platform

echo "========================================"
echo "启动所有服务"
echo "========================================"

# 1. 修复.env
echo "[1/6] 修复.env文件..."
sudo rm -f .env
sudo cp env.example .env
sudo chown ubuntu:ubuntu .env
echo "✅ .env已修复"

# 2. 启动Redis
echo "[2/6] 启动Redis..."
sudo docker compose up -d redis
sleep 3
echo "✅ Redis已启动"

# 3. 启动MCP Gateway
echo "[3/6] 启动MCP Gateway..."
sudo docker compose up -d --build mcp-gateway 2>&1 | tail -10
sleep 5
echo "✅ MCP Gateway已启动"

# 4. 启动Auth Service和Knowledge Base
echo "[4/6] 启动Auth Service和Knowledge Base..."
sudo docker compose up -d --build auth-service knowledge-base 2>&1 | tail -10
sleep 5
echo "✅ Auth Service和Knowledge Base已启动"

# 5. 启动Workflow Engine
echo "[5/6] 启动Workflow Engine..."
sudo docker compose up -d --build workflow-engine 2>&1 | tail -10
sleep 5
echo "✅ Workflow Engine已启动"

# 6. 启动Web UI
echo "[6/6] 启动Web UI..."
sudo docker compose up -d --build web-ui 2>&1 | tail -10
sleep 10
echo "✅ Web UI已启动"

# 检查状态
echo ""
echo "========================================"
echo "服务状态"
echo "========================================"
sudo docker compose ps

echo ""
echo "========================================"
echo "服务统计"
echo "========================================"

services=("redis" "mcp-gateway" "workflow-engine" "auth-service" "knowledge-base" "web-ui")
running=0
stopped=0

for svc in "${services[@]}"; do
    if sudo docker compose ps $svc 2>/dev/null | grep -q "Up"; then
        echo "✅ $svc - 运行中"
        running=$((running + 1))
    else
        echo "❌ $svc - 未运行"
        stopped=$((stopped + 1))
        echo "查看日志:"
        sudo docker compose logs --tail=10 $svc 2>&1 | tail -5
    fi
done

echo ""
echo "运行中: $running / ${#services[@]}"
echo "未运行: $stopped / ${#services[@]}"

if [ $stopped -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✅ 所有服务已启动！"
    echo "========================================"
    echo ""
    echo "服务地址:"
    echo "  - MCP Gateway:      http://43.143.139.197:8001"
    echo "  - Workflow Engine:   http://43.143.139.197:8002"
    echo "  - Auth Service:      http://43.143.139.197:8003"
    echo "  - Knowledge Base:    http://43.143.139.197:8004"
    echo "  - Web UI:            http://43.143.139.197:3000"
fi

