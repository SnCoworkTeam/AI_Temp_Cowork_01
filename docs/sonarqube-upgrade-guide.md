# SonarQube 升级指南

## 当前状态

您当前使用的 SonarQube 版本已超过支持期限，需要升级到受支持的版本。

## 支持的版本

### 推荐版本

1. **SonarQube 10.8 LTS** (推荐)
   - 版本号: 10.8.1.93247
   - 长期支持版本
   - 稳定可靠

2. **SonarQube 11.0** (最新)
   - 版本号: 11.0.0.89900
   - 最新功能
   - 需要Java 17+

## 升级前准备

### 1. 检查系统要求

```bash
# 检查Java版本（需要Java 17+）
java -version

# 检查数据库版本
sudo -u postgres psql -c "SELECT version();"

# 检查磁盘空间（至少需要5GB）
df -h /opt/sonarqube
```

### 2. 备份数据

升级前必须备份：

```bash
# 备份数据库
sudo -u postgres pg_dump sonarqube > sonarqube_backup_$(date +%Y%m%d).sql

# 备份配置和数据
sudo tar -czf sonarqube_backup_$(date +%Y%m%d).tar.gz \
    /opt/sonarqube/conf \
    /opt/sonarqube/data \
    /opt/sonarqube/extensions/plugins
```

## 升级方法

### 方法1: 使用自动升级脚本（推荐）

```bash
# 1. 上传升级脚本
scp -i SonarQube1.pem scripts/upgrade-sonarqube.sh ubuntu@124.220.181.231:/tmp/

# 2. SSH连接并执行
ssh -i SonarQube1.pem ubuntu@124.220.181.231
sudo bash /tmp/upgrade-sonarqube.sh
```

### 方法2: 手动升级

#### 步骤1: 停止服务

```bash
sudo systemctl stop sonarqube
```

#### 步骤2: 备份

```bash
# 备份数据库
sudo -u postgres pg_dump sonarqube > /backup/sonarqube_db_$(date +%Y%m%d).sql

# 备份文件
sudo tar -czf /backup/sonarqube_$(date +%Y%m%d).tar.gz /opt/sonarqube
```

#### 步骤3: 下载新版本

```bash
cd /tmp
wget https://binaries.sonarsource.com/Distribution/sonarqube/sonarqube-10.8.1.93247.zip
```

#### 步骤4: 安装新版本

```bash
# 备份当前安装
sudo mv /opt/sonarqube /opt/sonarqube.backup

# 解压新版本
unzip sonarqube-10.8.1.93247.zip
sudo mv sonarqube-10.8.1.93247 /opt/sonarqube

# 恢复配置
sudo cp /opt/sonarqube.backup/conf/sonar.properties /opt/sonarqube/conf/
sudo cp -r /opt/sonarqube.backup/data /opt/sonarqube/
sudo cp -r /opt/sonarqube.backup/extensions/plugins /opt/sonarqube/extensions/

# 设置权限
sudo chown -R sonarqube:sonarqube /opt/sonarqube
sudo chmod -R 755 /opt/sonarqube
```

#### 步骤5: 修复配置文件

```bash
# 修复路径变量
sudo sed -i 's|\$SONARQUBE_HOME|/opt/sonarqube|g' /opt/sonarqube/conf/sonar.properties
```

#### 步骤6: 启动服务

```bash
sudo systemctl start sonarqube
sudo systemctl status sonarqube
```

#### 步骤7: 验证升级

```bash
# 等待2-3分钟，然后检查
curl http://localhost:9000/api/system/status
```

## 升级后验证

1. **检查版本**
   ```bash
   curl http://localhost:9000/api/system/status
   ```

2. **检查服务状态**
   ```bash
   sudo systemctl status sonarqube
   ```

3. **访问Web界面**
   - 访问: http://124.220.181.231:9000
   - 确认没有版本警告

4. **验证数据**
   - 检查项目列表
   - 检查分析历史
   - 检查配置

## 回滚（如果升级失败）

如果升级出现问题，可以回滚：

```bash
# 1. 停止服务
sudo systemctl stop sonarqube

# 2. 恢复旧版本
sudo rm -rf /opt/sonarqube
sudo mv /opt/sonarqube.backup /opt/sonarqube

# 3. 恢复数据库（如果需要）
sudo -u postgres psql sonarqube < /backup/sonarqube_db_YYYYMMDD.sql

# 4. 启动服务
sudo systemctl start sonarqube
```

## 常见问题

### 1. 升级后服务无法启动

检查日志：
```bash
sudo journalctl -u sonarqube -n 100
sudo tail -100 /opt/sonarqube/logs/sonar.log
```

### 2. 数据库连接失败

检查配置文件：
```bash
sudo cat /opt/sonarqube/conf/sonar.properties | grep jdbc
```

### 3. 插件不兼容

某些插件可能需要更新：
- 进入 SonarQube Web界面
- 进入 Administration > Marketplace
- 更新不兼容的插件

## 升级路径

如果从很旧的版本升级，可能需要逐步升级：

1. 10.3 → 10.4 → 10.5 → 10.6 → 10.7 → 10.8
2. 或者直接升级到10.8（通常可以）

## 注意事项

1. **升级前必须备份**
2. **在维护窗口期间升级**
3. **升级后测试所有功能**
4. **检查插件兼容性**
5. **更新CI/CD配置（如果需要）**

## 获取帮助

- [SonarQube官方文档](https://docs.sonarqube.org/)
- [升级指南](https://docs.sonarqube.org/latest/setup/upgrading/)
- [社区论坛](https://community.sonarsource.com/)

