#!/bin/bash
# 统一意图识别LLM增强 - 部署脚本

set -e

echo "=========================================="
echo "统一意图识别LLM增强 - 部署脚本"
echo "=========================================="
echo ""

# 检查环境变量
if [ -z "$DEEPSEEK_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "错误: 未设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY"
    exit 1
fi

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 安装依赖
echo ""
echo "安装依赖..."
pip install -q httpx langchain-openai fastapi uvicorn sqlalchemy pydantic

# 检查数据库连接
echo ""
echo "检查数据库连接..."
python3 -c "
from database.src.core.database import get_database_manager
db = get_database_manager()
if db.test_connection():
    print('数据库连接成功')
else:
    print('数据库连接失败')
    exit(1)
"

# 运行测试
echo ""
echo "运行基础测试..."
python3 -c "
import asyncio
from services.unified_intent_service import UnifiedIntentService

async def test():
    service = UnifiedIntentService()
    result = await service.understand_intent('测试输入')
    print(f'测试通过: {result.base_intent}')

asyncio.run(test())
"

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "启动服务:"
echo "  python3 -m uvicorn api.unified_intent_api:app --host 0.0.0.0 --port 8002"
echo ""

