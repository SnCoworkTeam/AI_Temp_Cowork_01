#!/usr/bin/env bash
# 在服务器上将拆分的两个包合并为一个 .tar（本文件夹内执行）
# 用法: chmod +x join-opencode-tar.sh && ./join-opencode-tar.sh
# 合并后再执行 load-and-run.sh 加载镜像

set -e
cd "$(dirname "$0")"

PART1="enterprise-ai-opencode.tar.part1"
PART2="enterprise-ai-opencode.tar.part2"
OUT="enterprise-ai-opencode.tar"

if [ ! -f "$PART1" ] || [ ! -f "$PART2" ]; then
  echo "ERROR: 未找到 $PART1 或 $PART2，请先上传两个分卷到本目录。"
  exit 1
fi

echo "正在合并为 $OUT ..."
cat "$PART1" "$PART2" > "$OUT"
echo "合并完成。可执行 ./load-and-run.sh 加载镜像并启动。"
