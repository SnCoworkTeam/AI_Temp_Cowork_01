#!/bin/bash
# 同步本地Docker镜像到服务器测试环境
# 使用方法: ./scripts/sync-to-server.sh [service1] [service2] ...

set -e

SERVER_HOST="43.143.139.197"
SERVER_USER="ubuntu"
SSH_KEY="enterprise_ai_platform.pem"
SERVER_DOCKER_DIR="/home/ubuntu/enterprise-ai-platform"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 开始同步Docker镜像到服务器...${NC}"

# 检查SSH密钥
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}❌ SSH密钥文件不存在: $SSH_KEY${NC}"
    exit 1
fi

# 设置SSH密钥权限
chmod 600 "$SSH_KEY"

# 获取要同步的服务列表（如果未指定，则同步所有服务）
if [ $# -eq 0 ]; then
    SERVICES=(
        "api-gateway"
        "agent-service"
        "chat-service"
        "config-center"
        "knowledge-base"
        "mcp-gateway"
        "workflow-engine"
        "dag-orchestrator"
        "sap-mcp-server"
    )
else
    SERVICES=("$@")
fi

# 创建临时目录
TEMP_DIR=$(mktemp -d)
echo -e "${YELLOW}📦 临时目录: $TEMP_DIR${NC}"

# 导出并同步每个服务的镜像
for SERVICE in "${SERVICES[@]}"; do
    IMAGE_NAME="enterprise-ai-${SERVICE}"
    IMAGE_FILE="${TEMP_DIR}/${SERVICE}.tar"
    
    echo -e "${YELLOW}📦 导出镜像: $IMAGE_NAME${NC}"
    
    # 检查镜像是否存在
    if ! docker images | grep -q "$IMAGE_NAME"; then
        echo -e "${YELLOW}⚠️  镜像 $IMAGE_NAME 不存在，跳过...${NC}"
        continue
    fi
    
    # 导出镜像
    docker save "$IMAGE_NAME:latest" -o "$IMAGE_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 镜像导出成功: $IMAGE_FILE${NC}"
        
        # 压缩镜像文件（可选，减少传输时间）
        echo -e "${YELLOW}🗜️  压缩镜像文件...${NC}"
        gzip -f "$IMAGE_FILE"
        IMAGE_FILE="${IMAGE_FILE}.gz"
        
        # 上传到服务器
        echo -e "${YELLOW}📤 上传镜像到服务器...${NC}"
        scp -i "$SSH_KEY" "$IMAGE_FILE" "${SERVER_USER}@${SERVER_HOST}:${SERVER_DOCKER_DIR}/images/"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 镜像上传成功: $SERVICE${NC}"
            
            # 在服务器上加载镜像
            echo -e "${YELLOW}📥 在服务器上加载镜像...${NC}"
            ssh -i "$SSH_KEY" "${SERVER_USER}@${SERVER_HOST}" \
                "cd ${SERVER_DOCKER_DIR} && \
                 gunzip -c images/${SERVICE}.tar.gz | docker load && \
                 rm -f images/${SERVICE}.tar.gz"
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ 镜像加载成功: $SERVICE${NC}"
            else
                echo -e "${RED}❌ 镜像加载失败: $SERVICE${NC}"
            fi
        else
            echo -e "${RED}❌ 镜像上传失败: $SERVICE${NC}"
        fi
    else
        echo -e "${RED}❌ 镜像导出失败: $SERVICE${NC}"
    fi
done

# 清理临时文件
rm -rf "$TEMP_DIR"
echo -e "${GREEN}🧹 临时文件已清理${NC}"

# 同步docker-compose.yml和配置文件
echo -e "${YELLOW}📤 同步配置文件...${NC}"
scp -i "$SSH_KEY" docker-compose.yml "${SERVER_USER}@${SERVER_HOST}:${SERVER_DOCKER_DIR}/"
scp -i "$SSH_KEY" docker-compose.test.yml "${SERVER_USER}@${SERVER_HOST}:${SERVER_DOCKER_DIR}/" 2>/dev/null || true

# 重启服务（可选）
read -p "是否重启服务器上的服务? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🔄 重启服务器上的服务...${NC}"
    ssh -i "$SSH_KEY" "${SERVER_USER}@${SERVER_HOST}" \
        "cd ${SERVER_DOCKER_DIR} && \
         docker-compose -f docker-compose.test.yml down && \
         docker-compose -f docker-compose.test.yml up -d"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 服务重启成功${NC}"
    else
        echo -e "${RED}❌ 服务重启失败${NC}"
    fi
fi

echo -e "${GREEN}🎉 同步完成！${NC}"

