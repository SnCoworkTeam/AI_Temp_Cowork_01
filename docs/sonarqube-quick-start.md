# SonarQube 快速开始指南

## 概述

本指南将帮助您在服务器 `124.220.181.231` 上快速部署和配置 SonarQube，为所有服务提供统一的代码质量视图。

## 快速部署（Windows环境）

### 步骤1: 执行部署脚本

在项目根目录打开PowerShell，执行：

```powershell
.\scripts\deploy-sonarqube.ps1
```

脚本将自动完成：
- ✅ 测试SSH连接
- ✅ 上传安装脚本到服务器
- ✅ 安装Java 17
- ✅ 安装和配置PostgreSQL
- ✅ 下载并安装SonarQube
- ✅ 配置SonarQube服务
- ✅ 启动SonarQube

**预计时间**: 10-15分钟

### 步骤2: 访问SonarQube

安装完成后，访问：
- **URL**: http://124.220.181.231:9000
- **用户名**: `admin`
- **密码**: `admin` (首次登录后必须修改)

### 步骤3: 创建项目并生成Token

1. 登录后，点击 **"Create Project"** -> **"Manually"**
2. 填写项目信息：
   - **Project Key**: `enterprise-ai-platform`
   - **Display Name**: `Enterprise AI Platform`
3. 点击 **"Generate a token"**
4. 保存Token（只显示一次）

### 步骤4: 配置项目

运行项目配置脚本：

```powershell
# 在WSL或Git Bash中执行
bash scripts/setup-sonarqube-project.sh
```

或手动创建 `sonar-project.properties`：

```bash
cp sonar-project.properties.example sonar-project.properties
# 编辑文件，填入您的Token
```

## 手动部署（Linux环境）

如果您需要在服务器上手动执行安装：

```bash
# 1. 上传安装脚本
scp -i SonarQube.pem scripts/install-sonarqube.sh ubuntu@124.220.181.231:/tmp/

# 2. SSH连接到服务器
ssh -i SonarQube.pem ubuntu@124.220.181.231

# 3. 执行安装脚本
sudo bash /tmp/install-sonarqube.sh
```

## 运行代码分析

### 方式1: 使用Docker（推荐）

```bash
docker run --rm \
  -v ${PWD}:/usr/src \
  -w /usr/src \
  sonarsource/sonar-scanner-cli:latest \
  -Dsonar.projectKey=enterprise-ai-platform \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://124.220.181.231:9000 \
  -Dsonar.login=YOUR_TOKEN
```

### 方式2: 使用本地Scanner

```bash
# 下载并安装SonarQube Scanner
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
unzip sonar-scanner-cli-5.0.1.3006-linux.zip
export PATH=$PATH:$(pwd)/sonar-scanner-5.0.1.3006-linux/bin

# 运行分析
sonar-scanner
```

## CI/CD集成

### GitHub Actions

在 `.github/workflows/sonarqube.yml` 中添加：

```yaml
name: SonarQube Analysis

on: [push, pull_request]

jobs:
  sonarqube:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: SonarQube Scan
        uses: sonarsource/sonarqube-scan-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: http://124.220.181.231:9000
```

在GitHub仓库设置中添加Secret `SONAR_TOKEN`。

## 服务管理

### 检查服务状态

```bash
ssh -i SonarQube.pem ubuntu@124.220.181.231 "sudo systemctl status sonarqube"
```

### 查看日志

```bash
ssh -i SonarQube.pem ubuntu@124.220.181.231 "sudo journalctl -u sonarqube -f"
```

### 重启服务

```bash
ssh -i SonarQube.pem ubuntu@124.220.181.231 "sudo systemctl restart sonarqube"
```

## 可选配置

### Nginx反向代理

如果需要通过域名访问，可以配置Nginx：

```bash
# 上传Nginx配置脚本
scp -i SonarQube.pem scripts/configure-sonarqube-nginx.sh ubuntu@124.220.181.231:/tmp/

# 执行配置
ssh -i SonarQube.pem ubuntu@124.220.181.231 "sudo bash /tmp/configure-sonarqube-nginx.sh"
```

## 质量门禁配置

1. 登录SonarQube
2. 进入 **Quality Gates** -> **Create**
3. 设置规则：
   - 代码覆盖率 >= 80%
   - 重复代码 < 3%
   - 技术债务 < 5%
   - 安全漏洞 = 0
   - 严重问题 = 0
   - 阻断问题 = 0

## 多服务分析

为每个服务创建单独的项目：

```properties
# api-gateway/sonar-project.properties
sonar.projectKey=api-gateway
sonar.sources=.

# auth-service/sonar-project.properties
sonar.projectKey=auth-service
sonar.sources=.
```

## 故障排查

### 服务无法启动

```bash
# 检查日志
ssh -i SonarQube.pem ubuntu@124.220.181.231 "sudo journalctl -u sonarqube -n 100"

# 检查Java版本
ssh -i SonarQube.pem ubuntu@124.220.181.231 "java -version"

# 检查数据库连接
ssh -i SonarQube.pem ubuntu@124.220.181.231 "sudo -u postgres psql -d sonarqube -c '\conninfo'"
```

### 分析失败

- 检查网络连接
- 验证Token是否正确
- 检查项目配置
- 查看SonarQube日志

## 相关文档

- [完整集成指南](sonarqube-integration.md)
- [SonarQube官方文档](https://docs.sonarqube.org/)

## 支持

如有问题，请查看：
1. SonarQube日志: `sudo journalctl -u sonarqube -f`
2. 服务器系统日志: `sudo journalctl -xe`
3. SonarQube官方文档

