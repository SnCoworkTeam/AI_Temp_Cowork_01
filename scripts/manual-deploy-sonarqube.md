# SonarQube 手动部署指南

由于SSH连接可能存在问题，请按照以下步骤手动部署：

## 步骤1: 上传安装脚本到服务器

使用您能正常工作的SSH密钥，上传安装脚本：

```powershell
# 使用您能正常工作的密钥
scp -i "您的正常密钥路径" scripts\install-sonarqube.sh ubuntu@124.220.181.231:/tmp/install-sonarqube.sh
```

## 步骤2: SSH连接到服务器

```powershell
ssh -i "您的正常密钥路径" ubuntu@124.220.181.231
```

## 步骤3: 在服务器上执行安装

```bash
# 切换到root或使用sudo
sudo bash /tmp/install-sonarqube.sh
```

## 步骤4: 等待安装完成

安装过程大约需要10-15分钟，脚本会自动：
- 安装Java 17
- 安装PostgreSQL
- 创建SonarQube数据库
- 下载并安装SonarQube
- 配置systemd服务
- 启动SonarQube

## 步骤5: 验证安装

安装完成后，访问：
- **URL**: http://124.220.181.231:9000
- **用户名**: admin
- **密码**: admin (首次登录后需要修改)

## 如果遇到问题

### 查看安装日志
```bash
sudo journalctl -u sonarqube -f
```

### 检查服务状态
```bash
sudo systemctl status sonarqube
```

### 查看SonarQube日志
```bash
sudo tail -f /opt/sonarqube/logs/sonar.log
```

### 手动启动服务
```bash
sudo systemctl start sonarqube
```

## 获取数据库密码

安装脚本会生成数据库密码并保存到：
```bash
sudo cat /root/sonarqube_db_password.txt
```

