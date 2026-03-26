#!/bin/bash
# GitHub Actions 自托管 Runner 自动安装脚本

set -e

REPO_URL="https://github.com/PMLiuyubin/enterprise-ai-platform"
RUNNER_DIR="/opt/actions-runner"
RUNNER_VERSION="2.311.0"
RUNNER_USER="${RUNNER_USER:-ubuntu}"

echo "=========================================="
echo "GitHub Actions 自托管 Runner 安装脚本"
echo "=========================================="
echo "仓库: $REPO_URL"
echo "安装目录: $RUNNER_DIR"
echo "Runner 版本: $RUNNER_VERSION"
echo ""

# 检查是否为 root 或 sudo
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  需要 root 权限，使用 sudo 运行"
    echo "使用方法: sudo $0"
    exit 1
fi

# 检查是否已安装
if [ -d "$RUNNER_DIR" ] && [ -f "$RUNNER_DIR/.runner" ]; then
    echo "⚠️  Runner 已安装"
    read -p "是否要重新配置? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    echo "停止现有服务..."
    cd "$RUNNER_DIR"
    ./svc.sh stop || true
    ./svc.sh uninstall || true
fi

# 创建目录
echo "[1/6] 创建安装目录..."
mkdir -p "$RUNNER_DIR"
chown "$RUNNER_USER:$RUNNER_USER" "$RUNNER_DIR"
cd "$RUNNER_DIR"

# 下载 Runner
echo ""
echo "[2/6] 下载 GitHub Actions Runner..."
RUNNER_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"

if [ -f "actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" ]; then
    echo "✅ 安装包已存在，跳过下载"
else
    echo "下载中..."
    curl -o "actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" -L "$RUNNER_URL"
    echo "✅ 下载完成"
fi

# 解压
echo ""
echo "[3/6] 解压安装包..."
tar xzf "./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
chown -R "$RUNNER_USER:$RUNNER_USER" "$RUNNER_DIR"
echo "✅ 解压完成"

# 安装依赖
echo ""
echo "[4/6] 安装依赖..."
if command -v docker &> /dev/null; then
    echo "✅ Docker 已安装"
else
    echo "安装 Docker..."
    apt-get update
    apt-get install -y docker.io
    systemctl start docker
    systemctl enable docker
fi

# 确保用户在 docker 组中
usermod -aG docker "$RUNNER_USER" || true

# 配置 Runner
echo ""
echo "[5/6] 配置 Runner..."
echo "=========================================="
echo "请从以下链接获取配置 Token:"
echo "https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners/new"
echo ""
echo "选择: Linux + x64"
echo "然后复制配置命令中的 token"
echo "=========================================="
echo ""
read -p "请输入配置 Token: " RUNNER_TOKEN

if [ -z "$RUNNER_TOKEN" ]; then
    echo "❌ Token 不能为空"
    exit 1
fi

# 使用指定用户运行配置
sudo -u "$RUNNER_USER" ./config.sh \
    --url "$REPO_URL" \
    --token "$RUNNER_TOKEN" \
    --name "server-$(hostname)" \
    --work "_work" \
    --replace

echo "✅ 配置完成"

# 安装为服务
echo ""
echo "[6/6] 安装为系统服务..."
./svc.sh install "$RUNNER_USER"
./svc.sh start

echo ""
echo "=========================================="
echo "✅ Runner 安装完成！"
echo "=========================================="
echo ""
echo "服务状态:"
./svc.sh status
echo ""
echo "下一步:"
echo "1. 在 GitHub 上验证 Runner 状态:"
echo "   https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners"
echo ""
echo "2. 修改工作流使用自托管 Runner:"
echo "   runs-on: self-hosted"
echo ""
echo "3. 测试工作流"
echo ""

