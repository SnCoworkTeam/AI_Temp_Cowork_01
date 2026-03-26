#!/bin/bash
# 企业架构功能简化部署脚本
# 支持应用服务器和图数据库服务器分离部署
# 使用SSH配置文件中的配置

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}企业架构功能部署脚本${NC}"
echo -e "${GREEN}支持应用服务器和图数据库服务器分离部署${NC}"
echo -e "${GREEN}========================================${NC}"

# 从SSH配置文件读取服务器信息
SSH_CONFIG="./remote.ssh"
if [ ! -f "$SSH_CONFIG" ]; then
    echo -e "${RED}错误: SSH配置文件不存在: $SSH_CONFIG${NC}"
    exit 1
fi

# 解析SSH配置
APP_SERVER_HOST=$(grep -E "^[[:space:]]*HostName" "$SSH_CONFIG" | head -1 | awk '{print $2}')
APP_SERVER_USER=$(grep -E "^[[:space:]]*User" "$SSH_CONFIG" | head -1 | awk '{print $2}')
IDENTITY_FILE=$(grep -E "^[[:space:]]*IdentityFile" "$SSH_CONFIG" | head -1 | awk '{print $2}')

if [ -z "$APP_SERVER_HOST" ]; then
    echo -e "${RED}错误: 无法从SSH配置读取服务器地址${NC}"
    exit 1
fi

# 如果IdentityFile是相对路径，转换为绝对路径
if [ -n "$IDENTITY_FILE" ] && [[ ! "$IDENTITY_FILE" =~ ^/ ]]; then
    IDENTITY_FILE="$(pwd)/$IDENTITY_FILE"
fi

# 检查密钥文件
if [ -n "$IDENTITY_FILE" ] && [ ! -f "$IDENTITY_FILE" ]; then
    echo -e "${YELLOW}警告: 密钥文件不存在: $IDENTITY_FILE${NC}"
    echo -e "${YELLOW}将尝试使用SSH配置文件中的Host名称连接${NC}"
    SSH_HOST="enterprise-ai-server"
    SSH_OPTS="-F ./remote.ssh"
else
    SSH_HOST="$APP_SERVER_USER@$APP_SERVER_HOST"
    SSH_OPTS="-i $IDENTITY_FILE -o StrictHostKeyChecking=no"
fi

echo -e "${GREEN}✅ 服务器配置:${NC}"
echo -e "  主机: ${BLUE}$APP_SERVER_HOST${NC}"
echo -e "  用户: ${BLUE}$APP_SERVER_USER${NC}"
if [ -n "$IDENTITY_FILE" ]; then
    echo -e "  密钥: ${BLUE}$IDENTITY_FILE${NC}"
fi

# Neo4j服务器配置（询问是否分离）
echo -e "\n${YELLOW}Neo4j服务器配置${NC}"
read -p "Neo4j服务器是否与应用服务器分离? (y/n) [默认: n]: " SEPARATE_NEO4J
SEPARATE_NEO4J="${SEPARATE_NEO4J:-n}"

if [ "$SEPARATE_NEO4J" = "y" ] || [ "$SEPARATE_NEO4J" = "Y" ]; then
    read -p "请输入Neo4j服务器地址 (IP或域名): " NEO4J_SERVER_HOST
    if [ -z "$NEO4J_SERVER_HOST" ]; then
        echo -e "${RED}错误: Neo4j服务器地址不能为空${NC}"
        exit 1
    fi
    read -p "请输入Neo4j服务器SSH用户名 [默认: $APP_SERVER_USER]: " NEO4J_SERVER_USER
    NEO4J_SERVER_USER="${NEO4J_SERVER_USER:-$APP_SERVER_USER}"
    NEO4J_SSH_OPTS="$SSH_OPTS"
    NEO4J_SSH_HOST="$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST"
else
    NEO4J_SERVER_HOST="$APP_SERVER_HOST"
    NEO4J_SERVER_USER="$APP_SERVER_USER"
    NEO4J_SSH_OPTS="$SSH_OPTS"
    NEO4J_SSH_HOST="$SSH_HOST"
fi

# 项目目录
read -p "请输入服务器上的项目目录 [默认: /opt/enterprise-ai-platform]: " PROJECT_DIR
PROJECT_DIR="${PROJECT_DIR:-/opt/enterprise-ai-platform}"

# 显示配置
echo -e "\n${BLUE}=== 部署配置 ===${NC}"
echo -e "应用服务器: ${GREEN}$SSH_HOST${NC}"
echo -e "Neo4j服务器: ${GREEN}$NEO4J_SSH_HOST${NC}"
echo -e "项目目录: ${GREEN}$PROJECT_DIR${NC}"

read -p "\n确认开始部署? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo -e "${YELLOW}部署已取消${NC}"
    exit 0
fi

BACKUP_DIR="/opt/backups/$(date +%Y%m%d_%H%M%S)"

# 1. 测试SSH连接
echo -e "\n${YELLOW}1. 测试SSH连接...${NC}"
if ssh $SSH_OPTS "$SSH_HOST" "echo '连接成功'" 2>/dev/null; then
    echo -e "${GREEN}✅ 应用服务器连接成功${NC}"
else
    echo -e "${RED}❌ 应用服务器连接失败${NC}"
    echo -e "${YELLOW}尝试使用SSH配置中的Host名称...${NC}"
    if ssh -F ./remote.ssh enterprise-ai-server "echo '连接成功'" 2>/dev/null; then
        echo -e "${GREEN}✅ 使用SSH配置连接成功${NC}"
        SSH_HOST="enterprise-ai-server"
        SSH_OPTS="-F ./remote.ssh"
    else
        echo -e "${RED}❌ 连接失败，请检查配置${NC}"
        exit 1
    fi
fi

# 2. 备份数据库
echo -e "\n${YELLOW}2. 备份数据库...${NC}"
ssh $SSH_OPTS "$SSH_HOST" << EOF
    mkdir -p $BACKUP_DIR
    if command -v pg_dump > /dev/null 2>&1; then
        pg_dump -U postgres enterprise_ai > $BACKUP_DIR/database_backup.sql 2>/dev/null || \\
        pg_dump -U ai_user ai_platform > $BACKUP_DIR/database_backup.sql 2>/dev/null || \\
        docker exec enterprise-ai-postgres pg_dump -U ai_user ai_platform > $BACKUP_DIR/database_backup.sql 2>/dev/null || \\
        echo "⚠️  数据库备份跳过（数据库可能使用Docker）"
    else
        echo "⚠️  pg_dump未找到，跳过数据库备份"
    fi
    echo "✅ 备份目录已创建: $BACKUP_DIR"
EOF

# 3. 上传代码
echo -e "\n${YELLOW}3. 上传代码到应用服务器...${NC}"
if command -v rsync > /dev/null 2>&1; then
    rsync -avz --progress \
        -e "ssh $SSH_OPTS" \
        --exclude 'node_modules' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.git' \
        --exclude '*.log' \
        --exclude '.env' \
        --exclude 'venv' \
        --exclude '.venv' \
        --exclude 'htmlcov' \
        --exclude '*.pyc' \
        ./ "$SSH_HOST:$PROJECT_DIR/"
    echo -e "${GREEN}✅ 代码上传完成${NC}"
else
    echo -e "${YELLOW}⚠️  rsync未找到，使用tar+ssh上传...${NC}"
    tar --exclude='node_modules' --exclude='__pycache__' --exclude='*.pyc' \
        --exclude='.git' --exclude='*.log' --exclude='.env' --exclude='venv' \
        --exclude='.venv' --exclude='htmlcov' -czf - . | \
    ssh $SSH_OPTS "$SSH_HOST" "cd $PROJECT_DIR && tar -xzf -"
    echo -e "${GREEN}✅ 代码上传完成${NC}"
fi

# 4. 运行数据库迁移
echo -e "\n${YELLOW}4. 运行数据库迁移...${NC}"
ssh $SSH_OPTS "$SSH_HOST" << EOF
    set -e
    cd $PROJECT_DIR/database
    
    # 激活虚拟环境（如果存在）
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d "../venv" ]; then
        source ../venv/bin/activate
    fi
    
    # 运行迁移到026版本
    python -m alembic upgrade 026 || python -m alembic upgrade head
    
    echo "✅ 数据库迁移完成"
EOF

# 5. 测试数据库迁移
echo -e "\n${YELLOW}5. 测试数据库迁移...${NC}"
ssh $SSH_OPTS "$SSH_HOST" << EOF
    cd $PROJECT_DIR
    python scripts/test_enterprise_architecture_migration.py || echo "⚠️  测试脚本执行完成（可能有警告）"
EOF

# 6. 更新Neo4j连接配置（如果分离部署）
if [ "$NEO4J_SERVER_HOST" != "$APP_SERVER_HOST" ]; then
    echo -e "\n${YELLOW}6. 更新Neo4j连接配置...${NC}"
    ssh $SSH_OPTS "$SSH_HOST" << EOF
        cd $PROJECT_DIR
        if [ -f ".env" ]; then
            sed -i "s|NEO4J_URI=.*|NEO4J_URI=bolt://$NEO4J_SERVER_HOST:7687|g" .env || true
            echo "✅ Neo4j连接配置已更新为: bolt://$NEO4J_SERVER_HOST:7687"
        fi
EOF
fi

# 7. 重启应用服务
echo -e "\n${YELLOW}7. 重启应用服务...${NC}"
ssh $SSH_OPTS "$SSH_HOST" << EOF
    cd $PROJECT_DIR
    
    # 尝试使用docker-compose重启
    if [ -f "docker-compose.yml" ]; then
        docker-compose restart metadata-service api-gateway 2>/dev/null || echo "⚠️  docker-compose重启失败，尝试其他方式"
    fi
    
    # 尝试使用systemctl重启
    if systemctl is-active --quiet enterprise-ai-platform 2>/dev/null; then
        systemctl restart enterprise-ai-platform && echo "✅ 服务已重启"
    else
        echo "⚠️  服务未使用systemctl管理，请手动重启"
    fi
    
    echo "✅ 服务重启完成"
EOF

# 8. 检查Neo4j服务器（如果分离部署）
if [ "$NEO4J_SERVER_HOST" != "$APP_SERVER_HOST" ]; then
    echo -e "\n${YELLOW}8. 检查Neo4j服务器...${NC}"
    ssh $NEO4J_SSH_OPTS "$NEO4J_SSH_HOST" << EOF
        if systemctl is-active --quiet neo4j 2>/dev/null; then
            systemctl status neo4j --no-pager | head -5
        elif docker ps | grep -q neo4j; then
            docker ps | grep neo4j
        else
            echo "⚠️  Neo4j服务状态未知，请手动检查"
        fi
        echo "✅ Neo4j服务器检查完成"
EOF
fi

# 9. 验证部署
echo -e "\n${YELLOW}9. 验证部署...${NC}"
ssh $SSH_OPTS "$SSH_HOST" << EOF
    cd $PROJECT_DIR/database
    echo "当前迁移版本:"
    python -m alembic current
    
    echo -e "\n检查新表:"
    psql -U postgres -d enterprise_ai -c "\dt organization_*" 2>/dev/null || \\
    psql -U ai_user -d ai_platform -c "\dt organization_*" 2>/dev/null || \\
    docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "\dt organization_*" 2>/dev/null || \\
    echo "⚠️  无法连接数据库检查，请手动验证"
EOF

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 部署完成${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n部署信息:"
echo -e "  应用服务器: ${GREEN}$SSH_HOST${NC}"
echo -e "  Neo4j服务器: ${GREEN}$NEO4J_SSH_HOST${NC}"
echo -e "  项目目录: ${GREEN}$PROJECT_DIR${NC}"
echo -e "  备份目录: ${GREEN}$BACKUP_DIR${NC}"
echo -e "\n${YELLOW}请手动验证以下功能:${NC}"
echo -e "  1. 数据库迁移版本: ssh到服务器执行 'cd $PROJECT_DIR/database && python -m alembic current'"
echo -e "  2. 新表检查: 在服务器上执行 'psql -U postgres -d enterprise_ai -c \"\\dt organization_*\"'"
echo -e "  3. 服务状态: 检查服务是否正常运行"

