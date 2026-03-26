#!/bin/bash
# 自动修改docker-compose使用国内镜像源
# 使用方法: sudo bash use-china-mirrors.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "切换到国内镜像源"
echo "==========================================${NC}"
echo ""

# 检查是否为root或有sudo权限
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo -e "${RED}❌ 需要root权限或sudo权限${NC}"
    exit 1
fi

# 项目目录
PROJECT_DIR="${PROJECT_DIR:-/opt/enterprise-ai-platform}"
if [ ! -d "$PROJECT_DIR" ]; then
    PROJECT_DIR="$(pwd)"
fi

cd "$PROJECT_DIR"

# 备份文件
backup_file() {
    local file=$1
    if [ -f "$file" ]; then
        sudo cp "$file" "${file}.bak.$(date +%Y%m%d_%H%M%S)"
        echo "已备份: $file"
    fi
}

# 修改docker-compose.db.yml使用国内镜像
fix_docker_compose_db() {
    local file="docker-compose.db.yml"
    
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ 文件不存在: $file${NC}"
        return 1
    fi
    
    echo "修改 $file 使用国内镜像..."
    backup_file "$file"
    
    # 使用sed替换镜像地址
    # PostgreSQL: postgres:15 -> registry.cn-hangzhou.aliyuncs.com/acs/postgres:15
    sudo sed -i 's|image: postgres:15|image: registry.cn-hangzhou.aliyuncs.com/acs/postgres:15|g' "$file"
    
    # Redis: redis:7-alpine -> registry.cn-hangzhou.aliyuncs.com/acs/redis:7-alpine
    sudo sed -i 's|image: redis:7-alpine|image: registry.cn-hangzhou.aliyuncs.com/acs/redis:7-alpine|g' "$file"
    sudo sed -i 's|image: redis:7|image: registry.cn-hangzhou.aliyuncs.com/acs/redis:7|g' "$file"
    
    # Redis Commander: rediscommander/redis-commander:latest -> registry.cn-hangzhou.aliyuncs.com/acs/redis-commander:latest
    sudo sed -i 's|image: rediscommander/redis-commander:latest|image: registry.cn-hangzhou.aliyuncs.com/acs/redis-commander:latest|g' "$file"
    
    echo -e "${GREEN}✅ $file 已修改${NC}"
    echo ""
    echo "修改后的镜像配置:"
    grep -E "^\s+image:" "$file" | head -5
    echo ""
}

# 测试镜像拉取
test_image_pull() {
    echo "测试国内镜像拉取..."
    
    # 测试PostgreSQL镜像
    echo -n "测试PostgreSQL镜像... "
    if timeout 30 docker pull registry.cn-hangzhou.aliyuncs.com/acs/postgres:15 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 成功${NC}"
        # 打标签以便docker-compose使用
        docker tag registry.cn-hangzhou.aliyuncs.com/acs/postgres:15 postgres:15 2>/dev/null || true
    else
        echo -e "${YELLOW}⚠️  失败（可能镜像不存在，将使用其他镜像源）${NC}"
        # 尝试其他镜像源
        echo "尝试其他镜像源..."
        if timeout 30 docker pull registry.cn-shenzhen.aliyuncs.com/namespace/postgres:15 > /dev/null 2>&1 || \
           timeout 30 docker pull dockerhub.azk8s.cn/library/postgres:15 > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 使用备用镜像源成功${NC}"
        fi
    fi
    
    # 测试Redis镜像
    echo -n "测试Redis镜像... "
    if timeout 30 docker pull registry.cn-hangzhou.aliyuncs.com/acs/redis:7-alpine > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 成功${NC}"
        docker tag registry.cn-hangzhou.aliyuncs.com/acs/redis:7-alpine redis:7-alpine 2>/dev/null || true
    else
        echo -e "${YELLOW}⚠️  失败${NC}"
    fi
    
    echo ""
}

# 使用Docker Hub镜像加速后的直接地址（如果阿里云镜像不可用）
use_docker_hub_mirror() {
    echo "如果阿里云镜像不可用，使用Docker Hub镜像加速器..."
    echo ""
    echo "配置已存在的镜像加速器将自动生效"
    echo "如果仍未成功，请检查："
    echo "  1. 云服务器安全组是否开放443端口"
    echo "  2. 网络连接是否正常"
    echo ""
}

# 主函数
main() {
    echo "项目目录: $PROJECT_DIR"
    echo ""
    
    # 修改docker-compose.db.yml
    if fix_docker_compose_db; then
        echo -e "${GREEN}✅ 配置文件已更新${NC}"
    else
        echo -e "${RED}❌ 配置文件更新失败${NC}"
        exit 1
    fi
    
    # 测试镜像拉取
    test_image_pull
    
    # 提示
    echo -e "${GREEN}=========================================="
    echo "✅ 已切换到国内镜像源"
    echo "==========================================${NC}"
    echo ""
    echo "现在可以运行部署脚本:"
    echo "  cd $PROJECT_DIR"
    echo "  sudo bash scripts/deployment/deploy-server.sh"
    echo ""
    echo "如果仍然失败，请："
    echo "  1. 检查云服务器安全组（开放443端口）"
    echo "  2. 运行诊断脚本: sudo bash scripts/deployment/diagnose-docker-network.sh"
    echo ""
}

main

