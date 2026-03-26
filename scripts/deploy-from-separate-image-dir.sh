#!/bin/bash
# 部署：代码在 /opt/enterprise-ai-platform，镜像包在 /opt/enterprise-ai-platform1
# 用法: bash scripts/deploy-from-separate-image-dir.sh
# 保证后期在代码目录 git pull 后，容器内挂载的代码会更新（重启服务即可）

set -e
CODE_DIR="/opt/enterprise-ai-platform"
IMAGE_DIR="/opt/enterprise-ai-platform1"

echo "=== 1. 从镜像目录加载所有 .tar ==="
cd "$IMAGE_DIR" || { echo "ERROR: $IMAGE_DIR not found"; exit 1; }
for f in *.tar; do
  [ -f "$f" ] || continue
  echo "  Load: $f"
  docker load -i "$f"
done

echo "=== 2. 确保代码目录有 .env ==="
cd "$CODE_DIR" || { echo "ERROR: $CODE_DIR not found"; exit 1; }
if [ ! -f .env ]; then
  if [ -f "$IMAGE_DIR/.env" ]; then
    cp "$IMAGE_DIR/.env" .env
    echo "  Copied .env from $IMAGE_DIR"
  elif [ -f .env.example ]; then
    cp .env.example .env
    sed -i 's/\r$//' .env
    sed -i '1s/^\xEF\xBB\xBF//' .env
    echo "  Created .env from .env.example"
  else
    echo "  WARN: No .env or .env.example. Create .env manually."
  fi
fi

echo "=== 3. 在代码目录启动 19 服务（不构建，使用已加载镜像）==="
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-enterprise-ai-platform}"
docker compose up -d --no-build

echo "Done. Containers mount code from $CODE_DIR; after 'git pull' there, restart: docker compose restart <service>"
