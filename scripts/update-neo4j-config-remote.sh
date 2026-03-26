#!/bin/bash
# 在应用服务器上更新Neo4j配置

echo "=========================================="
echo "更新Neo4j配置"
echo "=========================================="

# 进入项目目录
cd /opt/enterprise-ai-platform 2>/dev/null || cd /root/enterprise-ai-platform 2>/dev/null || cd ~/enterprise-ai-platform 2>/dev/null || { echo "项目目录未找到"; exit 1; }

echo "当前目录: $(pwd)"
echo ""

# 检查.env文件
if [ ! -f .env ]; then
    echo "❌ .env文件不存在，创建新文件"
    touch .env
fi

# 备份现有配置
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ 已备份.env文件"
fi

# 移除旧的Neo4j配置
if grep -q "^NEO4J_" .env 2>/dev/null; then
    sed -i '/^NEO4J_/d' .env
    echo "✅ 已移除旧Neo4j配置"
fi

# 添加新的Neo4j配置
cat >> .env << 'EOF'
# Neo4j图数据库配置
NEO4J_URI=bolt://43.143.90.179:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=Neo4j@2024
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_ACQUISITION_TIMEOUT=60
NEO4J_CONNECTION_TIMEOUT=30
EOF

echo "✅ 已添加Neo4j配置"
echo ""

# 显示更新后的配置
echo "=== 更新后的Neo4j配置 ==="
grep -i neo4j .env

echo ""
echo "=========================================="
echo "配置更新完成"
echo "=========================================="
echo ""
echo "下一步: 重启相关服务以应用新配置"
echo "  docker-compose restart"



