#!/bin/bash
# 验证代码同步状态

echo "========================================"
echo "代码同步验证"
echo "========================================"
echo ""

echo "=== GitHub最新提交 ==="
git ls-remote https://github.com/PMLiuyubin/enterprise-ai-platform.git HEAD 2>&1 | head -1
echo ""

echo "=== 部署服务器代码状态 ==="
echo "服务器: 43.143.139.197"
echo "执行: ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197 'cd /opt/enterprise-ai-platform && git rev-parse --short HEAD && git log --oneline -1'"
echo ""

echo "=== Jenkins配置检查 ==="
echo "1. GitHub凭据是否配置: github-credentials"
echo "2. Pipeline任务是否配置Git凭据"
echo "3. Repository URL是否正确"
echo ""

echo "========================================"
echo "验证完成"
echo "========================================"

