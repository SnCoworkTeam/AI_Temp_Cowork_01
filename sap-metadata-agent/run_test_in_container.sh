#!/bin/bash
# 在sap-metadata-agent容器内运行语义分析测试

echo "=========================================="
echo "在容器内运行语义分析测试"
echo "=========================================="

# 检查是否在容器内
if [ ! -f /.dockerenv ] && [ -z "$DOCKER_CONTAINER" ]; then
    echo "⚠️  不在容器内，将尝试进入容器..."
    echo "使用方法:"
    echo "  docker exec -it enterprise-ai-sap-metadata-agent python test_semantic_in_container.py"
    echo ""
    echo "或者先进入容器:"
    echo "  docker exec -it enterprise-ai-sap-metadata-agent bash"
    echo "  python test_semantic_in_container.py"
    exit 1
fi

echo "✅ 检测到在容器内运行"
echo ""

# 运行测试
python test_semantic_in_container.py

