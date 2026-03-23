#!/bin/bash
# 配置Jenkins自动化部署
# 部署到: 43.143.139.197 (应用服务器) 和 43.143.90.179 (图数据库服务器)

set -e

echo "========================================"
echo "Jenkins自动化部署配置"
echo "========================================"
echo ""

JENKINS_HOME="/var/lib/jenkins"
DEPLOY_KEY_SOURCE="/home/ubuntu/.ssh/enterprise_ai_platform.pem"
DEPLOY_KEY_TARGET="$JENKINS_HOME/.ssh/deploy_key"

# 检查是否为root或使用sudo
if [ "$EUID" -ne 0 ]; then 
    SUDO="sudo"
else
    SUDO=""
fi

echo "[1/4] 配置Jenkins SSH目录..."
$SUDO mkdir -p $JENKINS_HOME/.ssh
$SUDO chown jenkins:jenkins $JENKINS_HOME/.ssh
$SUDO chmod 700 $JENKINS_HOME/.ssh

echo "[2/4] 配置部署SSH密钥..."
if [ -f "$DEPLOY_KEY_SOURCE" ]; then
    echo "找到部署密钥，复制到Jenkins目录..."
    $SUDO cp $DEPLOY_KEY_SOURCE $DEPLOY_KEY_TARGET
    $SUDO chown jenkins:jenkins $DEPLOY_KEY_TARGET
    $SUDO chmod 600 $DEPLOY_KEY_TARGET
    echo "✅ 部署密钥已配置"
else
    echo "⚠️  未找到部署密钥: $DEPLOY_KEY_SOURCE"
    echo "请手动将部署密钥复制到: $DEPLOY_KEY_TARGET"
fi

echo ""
echo "[3/4] 测试SSH连接到部署服务器..."
echo "测试连接到应用服务器 43.143.139.197..."
$SUDO -u jenkins ssh -i $DEPLOY_KEY_TARGET -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@43.143.139.197 "echo '✅ 应用服务器连接成功' && hostname" 2>&1 || echo "❌ 应用服务器连接失败，请检查密钥"

echo ""
echo "测试连接到图数据库服务器 43.143.90.179..."
$SUDO -u jenkins ssh -i $DEPLOY_KEY_TARGET -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@43.143.90.179 "echo '✅ 图数据库服务器连接成功' && hostname" 2>&1 || echo "⚠️  图数据库服务器连接失败（可能需要不同的密钥或配置）"

echo ""
echo "[4/4] 创建Pipeline配置目录..."
$SUDO mkdir -p $JENKINS_HOME/jobs/enterprise-ai-platform-deploy
$SUDO chown -R jenkins:jenkins $JENKINS_HOME/jobs

echo ""
echo "========================================"
echo "✅ Jenkins部署配置完成！"
echo "========================================"
echo ""
echo "下一步操作："
echo "1. 访问Jenkins: http://1.117.62.202:8080"
echo "2. 使用初始密码登录"
echo "3. 安装推荐插件"
echo "4. 创建管理员账户"
echo "5. 在Jenkins Web界面配置SSH凭据"
echo "6. 创建Pipeline任务并配置部署脚本"
echo ""

