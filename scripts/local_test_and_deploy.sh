#!/bin/bash
# 本地测试和部署流程脚本
# 1. 在本地Docker中测试
# 2. 测试通过后部署到服务器

set -e  # 遇到错误立即退出

echo "=========================================="
echo "数据库架构优化 - 本地测试和部署流程"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 步骤1: 检查环境
echo -e "${BLUE}步骤1: 检查环境${NC}"
echo ""

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker已安装${NC}"

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose已安装${NC}"

# 检查Python
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: Python未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python已安装${NC}"

echo ""

# 步骤2: 安装依赖
echo -e "${BLUE}步骤2: 安装Python依赖${NC}"
echo ""

pip install neo4j==5.14.0 qdrant-client || {
    echo -e "${RED}依赖安装失败${NC}"
    exit 1
}
echo -e "${GREEN}✅ 依赖安装完成${NC}"
echo ""

# 步骤3: 启动Neo4j服务
echo -e "${BLUE}步骤3: 启动Neo4j服务${NC}"
echo ""

echo "启动Neo4j容器..."
docker-compose up -d neo4j

echo "等待Neo4j启动（30秒）..."
sleep 30

echo "检查Neo4j状态..."
docker-compose ps neo4j

# 检查Neo4j健康状态
echo "检查Neo4j健康状态..."
for i in {1..10}; do
    if docker-compose exec -T neo4j cypher-shell -u neo4j -p neo4j_password "RETURN 1" &> /dev/null; then
        echo -e "${GREEN}✅ Neo4j服务正常${NC}"
        break
    else
        if [ $i -eq 10 ]; then
            echo -e "${RED}❌ Neo4j服务启动失败${NC}"
            docker-compose logs neo4j
            exit 1
        fi
        echo "等待Neo4j启动... ($i/10)"
        sleep 5
    fi
done

echo ""

# 步骤4: 运行数据迁移
echo -e "${BLUE}步骤4: 运行数据迁移${NC}"
echo ""

read -p "是否运行数据迁移? (yes/no): " run_migration

if [ "$run_migration" = "yes" ]; then
    echo "运行知识图谱数据迁移..."
    python scripts/migrate_data_to_neo4j.py || {
        echo -e "${RED}知识图谱数据迁移失败${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ 知识图谱数据迁移完成${NC}"
    
    echo ""
    echo "运行向量数据迁移..."
    python scripts/migrate_vectors_to_qdrant.py --qdrant-url http://localhost:6333 || {
        echo -e "${RED}向量数据迁移失败${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ 向量数据迁移完成${NC}"
else
    echo -e "${YELLOW}跳过数据迁移${NC}"
fi

echo ""

# 步骤5: 运行测试
echo -e "${BLUE}步骤5: 运行迁移测试${NC}"
echo ""

python scripts/test_database_migration.py
TEST_RESULT=$?

if [ $TEST_RESULT -ne 0 ]; then
    echo -e "${RED}❌ 测试失败，请检查上述错误${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 所有测试通过！${NC}"
echo ""

# 步骤6: 部署到服务器
echo -e "${BLUE}步骤6: 部署到服务器${NC}"
echo ""

read -p "测试通过，是否部署到服务器? (yes/no): " deploy_to_server

if [ "$deploy_to_server" = "yes" ]; then
    if [ -z "$SERVER_HOST" ]; then
        read -p "请输入服务器地址: " SERVER_HOST
        export SERVER_HOST
    fi
    
    if [ -f "scripts/deploy_to_server.sh" ]; then
        chmod +x scripts/deploy_to_server.sh
        ./scripts/deploy_to_server.sh
    else
        echo -e "${YELLOW}部署脚本不存在，请手动部署${NC}"
        echo "部署步骤:"
        echo "1. 上传 docker-compose.yml 到服务器"
        echo "2. 上传迁移脚本到服务器"
        echo "3. 在服务器上运行: docker-compose up -d neo4j"
        echo "4. 在服务器上运行迁移脚本"
    fi
else
    echo -e "${YELLOW}跳过服务器部署${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}本地测试完成${NC}"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 检查Neo4j Browser: http://localhost:7474"
echo "2. 检查服务状态: docker-compose ps"
echo "3. 查看日志: docker-compose logs neo4j"
echo ""



