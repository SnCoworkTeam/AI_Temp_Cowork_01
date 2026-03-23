#!/bin/bash
# 服务器Docker服务手动启动命令 - 简洁版
# 按顺序执行以下命令

cd /opt/enterprise-ai-platform

echo "=========================================="
echo "第一阶段：启动基础服务"
echo "=========================================="

# 1. 启动PostgreSQL数据库
echo "[1/8] 启动PostgreSQL..."
sudo docker compose up -d postgres
sleep 15
echo "✅ PostgreSQL已启动"

# 2. 启动Redis缓存
echo "[2/8] 启动Redis..."
sudo docker compose up -d redis
sleep 10
echo "✅ Redis已启动"

echo ""
echo "=========================================="
echo "第二阶段：启动核心服务"
echo "=========================================="

# 3. 构建并启动MCP Gateway
echo "[3/8] 构建并启动MCP Gateway..."
sudo docker compose up -d --build mcp-gateway
sleep 30
echo "✅ MCP Gateway已启动"

# 4. 构建并启动Auth Service
echo "[4/8] 构建并启动Auth Service..."
sudo docker compose up -d --build auth-service
sleep 30
echo "✅ Auth Service已启动"

# 5. 构建并启动Knowledge Base
echo "[5/8] 构建并启动Knowledge Base..."
sudo docker compose up -d --build knowledge-base
sleep 60
echo "✅ Knowledge Base已启动"

# 6. 构建并启动Metadata Service
echo "[6/8] 构建并启动Metadata Service..."
sudo docker compose up -d --build metadata-service
sleep 30
echo "✅ Metadata Service已启动"

echo ""
echo "=========================================="
echo "第三阶段：启动工作流引擎"
echo "=========================================="

# 7. 构建并启动Workflow Engine
echo "[7/8] 构建并启动Workflow Engine..."
sudo docker compose up -d --build workflow-engine
sleep 30
echo "✅ Workflow Engine已启动"

echo ""
echo "=========================================="
echo "第四阶段：启动Web UI"
echo "=========================================="

# 8. 构建并启动Web UI
echo "[8/8] 构建并启动Web UI..."
sudo docker compose up -d --build web-ui
sleep 60
echo "✅ Web UI已启动"

echo ""
echo "=========================================="
echo "所有服务启动完成！"
echo "=========================================="
echo ""
echo "查看服务状态："
sudo docker compose ps
echo ""
echo "服务访问地址："
echo "  - MCP Gateway:      http://43.143.139.197:8001"
echo "  - Workflow Engine:   http://43.143.139.197:8002"
echo "  - Auth Service:      http://43.143.139.197:8003"
echo "  - Knowledge Base:   http://43.143.139.197:8004"
echo "  - Metadata Service: http://43.143.139.197:8005"
echo "  - Web UI:            http://43.143.139.197:3000"
echo ""

