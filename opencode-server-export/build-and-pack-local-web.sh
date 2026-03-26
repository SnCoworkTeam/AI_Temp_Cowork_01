#!/usr/bin/env bash
# OpenCode 本地 Web：本机构建并把需上传的文件放到一个文件夹
# 在仓库根目录执行: ./opencode-server-export/build-and-pack-local-web.sh
# 完成后所有要上传的文件在 opencode-upload 目录下

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXPORT_DIR="$REPO_ROOT/opencode-server-export"
UPLOAD_DIR="$REPO_ROOT/opencode-upload"

cd "$REPO_ROOT"

echo "=== 1/3 构建镜像 ==="
docker build -f opencode-src/Dockerfile.local-web -t enterprise-ai-opencode-local-web:latest opencode-src

echo ""
echo "=== 2/3 导出镜像为 tar ==="
docker save -o "$EXPORT_DIR/enterprise-ai-opencode-local-web.tar" enterprise-ai-opencode-local-web:latest

echo ""
echo "=== 3/3 整理上传包到 opencode-upload ==="
rm -rf "$UPLOAD_DIR"
mkdir -p "$UPLOAD_DIR"

cp "$EXPORT_DIR/enterprise-ai-opencode-local-web.tar" "$UPLOAD_DIR/"
cp "$EXPORT_DIR/docker-compose.opencode.local-web.yml" "$UPLOAD_DIR/"
cp "$EXPORT_DIR/.env.example" "$UPLOAD_DIR/"
[ -f "$EXPORT_DIR/.env" ] && cp "$EXPORT_DIR/.env" "$UPLOAD_DIR/"

echo "完成. 上传目录: $UPLOAD_DIR"
echo "单步上传命令见: opencode-server-export/单步上传命令.md"
