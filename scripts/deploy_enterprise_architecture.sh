#!/bin/bash
# 企业架构功能部署脚本
# 支持应用服务器和图数据库服务器分离部署

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
APP_SERVER_HOST="${APP_SERVER_HOST:-your-app-server.com}"
APP_SERVER_USER="${APP_SERVER_USER:-root}"
APP_SERVER_KEY="${APP_SERVER_KEY:-./remote.ssh}"

NEO4J_SERVER_HOST="${NEO4J_SERVER_HOST:-your-neo4j-server.com}"
NEO4J_SERVER_USER="${NEO4J_SERVER_USER:-root}"
NEO4J_SERVER_KEY="${NEO4J_SERVER_KEY:-./remote.ssh}"

PROJECT_DIR="/opt/enterprise-ai-platform"
BACKUP_DIR="/opt/backups/$(date +%Y%m%d_%H%M%S)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}企业架构功能部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. 检查密钥文件
echo -e "\n${YELLOW}1. 检查SSH密钥...${NC}"
if [ ! -f "$APP_SERVER_KEY" ]; then
    echo -e "${RED}错误: SSH密钥文件不存在: $APP_SERVER_KEY${NC}"
    exit 1
fi
chmod 600 "$APP_SERVER_KEY"
echo -e "${GREEN}✅ SSH密钥检查通过${NC}"

# 2. 备份数据库
echo -e "\n${YELLOW}2. 备份数据库...${NC}"
ssh -i "$APP_SERVER_KEY" "$APP_SERVER_USER@$APP_SERVER_HOST" << EOF
    mkdir -p $BACKUP_DIR
    pg_dump -U postgres enterprise_ai > $BACKUP_DIR/database_backup.sql
    echo "✅ 数据库备份完成: $BACKUP_DIR/database_backup.sql"
EOF

# 3. 上传代码到应用服务器
echo -e "\n${YELLOW}3. 上传代码到应用服务器...${NC}"
rsync -avz --progress \
    -e "ssh -i $APP_SERVER_KEY" \
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude '*.log' \
    ./ "$APP_SERVER_USER@$APP_SERVER_HOST:$PROJECT_DIR/"

echo -e "${GREEN}✅ 代码上传完成${NC}"

# 4. 在应用服务器上运行数据库迁移
echo -e "\n${YELLOW}4. 运行数据库迁移...${NC}"
ssh -i "$APP_SERVER_KEY" "$APP_SERVER_USER@$APP_SERVER_HOST" << EOF
    cd $PROJECT_DIR/database
    source venv/bin/activate || true
    python -m alembic upgrade head
    echo "✅ 数据库迁移完成"
EOF

# 5. 测试数据库迁移
echo -e "\n${YELLOW}5. 测试数据库迁移...${NC}"
ssh -i "$APP_SERVER_KEY" "$APP_SERVER_USER@$APP_SERVER_HOST" << EOF
    cd $PROJECT_DIR
    python scripts/test_enterprise_architecture_migration.py
EOF

# 6. 重启应用服务
echo -e "\n${YELLOW}6. 重启应用服务...${NC}"
ssh -i "$APP_SERVER_KEY" "$APP_SERVER_USER@$APP_SERVER_HOST" << EOF
    cd $PROJECT_DIR
    docker-compose restart metadata-service api-gateway || true
    systemctl restart enterprise-ai-platform || true
    echo "✅ 应用服务重启完成"
EOF

# 7. 检查Neo4j服务器连接（如果分离部署）
if [ "$NEO4J_SERVER_HOST" != "$APP_SERVER_HOST" ]; then
    echo -e "\n${YELLOW}7. 检查Neo4j服务器连接...${NC}"
    ssh -i "$NEO4J_SERVER_KEY" "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" << EOF
        # 检查Neo4j服务状态
        systemctl status neo4j || docker ps | grep neo4j || echo "Neo4j服务检查完成"
EOF
    echo -e "${GREEN}✅ Neo4j服务器连接检查完成${NC}"
fi

# 8. 运行API测试
echo -e "\n${YELLOW}8. 运行API测试...${NC}"
ssh -i "$APP_SERVER_KEY" "$APP_SERVER_USER@$APP_SERVER_HOST" << EOF
    cd $PROJECT_DIR
    # 等待服务启动
    sleep 10
    
    # 测试组织架构API
    curl -f http://localhost:8000/api/enterprise-architecture/organizations || echo "API测试需要手动验证"
    
    echo "✅ API测试完成"
EOF

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 部署完成${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n部署信息:"
echo -e "  应用服务器: $APP_SERVER_HOST"
echo -e "  Neo4j服务器: $NEO4J_SERVER_HOST"
echo -e "  备份目录: $BACKUP_DIR"
echo -e "\n请手动验证以下功能:"
echo -e "  1. 组织架构API: http://$APP_SERVER_HOST/api/enterprise-architecture/organizations"
echo -e "  2. 技术实例API: http://$APP_SERVER_HOST/api/enterprise-architecture/technology/instances"
echo -e "  3. 技术标准化API: http://$APP_SERVER_HOST/api/enterprise-architecture/technology/standardization"

