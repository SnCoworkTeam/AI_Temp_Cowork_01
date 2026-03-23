#!/bin/bash
# SonarQube 升级脚本
# 从当前版本升级到最新LTS版本

set -e

echo "=========================================="
echo "SonarQube 升级脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置变量
NEW_VERSION="10.8.1.93247"  # SonarQube 10.8 LTS (最新LTS版本)
# 或者使用: "11.0.0.89900"  # SonarQube 11.0 (最新版本)
SONARQUBE_HOME="/opt/sonarqube"
SONARQUBE_USER="sonarqube"
BACKUP_DIR="/backup/sonarqube"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用sudo运行此脚本${NC}"
    exit 1
fi

echo -e "${GREEN}[1/8] 检查当前版本...${NC}"
CURRENT_VERSION=$(curl -s http://localhost:9000/api/system/status | grep -o '"version":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
echo "当前版本: $CURRENT_VERSION"
echo "目标版本: $NEW_VERSION"

if [ "$CURRENT_VERSION" = "$NEW_VERSION" ]; then
    echo -e "${GREEN}已是最新版本，无需升级${NC}"
    exit 0
fi

echo -e "${GREEN}[2/8] 停止SonarQube服务...${NC}"
systemctl stop sonarqube
sleep 5

echo -e "${GREEN}[3/8] 备份当前安装和数据...${NC}"
mkdir -p $BACKUP_DIR

# 备份数据库
DB_PASSWORD=$(cat /root/sonarqube_db_password.txt 2>/dev/null || echo "")
if [ -n "$DB_PASSWORD" ]; then
    sudo -u postgres pg_dump sonarqube > $BACKUP_DIR/sonarqube_db_${TIMESTAMP}.sql
    echo "数据库已备份到: $BACKUP_DIR/sonarqube_db_${TIMESTAMP}.sql"
fi

# 备份配置和数据
tar -czf $BACKUP_DIR/sonarqube_backup_${TIMESTAMP}.tar.gz \
    $SONARQUBE_HOME/conf \
    $SONARQUBE_HOME/data \
    $SONARQUBE_HOME/extensions/plugins 2>/dev/null || true

echo "配置和数据已备份到: $BACKUP_DIR/sonarqube_backup_${TIMESTAMP}.tar.gz"

echo -e "${GREEN}[4/8] 下载新版本...${NC}"
cd /tmp
if [ ! -f "sonarqube-${NEW_VERSION}.zip" ]; then
    echo "下载SonarQube ${NEW_VERSION}..."
    wget -q "https://binaries.sonarsource.com/Distribution/sonarqube/sonarqube-${NEW_VERSION}.zip"
else
    echo "安装包已存在，跳过下载"
fi

echo -e "${GREEN}[5/8] 备份当前安装目录...${NC}"
if [ -d "$SONARQUBE_HOME" ]; then
    mv $SONARQUBE_HOME ${SONARQUBE_HOME}.backup.${TIMESTAMP}
    echo "当前安装已备份到: ${SONARQUBE_HOME}.backup.${TIMESTAMP}"
fi

echo -e "${GREEN}[6/8] 安装新版本...${NC}"
unzip -q "sonarqube-${NEW_VERSION}.zip"
mv "sonarqube-${NEW_VERSION}" $SONARQUBE_HOME

# 恢复配置和数据
echo -e "${GREEN}[7/8] 恢复配置和数据...${NC}"
if [ -f "$BACKUP_DIR/sonarqube_backup_${TIMESTAMP}.tar.gz" ]; then
    cd $SONARQUBE_HOME
    tar -xzf $BACKUP_DIR/sonarqube_backup_${TIMESTAMP}.tar.gz --strip-components=3 2>/dev/null || true

    # 恢复配置文件（需要手动检查兼容性）
    if [ -f "${SONARQUBE_HOME}.backup.${TIMESTAMP}/conf/sonar.properties" ]; then
        # 复制数据库配置
        grep -E "^sonar.jdbc" ${SONARQUBE_HOME}.backup.${TIMESTAMP}/conf/sonar.properties >> $SONARQUBE_HOME/conf/sonar.properties 2>/dev/null || true
        grep -E "^sonar.web" ${SONARQUBE_HOME}.backup.${TIMESTAMP}/conf/sonar.properties >> $SONARQUBE_HOME/conf/sonar.properties 2>/dev/null || true
    fi
fi

# 设置权限
chown -R $SONARQUBE_USER:$SONARQUBE_USER $SONARQUBE_HOME
chmod -R 755 $SONARQUBE_HOME

# 修复配置文件中的路径变量
sed -i 's|\$SONARQUBE_HOME|/opt/sonarqube|g' $SONARQUBE_HOME/conf/sonar.properties 2>/dev/null || true

echo -e "${GREEN}[8/8] 启动SonarQube服务...${NC}"
systemctl start sonarqube

echo ""
echo "等待服务启动（约2分钟）..."
sleep 30

for i in {1..30}; do
    if curl -s http://localhost:9000/api/system/status | grep -q "UP"; then
        echo -e "${GREEN}✓ SonarQube 升级成功！${NC}"
        break
    fi
    echo "等待中... ($i/30)"
    sleep 5
done

# 检查服务状态
if systemctl is-active --quiet sonarqube; then
    NEW_VERSION_CHECK=$(curl -s http://localhost:9000/api/system/status | grep -o '"version":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
    echo ""
    echo "=========================================="
    echo "升级完成！"
    echo "=========================================="
    echo "旧版本: $CURRENT_VERSION"
    echo "新版本: $NEW_VERSION_CHECK"
    echo ""
    echo "备份位置:"
    echo "  数据库: $BACKUP_DIR/sonarqube_db_${TIMESTAMP}.sql"
    echo "  文件: $BACKUP_DIR/sonarqube_backup_${TIMESTAMP}.tar.gz"
    echo "  安装目录: ${SONARQUBE_HOME}.backup.${TIMESTAMP}"
    echo ""
else
    echo -e "${RED}✗ 服务启动失败，请检查日志: journalctl -u sonarqube${NC}"
    echo -e "${YELLOW}如需回滚，请恢复备份: ${SONARQUBE_HOME}.backup.${TIMESTAMP}${NC}"
    exit 1
fi

