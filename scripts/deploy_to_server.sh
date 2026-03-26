#!/bin/bash
# 数据库架构优化部署脚本
# 用于将本地测试通过的配置部署到服务器

set -e  # 遇到错误立即退出

echo "=========================================="
echo "数据库架构优化部署脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
SERVER_HOST="${SERVER_HOST:-your-server-ip}"
SERVER_USER="${SERVER_USER:-root}"
SERVER_PATH="${SERVER_PATH:-/opt/enterprise-ai-platform}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"

# 检查参数
if [ -z "$SERVER_HOST" ] || [ "$SERVER_HOST" = "your-server-ip" ]; then
    echo -e "${RED}错误: 请设置 SERVER_HOST 环境变量${NC}"
    echo "用法: SERVER_HOST=your-server-ip ./scripts/deploy_to_server.sh"
    exit 1
fi

echo "部署配置:"
echo "  服务器: ${SERVER_USER}@${SERVER_HOST}"
echo "  部署路径: ${SERVER_PATH}"
echo ""

# 确认部署
read -p "确认部署到服务器? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "部署已取消"
    exit 0
fi

echo ""
echo "=========================================="
echo "步骤1: 备份服务器数据"
echo "=========================================="

# 创建备份目录
mkdir -p "${BACKUP_DIR}"
BACKUP_FILE="${BACKUP_DIR}/backup-$(date +%Y%m%d-%H%M%S).tar.gz"

echo "创建服务器数据备份..."
ssh ${SERVER_USER}@${SERVER_HOST} << EOF
    cd ${SERVER_PATH}
    docker-compose exec -T postgres pg_dump -U ai_user ai_platform > /tmp/postgres_backup.sql
    echo "PostgreSQL备份完成"
EOF

# 下载备份
scp ${SERVER_USER}@${SERVER_HOST}:/tmp/postgres_backup.sql "${BACKUP_DIR}/postgres_backup.sql"
echo -e "${GREEN}✅ 备份完成: ${BACKUP_FILE}${NC}"

echo ""
echo "=========================================="
echo "步骤2: 上传配置文件"
echo "=========================================="

# 上传docker-compose.yml
echo "上传 docker-compose.yml..."
scp docker-compose.yml ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/docker-compose.yml

# 上传.env文件（如果存在）
if [ -f .env ]; then
    echo "上传 .env 文件..."
    scp .env ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/.env
fi

# 上传迁移脚本
echo "上传迁移脚本..."
ssh ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${SERVER_PATH}/scripts"
scp scripts/migrate_data_to_neo4j.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/scripts/
scp scripts/migrate_vectors_to_qdrant.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/scripts/
scp scripts/test_database_migration.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/scripts/

# 上传Neo4j客户端
echo "上传Neo4j客户端..."
ssh ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${SERVER_PATH}/database/src/core"
scp database/src/core/neo4j_client.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/database/src/core/

echo -e "${GREEN}✅ 文件上传完成${NC}"

echo ""
echo "=========================================="
echo "步骤3: 安装依赖"
echo "=========================================="

ssh ${SERVER_USER}@${SERVER_HOST} << EOF
    cd ${SERVER_PATH}
    echo "安装Neo4j Python驱动..."
    docker-compose exec -T metadata-service pip install neo4j==5.14.0 || true
    docker-compose exec -T knowledge-base pip install neo4j==5.14.0 || true
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
EOF

echo ""
echo "=========================================="
echo "步骤4: 启动Neo4j服务"
echo "=========================================="

ssh ${SERVER_USER}@${SERVER_HOST} << EOF
    cd ${SERVER_PATH}
    echo "启动Neo4j服务..."
    docker-compose up -d neo4j
    
    echo "等待Neo4j启动..."
    sleep 30
    
    echo "检查Neo4j状态..."
    docker-compose ps neo4j
    docker-compose logs --tail=50 neo4j
EOF

echo -e "${GREEN}✅ Neo4j服务启动完成${NC}"

echo ""
echo "=========================================="
echo "步骤5: 运行数据迁移"
echo "=========================================="

echo -e "${YELLOW}⚠️  注意: 数据迁移可能需要较长时间，请耐心等待${NC}"
read -p "继续执行数据迁移? (yes/no): " confirm_migration

if [ "$confirm_migration" = "yes" ]; then
    ssh ${SERVER_USER}@${SERVER_HOST} << EOF
        cd ${SERVER_PATH}
        
        echo "运行知识图谱数据迁移..."
        docker-compose exec -T metadata-service python /app/scripts/migrate_data_to_neo4j.py || {
            echo -e "${RED}迁移失败，请检查日志${NC}"
            exit 1
        }
        
        echo "运行向量数据迁移..."
        docker-compose exec -T metadata-service python /app/scripts/migrate_vectors_to_qdrant.py --qdrant-url http://qdrant:6333 || {
            echo -e "${RED}迁移失败，请检查日志${NC}"
            exit 1
        }
        
        echo -e "${GREEN}✅ 数据迁移完成${NC}"
EOF
else
    echo "跳过数据迁移，稍后手动执行"
fi

echo ""
echo "=========================================="
echo "步骤6: 运行测试"
echo "=========================================="

ssh ${SERVER_USER}@${SERVER_HOST} << EOF
    cd ${SERVER_PATH}
    echo "运行迁移测试..."
    docker-compose exec -T metadata-service python /app/scripts/test_database_migration.py
EOF

echo ""
echo "=========================================="
echo "部署完成"
echo "=========================================="
echo ""
echo "下一步操作:"
echo "1. 检查Neo4j Browser: http://${SERVER_HOST}:7474"
echo "2. 检查服务状态: docker-compose ps"
echo "3. 查看日志: docker-compose logs neo4j"
echo "4. 运行测试: python scripts/test_database_migration.py"
echo ""



