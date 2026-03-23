#!/bin/bash
# 在Docker容器中运行自动修复系统

set -e

PROJECT_DIR="/app"
SCRIPT_DIR="/app/scripts/cicd"

echo "=========================================="
echo "Docker容器中运行自动修复"
echo "=========================================="

# 检查是否在Docker中
if [ ! -f /.dockerenv ]; then
    echo "⚠️ 不在Docker容器中，使用docker-compose运行..."
    
    # 使用docker-compose运行
    docker-compose run --rm -v "$(pwd):/app" -w /app api-gateway bash "$SCRIPT_DIR/docker-auto-fix.sh"
    exit $?
fi

# 在Docker容器中执行
cd "$PROJECT_DIR"

# 安装依赖
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q requests pyyaml

# 运行Python自动修复脚本
python3 "$SCRIPT_DIR/local-auto-fix.py"





