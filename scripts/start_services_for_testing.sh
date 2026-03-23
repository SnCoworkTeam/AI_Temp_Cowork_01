#!/bin/bash
# 启动测试所需的服务

echo "=========================================="
echo "启动测试所需的服务"
echo "=========================================="

# 检查docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 启动核心服务
echo ""
echo "1. 启动PostgreSQL数据库..."
docker-compose up -d postgres

echo ""
echo "2. 启动Redis（用于缓存）..."
docker-compose up -d redis

echo ""
echo "3. 启动Qdrant向量数据库..."
docker-compose up -d qdrant

echo ""
echo "4. 启动Neo4j图数据库..."
docker-compose up -d neo4j

echo ""
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "检查服务状态:"
docker-compose ps postgres redis qdrant neo4j

echo ""
echo "=========================================="
echo "服务启动完成"
echo "=========================================="
echo ""
echo "可以运行测试:"
echo "  pytest tests/milestone_integration_test.py -v"

