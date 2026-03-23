#!/bin/bash
# Build zhgj 19 services only (15 app images; postgres/redis/qdrant/neo4j use pre-built images).
# Run from repo root: bash scripts/build-zhgj-19.sh
# On Linux if you see $'\r': command not found, run first: sed -i 's/\r$//' scripts/build-zhgj-19.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ZHGJ_19_APP_SERVICES="registry-service api-gateway config-center mcp-gateway workflow-engine web-ui auth-service knowledge-base metadata-service chat-service dag-orchestrator agent-service agent-orchestrator agent-registry memory-service"

echo "Building zhgj 19 services (15 app images; postgres/redis/qdrant/neo4j use pre-built images)..."
docker compose build $ZHGJ_19_APP_SERVICES
echo "Build done. Start with: docker compose up -d"
