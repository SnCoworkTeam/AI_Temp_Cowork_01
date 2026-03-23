#!/bin/bash
# zhgj 19 服务逐个启动（便于排查，某个失败不会影响已启动的）
# 在项目根目录执行: bash scripts/up-zhgj-19-one-by-one.sh
# 若脚本有 CRLF，先执行: sed -i 's/\r$//' scripts/up-zhgj-19-one-by-one.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-enterprise-ai-platform}"

# 19 个服务按依赖顺序逐个 up（基础 -> 注册/网关 -> 业务）
ZHGJ_19_SERVICES="postgres redis qdrant neo4j registry-service api-gateway config-center mcp-gateway workflow-engine web-ui auth-service knowledge-base metadata-service chat-service dag-orchestrator agent-service agent-orchestrator agent-registry memory-service"

for svc in $ZHGJ_19_SERVICES; do
  echo "========== Starting: $svc =========="
  docker compose up -d --no-build "$svc" || { echo "*** FAILED: $svc ***"; exit 1; }
  sleep 2
done

echo "========== All 19 services started =========="
docker compose ps
