#!/bin/bash
# 检查应用服务器的Neo4j配置

APP_SERVER="43.143.139.197"
APP_USER="root"
KEY_FILE="enterprise_ai_platform.pem"
NEO4J_SERVER="43.143.90.179"
NEO4J_PORT="7687"

echo "=========================================="
echo "检查应用服务器Neo4j配置"
echo "=========================================="
echo "应用服务器: ${APP_USER}@${APP_SERVER}"
echo "Neo4j服务器: ${NEO4J_SERVER}:${NEO4J_PORT}"
echo ""

# 检查1: 环境变量配置
echo "[1/4] 检查环境变量配置..."
ssh -i ${KEY_FILE} -o StrictHostKeyChecking=no ${APP_USER}@${APP_SERVER} << 'EOF'
cd /opt/enterprise-ai-platform 2>/dev/null || cd /root/enterprise-ai-platform 2>/dev/null || { echo "项目目录未找到"; exit 1; }

if [ -f .env ]; then
    echo "=== .env文件中的Neo4j配置 ==="
    grep -i neo4j .env 2>/dev/null || echo "❌ 未找到Neo4j配置"
    echo ""
    
    # 检查是否已配置
    if grep -q "NEO4J_URI" .env 2>/dev/null; then
        echo "✅ 已配置NEO4J_URI"
        grep "NEO4J_URI" .env
    else
        echo "❌ 未配置NEO4J_URI"
    fi
    
    if grep -q "NEO4J_USER" .env 2>/dev/null; then
        echo "✅ 已配置NEO4J_USER"
        grep "NEO4J_USER" .env
    else
        echo "❌ 未配置NEO4J_USER"
    fi
    
    if grep -q "NEO4J_PASSWORD" .env 2>/dev/null; then
        echo "✅ 已配置NEO4J_PASSWORD"
        grep "NEO4J_PASSWORD" .env | sed 's/PASSWORD=.*/PASSWORD=***/'
    else
        echo "❌ 未配置NEO4J_PASSWORD"
    fi
else
    echo "❌ .env文件不存在"
fi
EOF

# 检查2: Docker Compose配置
echo ""
echo "[2/4] 检查Docker Compose配置..."
ssh -i ${KEY_FILE} -o StrictHostKeyChecking=no ${APP_USER}@${APP_SERVER} << 'EOF'
cd /opt/enterprise-ai-platform 2>/dev/null || cd /root/enterprise-ai-platform 2>/dev/null || exit 1

if [ -f docker-compose.yml ]; then
    echo "=== Docker Compose中的Neo4j环境变量 ==="
    docker-compose config 2>/dev/null | grep -i "NEO4J" || echo "未找到Neo4j环境变量"
    
    echo ""
    echo "=== 服务中的Neo4j配置 ==="
    docker-compose config 2>/dev/null | grep -A 10 -B 5 -i "neo4j" || echo "未找到Neo4j服务配置"
else
    echo "❌ docker-compose.yml文件不存在"
fi
EOF

# 检查3: 网络连接测试
echo ""
echo "[3/4] 测试到Neo4j服务器的网络连接..."
ssh -i ${KEY_FILE} -o StrictHostKeyChecking=no ${APP_USER}@${APP_SERVER} << EOF
if timeout 5 bash -c "cat < /dev/null > /dev/tcp/${NEO4J_SERVER}/${NEO4J_PORT}" 2>/dev/null; then
    echo "✅ 网络连接成功: ${NEO4J_SERVER}:${NEO4J_PORT}"
else
    echo "❌ 网络连接失败: ${NEO4J_SERVER}:${NEO4J_PORT}"
    echo "   请检查防火墙和安全组设置"
fi
EOF

# 检查4: Python测试连接（如果可能）
echo ""
echo "[4/4] 测试Neo4j数据库连接..."
ssh -i ${KEY_FILE} -o StrictHostKeyChecking=no ${APP_USER}@${APP_SERVER} << EOF
python3 << 'PYTHON_EOF'
import sys
try:
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(
        'bolt://${NEO4J_SERVER}:${NEO4J_PORT}',
        auth=('neo4j', 'Neo4j@2024')
    )
    with driver.session() as session:
        result = session.run('RETURN 1 AS test')
        record = result.single()
        print(f"✅ Neo4j连接成功: {record['test']}")
    driver.close()
except ImportError:
    print("⚠️  neo4j库未安装，跳过连接测试")
except Exception as e:
    print(f"❌ Neo4j连接失败: {e}")
PYTHON_EOF
EOF

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="



