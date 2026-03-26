#!/bin/bash
# 更新镜像源为腾讯云并部署服务
# 使用方法: 在服务器上执行此脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "步骤1: 修改镜像源为腾讯云"
echo "=========================================="

cd /opt/enterprise-ai-platform

# 修改所有 Dockerfile 中的镜像源
echo "正在更新 mcp-gateway/Dockerfile..."
sudo sed -i 's|pypi.tuna.tsinghua.edu.cn|mirrors.cloud.tencent.com|g' mcp-gateway/Dockerfile

echo "正在更新 workflow-engine/Dockerfile..."
sudo sed -i 's|pypi.tuna.tsinghua.edu.cn|mirrors.cloud.tencent.com|g' workflow-engine/Dockerfile

echo "正在更新 auth-service/Dockerfile..."
sudo sed -i 's|pypi.tuna.tsinghua.edu.cn|mirrors.cloud.tencent.com|g' auth-service/Dockerfile

echo "正在更新 knowledge-base/Dockerfile..."
sudo sed -i 's|pypi.tuna.tsinghua.edu.cn|mirrors.cloud.tencent.com|g' knowledge-base/Dockerfile

echo "正在更新 metadata-service/Dockerfile..."
sudo sed -i 's|pypi.tuna.tsinghua.edu.cn|mirrors.cloud.tencent.com|g' metadata-service/Dockerfile

# 验证修改
echo ""
echo "验证修改结果:"
echo "----------------------------------------"
grep "mirrors.cloud.tencent.com" mcp-gateway/Dockerfile | head -1 || echo "未找到腾讯云镜像源配置"
echo "----------------------------------------"

echo ""
echo "=========================================="
echo "步骤2: 构建并启动所有服务"
echo "=========================================="

# 构建并启动服务
sudo docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo "使用以下命令查看服务状态:"
echo "  sudo docker compose -f docker-compose.prod.yml ps"
echo "使用以下命令查看日志:"
echo "  sudo docker compose -f docker-compose.prod.yml logs -f"
echo "=========================================="

