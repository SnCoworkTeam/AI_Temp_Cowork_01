#!/bin/bash
# Neo4j配置检查脚本 - 在应用服务器上执行

echo "=========================================="
echo "Neo4j配置检查"
echo "=========================================="

# 检查1: 环境变量
echo ""
echo "[1] 检查.env文件中的Neo4j配置"
cd /opt/enterprise-ai-platform 2>/dev/null || cd /root/enterprise-ai-platform 2>/dev/null || { echo "项目目录未找到"; exit 1; }

if [ -f .env ]; then
    echo "找到.env文件"
    if grep -q "NEO4J_URI" .env; then
        echo "✅ 已配置NEO4J_URI:"
        grep "NEO4J_URI" .env
    else
        echo "❌ 未配置NEO4J_URI"
    fi
    
    if grep -q "NEO4J_USER" .env; then
        echo "✅ 已配置NEO4J_USER:"
        grep "NEO4J_USER" .env
    else
        echo "❌ 未配置NEO4J_USER"
    fi
    
    if grep -q "NEO4J_PASSWORD" .env; then
        echo "✅ 已配置NEO4J_PASSWORD:"
        grep "NEO4J_PASSWORD" .env | sed 's/PASSWORD=.*/PASSWORD=***/'
    else
        echo "❌ 未配置NEO4J_PASSWORD"
    fi
else
    echo "❌ .env文件不存在"
fi

# 检查2: 网络连接
echo ""
echo "[2] 测试到Neo4j服务器的网络连接"
if timeout 5 bash -c 'cat < /dev/null > /dev/tcp/43.143.90.179/7687' 2>/dev/null; then
    echo "✅ 网络连接成功: 43.143.90.179:7687"
else
    echo "❌ 网络连接失败: 43.143.90.179:7687"
    echo "   请检查防火墙和安全组设置"
fi

# 检查3: Docker Compose配置
echo ""
echo "[3] 检查Docker Compose配置"
if [ -f docker-compose.yml ]; then
    echo "找到docker-compose.yml文件"
    docker-compose config 2>/dev/null | grep -i NEO4J || echo "未找到Neo4j配置"
else
    echo "docker-compose.yml文件不存在"
fi

# 检查4: 运行中的容器
echo ""
echo "[4] 检查运行中容器的环境变量"
for container in $(docker ps --format "{{.Names}}" 2>/dev/null); do
    if docker exec $container env 2>/dev/null | grep -q NEO4J; then
        echo "容器 $container 包含Neo4j配置:"
        docker exec $container env | grep NEO4J
    fi
done

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="



