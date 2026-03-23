#!/usr/bin/env bash
# 从 Git 拉取 OpenCode 源码到本地
# 用法: ./scripts/clone-opencode.sh [目标目录]
# 默认克隆到项目根目录下的 opencode-src（可通过 .gitignore 忽略）

set -e
REPO_URL="https://github.com/anomalyco/opencode.git"
BRANCH="${OPENCODE_BRANCH:-dev}"

# 项目根目录（脚本在 scripts/ 下）
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-$ROOT/opencode-src}"

if [[ -d "$DEST" ]]; then
  echo "目录已存在: $DEST"
  echo "进入目录并执行 git pull..."
  cd "$DEST"
  git fetch origin
  git checkout "$BRANCH" 2>/dev/null || true
  git pull origin "$BRANCH"
  echo "已更新。"
  exit 0
fi

echo "正在克隆 OpenCode 到: $DEST"
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$DEST"
echo "克隆完成。进入目录: cd $DEST"
