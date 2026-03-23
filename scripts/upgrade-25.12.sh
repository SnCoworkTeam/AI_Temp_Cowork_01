#!/bin/bash
set -e

NEW_VERSION="25.12.0.117093"
SONARQUBE_HOME="/opt/sonarqube"
SONARQUBE_USER="sonarqube"

echo "=========================================="
echo "SonarQube 升级到 25.12.0.117093"
echo "=========================================="
echo ""

echo "[1/5] 停止服务..."
systemctl stop sonarqube
sleep 3

echo "[2/5] 备份当前安装..."
if [ -d "$SONARQUBE_HOME" ]; then
    BACKUP_NAME="${SONARQUBE_HOME}.backup.$(date +%Y%m%d_%H%M%S)"
    mv $SONARQUBE_HOME $BACKUP_NAME
    echo "已备份到: $BACKUP_NAME"
    BACKUP_DIR=$BACKUP_NAME
else
    BACKUP_DIR=$(ls -td ${SONARQUBE_HOME}.backup.* 2>/dev/null | head -1)
fi

echo "[3/5] 解压并安装新版本..."
cd /tmp
if [ ! -f "sonarqube-${NEW_VERSION}.zip" ]; then
    echo "错误: 文件 sonarqube-${NEW_VERSION}.zip 不存在"
    echo "请先上传文件到 /tmp/"
    exit 1
fi

unzip -q -o "sonarqube-${NEW_VERSION}.zip"
rm -rf $SONARQUBE_HOME

# 查找解压后的目录名（可能是 sonarqube-25.12.0.117093 或其他）
EXTRACTED_DIR=$(ls -d sonarqube-* 2>/dev/null | head -1)
if [ -z "$EXTRACTED_DIR" ]; then
    echo "错误: 无法找到解压后的目录"
    exit 1
fi

mv "$EXTRACTED_DIR" $SONARQUBE_HOME

echo "[4/5] 恢复配置和数据..."
if [ -n "$BACKUP_DIR" ] && [ -d "$BACKUP_DIR" ]; then
    # 恢复数据库配置
    if [ -f "$BACKUP_DIR/conf/sonar.properties" ]; then
        grep "^sonar.jdbc" "$BACKUP_DIR/conf/sonar.properties" >> $SONARQUBE_HOME/conf/sonar.properties 2>/dev/null || true
        grep "^sonar.web" "$BACKUP_DIR/conf/sonar.properties" >> $SONARQUBE_HOME/conf/sonar.properties 2>/dev/null || true
    fi
    # 恢复数据目录
    if [ -d "$BACKUP_DIR/data" ]; then
        cp -r "$BACKUP_DIR/data" $SONARQUBE_HOME/ 2>/dev/null || true
    fi
fi

# 修复路径变量
sed -i 's|\$SONARQUBE_HOME|/opt/sonarqube|g' $SONARQUBE_HOME/conf/sonar.properties 2>/dev/null || true

# 设置权限
chown -R $SONARQUBE_USER:$SONARQUBE_USER $SONARQUBE_HOME
chmod -R 755 $SONARQUBE_HOME

echo "[5/5] 启动服务..."
systemctl start sonarqube

echo ""
echo "等待服务启动（约2分钟）..."
sleep 30

for i in {1..30}; do
    if curl -s http://localhost:9000/api/system/status 2>/dev/null | grep -q "UP"; then
        VERSION=$(curl -s http://localhost:9000/api/system/status 2>/dev/null | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        echo "✓ 升级成功！新版本: $VERSION"
        exit 0
    fi
    echo "等待中... ($i/30)"
    sleep 5
done

echo "服务可能还在启动中，请稍后检查"
systemctl status sonarqube --no-pager | head -10

