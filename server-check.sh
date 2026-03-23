#!/bin/bash
# 服务器检查和Jenkins配置检查脚本
# 在服务器 1.117.62.202 上运行

echo "========================================"
echo "服务器系统检查"
echo "========================================"
echo ""

echo "=== 系统信息 ==="
uname -a
echo ""

echo "=== 操作系统版本 ==="
cat /etc/os-release | head -5
echo ""

echo "=== 内存和CPU ==="
free -h
echo "CPU核心数: $(nproc)"
echo ""

echo "=== 磁盘空间 ==="
df -h | head -6
echo ""

echo "=== Docker检查 ==="
if command -v docker &> /dev/null; then
    docker --version
    docker ps | head -5
else
    echo "❌ Docker未安装"
fi
echo ""

echo "=== Java检查 ==="
if command -v java &> /dev/null; then
    java -version 2>&1 | head -3
else
    echo "❌ Java未安装"
fi
echo ""

echo "=== Git检查 ==="
if command -v git &> /dev/null; then
    git --version
else
    echo "❌ Git未安装"
fi
echo ""

echo "=== Jenkins检查 ==="
if systemctl is-active --quiet jenkins 2>/dev/null; then
    echo "✅ Jenkins已安装并运行"
    systemctl status jenkins --no-pager | head -5
    echo ""
    echo "Jenkins初始密码:"
    sudo cat /var/lib/jenkins/secrets/initialAdminPassword 2>/dev/null || echo "密码文件不存在"
else
    echo "❌ Jenkins未安装或未运行"
    if command -v jenkins &> /dev/null; then
        echo "Jenkins已安装但未运行，尝试启动..."
        sudo systemctl start jenkins
        sudo systemctl enable jenkins
    fi
fi
echo ""

echo "=== 已安装的相关软件包 ==="
dpkg -l | grep -E 'jenkins|docker|java|git' | head -10
echo ""

echo "=== 网络连接测试 ==="
echo "测试连接到部署服务器 43.143.139.197:"
ping -c 2 43.143.139.197 2>&1 | head -5
echo ""

echo "=== 公网IP ==="
curl -s ifconfig.me || curl -s ipinfo.io/ip
echo ""
echo ""

echo "=== 开放端口检查 ==="
ss -tuln | grep -E ':(8080|443|80|22|50000)' | head -10
echo ""

echo "=== SSH密钥配置 ==="
if [ -d ~/.ssh ]; then
    echo "SSH目录存在"
    ls -la ~/.ssh/ | head -10
else
    echo "SSH目录不存在"
fi
echo ""

echo "========================================"
echo "检查完成！"
echo "========================================"

