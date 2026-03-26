#!/usr/bin/env bash
# 同机部署：在 OpenCode 容器内调用 deployment-agent 发布指定服务（与 19 服务同一台机）
# 用法: ./scripts/deployment/deploy-one-service-same-host.sh <服务名>
# 示例: ./scripts/deployment/deploy-one-service-same-host.sh project-management
# 环境变量: DEPLOYMENT_AGENT_URL 默认 http://deployment-agent:8000（同 compose 网络）

set -e
SERVICE_NAME="${1:?用法: $0 <服务名>，例如 project-management}"
DEPLOYMENT_AGENT_URL="${DEPLOYMENT_AGENT_URL:-http://deployment-agent:8000}"
API="${DEPLOYMENT_AGENT_URL}/api/v1/deploy"

echo "同机发布服务: $SERVICE_NAME (deployment-agent: $DEPLOYMENT_AGENT_URL)"
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
