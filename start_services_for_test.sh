#!/bin/bash
# 启动测试所需的服务

echo "=========================================="
echo "启动统一意图识别MVP测试所需服务"
echo "=========================================="

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 启动基础服务（数据库、Redis）
echo ""
echo "1. 启动基础服务（PostgreSQL、Redis）..."
docker-compose up -d postgres redis

# 等待数据库就绪
echo ""
echo "2. 等待数据库就绪..."
sleep 5

# 启动agent-service
echo ""
echo "3. 启动agent-service..."
docker-compose up -d agent-service

# 等待服务启动
echo ""
echo "4. 等待agent-service启动..."
sleep 10

# 检查服务状态
echo ""
echo "5. 检查服务状态..."
docker-compose ps agent-service

echo ""
echo "=========================================="
echo "服务启动完成！"
echo "=========================================="
echo ""
echo "agent-service地址: http://localhost:8010"
echo "API文档: http://localhost:8010/docs"
echo "统一意图MVP端点: http://localhost:8010/api/v1/unified/process"
echo ""
echo "查看日志: docker-compose logs -f agent-service"
echo "停止服务: docker-compose stop agent-service"
echo ""




