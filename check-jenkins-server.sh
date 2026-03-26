#!/bin/bash
# 检查Jenkins服务器上安装的应用

echo "========================================"
echo "服务器应用检查"
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

echo "=== Docker信息 ==="
sudo docker --version 2>&1
echo ""
echo "运行中的容器:"
sudo docker ps 2>&1 | head -10
echo ""

echo "=== Docker Compose ==="
docker-compose --version 2>&1 || docker compose version 2>&1
echo ""

echo "=== Java ==="
java -version 2>&1 | head -3 || echo "Java未安装"
echo ""

echo "=== Git ==="
git --version 2>&1
echo ""

echo "=== Jenkins ==="
if systemctl is-active --quiet jenkins 2>/dev/null; then
    echo "✅ Jenkins正在运行"
    systemctl status jenkins --no-pager | head -5
else
    echo "❌ Jenkins未运行"
fi
dpkg -l | grep jenkins | head -3
echo ""

echo "=== 已安装的主要软件包 ==="
dpkg -l | grep -E 'docker|jenkins|java|git|nginx|apache|python|node' | head -20
echo ""

echo "=== 运行中的服务 ==="
systemctl list-units --type=service --state=running | grep -E 'docker|jenkins|nginx|apache' | head -10
echo ""

echo "=== 开放端口 ==="
sudo ss -tuln | grep -E ':(8080|443|80|22|50000|3000)' | head -10
echo ""

echo "=== /usr/bin目录下的Docker相关应用 ==="
ls -lah /usr/bin/docker* 2>&1
echo ""

echo "=== /usr/bin目录下的其他应用 ==="
ls -lah /usr/bin/ | grep -E 'jenkins|java|git|python|node' | head -10
echo ""

echo "========================================"
echo "检查完成"
echo "========================================"

