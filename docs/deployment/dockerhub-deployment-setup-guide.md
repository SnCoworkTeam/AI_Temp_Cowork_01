# Docker Hub自动化部署配置指南

## 📋 概述

本指南将帮助您配置GitHub Actions + Docker Hub的自动化部署方案。

## 🎯 方案流程

```
代码提交 → GitHub Actions触发 → 运行测试 → 构建镜像 → 推送到Docker Hub → SSH部署 → 服务器拉取镜像 → 重启服务
```

## 📝 配置步骤

### 步骤1：配置Docker Hub

#### 1.1 注册Docker Hub账号

1. 访问 https://hub.docker.com
2. 注册账号（如果还没有）
3. 登录Docker Hub

#### 1.2 创建Access Token

1. 登录Docker Hub
2. 进入 **Account Settings** → **Security** → **New Access Token**
3. 填写Token描述（如：`GitHub Actions Deployment`）
4. 权限选择：**Read & Write**
5. 点击 **Generate**
6. **重要**：复制Token并保存（只显示一次）

### 步骤2：配置GitHub Secrets

1. 进入GitHub仓库
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. 添加以下Secrets：

| Secret名称 | 值 | 说明 |
|-----------|-----|------|
| `DOCKER_HUB_USERNAME` | `your-dockerhub-username` | Docker Hub用户名 |
| `DOCKER_HUB_TOKEN` | `dckr_pat_xxxxx` | Docker Hub Access Token |
| `SSH_PRIVATE_KEY` | `-----BEGIN OPENSSH...` | SSH私钥内容（完整内容） |
| `SERVER_HOST` | `43.143.139.197` | 服务器IP地址 |
| `SERVER_USER` | `root` | 服务器用户名 |

#### 如何获取SSH_PRIVATE_KEY

```bash
# 在本地执行，读取私钥内容
cat E:\enterprise-ai-platform\enterprise_ai_platform.pem
```

复制完整内容（包括 `-----BEGIN OPENSSH PRIVATE KEY-----` 和 `-----END OPENSSH PRIVATE KEY-----`）

### 步骤3：服务器端初始化

#### 3.1 SSH到服务器

```bash
ssh -i E:\enterprise-ai-platform\enterprise_ai_platform.pem root@43.143.139.197
```

#### 3.2 创建项目目录

```bash
mkdir -p /opt/enterprise-ai-platform
cd /opt/enterprise-ai-platform
```

#### 3.3 初始化Git仓库（可选）

```bash
git init
git remote add origin https://github.com/PMLiuyubin/enterprise-ai-platform.git
git pull origin main
```

#### 3.4 配置Docker Hub登录

```bash
# 在服务器上登录Docker Hub（首次需要）
docker login -u your-dockerhub-username
# 输入Docker Hub密码或Access Token
```

#### 3.5 创建生产环境变量文件

```bash
cd /opt/enterprise-ai-platform
cp .env.example .env.prod
# 编辑.env.prod，配置生产环境变量
nano .env.prod
```

**关键环境变量：**
```bash
# Docker Hub配置
DOCKER_HUB_USERNAME=your-dockerhub-username
IMAGE_TAG=latest

# 数据库配置
DB_NAME=ai_platform
DB_USER=ai_user
DB_PASSWORD=your-secure-password
DB_PORT=5432

# Redis配置
REDIS_PORT=6379

# 服务端口配置
API_GATEWAY_PORT=8080
WEB_UI_PORT=3000
MCP_GATEWAY_PORT=8001
WORKFLOW_ENGINE_PORT=8002
# ... 其他服务端口
```

#### 3.6 创建docker-compose.prod.yml

将 `docker-compose.prod.yml` 上传到服务器：

```bash
# 在本地执行
scp -i E:\enterprise-ai-platform\enterprise_ai_platform.pem \
  docker-compose.prod.yml \
  root@43.143.139.197:/opt/enterprise-ai-platform/
```

### 步骤4：验证配置

#### 4.1 测试Docker Hub连接

在服务器上：

```bash
docker pull ${DOCKER_HUB_USERNAME}/enterprise-ai-platform-api-gateway:latest
```

#### 4.2 测试SSH连接

在本地：

```bash
ssh -i E:\enterprise-ai-platform\enterprise_ai_platform.pem root@43.143.139.197 "echo 'SSH连接成功'"
```

### 步骤5：首次部署

#### 5.1 手动触发GitHub Actions

1. 进入GitHub仓库
2. 点击 **Actions** 标签
3. 选择 **Build and Deploy to Docker Hub** workflow
4. 点击 **Run workflow**
5. 选择环境（production）
6. 点击 **Run workflow**

#### 5.2 监控部署过程

- 在GitHub Actions页面查看实时日志
- 等待所有步骤完成

#### 5.3 验证部署

```bash
# SSH到服务器
ssh -i E:\enterprise-ai-platform\enterprise_ai_platform.pem root@43.143.139.197

# 检查服务状态
cd /opt/enterprise-ai-platform
docker-compose -f docker-compose.prod.yml ps

# 检查健康状态
curl http://localhost:8080/health
curl http://localhost:3000/api/health
```

## 🔄 后续使用

### 自动部署

每次推送到 `main` 分支时，GitHub Actions会自动：
1. 运行测试
2. 构建所有服务镜像
3. 推送到Docker Hub
4. SSH到服务器执行部署

### 手动触发部署

1. 进入GitHub Actions
2. 选择 **Build and Deploy to Docker Hub**
3. 点击 **Run workflow**
4. 选择环境
5. 点击 **Run workflow**

### 查看部署历史

在GitHub Actions页面可以查看：
- 所有部署历史
- 每次部署的详细日志
- 构建和部署时间
- 成功/失败状态

## 🛠️ 故障排查

### 问题1：Docker Hub登录失败

**症状**：构建阶段失败，提示认证错误

**解决**：
1. 检查 `DOCKER_HUB_USERNAME` 和 `DOCKER_HUB_TOKEN` 是否正确
2. 确认Token权限是 Read & Write
3. 重新生成Token并更新Secret

### 问题2：SSH连接失败

**症状**：部署阶段失败，无法连接服务器

**解决**：
1. 检查 `SSH_PRIVATE_KEY` 是否完整（包括BEGIN和END行）
2. 检查 `SERVER_HOST` 和 `SERVER_USER` 是否正确
3. 测试SSH连接：`ssh -i key.pem user@host`

### 问题3：镜像拉取失败

**症状**：服务器上 `docker-compose pull` 失败

**解决**：
1. 检查服务器是否已登录Docker Hub：`docker login`
2. 检查镜像名称是否正确
3. 检查网络连接

### 问题4：服务启动失败

**症状**：部署完成但服务未启动

**解决**：
1. 查看服务日志：`docker-compose -f docker-compose.prod.yml logs service-name`
2. 检查环境变量配置
3. 检查端口冲突
4. 检查依赖服务是否正常

## 📊 监控和维护

### 查看部署日志

```bash
# 在服务器上
cd /opt/enterprise-ai-platform
docker-compose -f docker-compose.prod.yml logs -f
```

### 查看服务状态

```bash
docker-compose -f docker-compose.prod.yml ps
```

### 回滚到上一个版本

如果需要回滚：

```bash
# 在服务器上
cd /opt/enterprise-ai-platform
export IMAGE_TAG=previous-tag
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 🔐 安全建议

1. **定期轮换Secrets**：定期更新Docker Hub Token和SSH密钥
2. **最小权限原则**：Docker Hub Token只授予必要权限
3. **环境隔离**：生产、测试、开发环境使用不同的Docker Hub仓库
4. **日志审计**：定期检查GitHub Actions日志
5. **备份策略**：定期备份数据库和配置文件

## 📚 相关文档

- [GitHub Actions文档](https://docs.github.com/en/actions)
- [Docker Hub文档](https://docs.docker.com/docker-hub/)
- [Docker Compose文档](https://docs.docker.com/compose/)




