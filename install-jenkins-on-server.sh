#!/bin/bash
# 在服务器 1.117.62.202 上安装Jenkins

set -e

echo "========================================"
echo "Jenkins安装脚本"
echo "========================================"
echo ""

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  需要sudo权限，将使用sudo执行"
    SUDO="sudo"
else
    SUDO=""
fi

echo "[1/5] 更新系统包..."
$SUDO apt-get update

echo ""
echo "[2/5] 安装Java 17..."
$SUDO apt-get install -y openjdk-17-jdk
java -version

echo ""
echo "[3/5] 安装Jenkins..."
# 添加Jenkins仓库密钥
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | $SUDO tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null

# 添加Jenkins仓库
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/ | $SUDO tee /etc/apt/sources.list.d/jenkins.list > /dev/null

# 更新并安装
$SUDO apt-get update
$SUDO apt-get install -y jenkins

echo ""
echo "[4/5] 启动Jenkins服务..."
$SUDO systemctl start jenkins
$SUDO systemctl enable jenkins

# 等待Jenkins启动
echo "等待Jenkins启动..."
sleep 10

# 检查状态
$SUDO systemctl status jenkins --no-pager | head -10

echo ""
echo "[5/5] 配置防火墙..."
# 开放8080端口
$SUDO ufw allow 8080/tcp 2>&1 || echo "防火墙未启用或已配置"

echo ""
echo "========================================"
echo "✅ Jenkins安装完成！"
echo "========================================"
echo ""
echo "Jenkins初始管理员密码:"
$SUDO cat /var/lib/jenkins/secrets/initialAdminPassword
echo ""
echo "Jenkins访问地址:"
PUBLIC_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip)
echo "  http://$PUBLIC_IP:8080"
echo "  或"
echo "  http://1.117.62.202:8080"
echo ""
echo "下一步操作:"
echo "1. 访问Jenkins Web界面"
echo "2. 使用上面的初始密码登录"
echo "3. 安装推荐插件"
echo "4. 创建管理员账户"
echo ""

