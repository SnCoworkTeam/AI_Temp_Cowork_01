#!/bin/bash
# 阶段一第1周测试脚本（带Docker服务自动启动）

set -e

echo "========================================"
echo "  阶段一第1周测试 - Docker服务自动启动"
echo "========================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# 1. 启动Docker服务
echo "🚀 启动Docker服务..."
docker-compose up -d postgres

# 2. 等待服务就绪
echo "⏳ 等待postgres服务就绪..."
for i in {1..30}; do
    if docker ps --filter "name=postgres" --format "{{.Status}}" | grep -q "Up"; then
        echo "✅ postgres 服务已启动"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ postgres 服务启动超时"
        exit 1
    fi
    echo "  等待中... ($i/30)"
    sleep 2
done

# 额外等待数据库完全就绪
echo "⏳ 等待数据库完全就绪..."
sleep 5

# 3. 执行数据库迁移
echo ""
echo "📦 执行数据库迁移..."
cd database
alembic upgrade head
cd ..

# 4. 运行测试
echo ""
echo "🧪 运行测试..."
python -m pytest tests/test_stage1_week1_with_docker.py -v --tb=short -s

# 5. 测试结果
TEST_EXIT_CODE=$?

echo ""
echo "========================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ 所有测试通过！"
    echo "✅ 可以进入第2周"
else
    echo "❌ 测试失败，请检查错误信息"
    echo "❌ 不能进入第2周"
fi
echo "========================================"

exit $TEST_EXIT_CODE




