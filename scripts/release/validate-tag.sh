#!/bin/bash
# 验证Git标签格式

set -e

TAG="$1"

if [ -z "$TAG" ]; then
    echo "用法: $0 TAG"
    exit 1
fi

# 验证标签格式（语义化版本）
if [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$ ]]; then
    echo "❌ 标签格式不正确: $TAG"
    echo "正确格式: vMAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]"
    exit 1
fi

echo "✅ 标签格式正确: $TAG"









