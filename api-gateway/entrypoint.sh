#!/bin/bash
# API Gateway启动脚本
# 确保所有依赖已安装

set -e

echo "=== API Gateway启动脚本 ==="
echo "检查并安装依赖..."

# 检查sqlalchemy是否已安装
if ! python -c "import sqlalchemy" 2>/dev/null; then
    echo "安装sqlalchemy..."
    pip install --no-cache-dir sqlalchemy>=2.0.0 psycopg2-binary>=2.9.0
fi

# 检查其他关键依赖
python -c "import fastapi" || pip install --no-cache-dir fastapi>=0.104.0
python -c "import uvicorn" || pip install --no-cache-dir uvicorn[standard]>=0.24.0

echo "依赖检查完成"
echo "启动服务..."

# 执行原始命令
exec "$@"

