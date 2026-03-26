#!/bin/bash
# 在SonarQube中创建项目并生成Token的辅助脚本
# 需要先手动登录SonarQube创建项目，然后使用此脚本生成Token

set -e

SONARQUBE_URL="${SONARQUBE_URL:-http://124.220.181.231:9000}"
PROJECT_KEY="${PROJECT_KEY:-enterprise-ai-platform}"
PROJECT_NAME="${PROJECT_NAME:-Enterprise AI Platform}"

echo "=========================================="
echo "SonarQube 项目配置脚本"
echo "=========================================="
echo ""
echo "此脚本将帮助您配置SonarQube项目"
echo ""
echo "请先完成以下步骤："
echo "1. 访问 $SONARQUBE_URL"
echo "2. 使用 admin/admin 登录（首次登录需要修改密码）"
echo "3. 创建项目："
echo "   - Project Key: $PROJECT_KEY"
echo "   - Display Name: $PROJECT_NAME"
echo ""
read -p "已完成上述步骤？(y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "请先完成上述步骤后再运行此脚本"
    exit 1
fi

echo ""
echo "请输入SonarQube管理员用户名（默认: admin）:"
read -r SONAR_USER
SONAR_USER=${SONAR_USER:-admin}

echo "请输入SonarQube管理员密码:"
read -rs SONAR_PASSWORD

echo ""
echo "正在生成Token..."

# 使用SonarQube API生成Token
TOKEN_RESPONSE=$(curl -s -u "$SONAR_USER:$SONAR_PASSWORD" \
    -X POST \
    "$SONARQUBE_URL/api/user_tokens/generate" \
    -d "name=ci-token-$(date +%Y%m%d)" \
    -d "type=GLOBAL_ANALYSIS_TOKEN")

TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "错误: 无法生成Token，请检查用户名和密码"
    echo "响应: $TOKEN_RESPONSE"
    exit 1
fi

echo ""
echo "=========================================="
echo "Token生成成功！"
echo "=========================================="
echo ""
echo "项目信息:"
echo "  Project Key: $PROJECT_KEY"
echo "  Project Name: $PROJECT_NAME"
echo ""
echo "Token (请妥善保存，只显示一次):"
echo "  $TOKEN"
echo ""
echo "将此Token添加到以下位置:"
echo "1. GitHub Secrets: SONAR_TOKEN"
echo "2. Jenkins Credentials"
echo "3. 本地 sonar-project.properties: sonar.login=$TOKEN"
echo ""

# 保存Token到文件
TOKEN_FILE=".sonar-token"
echo "$TOKEN" > $TOKEN_FILE
chmod 600 $TOKEN_FILE
echo "Token已保存到 $TOKEN_FILE (请添加到.gitignore)"
echo ""

# 创建示例配置文件
cat > sonar-project.properties.example <<EOF
# SonarQube项目配置示例
# 复制此文件为 sonar-project.properties 并填写实际值

sonar.projectKey=$PROJECT_KEY
sonar.projectName=$PROJECT_NAME
sonar.projectVersion=1.0

# 源代码路径
sonar.sources=.
sonar.sourceEncoding=UTF-8

# 排除文件
sonar.exclusions=**/node_modules/**,**/dist/**,**/build/**,**/__pycache__/**,**/*.pyc,**/venv/**,**/env/**,**/.git/**,**/htmlcov/**,**/mypy-report/**,**/coverage/**,**/logs/**,**/backups/**,**/*.log

# 测试路径
sonar.tests=.
sonar.test.inclusions=**/test_*.py,**/tests/**,**/*_test.py

# Python配置
sonar.python.version=3.10,3.11

# 代码覆盖率报告路径
sonar.python.coverage.reportPaths=coverage.json,htmlcov/coverage.xml

# SonarQube服务器
sonar.host.url=$SONARQUBE_URL
sonar.login=YOUR_TOKEN_HERE
EOF

echo "已创建配置文件示例: sonar-project.properties.example"
echo ""

