#!/bin/bash
# 测试查询组织机构功能

echo "=== 测试查询组织机构功能 ==="
echo ""

# 等待服务启动
echo "等待服务启动..."
sleep 5

# 测试API Gateway健康检查
echo "1. 检查API Gateway健康状态..."
curl -s http://localhost:8080/health | jq '.' || echo "API Gateway未响应"

echo ""
echo "2. 检查Agent Service健康状态..."
curl -s http://localhost:8010/api/v1/health | jq '.' || echo "Agent Service未响应"

echo ""
echo "3. 检查Metadata Service健康状态..."
curl -s http://localhost:8005/api/health | jq '.' || echo "Metadata Service未响应"

echo ""
echo "4. 测试查询组织机构API..."
curl -X POST http://localhost:8080/api/v1/dynamic-workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "查询组织机构",
    "context": {},
    "stream": false
  }' | jq '.' || echo "查询失败"

echo ""
echo "=== 测试完成 ==="








