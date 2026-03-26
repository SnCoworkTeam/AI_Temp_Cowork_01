#!/bin/bash
# 手动安装Docker脚本（适用于网络受限环境）
# 使用方法: sudo bash install-docker-manual.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "手动安装Docker（使用国内镜像源）"
echo "==========================================${NC}"

# 检测系统类型
if [ -f /etc/debian_version ]; then
    OS="debian"
    echo "检测到 Debian/Ubuntu 系统"
elif [ -f /etc/redhat-release ]; then
    OS="rhel"
    echo "检测到 CentOS/RHEL 系统"
else
    echo -e "${RED}❌ 不支持的系统类型${NC}"
    exit 1
fi

# Ubuntu/Debian安装
install_docker_debian() {
    echo ""
    echo -e "${BLUE}安装Docker (Ubuntu/Debian)...${NC}"
    
    # 更新包索引
    sudo apt-get update
    
    # 安装必要工具
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # 添加阿里云Docker镜像源
    echo "添加阿里云Docker镜像源..."
    sudo mkdir -p /etc/apt/keyrings
    
    # 下载GPG密钥（使用阿里云镜像）
    curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # 添加镜像源
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 更新包索引
    sudo apt-get update
    
    # 安装Docker
    sudo apt-get install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin
    
    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    echo -e "${GREEN}✅ Docker安装完成${NC}"
}

# CentOS/RHEL安装
install_docker_rhel() {
    echo ""
    echo -e "${BLUE}安装Docker (CentOS/RHEL)...${NC}"
    
    # 安装必要工具
    sudo yum install -y yum-utils
    
    # 添加阿里云Docker镜像源
    echo "添加阿里云Docker镜像源..."
    sudo yum-config-manager \
        --add-repo \
        https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
    
    # 安装Docker
    sudo yum install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin
    
    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    echo -e "${GREEN}✅ Docker安装完成${NC}"
}

# 安装Docker Compose（如果需要独立版本）
install_docker_compose_standalone() {
    echo ""
    echo -e "${BLUE}安装Docker Compose（独立版本）...${NC}"
    
    # 使用daocloud镜像下载
    DOCKER_COMPOSE_VERSION="v2.24.0"
    
    echo "从daocloud镜像下载 Docker Compose ${DOCKER_COMPOSE_VERSION}..."
    sudo curl -L "https://get.daocloud.io/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    
    sudo chmod +x /usr/local/bin/docker-compose
    
    echo -e "${GREEN}✅ Docker Compose安装完成${NC}"
}

# 配置Docker镜像加速器（可选）
configure_docker_mirror() {
    echo ""
    echo -e "${BLUE}配置Docker镜像加速器...${NC}"
    
    read -p "是否配置Docker镜像加速器（推荐）? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        sudo mkdir -p /etc/docker
        
        # 配置镜像加速器（使用阿里云、腾讯云、网易等）
        sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ],
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2"
}
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl restart docker
        
        echo -e "${GREEN}✅ Docker镜像加速器配置完成${NC}"
    fi
}

# 主执行流程
main() {
    # 检查是否已安装
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✅ Docker已安装，版本: $(docker --version)${NC}"
    else
        if [ "$OS" = "debian" ]; then
            install_docker_debian
        elif [ "$OS" = "rhel" ]; then
            install_docker_rhel
        fi
    fi
    
    # 检查Docker Compose
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        echo -e "${GREEN}✅ Docker Compose已安装${NC}"
    else
        install_docker_compose_standalone
    fi
    
    # 配置镜像加速器
    configure_docker_mirror
    
    # 将当前用户添加到docker组
    if [ "$EUID" -ne 0 ]; then
        USER=$(whoami)
        sudo usermod -aG docker $USER
        echo -e "${YELLOW}⚠️  已将用户 $USER 添加到docker组${NC}"
        echo -e "${YELLOW}⚠️  请重新登录以使权限生效${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✅ Docker安装完成！"
    echo "==========================================${NC}"
    echo ""
    echo "验证安装:"
    echo "  docker --version"
    echo "  docker-compose --version"
    echo "  sudo docker run hello-world"
    echo ""
}

main

