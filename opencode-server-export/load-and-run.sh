#!/usr/bin/env bash
# 在内网服务器上加载 OpenCode 镜像并启动（本文件夹内执行）
# 用法: chmod +x load-and-run.sh && ./load-and-run.sh
# 请先配置 .env 中的 OPENCODE_WORKSPACE

set -e
cd "$(dirname "$0")"

# 若为分卷包，先合并
if [ -f enterprise-ai-opencode.tar.part1 ] && [ -f enterprise-ai-opencode.tar.part2 ]; then
  [ ! -f enterprise-ai-opencode.tar ] || rm -f enterprise-ai-opencode.tar
  echo "检测到分卷，先合并..."
  cat enterprise-ai-opencode.tar.part1 enterprise-ai-opencode.tar.part2 > enterprise-ai-opencode.tar
fi

echo "Loading OpenCode image..."
[ -f enterprise-ai-opencode.tar ] || { echo "ERROR: enterprise-ai-opencode.tar 未找到（若为分卷请先运行 join-opencode-tar.sh）"; exit 1; }
docker load -i enterprise-ai-opencode.tar

if [ ! -f .env ]; then
  echo "WARN: .env not found. Copy .env.example to .env and set OPENCODE_WORKSPACE."
  echo "Example: OPENCODE_WORKSPACE=/opt/enterprise-ai-platform"
  exit 1
fi

echo "Starting OpenCode..."
docker compose -f docker-compose.opencode.yml --env-file .env up -d
echo "Done. Check: docker compose -f docker-compose.opencode.yml ps"
