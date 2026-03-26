#!/bin/bash
# 在Docker容器内构建语义索引的便捷脚本

CONTAINER_NAME="enterprise-ai-sap-metadata-agent"
SCRIPT_PATH="/app/build_semantic_in_docker.py"

echo "=========================================="
echo "在Docker容器内构建语义索引"
echo "=========================================="
echo ""

# 检查容器是否运行
if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ 容器 ${CONTAINER_NAME} 未运行"
    echo "请先启动容器: docker-compose up -d sap-metadata-agent"
    exit 1
fi

echo "✅ 容器 ${CONTAINER_NAME} 正在运行"
echo ""

# 执行构建
echo "开始构建语义索引..."
echo ""

docker exec -it ${CONTAINER_NAME} python ${SCRIPT_PATH} "$@"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ 语义索引构建完成！"
else
    echo ""
    echo "❌ 语义索引构建失败（退出码: $exit_code）"
fi

exit $exit_code


