#!/bin/bash
# API使用示例 - cURL

BASE_URL="http://localhost:8000"
AUTH_TOKEN="your-auth-token"

# 获取工具列表
curl -X GET "${BASE_URL}/api/tools" \
  -H "Authorization: Bearer ${AUTH_TOKEN}"

# 执行工具
curl -X POST "${BASE_URL}/api/tools/test_tool/execute" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"input": "test"}}'

# 用户登录
curl -X POST "http://localhost:8002/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass"
  }'

# 创建工作流
curl -X POST "http://localhost:8001/api/workflows" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example_workflow",
    "description": "Example workflow",
    "config": {
      "nodes": [],
      "connections": []
    }
  }'









