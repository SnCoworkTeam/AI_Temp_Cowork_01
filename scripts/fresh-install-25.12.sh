#!/bin/bash
# SonarQube 全新安装脚本 - 25.12.0.117093
# 删除旧版本，全新安装最新版本

set -e

NEW_VERSION="25.12.0.117093"
SONARQUBE_HOME="/opt/sonarqube"
SONARQUBE_USER="sonarqube"
SONARQUBE_DB_NAME="sonarqube"
SONARQUBE_DB_USER="sonarqube"

echo "=========================================="
echo "SonarQube 全新安装 25.12.0.117093"
echo "=========================================="
echo ""

echo "[1/7] 停止服务..."
systemctl stop sonarqube 2>/dev/null || true
sleep 2

echo "[2/7] 删除旧版本..."
if [ -d "$SONARQUBE_HOME" ]; then
    rm -rf $SONARQUBE_HOME
    echo "旧版本已删除"
fi

# 清理备份
rm -rf ${SONARQUBE_HOME}.backup.* 2>/dev/null || true

echo "[3/7] 检查数据库..."
# 检查数据库是否存在，如果存在则删除（全新安装）
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $SONARQUBE_DB_NAME; then
    echo "删除旧数据库..."
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS $SONARQUBE_DB_NAME;" 2>/dev/null || true
    sudo -u postgres psql -c "DROP USER IF EXISTS $SONARQUBE_DB_USER;" 2>/dev/null || true
fi

# 创建新数据库
echo "创建新数据库..."
SONARQUBE_DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
sudo -u postgres psql <<EOF
CREATE USER $SONARQUBE_DB_USER WITH PASSWORD '$SONARQUBE_DB_PASSWORD';
CREATE DATABASE $SONARQUBE_DB_NAME OWNER $SONARQUBE_DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $SONARQUBE_DB_NAME TO $SONARQUBE_DB_USER;
ALTER DATABASE $SONARQUBE_DB_NAME SET timezone TO 'UTC';
\q
EOF

echo "$SONARQUBE_DB_PASSWORD" > /root/sonarqube_db_password.txt
chmod 600 /root/sonarqube_db_password.txt
echo "数据库密码已保存到: /root/sonarqube_db_password.txt"

echo "[4/7] 解压并安装新版本..."
cd /tmp
if [ ! -f "sonarqube-${NEW_VERSION}.zip" ]; then
    echo "错误: 文件 sonarqube-${NEW_VERSION}.zip 不存在"
    exit 1
fi

unzip -q -o "sonarqube-${NEW_VERSION}.zip"

# 查找解压后的目录
EXTRACTED_DIR=$(ls -d sonarqube-* 2>/dev/null | head -1)
if [ -z "$EXTRACTED_DIR" ]; then
    echo "错误: 无法找到解压后的目录"
    exit 1
fi

mv "$EXTRACTED_DIR" $SONARQUBE_HOME

echo "[5/7] 配置SonarQube..."
cat > $SONARQUBE_HOME/conf/sonar.properties <<EOF
# 数据库配置
sonar.jdbc.url=jdbc:postgresql://localhost:5432/$SONARQUBE_DB_NAME
sonar.jdbc.username=$SONARQUBE_DB_USER
sonar.jdbc.password=$SONARQUBE_DB_PASSWORD

# Web服务器配置
sonar.web.host=0.0.0.0
sonar.web.port=9000
sonar.web.context=/

# 内存配置
sonar.ce.javaOpts=-Xmx2g -Xms512m -XX:+HeapDumpOnOutOfMemoryError
sonar.web.javaOpts=-Xmx1g -Xms256m -XX:+HeapDumpOnOutOfMemoryError

# 路径配置
sonar.path.data=$SONARQUBE_HOME/data
sonar.path.temp=$SONARQUBE_HOME/temp
sonar.path.logs=$SONARQUBE_HOME/logs

# 安全配置
sonar.forceAuthentication=true
EOF

chown $SONARQUBE_USER:$SONARQUBE_USER $SONARQUBE_HOME/conf/sonar.properties
chmod 600 $SONARQUBE_HOME/conf/sonar.properties

echo "[6/7] 设置权限..."
chown -R $SONARQUBE_USER:$SONARQUBE_USER $SONARQUBE_HOME
chmod -R 755 $SONARQUBE_HOME

echo "[7/7] 启动服务..."
systemctl start sonarqube

echo ""
echo "等待服务启动（约2-3分钟）..."
sleep 30

for i in {1..40}; do
    if curl -s http://localhost:9000/api/system/status 2>/dev/null | grep -q "UP"; then
        VERSION=$(curl -s http://localhost:9000/api/system/status 2>/dev/null | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        echo "✓ 安装成功！版本: $VERSION"
        echo ""
        echo "访问地址: http://124.220.181.231:9000"
        echo "默认登录: admin / admin"
        echo "数据库密码: $SONARQUBE_DB_PASSWORD"
        exit 0
    fi
    echo "等待中... ($i/40)"
    sleep 5
done

echo "服务可能还在启动中，请检查日志"
systemctl status sonarqube --no-pager | head -10

