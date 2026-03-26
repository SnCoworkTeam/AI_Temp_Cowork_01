#!/bin/bash
# 修复Docker镜像加速器配置
# 使用方法: sudo bash fix-docker-mirror.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "Docker镜像加速器修复脚本"
echo "==========================================${NC}"
echo ""

# 检查是否为root或有sudo权限
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo -e "${RED}❌ 需要root权限或sudo权限${NC}"
    exit 1
fi

# 配置镜像加速器
configure_mirror() {
    echo "配置Docker镜像加速器..."
    
    # 创建目录
    sudo mkdir -p /etc/docker
    
    # 备份现有配置
    if [ -f /etc/docker/daemon.json ]; then
        sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.bak.$(date +%Y%m%d_%H%M%S)
        echo "已备份现有配置"
    fi
    
    # 配置镜像加速器
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
    
    echo -e "${GREEN}✅ 镜像加速器配置已写入${NC}"
    echo ""
    echo "配置内容:"
    cat /etc/docker/daemon.json
    echo ""
}

# 重启Docker
restart_docker() {
    echo "重启Docker服务..."
    sudo systemctl daemon-reload
    sudo systemctl restart docker
    
    echo "等待Docker启动..."
    sleep 5
    
    if docker info &> /dev/null; then
        echo -e "${GREEN}✅ Docker服务已重启${NC}"
        return 0
    else
        echo -e "${RED}❌ Docker服务启动失败${NC}"
        return 1
    fi
}

# 验证配置
verify_config() {
    echo "验证镜像加速器配置..."
    echo ""
    
    # 检查配置
    if [ -f /etc/docker/daemon.json ]; then
        if grep -q "registry-mirrors" /etc/docker/daemon.json; then
            echo -e "${GREEN}✅ 镜像加速器配置存在${NC}"
            echo "配置的镜像源:"
            grep -A 5 "registry-mirrors" /etc/docker/daemon.json | head -6
            echo ""
        else
            echo -e "${RED}❌ 镜像加速器配置不存在${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Docker配置文件不存在${NC}"
        return 1
    fi
    
    # 测试镜像拉取
    echo "测试镜像拉取..."
    if timeout 30 docker pull hello-world:latest > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 镜像拉取测试成功${NC}"
        docker rmi hello-world:latest > /dev/null 2>&1 || true
        return 0
    else
        echo -e "${YELLOW}⚠️  镜像拉取测试失败${NC}"
        echo ""
        echo "可能原因:"
        echo "  1. 网络连接问题"
        echo "  2. 云服务器安全组未开放443端口"
        echo "  3. 镜像源服务器暂时不可用"
        echo ""
        echo "建议:"
        echo "  1. 检查网络连接: ping docker.mirrors.ustc.edu.cn"
        echo "  2. 检查云服务器安全组（开放443端口）"
        echo "  3. 尝试手动拉取: docker pull hello-world:latest"
        return 1
    fi
}

# 主函数
main() {
    echo "步骤1: 配置镜像加速器"
    configure_mirror
    
    echo ""
    echo "步骤2: 重启Docker服务"
    if ! restart_docker; then
        echo -e "${RED}❌ Docker重启失败，请检查配置${NC}"
        exit 1
    fi
    
    echo ""
    echo "步骤3: 验证配置"
    if verify_config; then
        echo ""
        echo -e "${GREEN}=========================================="
        echo "✅ Docker镜像加速器配置成功"
        echo "==========================================${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠️  镜像加速器已配置，但测试失败${NC}"
        echo "请检查网络连接和云服务器安全组设置"
        exit 1
    fi
}

main

