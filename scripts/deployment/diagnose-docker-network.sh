#!/bin/bash
# Docker网络诊断和修复脚本
# 自动检测网络问题并尝试修复

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "Docker网络诊断和修复脚本"
echo "==========================================${NC}"
echo ""

# 检查是否为root或有sudo权限
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo -e "${RED}❌ 需要root权限或sudo权限${NC}"
    exit 1
fi

# 测试网络连接
test_connection() {
    local url=$1
    local name=$2
    
    echo -n "测试 $name ... "
    if timeout 5 curl -s --connect-timeout 3 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 可访问${NC}"
        return 0
    else
        echo -e "${RED}❌ 不可访问${NC}"
        return 1
    fi
}

# 诊断网络
diagnose_network() {
    echo -e "${BLUE}[1/4] 诊断网络连接...${NC}"
    echo ""
    
    PASSED=0
    FAILED=0
    
    # 测试DNS
    echo "DNS解析测试:"
    if timeout 3 nslookup docker.mirrors.ustc.edu.cn > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ DNS解析正常${NC}"
        ((PASSED++))
    else
        echo -e "  ${RED}❌ DNS解析失败${NC}"
        ((FAILED++))
    fi
    
    # 测试镜像源
    echo ""
    echo "镜像源连接测试:"
    test_connection "https://docker.mirrors.ustc.edu.cn" "USTC镜像源" && ((PASSED++)) || ((FAILED++))
    test_connection "https://hub-mirror.c.163.com" "163镜像源" && ((PASSED++)) || ((FAILED++))
    test_connection "https://mirror.baidubce.com" "百度镜像源" && ((PASSED++)) || ((FAILED++))
    test_connection "https://registry-1.docker.io" "Docker Hub" && ((PASSED++)) || ((FAILED++))
    
    # 测试端口
    echo ""
    echo "端口连通性测试:"
    if timeout 3 bash -c "echo >/dev/tcp/docker.mirrors.ustc.edu.cn/443" 2>/dev/null; then
        echo -e "  ${GREEN}✅ 443端口可访问${NC}"
        ((PASSED++))
    else
        echo -e "  ${RED}❌ 443端口被阻止（可能是防火墙或安全组）${NC}"
        ((FAILED++))
    fi
    
    echo ""
    echo "测试结果: 通过 $PASSED, 失败 $FAILED"
    echo ""
    
    if [ $FAILED -gt 0 ]; then
        return 1
    fi
    return 0
}

# 检查并修复Docker配置
fix_docker_config() {
    echo -e "${BLUE}[2/4] 检查并修复Docker配置...${NC}"
    echo ""
    
    # 确保镜像加速器已配置
    if [ ! -f /etc/docker/daemon.json ] || ! grep -q "registry-mirrors" /etc/docker/daemon.json; then
        echo "配置Docker镜像加速器..."
        sudo mkdir -p /etc/docker
        sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
EOF
        echo -e "${GREEN}✅ Docker镜像加速器已配置${NC}"
        
        # 重启Docker
        echo "重启Docker服务..."
        sudo systemctl daemon-reload
        sudo systemctl restart docker
        sleep 5
    else
        echo -e "${GREEN}✅ Docker镜像加速器已配置${NC}"
        echo "当前配置:"
        grep -A 5 "registry-mirrors" /etc/docker/daemon.json | head -6
    fi
    echo ""
}

# 尝试使用代理或其他方法
try_alternative_methods() {
    echo -e "${BLUE}[3/4] 尝试替代方法...${NC}"
    echo ""
    
    # 方法1: 尝试直接使用镜像源拉取
    echo "方法1: 尝试直接使用镜像源拉取 hello-world..."
    if timeout 30 docker pull hello-world:latest > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 镜像拉取成功！${NC}"
        docker rmi hello-world:latest > /dev/null 2>&1 || true
        return 0
    else
        echo -e "${YELLOW}⚠️  直接拉取失败${NC}"
    fi
    
    # 方法2: 尝试使用国内镜像站的直接地址
    echo ""
    echo "方法2: 尝试使用阿里云镜像..."
    if docker pull registry.cn-hangzhou.aliyuncs.com/library/hello-world:latest > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 使用阿里云镜像成功${NC}"
        docker rmi registry.cn-hangzhou.aliyuncs.com/library/hello-world:latest > /dev/null 2>&1 || true
        return 0
    else
        echo -e "${YELLOW}⚠️  阿里云镜像拉取失败${NC}"
    fi
    
    return 1
}

# 生成解决方案
generate_solution() {
    echo -e "${BLUE}[4/4] 生成解决方案...${NC}"
    echo ""
    
    echo -e "${YELLOW}检测到网络连接问题，提供以下解决方案：${NC}"
    echo ""
    
    # 方案1: 修改docker-compose使用国内镜像
    echo "方案1: 修改docker-compose.db.yml使用国内镜像地址"
    echo "----------------------------------------"
    echo "编辑 docker-compose.db.yml，将镜像地址改为："
    echo ""
    echo "  postgres:"
    echo "    image: registry.cn-hangzhou.aliyuncs.com/acs/postgres:15"
    echo ""
    echo "  redis:"
    echo "    image: registry.cn-hangzhou.aliyuncs.com/acs/redis:7"
    echo ""
    echo "  redis-commander:"
    echo "    image: registry.cn-hangzhou.aliyuncs.com/acs/redis-commander:latest"
    echo ""
    
    # 方案2: 检查云服务器安全组
    echo ""
    echo "方案2: 检查云服务器安全组（最重要）"
    echo "----------------------------------------"
    echo "如果使用云服务器（阿里云、腾讯云等），需要在云控制台配置安全组："
    echo ""
    echo "1. 登录云控制台"
    echo "2. 找到服务器实例 -> 安全组"
    echo "3. 添加入站规则："
    echo "   - 端口: 443"
    echo "   - 协议: TCP"
    echo "   - 源: 0.0.0.0/0"
    echo "   - 描述: 允许HTTPS访问（Docker镜像拉取需要）"
    echo ""
    
    # 方案3: 手动下载镜像
    echo ""
    echo "方案3: 手动下载镜像（如果网络正常）"
    echo "----------------------------------------"
    echo "如果443端口已开放，可以尝试："
    echo ""
    echo "  docker pull postgres:15"
    echo "  docker pull redis:7"
    echo "  docker pull rediscommander/redis-commander:latest"
    echo ""
    
    # 方案4: 使用代理
    echo ""
    echo "方案4: 配置Docker代理（如果有代理服务器）"
    echo "----------------------------------------"
    echo "创建 /etc/systemd/system/docker.service.d/http-proxy.conf:"
    echo ""
    echo "  [Service]"
    echo "  Environment=\"HTTP_PROXY=http://proxy.example.com:8080\""
    echo "  Environment=\"HTTPS_PROXY=http://proxy.example.com:8080\""
    echo ""
    echo "然后运行:"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl restart docker"
    echo ""
}

# 主函数
main() {
    # 诊断网络
    if ! diagnose_network; then
        echo -e "${YELLOW}⚠️  检测到网络连接问题${NC}"
        echo ""
    fi
    
    # 修复Docker配置
    fix_docker_config
    
    # 尝试替代方法
    if try_alternative_methods; then
        echo ""
        echo -e "${GREEN}=========================================="
        echo "✅ Docker镜像拉取已恢复正常"
        echo "==========================================${NC}"
        echo ""
        echo "现在可以运行部署脚本:"
        echo "  sudo bash deploy-server.sh"
        exit 0
    else
        echo ""
        echo -e "${YELLOW}⚠️  自动修复失败，需要手动处理${NC}"
        echo ""
        generate_solution
        exit 1
    fi
}

main

