#!/bin/bash
# 简化版部署脚本 - 在服务器上直接执行
# 如果无法通过SSH自动部署，可以手动复制此脚本内容到服务器执行

set -e

echo "=========================================="
echo "SonarQube 安装和配置"
echo "=========================================="
echo ""

# 配置变量
SONARQUBE_VERSION="10.3.0.82913"
SONARQUBE_HOME="/opt/sonarqube"
SONARQUBE_USER="sonarqube"
SONARQUBE_DB_NAME="sonarqube"
SONARQUBE_DB_USER="sonarqube"
SONARQUBE_DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
SONARQUBE_PORT="9000"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "错误: 请使用sudo运行此脚本"
    exit 1
fi

echo "[1/10] 更新系统包..."
apt-get update -qq
apt-get install -y wget curl unzip

echo "[2/10] 安装Java 17..."
if ! command -v java &> /dev/null || ! java -version 2>&1 | grep -q "17"; then
    apt-get install -y openjdk-17-jdk
fi

echo "[3/10] 创建SonarQube用户..."
if ! id "$SONARQUBE_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d $SONARQUBE_HOME -m $SONARQUBE_USER
fi

echo "[4/10] 安装PostgreSQL..."
if ! command -v psql &> /dev/null; then
    apt-get install -y postgresql postgresql-contrib
    systemctl start postgresql
    systemctl enable postgresql
fi

echo "[5/10] 创建SonarQube数据库..."
sudo -u postgres psql <<EOF
CREATE USER $SONARQUBE_DB_USER WITH PASSWORD '$SONARQUBE_DB_PASSWORD';
CREATE DATABASE $SONARQUBE_DB_NAME OWNER $SONARQUBE_DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $SONARQUBE_DB_NAME TO $SONARQUBE_DB_USER;
ALTER DATABASE $SONARQUBE_DB_NAME SET timezone TO 'UTC';
\q
EOF

echo "$SONARQUBE_DB_PASSWORD" > /root/sonarqube_db_password.txt
chmod 600 /root/sonarqube_db_password.txt
echo "数据库密码: $SONARQUBE_DB_PASSWORD (已保存到 /root/sonarqube_db_password.txt)"

echo "[6/10] 下载并安装SonarQube..."
cd /tmp
if [ ! -f "sonarqube-${SONARQUBE_VERSION}.zip" ]; then
    wget -q "https://binaries.sonarsource.com/Distribution/sonarqube/sonarqube-${SONARQUBE_VERSION}.zip"
fi

if [ -d "$SONARQUBE_HOME" ]; then
    mv $SONARQUBE_HOME ${SONARQUBE_HOME}.backup.$(date +%Y%m%d_%H%M%S)
fi

unzip -q "sonarqube-${SONARQUBE_VERSION}.zip"
mv "sonarqube-${SONARQUBE_VERSION}" $SONARQUBE_HOME
chown -R $SONARQUBE_USER:$SONARQUBE_USER $SONARQUBE_HOME
chmod -R 755 $SONARQUBE_HOME

echo "[7/10] 配置SonarQube..."
cat > $SONARQUBE_HOME/conf/sonar.properties <<EOF
sonar.jdbc.url=jdbc:postgresql://localhost:5432/$SONARQUBE_DB_NAME
sonar.jdbc.username=$SONARQUBE_DB_USER
sonar.jdbc.password=$SONARQUBE_DB_PASSWORD
sonar.web.host=0.0.0.0
sonar.web.port=$SONARQUBE_PORT
sonar.web.context=/
sonar.ce.javaOpts=-Xmx2g -Xms512m -XX:+HeapDumpOnOutOfMemoryError
sonar.web.javaOpts=-Xmx1g -Xms256m -XX:+HeapDumpOnOutOfMemoryError
sonar.path.data=\$SONARQUBE_HOME/data
sonar.path.temp=\$SONARQUBE_HOME/temp
sonar.path.logs=\$SONARQUBE_HOME/logs
sonar.forceAuthentication=true
EOF

chown $SONARQUBE_USER:$SONARQUBE_USER $SONARQUBE_HOME/conf/sonar.properties
chmod 600 $SONARQUBE_HOME/conf/sonar.properties

echo "[8/10] 创建systemd服务..."
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

echo "[9/10] 配置防火墙..."
if command -v ufw &> /dev/null; then
    ufw allow $SONARQUBE_PORT/tcp
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=$SONARQUBE_PORT/tcp
    firewall-cmd --reload
fi

echo "[10/10] 启动SonarQube服务..."
systemctl start sonarqube

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "访问地址: http://124.220.181.231:9000"
echo "默认登录: admin / admin"
echo ""
echo "等待服务启动（约1-2分钟）..."
sleep 30

for i in {1..30}; do
    if curl -s http://localhost:$SONARQUBE_PORT/api/system/status | grep -q "UP"; then
        echo "✓ SonarQube 已成功启动！"
        break
    fi
    echo "等待中... ($i/30)"
    sleep 5
done

echo ""
echo "服务管理命令:"
echo "  状态: sudo systemctl status sonarqube"
echo "  日志: sudo journalctl -u sonarqube -f"
echo "  重启: sudo systemctl restart sonarqube"
echo ""

