#!/bin/bash
# SonarQube 安装和配置脚本
# 在服务器 124.220.181.231 上执行
# 使用方法: bash install-sonarqube.sh

set -e

echo "=========================================="
echo "SonarQube 安装和配置"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
SONARQUBE_VERSION="10.3.0.82913"
SONARQUBE_HOME="/opt/sonarqube"
SONARQUBE_USER="sonarqube"
SONARQUBE_DB_NAME="sonarqube"
SONARQUBE_DB_USER="sonarqube"
SONARQUBE_DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
SONARQUBE_PORT="9000"
SONARQUBE_WEB_URL="http://124.220.181.231:9000"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用sudo运行此脚本${NC}"
    exit 1
fi

echo -e "${GREEN}[1/10] 更新系统包...${NC}"
apt-get update
apt-get install -y wget curl unzip

echo -e "${GREEN}[2/10] 安装Java 17...${NC}"
if ! command -v java &> /dev/null || ! java -version 2>&1 | grep -q "17"; then
    apt-get install -y openjdk-17-jdk
    echo "Java 17 安装完成"
else
    echo "Java 17 已安装"
fi

# 验证Java版本
JAVA_VERSION=$(java -version 2>&1 | head -n 1)
echo "Java版本: $JAVA_VERSION"

echo -e "${GREEN}[3/10] 创建SonarQube用户...${NC}"
if ! id "$SONARQUBE_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d $SONARQUBE_HOME -m $SONARQUBE_USER
    echo "用户 $SONARQUBE_USER 已创建"
else
    echo "用户 $SONARQUBE_USER 已存在"
fi

echo -e "${GREEN}[4/10] 安装PostgreSQL（如果未安装）...${NC}"
if ! command -v psql &> /dev/null; then
    apt-get install -y postgresql postgresql-contrib
    systemctl start postgresql
    systemctl enable postgresql
    echo "PostgreSQL 已安装并启动"
else
    echo "PostgreSQL 已安装"
    systemctl start postgresql || true
fi

echo -e "${GREEN}[5/10] 创建SonarQube数据库...${NC}"
sudo -u postgres psql <<EOF
-- 创建数据库用户
CREATE USER $SONARQUBE_DB_USER WITH PASSWORD '$SONARQUBE_DB_PASSWORD';

-- 创建数据库
CREATE DATABASE $SONARQUBE_DB_NAME OWNER $SONARQUBE_DB_USER;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE $SONARQUBE_DB_NAME TO $SONARQUBE_DB_USER;

-- 设置编码
ALTER DATABASE $SONARQUBE_DB_NAME SET timezone TO 'UTC';
\q
EOF

echo "数据库创建完成"
echo "数据库名称: $SONARQUBE_DB_NAME"
echo "数据库用户: $SONARQUBE_DB_USER"
echo "数据库密码: $SONARQUBE_DB_PASSWORD"
echo ""

# 保存数据库密码到文件
echo "$SONARQUBE_DB_PASSWORD" > /root/sonarqube_db_password.txt
chmod 600 /root/sonarqube_db_password.txt
echo "数据库密码已保存到 /root/sonarqube_db_password.txt"

echo -e "${GREEN}[6/10] 下载并安装SonarQube...${NC}"
cd /tmp
if [ ! -f "sonarqube-${SONARQUBE_VERSION}.zip" ]; then
    echo "下载SonarQube ${SONARQUBE_VERSION}..."
    wget -q "https://binaries.sonarsource.com/Distribution/sonarqube/sonarqube-${SONARQUBE_VERSION}.zip"
fi

# 解压并移动到安装目录
if [ -d "$SONARQUBE_HOME" ]; then
    echo "备份现有安装..."
    mv $SONARQUBE_HOME ${SONARQUBE_HOME}.backup.$(date +%Y%m%d_%H%M%S)
fi

unzip -q "sonarqube-${SONARQUBE_VERSION}.zip"
mv "sonarqube-${SONARQUBE_VERSION}" $SONARQUBE_HOME

# 设置权限
chown -R $SONARQUBE_USER:$SONARQUBE_USER $SONARQUBE_HOME
chmod -R 755 $SONARQUBE_HOME

echo "SonarQube 已安装到 $SONARQUBE_HOME"

echo -e "${GREEN}[7/10] 配置SonarQube...${NC}"
cat > $SONARQUBE_HOME/conf/sonar.properties <<EOF
# 数据库配置
sonar.jdbc.url=jdbc:postgresql://localhost:5432/$SONARQUBE_DB_NAME
sonar.jdbc.username=$SONARQUBE_DB_USER
sonar.jdbc.password=$SONARQUBE_DB_PASSWORD

# Web服务器配置
sonar.web.host=0.0.0.0
sonar.web.port=$SONARQUBE_PORT
sonar.web.context=/

# 内存配置（根据服务器资源调整）
sonar.ce.javaOpts=-Xmx2g -Xms512m -XX:+HeapDumpOnOutOfMemoryError
sonar.web.javaOpts=-Xmx1g -Xms256m -XX:+HeapDumpOnOutOfMemoryError

# 路径配置
sonar.path.data=\$SONARQUBE_HOME/data
sonar.path.temp=\$SONARQUBE_HOME/temp
sonar.path.logs=\$SONARQUBE_HOME/logs

# 安全配置
sonar.forceAuthentication=true

# 更新中心（可选，用于插件更新）
sonar.updatecenter.url=https://update.sonarsource.org/update-center.properties
EOF

chown $SONARQUBE_USER:$SONARQUBE_USER $SONARQUBE_HOME/conf/sonar.properties
chmod 600 $SONARQUBE_HOME/conf/sonar.properties

echo "SonarQube 配置完成"

echo -e "${GREEN}[8/10] 创建systemd服务...${NC}"
cat > /etc/systemd/system/sonarqube.service <<EOF
[Unit]
Description=SonarQube service
After=syslog.target network.target postgresql.service

[Service]
Type=forking
User=$SONARQUBE_USER
Group=$SONARQUBE_USER
ExecStart=$SONARQUBE_HOME/bin/linux-x86-64/sonar.sh start
ExecStop=$SONARQUBE_HOME/bin/linux-x86-64/sonar.sh stop
ExecReload=$SONARQUBE_HOME/bin/linux-x86-64/sonar.sh restart
PIDFile=$SONARQUBE_HOME/logs/sonar.pid
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable sonarqube

echo "systemd 服务已创建并启用"

echo -e "${GREEN}[9/10] 配置防火墙...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow $SONARQUBE_PORT/tcp
    echo "防火墙规则已添加"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=$SONARQUBE_PORT/tcp
    firewall-cmd --reload
    echo "防火墙规则已添加"
else
    echo -e "${YELLOW}警告: 未找到防火墙工具，请手动开放端口 $SONARQUBE_PORT${NC}"
fi

echo -e "${GREEN}[10/10] 启动SonarQube服务...${NC}"
systemctl start sonarqube

# 等待服务启动
echo "等待SonarQube启动（这可能需要1-2分钟）..."
sleep 30

# 检查服务状态
for i in {1..30}; do
    if curl -s http://localhost:$SONARQUBE_PORT/api/system/status | grep -q "UP"; then
        echo -e "${GREEN}SonarQube 已成功启动！${NC}"
        break
    fi
    echo "等待中... ($i/30)"
    sleep 5
done

# 检查服务状态
if systemctl is-active --quiet sonarqube; then
    echo -e "${GREEN}✓ SonarQube 服务运行正常${NC}"
else
    echo -e "${RED}✗ SonarQube 服务启动失败，请检查日志: journalctl -u sonarqube${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "访问地址: $SONARQUBE_WEB_URL"
echo ""
echo "默认登录信息:"
echo "  用户名: admin"
echo "  密码: admin (首次登录后需要修改)"
echo ""
echo "数据库信息:"
echo "  数据库: $SONARQUBE_DB_NAME"
echo "  用户: $SONARQUBE_DB_USER"
echo "  密码: $SONARQUBE_DB_PASSWORD (已保存到 /root/sonarqube_db_password.txt)"
echo ""
echo "服务管理命令:"
echo "  启动: sudo systemctl start sonarqube"
echo "  停止: sudo systemctl stop sonarqube"
echo "  重启: sudo systemctl restart sonarqube"
echo "  状态: sudo systemctl status sonarqube"
echo "  日志: sudo journalctl -u sonarqube -f"
echo ""
echo -e "${YELLOW}重要提示:${NC}"
echo "1. 首次登录后请立即修改admin密码"
echo "2. 建议配置Nginx反向代理（可选）"
echo "3. 建议配置HTTPS（生产环境）"
echo ""

