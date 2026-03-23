#!/bin/bash
# 服务器初始化脚本（在服务器上运行）
# 使用方法: 在服务器上执行此脚本

set -e

echo "🔧 初始化服务器环境..."

# 创建必要的目录
mkdir -p ~/enterprise-ai-platform/images
mkdir -p ~/enterprise-ai-platform/logs
mkdir -p ~/enterprise-ai-platform/data

# 安装Docker（如果未安装）
if ! command -v docker &> /dev/null; then
    echo "📦 安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# 安装Docker Compose（如果未安装）
if ! command -v docker-compose &> /dev/null; then
    echo "📦 安装Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 创建docker-compose.test.yml（如果不存在）
if [ ! -f ~/enterprise-ai-platform/docker-compose.test.yml ]; then
    echo "📝 创建docker-compose.test.yml..."
    cat > ~/enterprise-ai-platform/docker-compose.test.yml << 'EOF'
# 从同步脚本自动生成
version: '3.8'
# 配置内容将由同步脚本更新
EOF
fi

echo "✅ 服务器环境初始化完成！"
echo "📝 请确保已配置SSH密钥访问"





































