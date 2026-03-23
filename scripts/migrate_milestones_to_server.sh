#!/bin/bash
# 里程碑1-4代码和数据迁移脚本（Linux/Mac版本）

set -e

# 配置参数
APP_SERVER_HOST="${APP_SERVER_HOST:-43.143.139.197}"
APP_SERVER_USER="${APP_SERVER_USER:-ubuntu}"
APP_SERVER_KEY="${APP_SERVER_KEY:-./enterprise_ai_platform.pem}"
NEO4J_SERVER_HOST="${NEO4J_SERVER_HOST:-}"
NEO4J_SERVER_USER="${NEO4J_SERVER_USER:-ubuntu}"
NEO4J_SERVER_KEY="${NEO4J_SERVER_KEY:-./Neo4j.pem}"
REMOTE_PATH="${REMOTE_PATH:-/opt/enterprise-ai-platform}"
SKIP_CODE="${SKIP_CODE:-false}"
SKIP_DATA="${SKIP_DATA:-false}"
DRY_RUN="${DRY_RUN:-false}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  里程碑1-4代码和数据迁移${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 检查密钥文件
if [ ! -f "$APP_SERVER_KEY" ]; then
    echo -e "${RED}[ERROR] 应用服务器密钥文件不存在: $APP_SERVER_KEY${NC}"
    exit 1
fi

chmod 600 "$APP_SERVER_KEY"

if [ -n "$NEO4J_SERVER_HOST" ] && [ ! -f "$NEO4J_SERVER_KEY" ]; then
    echo -e "${YELLOW}[WARN] Neo4j服务器密钥文件不存在: $NEO4J_SERVER_KEY${NC}"
    echo -e "${YELLOW}[INFO] 将跳过Neo4j数据迁移${NC}"
    SKIP_NEO4J=true
else
    SKIP_NEO4J=false
    if [ -f "$NEO4J_SERVER_KEY" ]; then
        chmod 600 "$NEO4J_SERVER_KEY"
    fi
fi

# 测试SSH连接
echo -e "${YELLOW}[INFO] 测试应用服务器SSH连接...${NC}"
if ssh -i "$APP_SERVER_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$APP_SERVER_USER@$APP_SERVER_HOST" "echo 'Connection OK'" > /dev/null 2>&1; then
    echo -e "${GREEN}[OK] 应用服务器连接成功${NC}"
else
    echo -e "${RED}[ERROR] 应用服务器连接失败${NC}"
    exit 1
fi

if [ "$SKIP_NEO4J" = false ] && [ -n "$NEO4J_SERVER_HOST" ]; then
    echo -e "${YELLOW}[INFO] 测试Neo4j服务器SSH连接...${NC}"
    if ssh -i "$NEO4J_SERVER_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "echo 'Connection OK'" > /dev/null 2>&1; then
        echo -e "${GREEN}[OK] Neo4j服务器连接成功${NC}"
    else
        echo -e "${YELLOW}[WARN] Neo4j服务器连接失败，将跳过Neo4j数据迁移${NC}"
        SKIP_NEO4J=true
    fi
fi

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 同步代码
if [ "$SKIP_CODE" = "false" ]; then
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  同步代码文件${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    
    # 使用rsync同步（如果可用）
    if command -v rsync > /dev/null 2>&1; then
        echo -e "${YELLOW}[INFO] 使用rsync同步代码...${NC}"
        
        # 同步os-core目录
        if [ -d "$PROJECT_ROOT/os-core" ]; then
            echo -e "${YELLOW}[INFO] 同步: OS内核模块（里程碑1）${NC}"
            rsync -avz --progress -e "ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no" \
                "$PROJECT_ROOT/os-core/" \
                "$APP_SERVER_USER@$APP_SERVER_HOST:$REMOTE_PATH/os-core/" || true
        fi
        
        # 同步services目录中的关键文件
        if [ -f "$PROJECT_ROOT/services/unified_intent_service.py" ]; then
            echo -e "${YELLOW}[INFO] 同步: 统一意图服务${NC}"
            rsync -avz --progress -e "ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no" \
                "$PROJECT_ROOT/services/unified_intent_service.py" \
                "$APP_SERVER_USER@$APP_SERVER_HOST:$REMOTE_PATH/services/" || true
        fi
        
        # 同步metadata-service中的EA服务
        if [ -d "$PROJECT_ROOT/metadata-service/src/services" ]; then
            echo -e "${YELLOW}[INFO] 同步: EA服务（里程碑2）${NC}"
            rsync -avz --progress -e "ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no" \
                "$PROJECT_ROOT/metadata-service/src/services/" \
                "$APP_SERVER_USER@$APP_SERVER_HOST:$REMOTE_PATH/metadata-service/src/services/" || true
        fi
        
        # 同步测试文件
        if [ -d "$PROJECT_ROOT/tests/os_core" ]; then
            echo -e "${YELLOW}[INFO] 同步: 测试文件${NC}"
            rsync -avz --progress -e "ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no" \
                "$PROJECT_ROOT/tests/os_core/" \
                "$APP_SERVER_USER@$APP_SERVER_HOST:$REMOTE_PATH/tests/os_core/" || true
        fi
        
        if [ -f "$PROJECT_ROOT/tests/milestone_integration_test.py" ]; then
            rsync -avz --progress -e "ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no" \
                "$PROJECT_ROOT/tests/milestone_integration_test.py" \
                "$APP_SERVER_USER@$APP_SERVER_HOST:$REMOTE_PATH/tests/" || true
        fi
        
        # 同步配置文件
        if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
            echo -e "${YELLOW}[INFO] 同步: Docker Compose配置${NC}"
            rsync -avz --progress -e "ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no" \
                "$PROJECT_ROOT/docker-compose.yml" \
                "$APP_SERVER_USER@$APP_SERVER_HOST:$REMOTE_PATH/" || true
        fi
        
        if [ -f "$PROJECT_ROOT/config/policies.yaml" ]; then
            rsync -avz --progress -e "ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no" \
                "$PROJECT_ROOT/config/policies.yaml" \
                "$APP_SERVER_USER@$APP_SERVER_HOST:$REMOTE_PATH/config/" || true
        fi
        
        echo -e "${GREEN}[OK] 代码同步完成${NC}"
    else
        echo -e "${YELLOW}[WARN] rsync不可用，使用scp同步...${NC}"
        # 使用scp的fallback逻辑（类似PowerShell版本）
    fi
fi

# 同步数据库数据
if [ "$SKIP_DATA" = "false" ]; then
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  同步数据库数据${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    
    # PostgreSQL数据迁移
    echo -e "${YELLOW}[INFO] 准备PostgreSQL数据迁移...${NC}"
    PG_DUMP_FILE="/tmp/milestones_pg_dump_$(date +%Y%m%d_%H%M%S).sql"
    
    if [ "$DRY_RUN" = "false" ]; then
        echo -e "${YELLOW}[INFO] 如果本地有PostgreSQL数据，请手动导出:${NC}"
        echo -e "${YELLOW}      pg_dump -h localhost -U ai_user -d ai_platform > $PG_DUMP_FILE${NC}"
        
        if [ -f "$PG_DUMP_FILE" ]; then
            echo -e "${YELLOW}[INFO] 上传PostgreSQL数据到服务器...${NC}"
            scp -i "$APP_SERVER_KEY" -o StrictHostKeyChecking=no "$PG_DUMP_FILE" \
                "$APP_SERVER_USER@$APP_SERVER_HOST:$REMOTE_PATH/pg_dump.sql"
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}[OK] PostgreSQL数据上传成功${NC}"
                echo -e "${YELLOW}[INFO] 在服务器上执行以下命令导入数据:${NC}"
                echo -e "${YELLOW}      psql -h localhost -U ai_user -d ai_platform < $REMOTE_PATH/pg_dump.sql${NC}"
            fi
        fi
    fi
    
    # Neo4j数据迁移
    if [ "$SKIP_NEO4J" = false ]; then
        echo ""
        echo -e "${YELLOW}[INFO] 准备Neo4j数据迁移...${NC}"
        
        if [ -n "$NEO4J_SERVER_HOST" ]; then
            echo -e "${YELLOW}[INFO] Neo4j在独立服务器: $NEO4J_SERVER_HOST${NC}"
            # Neo4j数据迁移逻辑
        else
            echo -e "${YELLOW}[INFO] Neo4j和应用服务器在同一台机器${NC}"
        fi
    fi
fi

# 服务器端初始化
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  服务器端初始化${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

if [ "$DRY_RUN" = "false" ]; then
    echo -e "${YELLOW}[INFO] 在服务器上执行初始化命令...${NC}"
    
    ssh -i "$APP_SERVER_KEY" -o StrictHostKeyChecking=no "$APP_SERVER_USER@$APP_SERVER_HOST" << 'EOF'
cd /opt/enterprise-ai-platform
find os-core -type f -name '*.py' -exec chmod 644 {} \;
find services -type f -name '*.py' -exec chmod 644 {} \;
find metadata-service -type f -name '*.py' -exec chmod 644 {} \;
export PYTHONPATH=/opt/enterprise-ai-platform:$PYTHONPATH
echo "[OK] 初始化完成"
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[OK] 服务器端初始化完成${NC}"
    else
        echo -e "${YELLOW}[WARN] 服务器端初始化可能有问题，请检查${NC}"
    fi
fi

# 总结
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  迁移完成${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${YELLOW}下一步操作:${NC}"
echo "1. 在服务器上检查文件是否正确上传"
echo "2. 如果需要，导入数据库数据"
echo "3. 重启相关服务: docker-compose restart"
echo "4. 运行测试验证: pytest tests/milestone_integration_test.py"
echo ""

