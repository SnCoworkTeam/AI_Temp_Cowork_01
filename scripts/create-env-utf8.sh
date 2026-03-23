#!/bin/bash
# Create UTF-8 .env in project root (fix "unexpected character" when .env was UTF-16).
# Run from project root: ./scripts/create-env-utf8.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f .env ]; then
  echo "Backing up existing .env to .env.bak.utf16"
  mv .env .env.bak.utf16
fi

cat > .env << 'ENVEOF'
# UTF-8 .env for docker compose
PYTHON_VERSION=3.11
NODE_VERSION=20
DEBUG=true
LOG_LEVEL=info

DB_HOST=postgres
DB_PORT=5432
DB_USER=ai_user
DB_PASSWORD=ai_password
DB_NAME=ai_platform

REDIS_HOST=redis
REDIS_PORT=6379

MCP_GATEWAY_PORT=8001
WORKFLOW_ENGINE_PORT=8002
WEB_UI_PORT=3000
AUTH_SERVICE_PORT=8003
KNOWLEDGE_BASE_PORT=8004
VECTOR_STORE_TYPE=chroma
CHROMA_PERSIST_DIR=./chroma_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
DOCUMENT_STORAGE_DIR=./documents
MAX_FILE_SIZE=104857600
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

OPENAI_API_KEY=your_openai_api_key_here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
LANGCHAIN_API_KEY=your_langchain_api_key_here
LANGCHAIN_TRACING_V2=false

NEXT_PUBLIC_MCP_GATEWAY_URL=http://localhost:8001
NEXT_PUBLIC_WORKFLOW_ENGINE_URL=http://localhost:8002
NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8003
NEXT_PUBLIC_KNOWLEDGE_BASE_URL=http://localhost:8004

WORKFLOW_ENGINE_URL=http://workflow-engine:8002
MCP_GATEWAY_URL=http://mcp-gateway:8001
AUTH_SERVICE_URL=http://auth-service:8003
KNOWLEDGE_BASE_URL=http://knowledge-base:8004

COMPOSE_PROJECT_NAME=enterprise-ai-platform
ENVEOF

# Remove UTF-8 BOM if present (docker compose does not accept BOM)
sed -i '1s/^\xEF\xBB\xBF//' .env 2>/dev/null || true
# Remove Windows CRLF
sed -i 's/\r$//' .env 2>/dev/null || true

echo "Created .env (UTF-8, no BOM). Edit if needed, then: docker compose build"
