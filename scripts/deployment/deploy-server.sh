#!/bin/bash
# 服务器部署脚本
# 使用方法: ./deploy-server.sh [选项]
# 
# 选项:
#   --git-url <url>          Git仓库地址（首次部署时使用）
#   --env <env>               部署环境 (production|staging|development)
#   --branch <branch>         Git分支 (默认: main)
#   --skip-tests              跳过测试
#   --skip-backup            跳过备份
#   --skip-migration          跳过数据库迁移
#   --force                   强制重新构建镜像
#
# 安全提示: 此脚本包含默认的Git Token，请不要将此文件提交到公共仓库！
# 建议使用环境变量 GIT_TOKEN 来设置Token，而不是在代码中硬编码

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 默认配置
ENV="production"
BRANCH="main"
SKIP_TESTS=false
SKIP_BACKUP=false
SKIP_MIGRATION=false
FORCE_BUILD=false
OFFLINE_MODE=false
GIT_URL="https://github.com/PMLiuyubin/enterprise-ai-platform.git"
GIT_USERNAME="${GIT_USERNAME:-lyb-005@163.com}"
GIT_TOKEN="${GIT_TOKEN:-${GIT_PASSWORD:-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}}"  # 支持GIT_TOKEN或GIT_PASSWORD环境变量
PROJECT_DIR="/opt/enterprise-ai-platform"

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --git-url)
            GIT_URL="$2"
            shift 2
            ;;
        --env)
            ENV="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-migration)
            SKIP_MIGRATION=true
            shift
            ;;
        --force)
            FORCE_BUILD=true
            shift
            ;;
        --offline)
            OFFLINE_MODE=true
            shift
            ;;
        --project-dir)
            PROJECT_DIR="$2"
            shift 2
            ;;
        --git-username)
            GIT_USERNAME="$2"
            shift 2
            ;;
        --git-password)
            GIT_TOKEN="$2"
            shift 2
            ;;
        --git-token)
            GIT_TOKEN="$2"
            shift 2
            ;;
        *)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --git-url <url>          Git仓库地址（首次部署时使用）"
            echo "  --env <env>               部署环境 (production|staging|development)"
            echo "  --branch <branch>         Git分支 (默认: main)"
            echo "  --skip-tests              跳过测试"
            echo "  --skip-backup            跳过备份"
            echo "  --skip-migration          跳过数据库迁移"
            echo "  --force                   强制重新构建镜像"
            echo "  --offline                 离线模式（不拉取镜像，使用本地镜像）"
            echo "  --project-dir <dir>       项目目录 (默认: /opt/enterprise-ai-platform)"
            echo "  --git-username <user>     Git用户名（可选，也可通过GIT_USERNAME环境变量）"
            echo "  --git-token <token>       Git Personal Access Token（必需，也可通过GIT_TOKEN环境变量）"
            echo "  注意: GitHub不再支持密码认证，必须使用Personal Access Token"
            exit 1
            ;;
    esac
done

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "企业AI平台 - 服务器部署脚本"
echo "==========================================${NC}"
echo "环境: $ENV"
echo "分支: $BRANCH"
echo "项目目录: $PROJECT_DIR"
if [ "$OFFLINE_MODE" = true ]; then
    echo -e "${GREEN}模式: 离线模式（不拉取镜像）${NC}"
fi
echo "Git仓库: $GIT_URL"
if [ -n "$GIT_USERNAME" ]; then
    echo "Git用户: $GIT_USERNAME"
fi
if [ -n "$GIT_TOKEN" ]; then
    # 只显示Token的前4位和后4位，隐藏中间部分
    TOKEN_PREVIEW=$(echo "$GIT_TOKEN" | sed 's/\(.\{4\}\).*\(.\{4\}\)/\1****\2/')
    echo "Git Token: $TOKEN_PREVIEW (已配置)"
else
    echo -e "${YELLOW}⚠️  Git Token未配置，可能需要手动输入${NC}"
fi
echo -e "${YELLOW}⚠️  安全提示: 请勿将此脚本提交到公共Git仓库！${NC}"
echo ""

# 配置Docker镜像加速器
configure_docker_mirror() {
    echo -e "${BLUE}[0/12] 检查Docker镜像加速器...${NC}"
    
    # 检查是否已经配置了镜像加速器
    if [ -f /etc/docker/daemon.json ]; then
        if grep -q "registry-mirrors" /etc/docker/daemon.json; then
            echo -e "${GREEN}✅ Docker镜像加速器已配置${NC}"
            # 显示当前配置的镜像源
            echo "当前镜像加速器配置:"
            grep -A 5 "registry-mirrors" /etc/docker/daemon.json | head -6 || echo "  (无法读取配置)"
            
            # 即使已配置，也测试一下连接
            echo "测试Docker镜像拉取..."
            if timeout 15 docker pull hello-world:latest > /dev/null 2>&1; then
                docker rmi hello-world:latest > /dev/null 2>&1 || true
                echo -e "${GREEN}✅ Docker镜像拉取测试成功${NC}"
                echo ""
                return 0
            else
                echo -e "${YELLOW}⚠️  Docker镜像拉取测试失败，重新加载Docker配置...${NC}"
                # 重新加载Docker配置
                echo "重启Docker服务以应用镜像加速器配置..."
                sudo systemctl daemon-reload || true
                sudo systemctl restart docker || true
                sleep 3
                
                # 再次测试
                echo "再次测试Docker镜像拉取..."
                if timeout 15 docker pull hello-world:latest > /dev/null 2>&1; then
                    docker rmi hello-world:latest > /dev/null 2>&1 || true
                    echo -e "${GREEN}✅ Docker镜像拉取测试成功（重启后）${NC}"
                    echo ""
                    return 0
                else
                    echo -e "${YELLOW}⚠️  镜像拉取仍然失败，可能是网络问题${NC}"
                    echo "提示: 如果使用云服务器，请检查云控制台的安全组设置"
                    echo ""
                fi
            fi
        fi
    fi
    
    # 测试Docker Hub连接
    echo "测试Docker Hub连接..."
    if timeout 10 curl -s --connect-timeout 5 https://registry-1.docker.io/v2/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Hub连接正常${NC}"
        echo ""
        return 0
    else
        echo -e "${YELLOW}⚠️  Docker Hub连接失败（可能是网络问题或防火墙阻止）${NC}"
        echo "自动配置Docker镜像加速器（使用国内镜像源）..."
        
        # 创建或更新daemon.json
        sudo mkdir -p /etc/docker
        
        # 备份现有配置
        if [ -f /etc/docker/daemon.json ]; then
            sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.bak.$(date +%Y%m%d_%H%M%S)
        fi
        
        # 读取现有配置（如果有）
        EXISTING_CONFIG="{}"
        if [ -f /etc/docker/daemon.json ]; then
            EXISTING_CONFIG=$(sudo cat /etc/docker/daemon.json 2>/dev/null || echo "{}")
        fi
        
        # 配置镜像加速器（使用国内镜像源）
        # 合并现有配置，只添加registry-mirrors
        sudo python3 <<EOF 2>/dev/null || sudo tee /etc/docker/daemon.json > /dev/null <<'JSONEOF'
import json
import sys

try:
    with open('/etc/docker/daemon.json', 'r') as f:
        config = json.load(f)
except:
    config = {}

config['registry-mirrors'] = [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
]

# 保留其他配置
if 'exec-opts' not in config:
    config['exec-opts'] = ["native.cgroupdriver=systemd"]
if 'log-driver' not in config:
    config['log-driver'] = "json-file"
if 'log-opts' not in config:
    config['log-opts'] = {"max-size": "100m"}
if 'storage-driver' not in config:
    config['storage-driver'] = "overlay2"

with open('/etc/docker/daemon.json', 'w') as f:
    json.dump(config, f, indent=2)
EOF
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
JSONEOF
        
        # 重启Docker服务
        echo "重启Docker服务以应用新配置..."
        sudo systemctl daemon-reload || true
        sudo systemctl restart docker || {
            echo -e "${RED}❌ Docker重启失败${NC}"
            # 恢复备份
            if ls /etc/docker/daemon.json.bak.* 1> /dev/null 2>&1; then
                LATEST_BACKUP=$(ls -t /etc/docker/daemon.json.bak.* | head -1)
                echo "恢复备份配置: $LATEST_BACKUP"
                sudo mv "$LATEST_BACKUP" /etc/docker/daemon.json
                sudo systemctl restart docker
            fi
            echo -e "${YELLOW}⚠️  Docker镜像加速器配置失败，将尝试继续部署${NC}"
            echo ""
            return 1
        }
        
        # 等待Docker启动
        echo "等待Docker服务启动..."
        sleep 5
        
        # 验证Docker是否正常运行
        if docker info &> /dev/null; then
            echo -e "${GREEN}✅ Docker镜像加速器配置完成，Docker服务正常运行${NC}"
            echo ""
            return 0
        else
            echo -e "${RED}❌ Docker服务异常，请检查配置${NC}"
            echo ""
            return 1
        fi
    fi
}

# 检查并配置防火墙
check_firewall() {
    echo -e "${BLUE}[0.5/12] 检查防火墙和网络连接...${NC}"
    
    FIREWALL_NEEDED=false
    
    # 检查443端口是否可访问（GitHub和Docker Hub都需要）
    echo "检查443端口（HTTPS）..."
    if ! timeout 3 bash -c "echo >/dev/tcp/github.com/443" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  端口443无法访问GitHub，可能被防火墙阻止${NC}"
        FIREWALL_NEEDED=true
    else
        echo -e "${GREEN}✅ 端口443可访问GitHub${NC}"
    fi
    
    # 检查Docker Hub连接
    echo "检查Docker Hub连接..."
    if ! timeout 5 curl -s --connect-timeout 3 https://registry-1.docker.io/v2/ > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Docker Hub连接失败（可能是网络问题或防火墙阻止443端口）${NC}"
        FIREWALL_NEEDED=true
    else
        echo -e "${GREEN}✅ Docker Hub连接正常${NC}"
    fi
    
    # 如果需要配置防火墙
    if [ "$FIREWALL_NEEDED" = true ]; then
        echo ""
        echo -e "${YELLOW}检测到网络连接问题，建议配置防火墙开放端口${NC}"
        echo "需要开放的端口: 22 (SSH), 80 (HTTP), 443 (HTTPS), 3000 (Web UI), 8001-8004 (Services)"
        
        if [ -f "$(cd "$SCRIPT_DIR" && pwd)/configure-firewall.sh" ]; then
            FIREWALL_SCRIPT="$(cd "$SCRIPT_DIR" && pwd)/configure-firewall.sh"
        elif [ -f "scripts/deployment/configure-firewall.sh" ]; then
            FIREWALL_SCRIPT="scripts/deployment/configure-firewall.sh"
        elif [ -f "$PROJECT_DIR/scripts/deployment/configure-firewall.sh" ]; then
            FIREWALL_SCRIPT="$PROJECT_DIR/scripts/deployment/configure-firewall.sh"
        fi
        
        if [ -n "$FIREWALL_SCRIPT" ] && [ -f "$FIREWALL_SCRIPT" ]; then
            read -p "是否自动配置防火墙开放端口? (Y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                echo "配置防火墙..."
                sudo bash "$FIREWALL_SCRIPT" || {
                    echo -e "${YELLOW}⚠️  防火墙配置失败，请手动配置${NC}"
                    echo "手动配置命令: sudo bash scripts/deployment/configure-firewall.sh"
                }
            else
                echo -e "${YELLOW}⚠️  跳过防火墙配置${NC}"
                echo "如果Docker镜像拉取失败，请手动运行: sudo bash scripts/deployment/configure-firewall.sh"
            fi
        else
            echo -e "${YELLOW}⚠️  防火墙配置脚本不存在${NC}"
            echo "请手动配置防火墙或检查脚本路径"
        fi
    fi
    echo ""
}

# 检查Docker
check_docker() {
    echo -e "${BLUE}[1/12] 检查Docker环境...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker未安装${NC}"
        echo "安装命令: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    
    # 检查Docker Compose（支持新版本插件和旧版本独立命令）
    DOCKER_COMPOSE_CMD=""
    if docker compose version &> /dev/null; then
        # 新版本Docker Compose插件
        DOCKER_COMPOSE_CMD="docker compose"
        echo -e "${GREEN}✅ 检测到Docker Compose插件（新版本）${NC}"
    elif command -v docker-compose &> /dev/null; then
        # 旧版本独立命令
        DOCKER_COMPOSE_CMD="docker-compose"
        echo -e "${GREEN}✅ 检测到docker-compose命令（旧版本）${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker Compose未安装，尝试安装...${NC}"
        
        # 尝试安装Docker Compose插件（新版本方式）
        if docker plugin ls &> /dev/null; then
            echo "安装Docker Compose插件..."
            # 对于新版本Docker，通常已经包含compose插件
            # 如果没有，需要安装docker-compose-plugin包
            if [ -f /etc/debian_version ]; then
                sudo apt-get update
                sudo apt-get install -y docker-compose-plugin || {
                    echo -e "${YELLOW}⚠️  插件安装失败，尝试安装独立版本...${NC}"
                }
            fi
        fi
        
        # 如果插件方式失败，安装独立版本
        if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
            echo "安装Docker Compose独立版本..."
            DOCKER_COMPOSE_VERSION="v2.24.0"
            
            # 尝试从GitHub下载
            if sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose 2>/dev/null; then
                sudo chmod +x /usr/local/bin/docker-compose
                DOCKER_COMPOSE_CMD="docker-compose"
                echo -e "${GREEN}✅ Docker Compose安装成功${NC}"
            else
                # 尝试使用镜像源
                echo "使用镜像源下载..."
                if sudo curl -L "https://get.daocloud.io/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose 2>/dev/null; then
                    sudo chmod +x /usr/local/bin/docker-compose
                    DOCKER_COMPOSE_CMD="docker-compose"
                    echo -e "${GREEN}✅ Docker Compose安装成功${NC}"
                else
                    echo -e "${RED}❌ Docker Compose安装失败${NC}"
                    echo "请手动安装: sudo apt-get install docker-compose-plugin"
                    exit 1
                fi
            fi
        else
            # 重新检测
            if docker compose version &> /dev/null; then
                DOCKER_COMPOSE_CMD="docker compose"
            elif command -v docker-compose &> /dev/null; then
                DOCKER_COMPOSE_CMD="docker-compose"
            fi
        fi
    fi
    
    # 检查Docker服务是否运行
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker服务未运行${NC}"
        echo "启动命令: sudo systemctl start docker"
        exit 1
    fi
    
    # 导出DOCKER_COMPOSE_CMD供后续使用
    export DOCKER_COMPOSE_CMD
    
    echo -e "${GREEN}✅ Docker环境检查通过${NC}"
    echo "   Docker版本: $(docker --version)"
    if [ "$DOCKER_COMPOSE_CMD" = "docker compose" ]; then
        echo "   Docker Compose版本: $(docker compose version)"
    else
        echo "   Docker Compose版本: $(docker-compose --version)"
    fi
}

# URL编码函数（处理用户名中的特殊字符）
urlencode() {
    local string="${1}"
    local strlen=${#string}
    local encoded=""
    local pos c o

    for (( pos=0 ; pos<strlen ; pos++ )); do
        c=${string:$pos:1}
        case "$c" in
            [-_.~a-zA-Z0-9] ) o="${c}" ;;
            * ) printf -v o '%%%02x' "'$c"
        esac
        encoded+="${o}"
    done
    echo "${encoded}"
}

# 配置Git认证
configure_git_auth() {
    # GitHub从2021年8月13日开始不再支持密码认证，必须使用Personal Access Token
    if [ -n "$GIT_USERNAME" ] && [ -n "$GIT_TOKEN" ]; then
        # 从URL中提取域名（处理github.com）
        GIT_DOMAIN=$(echo "$GIT_URL" | sed -E 's|https?://([^/]+).*|\1|')
        
        # 配置Git凭据（使用credential helper）
        git config --global credential.helper store
        
        # URL编码用户名（处理@等特殊字符）
        GIT_USERNAME_ENCODED=$(urlencode "$GIT_USERNAME")
        
        # 清理旧的凭据文件中的该域名记录
        if [ -f ~/.git-credentials ]; then
            # 移除旧的凭据（如果存在）
            grep -v "${GIT_DOMAIN}" ~/.git-credentials > ~/.git-credentials.tmp 2>/dev/null || true
            if [ -f ~/.git-credentials.tmp ]; then
                mv ~/.git-credentials.tmp ~/.git-credentials
            fi
        fi
        
        # 添加新的凭据（使用Token而不是密码）
        # 格式: https://username:token@github.com
        # 注意：凭据文件中使用原始用户名（Git会自动处理）
        echo "https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_DOMAIN}" >> ~/.git-credentials
        chmod 600 ~/.git-credentials
        
        # 构建带认证信息的Git URL（使用Token）
        # 注意：URL中用户名中的@需要URL编码
        # 格式: https://username%40example.com:token@github.com/...
        GIT_AUTH_URL=$(echo "$GIT_URL" | sed -E "s|https?://|https://${GIT_USERNAME_ENCODED}:${GIT_TOKEN}@|")
        
        echo -e "${GREEN}✅ Git认证配置完成（使用Personal Access Token）${NC}"
    elif [ -n "$GIT_USERNAME" ] && [ -z "$GIT_TOKEN" ]; then
        echo -e "${YELLOW}⚠️  Git Token未提供${NC}"
        echo -e "${YELLOW}⚠️  GitHub不再支持密码认证，请使用Personal Access Token${NC}"
        echo -e "${YELLOW}⚠️  创建Token: https://github.com/settings/tokens${NC}"
        GIT_AUTH_URL="$GIT_URL"
    else
        GIT_AUTH_URL="$GIT_URL"
    fi
}

# 准备项目目录
prepare_project() {
    echo ""
    echo -e "${BLUE}[2/12] 准备项目目录...${NC}"
    
    # 配置Git认证
    configure_git_auth
    
    # 如果是首次部署，从Git克隆
    if [ -n "$GIT_URL" ] && [ ! -d "$PROJECT_DIR" ]; then
        echo "首次部署，从Git克隆代码..."
        sudo mkdir -p "$(dirname "$PROJECT_DIR")"
        
        # 使用带认证信息的URL克隆
        if [ -n "$GIT_USERNAME" ] && [ -n "$GIT_TOKEN" ]; then
            # 使用Personal Access Token进行认证
            echo "使用Personal Access Token进行认证..."
            
            # 方法1: 使用Git凭据存储（推荐，最可靠）
            # 配置Git使用凭据存储（同时配置当前用户和root）
            git config --global credential.helper store
            sudo git config --global credential.helper store
            
            # 确保凭据文件存在并包含正确的凭据
            GIT_DOMAIN=$(echo "$GIT_URL" | sed -E 's|https?://([^/]+).*|\1|')
            CREDENTIAL_LINE="https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_DOMAIN}"
            
            # 为当前用户配置凭据
            if [ -f ~/.git-credentials ]; then
                grep -v "${GIT_DOMAIN}" ~/.git-credentials > /tmp/git-credentials-user.tmp 2>/dev/null || true
                if [ -f /tmp/git-credentials-user.tmp ]; then
                    mv /tmp/git-credentials-user.tmp ~/.git-credentials
                fi
            fi
            echo "$CREDENTIAL_LINE" >> ~/.git-credentials
            chmod 600 ~/.git-credentials
            
            # 为root用户配置凭据（因为sudo git clone会使用root的凭据）
            if [ -f /root/.git-credentials ]; then
                sudo grep -v "${GIT_DOMAIN}" /root/.git-credentials > /tmp/git-credentials-root.tmp 2>/dev/null || true
                if [ -f /tmp/git-credentials-root.tmp ]; then
                    sudo mv /tmp/git-credentials-root.tmp /root/.git-credentials
                fi
            fi
            echo "$CREDENTIAL_LINE" | sudo tee -a /root/.git-credentials > /dev/null
            sudo chmod 600 /root/.git-credentials
            
            # 使用普通URL，Git会自动从凭据存储中获取认证信息
            echo "使用Git凭据存储进行克隆..."
            sudo git clone -b "$BRANCH" "$GIT_URL" "$PROJECT_DIR" || {
                echo -e "${YELLOW}⚠️  凭据存储方式失败，尝试直接使用Token URL...${NC}"
                
                # 方法2: 使用URL编码的认证URL（备选方案）
                # 将用户名中的@编码为%40
                GIT_USERNAME_ENCODED=$(echo "$GIT_USERNAME" | sed 's/@/%40/g')
                GIT_TOKEN_URL="https://${GIT_USERNAME_ENCODED}:${GIT_TOKEN}@github.com/PMLiuyubin/enterprise-ai-platform.git"
                
                sudo git clone -b "$BRANCH" "$GIT_TOKEN_URL" "$PROJECT_DIR" || {
                    echo -e "${RED}❌ Git克隆失败${NC}"
                    echo -e "${RED}请检查：${NC}"
                    echo "  1. Git Token是否正确（已配置）"
                    echo "  2. Token是否有仓库访问权限"
                    echo "  3. 网络连接是否正常（特别是443端口）"
                    echo "  4. 用户名是否正确: $GIT_USERNAME"
                    echo ""
                    echo "调试信息:"
                    echo "  Git URL: $GIT_URL"
                    echo "  Git Domain: $GIT_DOMAIN"
                    echo "  凭据行: https://USERNAME:TOKEN@${GIT_DOMAIN}"
                    echo ""
                    echo "手动测试:"
                    echo "  git ls-remote $GIT_URL"
                    exit 1
                }
            }
        else
            echo -e "${YELLOW}⚠️  未配置Git Token，尝试交互式认证...${NC}"
            sudo git clone -b "$BRANCH" "$GIT_URL" "$PROJECT_DIR" || {
                echo -e "${RED}❌ Git克隆失败${NC}"
                echo -e "${RED}请配置Git Personal Access Token:${NC}"
                echo ""
                echo "📝 创建Token步骤:"
                echo "  1. 访问: https://github.com/settings/tokens/new"
                echo "  2. 点击 'Generate new token (classic)'"
                echo "  3. Note填写: enterprise-ai-platform"
                echo "  4. 勾选权限: ✅ repo"
                echo "  5. 点击 'Generate token'"
                echo "  6. 复制Token（格式: ghp_xxxxxxxxxxxx）"
                echo ""
                echo "💡 使用Token:"
                echo "  方式1: export GIT_TOKEN=ghp_your_token_here"
                echo "  方式2: --git-token ghp_your_token_here"
                echo ""
                echo "📖 详细说明: scripts/deployment/GIT_TOKEN_SETUP.md"
                exit 1
            }
        fi
        
        sudo chown -R $USER:$USER "$PROJECT_DIR"
        echo -e "${GREEN}✅ 代码克隆完成${NC}"
    elif [ ! -d "$PROJECT_DIR" ]; then
        echo -e "${RED}❌ 项目目录不存在且未提供Git地址${NC}"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # 如果项目目录存在，更新代码
    if [ -d ".git" ]; then
        echo "更新代码..."
        
        # 配置当前仓库的认证（如果需要）
        if [ -n "$GIT_USERNAME" ] && [ -n "$GIT_TOKEN" ]; then
            # 获取远程URL的域名部分
            GIT_DOMAIN=$(git remote get-url origin 2>/dev/null | sed -E 's|https?://([^@/]+).*|\1|' | sed 's|@.*||')
            if [ -n "$GIT_DOMAIN" ]; then
                git config credential.helper store
                # 清理旧凭据
                if [ -f ~/.git-credentials ]; then
                    grep -v "${GIT_DOMAIN}" ~/.git-credentials > ~/.git-credentials.tmp 2>/dev/null || true
                    if [ -f ~/.git-credentials.tmp ]; then
                        mv ~/.git-credentials.tmp ~/.git-credentials
                    fi
                fi
                # 添加凭据（Git会自动处理特殊字符）
                echo "https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_DOMAIN}" >> ~/.git-credentials
                chmod 600 ~/.git-credentials
                echo -e "${GREEN}✅ Git凭据已配置${NC}"
            fi
        fi
        
        git fetch origin || {
            echo -e "${YELLOW}⚠️  Git fetch失败，使用本地代码${NC}"
        }
        git checkout "$BRANCH" || {
            echo -e "${YELLOW}⚠️  分支 $BRANCH 不存在，使用当前分支${NC}"
        }
        git pull origin "$BRANCH" || {
            echo -e "${YELLOW}⚠️  Git pull失败，使用本地代码${NC}"
        }
        echo -e "${GREEN}✅ 代码更新完成${NC}"
    elif [ -z "$GIT_URL" ]; then
        # 如果目录不存在且没有指定Git URL，使用默认的Git URL
        if [ ! -d "$PROJECT_DIR" ]; then
            echo "项目目录不存在，使用默认Git仓库克隆..."
            GIT_URL="https://github.com/PMLiuyubin/enterprise-ai-platform.git"
            configure_git_auth
            sudo mkdir -p "$(dirname "$PROJECT_DIR")"
            
            if [ -n "$GIT_USERNAME" ] && [ -n "$GIT_TOKEN" ]; then
                # 配置Git凭据
                git config --global credential.helper store
                GIT_DOMAIN=$(echo "$GIT_URL" | sed -E 's|https?://([^/]+).*|\1|')
                echo "https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_DOMAIN}" >> ~/.git-credentials
                chmod 600 ~/.git-credentials
                
                # 使用普通URL，Git会自动使用凭据
                sudo git clone -b "$BRANCH" "$GIT_URL" "$PROJECT_DIR" || {
                    echo -e "${YELLOW}⚠️  使用凭据存储失败，尝试URL编码方式...${NC}"
                    sudo git clone -b "$BRANCH" "$GIT_AUTH_URL" "$PROJECT_DIR" || {
                        sudo git clone -b "$BRANCH" "$GIT_URL" "$PROJECT_DIR"
                    }
                }
            else
                sudo git clone -b "$BRANCH" "$GIT_URL" "$PROJECT_DIR"
            fi
            
            sudo chown -R $USER:$USER "$PROJECT_DIR"
            echo -e "${GREEN}✅ 代码克隆完成${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  不是Git仓库，使用现有代码${NC}"
    fi
}

# 检查环境变量
check_env() {
    echo ""
    echo -e "${BLUE}[3/12] 检查环境变量配置...${NC}"
    
    ENV_FILE=".env.${ENV}"
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "env.example" ]; then
            echo "从 env.example 创建 $ENV_FILE..."
            cp env.example "$ENV_FILE"
            echo -e "${YELLOW}⚠️  请编辑 $ENV_FILE 并配置必要的环境变量${NC}"
            echo "必需的环境变量："
            echo "  - DATABASE_URL"
            echo "  - REDIS_HOST"
            echo "  - JWT_SECRET_KEY"
            echo "  - OPENAI_API_KEY"
            read -p "按Enter继续或Ctrl+C取消..."
        else
            echo -e "${RED}❌ 环境变量文件不存在${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✅ 环境变量文件检查完成${NC}"
}

# 备份数据
backup_data() {
    if [ "$SKIP_BACKUP" = false ]; then
        echo ""
        echo -e "${BLUE}[4/12] 备份数据...${NC}"
        
        if [ -f "scripts/backup/backup-all.sh" ]; then
            bash scripts/backup/backup-all.sh || {
                echo -e "${YELLOW}⚠️  备份失败，但继续部署${NC}"
            }
        else
            echo -e "${YELLOW}⚠️  备份脚本不存在，跳过备份${NC}"
        fi
    else
        echo ""
        echo -e "${YELLOW}[4/12] 跳过备份（--skip-backup）${NC}"
    fi
}

# 停止现有服务
stop_services() {
    echo ""
    echo -e "${BLUE}[5/12] 停止现有服务...${NC}"
    
    # 使用检测到的docker-compose命令
    COMPOSE_CMD="${DOCKER_COMPOSE_CMD:-docker compose}"
    
    # 停止生产服务
    if [ -f "docker-compose.${ENV}.yml" ]; then
        $COMPOSE_CMD -f docker-compose.${ENV}.yml down || true
    fi
    
    # 停止开发服务（如果存在）
    if [ -f "docker-compose.yml" ]; then
        $COMPOSE_CMD down || true
    fi
    
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

# 等待服务就绪
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://localhost:${port}/api/health" > /dev/null 2>&1; then
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    return 1
}

# 启动数据库服务
start_database() {
    echo ""
    echo -e "${BLUE}[6/12] 启动数据库服务...${NC}"
    
    COMPOSE_CMD="${DOCKER_COMPOSE_CMD:-docker compose}"
    
    if [ -f "docker-compose.db.yml" ]; then
        if [ "$OFFLINE_MODE" = true ]; then
            echo "离线模式: 跳过镜像拉取，使用本地镜像"
            echo "检查本地镜像..."
            docker images | head -10
        else
            echo "拉取数据库镜像..."
            
            # 先尝试拉取，如果失败则自动切换到国内镜像
            if ! timeout 60 $COMPOSE_CMD -f docker-compose.db.yml pull 2>&1 | tee /tmp/docker-pull.log; then
            echo -e "${YELLOW}⚠️  镜像拉取失败，尝试切换到国内镜像源...${NC}"
            
            # 检查是否已经使用国内镜像
            if grep -q "registry.cn-hangzhou.aliyuncs.com" docker-compose.db.yml 2>/dev/null; then
                echo -e "${YELLOW}⚠️  已使用国内镜像，但拉取仍然失败${NC}"
            else
                # 自动切换到国内镜像
                if [ -f "scripts/deployment/use-china-mirrors.sh" ]; then
                    echo "自动切换到国内镜像源..."
                    bash scripts/deployment/use-china-mirrors.sh
                    echo "再次尝试拉取镜像..."
                    if ! timeout 60 $COMPOSE_CMD -f docker-compose.db.yml pull 2>&1; then
                        echo -e "${YELLOW}⚠️  使用国内镜像源仍失败${NC}"
                    else
                        echo -e "${GREEN}✅ 使用国内镜像源拉取成功${NC}"
                    fi
                else
                    echo -e "${YELLOW}⚠️  未找到镜像切换脚本，请手动运行: bash scripts/deployment/use-china-mirrors.sh${NC}"
                fi
            fi
            
            # 检查本地是否有镜像
            POSTGRES_IMAGE=$(grep -E "image:" docker-compose.db.yml | grep postgres | awk '{print $2}' | head -1)
            REDIS_IMAGE=$(grep -E "image:" docker-compose.db.yml | grep redis | awk '{print $2}' | head -1)
            
            if [ -n "$POSTGRES_IMAGE" ]; then
                IMAGE_NAME=$(echo $POSTGRES_IMAGE | cut -d: -f1)
                if docker images | grep -q "$IMAGE_NAME"; then
                    echo -e "${GREEN}✅ 找到本地PostgreSQL镜像: $POSTGRES_IMAGE${NC}"
                else
                    echo -e "${YELLOW}⚠️  未找到本地PostgreSQL镜像${NC}"
                fi
            fi
            
            if [ -n "$REDIS_IMAGE" ]; then
                IMAGE_NAME=$(echo $REDIS_IMAGE | cut -d: -f1)
                if docker images | grep -q "$IMAGE_NAME"; then
                    echo -e "${GREEN}✅ 找到本地Redis镜像: $REDIS_IMAGE${NC}"
                else
                    echo -e "${YELLOW}⚠️  未找到本地Redis镜像${NC}"
                fi
            fi
            
            echo ""
            echo -e "${YELLOW}提示：${NC}"
            echo "  如果镜像拉取仍然失败，请："
            echo "  1. 检查云服务器安全组（开放443端口）"
            echo "  2. 运行诊断: sudo bash scripts/deployment/diagnose-docker-network.sh"
            echo "  3. 手动切换镜像: sudo bash scripts/deployment/use-china-mirrors.sh"
            echo ""
            else
                echo -e "${GREEN}✅ 镜像拉取成功${NC}"
            fi
        fi
        
        echo "启动数据库服务..."
        if ! $COMPOSE_CMD -f docker-compose.db.yml up -d 2>&1; then
            echo ""
            echo -e "${RED}❌ 数据库服务启动失败${NC}"
            echo ""
            echo "可能原因和解决方案:"
            echo "  1. 镜像不存在: 手动拉取镜像"
            echo "     docker pull postgres:15"
            echo "     docker pull redis:7"
            echo "     docker pull rediscommander/redis-commander:latest"
            echo ""
            echo "  2. 检查Docker镜像加速器:"
            echo "     cat /etc/docker/daemon.json"
            echo "     sudo systemctl restart docker"
            echo ""
            echo "  3. 查看详细错误:"
            echo "     $COMPOSE_CMD -f docker-compose.db.yml logs"
            echo ""
            echo "  4. 如果使用云服务器，检查安全组设置（开放443端口）"
            echo ""
            exit 1
        fi
        
        echo "等待数据库就绪..."
        sleep 5
        
        # 检查PostgreSQL
        if $COMPOSE_CMD -f docker-compose.db.yml ps | grep -q postgres; then
            echo -e "${GREEN}✅ PostgreSQL已启动${NC}"
        else
            echo -e "${YELLOW}⚠️  PostgreSQL启动检查失败，请查看日志: $COMPOSE_CMD -f docker-compose.db.yml logs postgres${NC}"
        fi
        
        # 检查Redis
        if $COMPOSE_CMD -f docker-compose.db.yml ps | grep -q redis; then
            echo -e "${GREEN}✅ Redis已启动${NC}"
        else
            echo -e "${YELLOW}⚠️  Redis启动检查失败，请查看日志: $COMPOSE_CMD -f docker-compose.db.yml logs redis${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  数据库配置文件不存在，假设使用外部数据库${NC}"
    fi
}

# 构建镜像
build_images() {
    echo ""
    echo -e "${BLUE}[7/12] 构建Docker镜像...${NC}"
    
    COMPOSE_CMD="${DOCKER_COMPOSE_CMD:-docker compose}"
    COMPOSE_FILE="docker-compose.${ENV}.yml"
    if [ ! -f "$COMPOSE_FILE" ]; then
        COMPOSE_FILE="docker-compose.yml"
    fi
    
    if [ "$OFFLINE_MODE" = true ]; then
        echo "离线模式: 跳过镜像拉取，直接构建..."
    else
        echo "拉取基础镜像..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" pull || {
            echo -e "${YELLOW}⚠️  部分镜像拉取失败，将使用本地镜像或重新构建${NC}"
        }
    fi
    
    echo "构建应用镜像..."
    if [ "$FORCE_BUILD" = true ]; then
        $COMPOSE_CMD -f "$COMPOSE_FILE" build --no-cache || {
            echo -e "${RED}❌ 镜像构建失败${NC}"
            echo "可能原因:"
            echo "  1. Docker Hub连接超时（需要配置镜像加速器）"
            echo "  2. 网络连接问题"
            echo "  3. Dockerfile配置错误"
            echo ""
            echo "解决方案:"
            echo "  1. 运行: sudo bash scripts/deployment/configure-firewall.sh"
            echo "  2. 配置Docker镜像加速器（已在脚本开始处自动配置）"
            exit 1
        }
    else
        $COMPOSE_CMD -f "$COMPOSE_FILE" build || {
            echo -e "${RED}❌ 镜像构建失败${NC}"
            echo "尝试使用 --force 参数重新构建: bash deploy-server.sh --force"
            exit 1
        }
    fi
    
    echo -e "${GREEN}✅ 镜像构建完成${NC}"
}

# 按顺序启动服务
start_services() {
    echo ""
    echo -e "${BLUE}[8/12] 按顺序启动服务...${NC}"
    
    COMPOSE_CMD="${DOCKER_COMPOSE_CMD:-docker compose}"
    COMPOSE_FILE="docker-compose.${ENV}.yml"
    if [ ! -f "$COMPOSE_FILE" ]; then
        COMPOSE_FILE="docker-compose.yml"
    fi
    
    # 步骤1: 启动Redis（如果使用内部Redis）
    echo "步骤1: 启动Redis..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d redis || {
        echo -e "${YELLOW}⚠️  Redis启动失败（可能使用外部Redis）${NC}"
    }
    sleep 3
    
    # 步骤2: 启动MCP Gateway（基础服务）
    echo "步骤2: 启动MCP Gateway..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d mcp-gateway
    echo "等待MCP Gateway就绪..."
    if wait_for_service "MCP Gateway" "8001"; then
        echo -e "${GREEN}✅ MCP Gateway已就绪${NC}"
    else
        echo -e "${YELLOW}⚠️  MCP Gateway启动中...${NC}"
    fi
    sleep 3
    
    # 步骤3: 启动Auth Service
    echo "步骤3: 启动Auth Service..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d auth-service
    echo "等待Auth Service就绪..."
    if wait_for_service "Auth Service" "8003"; then
        echo -e "${GREEN}✅ Auth Service已就绪${NC}"
    else
        echo -e "${YELLOW}⚠️  Auth Service启动中...${NC}"
    fi
    sleep 3
    
    # 步骤4: 启动Knowledge Base
    echo "步骤4: 启动Knowledge Base..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d knowledge-base
    echo "等待Knowledge Base就绪..."
    if wait_for_service "Knowledge Base" "8004"; then
        echo -e "${GREEN}✅ Knowledge Base已就绪${NC}"
    else
        echo -e "${YELLOW}⚠️  Knowledge Base启动中...${NC}"
    fi
    sleep 3
    
    # 步骤5: 启动Workflow Engine（依赖MCP Gateway）
    echo "步骤5: 启动Workflow Engine..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d workflow-engine
    echo "等待Workflow Engine就绪..."
    if wait_for_service "Workflow Engine" "8002"; then
        echo -e "${GREEN}✅ Workflow Engine已就绪${NC}"
    else
        echo -e "${YELLOW}⚠️  Workflow Engine启动中...${NC}"
    fi
    sleep 3
    
    # 步骤6: 启动Web UI（最后启动，依赖所有后端服务）
    echo "步骤6: 启动Web UI..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d web-ui
    echo "等待Web UI就绪..."
    sleep 5
    
    echo -e "${GREEN}✅ 所有服务启动完成${NC}"
}

# 运行数据库迁移
run_migration() {
    if [ "$SKIP_MIGRATION" = false ]; then
        echo ""
        echo -e "${BLUE}[9/12] 运行数据库迁移...${NC}"
        
        COMPOSE_CMD="${DOCKER_COMPOSE_CMD:-docker compose}"
        COMPOSE_FILE="docker-compose.${ENV}.yml"
        if [ ! -f "$COMPOSE_FILE" ]; then
            COMPOSE_FILE="docker-compose.yml"
        fi
        
        services=("mcp-gateway" "workflow-engine" "auth-service" "knowledge-base")
        for service in "${services[@]}"; do
            echo "迁移 $service..."
            if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T $service alembic upgrade head 2>/dev/null; then
                echo -e "${GREEN}✅ $service 迁移完成${NC}"
            else
                echo -e "${YELLOW}⚠️  $service 迁移失败或不需要迁移${NC}"
            fi
        done
    else
        echo ""
        echo -e "${YELLOW}[9/12] 跳过数据库迁移（--skip-migration）${NC}"
    fi
}

# 验证部署
verify_deployment() {
    echo ""
    echo -e "${BLUE}[10/12] 验证部署...${NC}"
    
    if [ "$SKIP_TESTS" = false ] && [ -f "scripts/test-deployment.sh" ]; then
        bash scripts/test-deployment.sh || {
            echo -e "${YELLOW}⚠️  测试失败，请检查服务状态${NC}"
        }
    else
        echo "执行基本健康检查..."
        services=("8001:MCP Gateway" "8002:Workflow Engine" "8003:Auth Service" "8004:Knowledge Base" "3000:Web UI")
        for service_info in "${services[@]}"; do
            port=$(echo $service_info | cut -d: -f1)
            name=$(echo $service_info | cut -d: -f2)
            if curl -f -s "http://localhost:${port}/api/health" > /dev/null 2>&1; then
                echo -e "${GREEN}✅ $name (端口 $port) 健康${NC}"
            else
                echo -e "${YELLOW}⚠️  $name (端口 $port) 未响应${NC}"
            fi
        done
    fi
}

# 显示服务状态
show_status() {
    echo ""
    echo -e "${BLUE}[11/12] 服务状态...${NC}"
    
    COMPOSE_CMD="${DOCKER_COMPOSE_CMD:-docker compose}"
    COMPOSE_FILE="docker-compose.${ENV}.yml"
    if [ ! -f "$COMPOSE_FILE" ]; then
        COMPOSE_FILE="docker-compose.yml"
    fi
    
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps
}

# 显示部署信息
show_info() {
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✅ 部署完成！"
    echo "==========================================${NC}"
    echo ""
    echo "服务地址:"
    echo "  - MCP Gateway:      http://localhost:8001"
    echo "  - Workflow Engine:   http://localhost:8002"
    echo "  - Auth Service:      http://localhost:8003"
    echo "  - Knowledge Base:    http://localhost:8004"
    echo "  - Web UI:            http://localhost:3000"
    echo ""
    COMPOSE_CMD="${DOCKER_COMPOSE_CMD:-docker compose}"
    echo "常用命令:"
    echo "  查看日志:   $COMPOSE_CMD -f docker-compose.${ENV}.yml logs -f"
    echo "  查看状态:   $COMPOSE_CMD -f docker-compose.${ENV}.yml ps"
    echo "  停止服务:   $COMPOSE_CMD -f docker-compose.${ENV}.yml down"
    echo "  重启服务:   $COMPOSE_CMD -f docker-compose.${ENV}.yml restart"
    echo ""
    echo "自动化调试系统:"
    echo "  - 决策面板: http://localhost:3000/admin/auto-debug/decision-panel"
    echo "  - API健康:  http://localhost:8001/api/health"
    echo ""
}

# 主执行流程
main() {
    configure_docker_mirror
    check_firewall
    check_docker
    prepare_project
    check_env
    backup_data
    stop_services
    start_database
    build_images
    start_services
    run_migration
    verify_deployment
    show_status
    show_info
}

# 执行主函数
main

