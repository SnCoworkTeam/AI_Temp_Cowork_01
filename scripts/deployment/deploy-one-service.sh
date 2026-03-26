#!/usr/bin/env bash
# 单服务发布：通过 deployment-agent API 发布指定服务到目标服务器
# 用法: ./scripts/deployment/deploy-one-service.sh <服务名>
# 示例: ./scripts/deployment/deploy-one-service.sh project-management
# 环境变量: DEPLOYMENT_AGENT_URL 默认 http://localhost:8007

set -e
SERVICE_NAME="${1:?请传入服务名，例如 project-management}"
DEPLOYMENT_AGENT_URL="${DEPLOYMENT_AGENT_URL:-http://localhost:8007}"
API="${DEPLOYMENT_AGENT_URL}/api/v1/deploy"

echo "正在发布服务: $SERVICE_NAME (deployment-agent: $DEPLOYMENT_AGENT_URL)"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API" \
  -H "Content-Type: application/json" \
  -d "{\"services\": [\"$SERVICE_NAME\"], \"skip_data_sync\": true, \"skip_migration\": false}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [[ "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]]; then
  echo "请求已接受 (HTTP $HTTP_CODE)"
  echo "$BODY" | head -c 500
  echo ""
  exit 0
else
  echo "请求失败 (HTTP $HTTP_CODE)"
  echo "$BODY"
  exit 1
fi
