#!/bin/bash

# 检查服务状态的脚本

echo "=== 检查 Docker 服务状态 ==="
docker-compose ps

echo ""
echo "=== 检查 API Gateway 日志（最近20行）==="
docker-compose logs --tail=20 api-gateway

echo ""
echo "=== 检查 Agent Service 日志（最近20行）==="
docker-compose logs --tail=20 agent-service

echo ""
echo "=== 检查服务健康状态 ==="
echo "API Gateway:"
curl -s http://localhost:8080/health || echo "❌ API Gateway 无法访问"

echo ""
echo "Agent Service:"
curl -s http://localhost:8010/health || echo "❌ Agent Service 无法访问"

echo ""
echo "=== 测试聊天端点 ==="
curl -X POST http://localhost:8080/api/chat/intelligent/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "你好", "conversation_history": [], "user_context": {"user_id": "test"}}' \
  --max-time 5 || echo "❌ 聊天端点无法访问"





































