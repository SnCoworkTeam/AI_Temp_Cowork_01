#!/bin/bash
# 服务器初始化脚本
# 用于首次部署时设置服务器环境
# 使用方法: ./setup-server.sh [--git-url <url>] [--branch <branch>]

set -e

# 默认配置
GIT_URL="https://github.com/PMLiuyubin/enterprise-ai-platform.git"
BRANCH="main"
PROJECT_DIR="/opt/enterprise-ai-platform"
USER=$(whoami)

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --git-url)
            GIT_URL="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --project-dir)
            PROJECT_DIR="$2"
            shift 2
            ;;
        *)
            echo "用法: $0 [--git-url <url>] [--branch <branch>] [--project-dir <dir>]"
            exit 1
            ;;
    esac
done

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "企业AI平台 - 服务器初始化脚本"
echo "==========================================${NC}"
echo ""

# 检查是否为root或有sudo权限
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo -e "${RED}❌ 需要root权限或sudo权限${NC}"
    exit 1
fi

# 安装Docker
install_docker() {
    echo -e "${BLUE}[1/6] 安装Docker...${NC}"
    
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✅ Docker已安装${NC}"
        return
    fi
    
    echo "安装Docker..."
    
    # 检测网络连接，如果官方源失败则使用国内镜像
    if curl -fsSL https://get.docker.com -o /tmp/get-docker.sh 2>/dev/null; then
        echo "使用Docker官方源安装..."
        sudo sh /tmp/get-docker.sh
    else
        echo -e "${YELLOW}⚠️  Docker官方源连接失败，尝试使用国内镜像源...${NC}"
        
        # 使用阿里云镜像源安装Docker
        if [ -f /etc/debian_version ]; then
            # Ubuntu/Debian
            echo "配置阿里云Docker镜像源..."
            sudo apt-get update
            sudo apt-get install -y ca-certificates curl gnupg lsb-release
            
            # 添加阿里云Docker镜像源
            sudo mkdir -p /etc/apt/keyrings
            curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            
        elif [ -f /etc/redhat-release ]; then
            # CentOS/RHEL
            echo "配置阿里云Docker镜像源..."
            sudo yum install -y yum-utils
            
            sudo yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        fi
        
        # 启动Docker服务
        sudo systemctl start docker
        sudo systemctl enable docker
    fi
    
    # 将当前用户添加到docker组
    sudo usermod -aG docker $USER
    
    echo -e "${GREEN}✅ Docker安装完成${NC}"
    echo -e "${YELLOW}⚠️  请重新登录以使docker组权限生效${NC}"
}

# 安装Docker Compose
install_docker_compose() {
    echo ""
    echo -e "${BLUE}[2/6] 安装Docker Compose...${NC}"
    
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✅ Docker Compose已安装${NC}"
        return
    fi
    
    echo "安装Docker Compose..."
    
    # 尝试从GitHub获取最新版本，如果失败则使用固定版本或镜像源
    if DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest 2>/dev/null | grep 'tag_name' | cut -d\" -f4); then
        echo "使用版本: $DOCKER_COMPOSE_VERSION"
    else
        echo -e "${YELLOW}⚠️  无法获取最新版本，使用固定版本 v2.24.0${NC}"
        DOCKER_COMPOSE_VERSION="v2.24.0"
    fi
    
    # 尝试从GitHub下载，如果失败则使用镜像源
    if sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose 2>/dev/null; then
        echo "从GitHub下载成功"
    else
        echo -e "${YELLOW}⚠️  GitHub下载失败，尝试使用镜像源...${NC}"
        # 使用daocloud镜像
        sudo curl -L "https://get.daocloud.io/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose || {
            echo -e "${RED}❌ Docker Compose下载失败${NC}"
            echo "请手动安装Docker Compose或检查网络连接"
            exit 1
        }
    fi
    
    sudo chmod +x /usr/local/bin/docker-compose
    
    echo -e "${GREEN}✅ Docker Compose安装完成${NC}"
}

# 安装Git
install_git() {
    echo ""
    echo -e "${BLUE}[3/6] 安装Git...${NC}"
    
    if command -v git &> /dev/null; then
        echo -e "${GREEN}✅ Git已安装${NC}"
        return
    fi
    
    if [ -f /etc/debian_version ]; then
        sudo apt-get update
        sudo apt-get install -y git
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y git
    fi
    
    echo -e "${GREEN}✅ Git安装完成${NC}"
}

# 安装其他工具
install_tools() {
    echo ""
    echo -e "${BLUE}[4/6] 安装必要工具...${NC}"
    
    if [ -f /etc/debian_version ]; then
        sudo apt-get update
        sudo apt-get install -y curl wget net-tools
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y curl wget net-tools
    fi
    
    echo -e "${GREEN}✅ 工具安装完成${NC}"
}

# 创建项目目录
create_project_dir() {
    echo ""
    echo -e "${BLUE}[5/6] 创建项目目录...${NC}"
    
    if [ -n "$GIT_URL" ]; then
        if [ -d "$PROJECT_DIR" ]; then
            echo -e "${YELLOW}⚠️  项目目录已存在，跳过克隆${NC}"
        else
            echo "从Git克隆项目..."
            sudo mkdir -p "$(dirname "$PROJECT_DIR")"
            sudo git clone -b "$BRANCH" "$GIT_URL" "$PROJECT_DIR"
            sudo chown -R $USER:$USER "$PROJECT_DIR"
            echo -e "${GREEN}✅ 项目克隆完成${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  未提供Git URL，跳过项目克隆${NC}"
        echo "请手动克隆项目到: $PROJECT_DIR"
    fi
}

# 配置防火墙（可选）
configure_firewall() {
    echo ""
    echo -e "${BLUE}[6/6] 配置防火墙...${NC}"
    
    read -p "是否配置防火墙规则? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v ufw &> /dev/null; then
            # Ubuntu/Debian UFW
            sudo ufw allow 22/tcp   # SSH
            sudo ufw allow 80/tcp    # HTTP
            sudo ufw allow 443/tcp  # HTTPS
            sudo ufw allow 8001/tcp # MCP Gateway
            sudo ufw allow 8002/tcp # Workflow Engine
            sudo ufw allow 8003/tcp # Auth Service
            sudo ufw allow 8004/tcp # Knowledge Base
            sudo ufw allow 3000/tcp # Web UI
            echo -e "${GREEN}✅ 防火墙规则已添加${NC}"
        elif command -v firewall-cmd &> /dev/null; then
            # CentOS/RHEL Firewalld
            sudo firewall-cmd --permanent --add-port=22/tcp
            sudo firewall-cmd --permanent --add-port=80/tcp
            sudo firewall-cmd --permanent --add-port=443/tcp
            sudo firewall-cmd --permanent --add-port=8001/tcp
            sudo firewall-cmd --permanent --add-port=8002/tcp
            sudo firewall-cmd --permanent --add-port=8003/tcp
            sudo firewall-cmd --permanent --add-port=8004/tcp
            sudo firewall-cmd --permanent --add-port=3000/tcp
            sudo firewall-cmd --reload
            echo -e "${GREEN}✅ 防火墙规则已添加${NC}"
        else
            echo -e "${YELLOW}⚠️  未找到防火墙工具，跳过配置${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  跳过防火墙配置${NC}"
    fi
}

# 主执行流程
main() {
    install_docker
    install_docker_compose
    install_git
    install_tools
    create_project_dir
    configure_firewall
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✅ 服务器初始化完成！"
    echo "==========================================${NC}"
    echo ""
    echo "下一步："
    echo "1. 编辑环境变量文件: $PROJECT_DIR/.env.production"
    echo "2. 运行部署脚本: cd $PROJECT_DIR && bash scripts/deployment/deploy-server.sh"
    echo ""
    if [ -n "$GIT_URL" ]; then
        echo "项目已克隆到: $PROJECT_DIR"
    fi
    echo ""
    echo -e "${YELLOW}⚠️  如果Docker是新安装的，请重新登录以使docker组权限生效${NC}"
    echo ""
}

main

