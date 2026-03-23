# Docker Hub自动化部署 - 快速开始

## 🚀 5分钟快速配置

### 步骤1：配置Docker Hub（2分钟）

1. **注册/登录Docker Hub**
   - 访问 https://hub.docker.com
   - 注册账号（如果还没有）

2. **创建Access Token**
   - Account Settings → Security → New Access Token
   - 权限：Read & Write
   - 复制Token（只显示一次）

### 步骤2：配置GitHub Secrets（2分钟）

进入GitHub仓库 → Settings → Secrets and variables → Actions → New repository secret

添加以下5个Secrets：

```
DOCKER_HUB_USERNAME = your-dockerhub-username
DOCKER_HUB_TOKEN = dckr_pat_xxxxx
SSH_PRIVATE_KEY = [从 enterprise_ai_platform.pem 文件读取完整内容]
SERVER_HOST = 43.143.139.197
SERVER_USER = root
```

### 步骤3：服务器初始化（1分钟）

SSH到服务器执行：

```bash
# 创建目录
mkdir -p /opt/enterprise-ai-platform
cd /opt/enterprise-ai-platform

# 初始化Git（可选）
git init
git remote add origin https://github.com/PMLiuyubin/enterprise-ai-platform.git
git pull origin main

# 登录Docker Hub
docker login

# 创建环境变量文件
cp .env.example .env.prod
# 编辑 .env.prod 配置生产环境变量
```

### 步骤4：首次部署

1. 在GitHub仓库点击 **Actions**
2. 选择 **Build and Deploy to Docker Hub**
3. 点击 **Run workflow**
4. 等待完成

## ✅ 完成！

之后每次推送到 `main` 分支都会自动部署。

## 📋 检查清单

- [ ] Docker Hub账号已注册
- [ ] Access Token已创建
- [ ] GitHub Secrets已配置（5个）
- [ ] 服务器目录已创建
- [ ] 服务器已登录Docker Hub
- [ ] docker-compose.prod.yml已上传到服务器
- [ ] 首次部署已测试

## 🔍 验证部署

```bash
# SSH到服务器
ssh -i enterprise_ai_platform.pem root@43.143.139.197

# 检查服务状态
cd /opt/enterprise-ai-platform
docker-compose -f docker-compose.prod.yml ps

# 检查健康状态
curl http://localhost:8080/health
curl http://localhost:3000/api/health
```

## 🆘 遇到问题？

参考详细文档：
- `docs/deployment/dockerhub-deployment-setup-guide.md` - 详细配置指南
- `docs/deployment/dockerhub-deployment-analysis.md` - 方案分析
- `docs/deployment/github-actions-dockerhub-deployment.md` - 完整文档




