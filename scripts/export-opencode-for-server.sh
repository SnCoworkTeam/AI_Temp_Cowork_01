#!/usr/bin/env bash
# 在本地构建 OpenCode 镜像、打包并导出到 opencode-server-export 文件夹，供上传内网服务器
# 用法: 在项目根目录执行 ./scripts/export-opencode-for-server.sh
# 输出: opencode-server-export/ 下含镜像 .tar 及部署所需全部文件

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

EXPORT_DIR="$ROOT/opencode-server-export"
IMAGE_NAME="enterprise-ai-opencode:latest"
TAR_NAME="enterprise-ai-opencode.tar"

echo "========== 1/3 构建 OpenCode 镜像 =========="
docker compose build opencode

echo ""
echo "========== 2/3 导出镜像为 .tar =========="
mkdir -p "$EXPORT_DIR"
docker save -o "$EXPORT_DIR/$TAR_NAME" "$IMAGE_NAME"
echo "已保存: $EXPORT_DIR/$TAR_NAME"

echo ""
echo "========== 3/3 检查导出文件夹 =========="
for f in docker-compose.opencode.yml .env.example 服务器启动说明.txt load-and-run.sh load-and-run.ps1; do
  [ -f "$EXPORT_DIR/$f" ] && echo "  OK $f" || echo "  缺失 $f"
done

echo ""
echo "完成。请将整个 opencode-server-export 文件夹上传到内网服务器，按 服务器启动说明.txt 操作。"
