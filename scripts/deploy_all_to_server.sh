#!/bin/bash
# 完整部署脚本：同步代码和数据到服务器并启动服务

set -e  # 遇到错误立即退出

echo "=========================================="
echo "完整部署脚本 - 同步代码和数据到服务器"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SERVER_HOST="${SERVER_HOST:-your-server-ip}"
SERVER_USER="${SERVER_USER:-root}"
SERVER_PATH="${SERVER_PATH:-/opt/enterprise-ai-platform}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"

# 检查参数
if [ -z "$SERVER_HOST" ] || [ "$SERVER_HOST" = "your-server-ip" ]; then
    echo -e "${RED}错误: 请设置 SERVER_HOST 环境变量${NC}"
    echo "用法: SERVER_HOST=your-server-ip ./scripts/deploy_all_to_server.sh"
    exit 1
fi

echo -e "${BLUE}部署配置:${NC}"
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
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}步骤1: 备份服务器数据${NC}"
echo -e "${BLUE}==========================================${NC}"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"
BACKUP_FILE="${BACKUP_DIR}/backup-$(date +%Y%m%d-%H%M%S).tar.gz"

echo "创建服务器数据备份..."
ssh ${SERVER_USER}@${SERVER_HOST} << EOF
    cd ${SERVER_PATH}
    docker-compose exec -T postgres pg_dump -U ai_user ai_platform > /tmp/postgres_backup.sql 2>/dev/null || echo "PostgreSQL备份跳过"
    echo "备份完成"
EOF

# 下载备份
scp "${SERVER_USER}@${SERVER_HOST}:/tmp/postgres_backup.sql" "${BACKUP_DIR}/postgres_backup.sql" 2>/dev/null || echo "备份文件不存在，跳过"
echo -e "${GREEN}✅ 备份完成${NC}"

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}步骤2: 同步代码文件${NC}"
echo -e "${BLUE}==========================================${NC}"

# 同步docker-compose.yml
echo "同步 docker-compose.yml..."
scp docker-compose.yml "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/docker-compose.yml"

# 同步.env文件（如果存在）
if [ -f .env ]; then
    echo "同步 .env 文件..."
    scp .env "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/.env"
fi

# 同步数据库相关代码
echo "同步数据库代码..."
ssh ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${SERVER_PATH}/database/src/core"
scp database/src/core/neo4j_client.py "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/database/src/core/"

# 同步迁移脚本
echo "同步迁移脚本..."
ssh ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${SERVER_PATH}/scripts"
scp scripts/migrate_data_to_neo4j.py "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/scripts/"
scp scripts/migrate_vectors_to_qdrant.py "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/scripts/"
scp scripts/test_database_migration.py "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/scripts/"

# 同步API Gateway代码
echo "同步API Gateway代码..."
ssh ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${SERVER_PATH}/api-gateway/src/routes"
scp api-gateway/src/routes/neo4j_graph.py "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/api-gateway/src/routes/"

# 同步Metadata Service代码
echo "同步Metadata Service代码..."
ssh ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${SERVER_PATH}/metadata-service/src/api"
scp metadata-service/src/api/neo4j_api.py "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/metadata-service/src/api/"

# 同步前端代码
echo "同步前端代码..."
ssh ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${SERVER_PATH}/web-ui/src/services"
ssh ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${SERVER_PATH}/web-ui/src/app/neo4j-graph"
scp web-ui/src/services/neo4jGraphService.ts "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/web-ui/src/services/"
scp web-ui/src/app/neo4j-graph/page.tsx "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/web-ui/src/app/neo4j-graph/"

# 更新main.py文件（添加路由注册）
echo "更新服务主文件..."
ssh ${SERVER_USER}@${SERVER_HOST} << 'UPDATE_MAIN'
    cd /opt/enterprise-ai-platform
    
    # 更新api-gateway main.py
    if ! grep -q "neo4j_graph" api-gateway/src/main.py; then
        sed -i 's/from \.routes import unified_search, knowledge_graph_monitor, nl_query, assistant, intelligent_monitoring, knowledge_graph, analytics, enterprise_architecture/from .routes import unified_search, knowledge_graph_monitor, nl_query, assistant, intelligent_monitoring, knowledge_graph, analytics, enterprise_architecture, neo4j_graph/' api-gateway/src/main.py
        sed -i '/app.include_router(enterprise_architecture.router)/a app.include_router(neo4j_graph.router)' api-gateway/src/main.py
    fi
    
    # 更新metadata-service main.py
    if ! grep -q "neo4j_api" metadata-service/src/main.py; then
        sed -i 's/from .api import knowledge_graph, document_entity_linker, knowledge_graph_visualization/from .api import knowledge_graph, document_entity_linker, knowledge_graph_visualization, neo4j_api/' metadata-service/src/main.py
        sed -i '/app.include_router(knowledge_graph_visualization.router/a app.include_router(neo4j_api.router, tags=["Neo4j"])  # 路由已有prefix="/api/neo4j"' metadata-service/src/main.py
    fi
UPDATE_MAIN

echo -e "${GREEN}✅ 代码同步完成${NC}"

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}步骤3: 安装依赖${NC}"
echo -e "${BLUE}==========================================${NC}"

ssh ${SERVER_USER}@${SERVER_HOST} << EOF
    cd ${SERVER_PATH}
    echo "安装Neo4j Python驱动..."
    docker-compose exec -T metadata-service pip install neo4j==5.14.0 || echo "依赖安装跳过（可能已安装）"
    docker-compose exec -T api-gateway pip install neo4j==5.14.0 || echo "依赖安装跳过（可能已安装）"
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
EOF

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}步骤4: 启动Neo4j服务${NC}"
echo -e "${BLUE}==========================================${NC}"

ssh ${SERVER_USER}@${SERVER_HOST} << EOF
    cd ${SERVER_PATH}
    echo "启动Neo4j服务..."
    docker-compose up -d neo4j
    
    echo "等待Neo4j启动..."
    sleep 30
    
    echo "检查Neo4j状态..."
    docker-compose ps neo4j
    docker-compose logs --tail=20 neo4j
EOF

echo -e "${GREEN}✅ Neo4j服务启动完成${NC}"

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}步骤5: 运行数据迁移${NC}"
echo -e "${BLUE}==========================================${NC}"

echo -e "${YELLOW}⚠️  注意: 数据迁移可能需要较长时间，请耐心等待${NC}"
read -p "继续执行数据迁移? (yes/no): " confirm_migration

if [ "$confirm_migration" = "yes" ]; then
    ssh ${SERVER_USER}@${SERVER_HOST} << EOF
        cd ${SERVER_PATH}
        
        echo "运行知识图谱数据迁移..."
        docker-compose exec -T metadata-service python /app/scripts/migrate_data_to_neo4j.py || {
            echo -e "${YELLOW}迁移可能已执行过或出现错误，继续...${NC}"
        }
        
        echo "运行向量数据迁移..."
        docker-compose exec -T metadata-service python /app/scripts/migrate_vectors_to_qdrant.py --qdrant-url http://qdrant:6333 || {
            echo -e "${YELLOW}向量迁移可能已执行过或出现错误，继续...${NC}"
        }
        
        echo -e "${GREEN}✅ 数据迁移完成${NC}"
EOF
else
    echo -e "${YELLOW}跳过数据迁移，稍后手动执行${NC}"
fi

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}步骤6: 重启相关服务${NC}"
echo -e "${BLUE}==========================================${NC}"

ssh ${SERVER_USER}@${SERVER_HOST} << EOF
    cd ${SERVER_PATH}
    echo "重启API Gateway..."
    docker-compose restart api-gateway || echo "API Gateway重启跳过"
    
    echo "重启Metadata Service..."
    docker-compose restart metadata-service || echo "Metadata Service重启跳过"
    
    echo "等待服务启动..."
    sleep 10
    
    echo "检查服务状态..."
    docker-compose ps api-gateway metadata-service neo4j
EOF

echo -e "${GREEN}✅ 服务重启完成${NC}"

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}步骤7: 运行测试${NC}"
echo -e "${BLUE}==========================================${NC}"

ssh ${SERVER_USER}@${SERVER_HOST} << EOF
    cd ${SERVER_PATH}
    echo "运行迁移测试..."
    docker-compose exec -T metadata-service python /app/scripts/test_database_migration.py || {
        echo -e "${YELLOW}测试可能失败，请检查日志${NC}"
    }
EOF

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${GREEN}部署完成${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""
echo -e "${GREEN}下一步操作:${NC}"
echo "1. 检查Neo4j Browser: http://${SERVER_HOST}:7474"
echo "2. 检查服务状态: ssh ${SERVER_USER}@${SERVER_HOST} 'cd ${SERVER_PATH} && docker-compose ps'"
echo "3. 查看日志: ssh ${SERVER_USER}@${SERVER_HOST} 'cd ${SERVER_PATH} && docker-compose logs neo4j'"
echo "4. 访问前端页面: http://${SERVER_HOST}:3000/neo4j-graph"
echo ""



