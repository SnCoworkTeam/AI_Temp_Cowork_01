#!/bin/bash
# GitHub Actions 自托管 Runner 安装脚本
# 使用方法: bash install-runner-on-server.sh YOUR_TOKEN_HERE

set -e

if [ -z "$1" ]; then
    echo "=========================================="
    echo "GitHub Actions Runner 安装脚本"
    echo "=========================================="
    echo ""
    echo "使用方法:"
    echo "  bash install-runner-on-server.sh YOUR_TOKEN_HERE"
    echo ""
    echo "获取 Token:"
    echo "  1. 访问: https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners/new"
    echo "  2. 选择: Linux + x64"
    echo "  3. 复制配置命令中的 token"
    echo ""
    exit 1
fi

RUNNER_VERSION="2.311.0"
REPO_URL="https://github.com/PMLiuyubin/enterprise-ai-platform"
RUNNER_TOKEN="$1"
RUNNER_DIR="/opt/actions-runner"
RUNNER_USER="ubuntu"

echo "=========================================="
echo "GitHub Actions Runner 安装"
echo "=========================================="
echo "仓库: $REPO_URL"
echo "版本: $RUNNER_VERSION"
echo "目录: $RUNNER_DIR"
echo ""

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
    sudo ./svc.sh stop || true
    sudo ./svc.sh uninstall || true
fi

# 创建目录
echo "[1/6] 创建安装目录..."
sudo mkdir -p "$RUNNER_DIR"
sudo chown "$RUNNER_USER:$RUNNER_USER" "$RUNNER_DIR"
cd "$RUNNER_DIR"

# 检查文件是否存在
RUNNER_FILE="actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
if [ -f "$RUNNER_FILE" ]; then
    echo "[2/6] 安装包已存在，跳过下载"
else
    echo "[2/6] 下载 Runner..."
    echo "下载地址:"
    echo "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_FILE}"
    echo ""
    echo "如果下载失败，请手动下载并上传到服务器:"
    echo "  scp ${RUNNER_FILE} ubuntu@43.143.139.197:/opt/actions-runner/"
    echo ""
    
    # 尝试下载
    if command -v wget &> /dev/null; then
        wget "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_FILE}" || {
            echo "❌ 下载失败，请手动下载并上传"
            exit 1
        }
    elif command -v curl &> /dev/null; then
        curl -L -o "$RUNNER_FILE" "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_FILE}" || {
            echo "❌ 下载失败，请手动下载并上传"
            exit 1
        }
    else
        echo "❌ 未找到 wget 或 curl，请手动下载"
        exit 1
    fi
    echo "✅ 下载完成"
fi

# 解压
echo ""
echo "[3/6] 解压安装包..."
if [ ! -d "bin" ]; then
    tar xzf "$RUNNER_FILE"
    sudo chown -R "$RUNNER_USER:$RUNNER_USER" "$RUNNER_DIR"
    echo "✅ 解压完成"
else
    echo "✅ 已解压"
fi

# 检查 Docker
echo ""
echo "[4/6] 检查依赖..."
if command -v docker &> /dev/null; then
    echo "✅ Docker 已安装"
    # 确保用户在 docker 组中
    sudo usermod -aG docker "$RUNNER_USER" || true
else
    echo "⚠️  Docker 未安装，Runner 可能无法正常工作"
fi

if command -v git &> /dev/null; then
    echo "✅ Git 已安装"
else
    echo "⚠️  Git 未安装"
fi

# 配置 Runner
echo ""
echo "[5/6] 配置 Runner..."
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
sudo ./svc.sh install "$RUNNER_USER"
sudo ./svc.sh start

echo ""
echo "=========================================="
echo "✅ Runner 安装完成！"
echo "=========================================="
echo ""
echo "服务状态:"
sudo ./svc.sh status
echo ""
echo "下一步:"
echo "1. 在 GitHub 上验证 Runner 状态:"
echo "   https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners"
echo ""
echo "2. 使用自托管 Runner 工作流:"
echo "   - deploy-self-hosted.yml"
echo ""

