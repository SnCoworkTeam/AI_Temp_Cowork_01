#!/bin/bash
# Jenkins安装脚本

echo "=== 更新系统 ==="
sudo apt-get update

echo "=== 安装Java ==="
sudo apt-get install -y openjdk-17-jdk

echo "=== 安装Jenkins ==="
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/ | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt-get update
sudo apt-get install -y jenkins

echo "=== 启动Jenkins ==="
sudo systemctl start jenkins
sudo systemctl enable jenkins

echo "=== 检查Jenkins状态 ==="
sudo systemctl status jenkins --no-pager | head -10

echo "=== 获取初始密码 ==="
echo "Jenkins初始管理员密码:"
sudo cat /var/lib/jenkins/secrets/initialAdminPassword

echo ""
echo "=== 防火墙配置 ==="
echo "如果需要，请开放8080端口:"
echo "  sudo ufw allow 8080"
echo ""
echo "Jenkins访问地址: http://\101.230.216.150:8080"