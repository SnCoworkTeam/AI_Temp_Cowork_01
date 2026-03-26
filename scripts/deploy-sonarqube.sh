#!/bin/bash
# 部署SonarQube到服务器的完整脚本
# 从本地Windows机器执行，通过SSH连接到服务器并安装SonarQube

set -e

# 服务器配置
SERVER_IP="124.220.181.231"
SERVER_USER="ubuntu"
SERVER_PASSWORD="Liu@bner1983"
SSH_KEY="E:\\enterprise-ai-platform\\SonarQube.pem"
REMOTE_SCRIPT="/tmp/install-sonarqube.sh"

echo "=========================================="
echo "部署SonarQube到服务器"
echo "=========================================="
echo ""
echo "服务器: $SERVER_USER@$SERVER_IP"
echo ""

# 检查SSH密钥文件
if [ ! -f "$SSH_KEY" ]; then
    echo "错误: SSH密钥文件不存在: $SSH_KEY"
    exit 1
fi

# 设置SSH密钥权限（Windows上可能不需要，但为了安全）
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows环境
    echo "检测到Windows环境"
    SSH_CMD="ssh -i \"$SSH_KEY\" -o StrictHostKeyChecking=no"
    SCP_CMD="scp -i \"$SSH_KEY\" -o StrictHostKeyChecking=no"
else
    # Linux/Mac环境
    chmod 600 "$SSH_KEY"
    SSH_CMD="ssh -i \"$SSH_KEY\" -o StrictHostKeyChecking=no"
    SCP_CMD="scp -i \"$SSH_KEY\" -o StrictHostKeyChecking=no"
fi

echo "[1/5] 测试SSH连接..."
if $SSH_CMD $SERVER_USER@$SERVER_IP "echo 'SSH连接成功'"; then
    echo "✓ SSH连接正常"
else
    echo "✗ SSH连接失败，请检查："
    echo "  1. 服务器IP是否正确"
    echo "  2. SSH密钥文件路径是否正确"
    echo "  3. 服务器是否允许SSH连接"
    exit 1
fi

echo ""
echo "[2/5] 上传安装脚本..."
$SCP_CMD scripts/install-sonarqube.sh $SERVER_USER@$SERVER_IP:$REMOTE_SCRIPT
echo "✓ 脚本已上传"

echo ""
echo "[3/5] 设置脚本执行权限..."
$SSH_CMD $SERVER_USER@$SERVER_IP "chmod +x $REMOTE_SCRIPT"
echo "✓ 权限已设置"

echo ""
echo "[4/5] 执行安装脚本..."
echo "注意: 安装过程可能需要10-15分钟，请耐心等待..."
echo ""

# 执行安装脚本（使用sudo）
$SSH_CMD $SERVER_USER@$SERVER_IP "sudo bash $REMOTE_SCRIPT"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ SonarQube安装完成"
else
    echo ""
    echo "✗ 安装过程中出现错误，请检查服务器日志"
    echo "查看日志: ssh -i \"$SSH_KEY\" $SERVER_USER@$SERVER_IP 'sudo journalctl -u sonarqube -n 50'"
    exit 1
fi

echo ""
echo "[5/5] 验证安装..."
sleep 10

# 检查服务状态
if $SSH_CMD $SERVER_USER@$SERVER_IP "sudo systemctl is-active sonarqube" | grep -q "active"; then
    echo "✓ SonarQube服务运行正常"
else
    echo "⚠ SonarQube服务可能未完全启动，请稍后检查"
fi

# 检查Web访问
if curl -s --connect-timeout 5 "http://$SERVER_IP:9000/api/system/status" | grep -q "UP"; then
    echo "✓ SonarQube Web界面可访问"
else
    echo "⚠ SonarQube Web界面可能尚未就绪，请稍后访问 http://$SERVER_IP:9000"
fi

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "访问地址: http://$SERVER_IP:9000"
echo "默认登录: admin / admin (首次登录后需要修改)"
echo ""
echo "后续步骤:"
echo "1. 访问 http://$SERVER_IP:9000 并登录"
echo "2. 修改admin密码"
echo "3. 创建项目并生成Token"
echo "4. 运行 scripts/setup-sonarqube-project.sh 配置项目"
echo "5. 参考 docs/sonarqube-integration.md 进行集成"
echo ""

