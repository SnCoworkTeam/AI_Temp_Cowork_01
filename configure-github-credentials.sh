#!/bin/bash
# 配置Jenkins GitHub凭据的辅助脚本

echo "========================================"
echo "Jenkins GitHub凭据配置辅助"
echo "========================================"
echo ""

echo "当前Jenkins用户:"
whoami
echo ""

echo "Jenkins主目录:"
echo "/var/lib/jenkins"
echo ""

echo "检查Git配置:"
sudo -u jenkins git config --global --list 2>&1 | head -10
echo ""

echo "测试GitHub连接（HTTPS）:"
sudo -u jenkins git ls-remote https://github.com/PMLiuyubin/enterprise-ai-platform.git HEAD 2>&1
echo ""

echo "测试GitHub连接（SSH）:"
if [ -f /var/lib/jenkins/.ssh/id_ed25519.pub ]; then
    echo "SSH公钥:"
    sudo cat /var/lib/jenkins/.ssh/id_ed25519.pub
    echo ""
    echo "测试SSH连接:"
    sudo -u jenkins ssh -T git@github.com 2>&1 | head -5
else
    echo "未找到SSH密钥"
    echo ""
    echo "生成SSH密钥:"
    echo "sudo -u jenkins ssh-keygen -t ed25519 -C 'jenkins@1.117.62.202' -f /var/lib/jenkins/.ssh/id_ed25519 -N ''"
fi
echo ""

echo "========================================"
echo "配置说明"
echo "========================================"
echo ""
echo "方案1: 使用Personal Access Token（推荐）"
echo "1. 在GitHub创建Token: https://github.com/settings/tokens"
echo "2. 在Jenkins Web界面添加凭据:"
echo "   - Kind: Username with password"
echo "   - Username: 你的GitHub用户名"
echo "   - Password: Personal Access Token"
echo "   - ID: github-credentials"
echo ""
echo "方案2: 使用SSH密钥"
echo "1. 如果上面显示了SSH公钥，复制它"
echo "2. 添加到GitHub: https://github.com/settings/keys"
echo "3. 在Jenkins Web界面添加SSH凭据"
echo ""

