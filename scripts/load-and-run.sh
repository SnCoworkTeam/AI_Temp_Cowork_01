#!/bin/bash
# 在内网服务器上（Linux）：加载导出的镜像并启动
# 服务器目录: /opt/enterprise-ai-platform/
# 用法: 进入部署目录后执行
#   chmod +x load-and-run.sh && ./load-and-run.sh
# 或指定导出所在子目录: ./load-and-run.sh docker-images-export

set -e
EXPORT_DIR="${1:-.}"
cd "$EXPORT_DIR" || { echo "ERROR: Directory not found: $EXPORT_DIR"; exit 1; }

echo "Loading images from $EXPORT_DIR..."
for f in *.tar; do
  [ -f "$f" ] || continue
  echo "  Load: $f"
  docker load -i "$f"
done

if [ ! -f docker-compose.yml ]; then
  echo "WARN: docker-compose.yml not found in $EXPORT_DIR. Start manually."
  exit 0
fi

# 与导出镜像名一致，确保 compose 找到已加载的镜像
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-enterprise-ai-platform}"
echo "Starting stack (--no-build, use loaded images only)..."
docker compose up -d --no-build
echo "Done. Use 'docker compose ps' to check status."
