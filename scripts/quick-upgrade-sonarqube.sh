#!/bin/bash
# SonarQube 快速升级脚本 - 直接升级到10.8 LTS，不备份

set -e

NEW_VERSION="10.8.1.93247"
SONARQUBE_HOME="/opt/sonarqube"
SONARQUBE_USER="sonarqube"

echo "=========================================="
echo "SonarQube 升级到 10.8 LTS"
echo "=========================================="
echo ""

echo "[1/6] 停止SonarQube服务..."
systemctl stop sonarqube
sleep 3

echo "[2/6] 备份当前安装目录..."
if [ -d "$SONARQUBE_HOME" ]; then
    BACKUP_NAME="${SONARQUBE_HOME}.backup.$(date +%Y%m%d_%H%M%S)"
    mv $SONARQUBE_HOME $BACKUP_NAME
    echo "已备份到: $BACKUP_NAME"
fi

echo "[3/6] 下载新版本..."
cd /tmp
if [ ! -f "sonarqube-${NEW_VERSION}.zip" ]; then
    echo "下载SonarQube ${NEW_VERSION}..."
    wget -q "https://binaries.sonarsource.com/Distribution/sonarqube/sonarqube-${NEW_VERSION}.zip"
fi

echo "[4/6] 安装新版本..."
unzip -q "sonarqube-${NEW_VERSION}.zip"
mv "sonarqube-${NEW_VERSION}" $SONARQUBE_HOME

echo "[5/6] 恢复配置..."
# 恢复数据库配置
if [ -d "${SONARQUBE_HOME}.backup."* ]; then
    OLD_CONF=$(ls -td ${SONARQUBE_HOME}.backup.*/conf/sonar.properties 2>/dev/null | head -1)
    if [ -f "$OLD_CONF" ]; then
        grep -E "^sonar.jdbc" "$OLD_CONF" >> $SONARQUBE_HOME/conf/sonar.properties 2>/dev/null || true
        grep -E "^sonar.web" "$OLD_CONF" >> $SONARQUBE_HOME/conf/sonar.properties 2>/dev/null || true
    fi
    
    # 恢复数据目录
    OLD_DATA=$(ls -td ${SONARQUBE_HOME}.backup.*/data 2>/dev/null | head -1)
    if [ -d "$OLD_DATA" ]; then
        cp -r "$OLD_DATA" $SONARQUBE_HOME/ 2>/dev/null || true
    fi
fi

# 修复路径变量
sed -i 's|\$SONARQUBE_HOME|/opt/sonarqube|g' $SONARQUBE_HOME/conf/sonar.properties 2>/dev/null || true

# 设置权限
chown -R $SONARQUBE_USER:$SONARQUBE_USER $SONARQUBE_HOME
chmod -R 755 $SONARQUBE_HOME

echo "[6/6] 启动SonarQube服务..."
systemctl start sonarqube

echo ""
echo "等待服务启动（约2分钟）..."
sleep 30

for i in {1..30}; do
    if curl -s http://localhost:9000/api/system/status | grep -q "UP"; then
        echo "✓ SonarQube 升级成功！"
        VERSION=$(curl -s http://localhost:9000/api/system/status | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        echo "新版本: $VERSION"
        break
    fi
    echo "等待中... ($i/30)"
    sleep 5
done

