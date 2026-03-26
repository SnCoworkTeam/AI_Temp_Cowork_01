# Git 自动化 Docker 容器部署完整指南

## 📋 概述

本项目通过 **GitHub Actions** 实现完整的 CI/CD 自动化部署流程，支持从代码提交到 Docker 容器自动部署的全流程自动化。

## 🏗️ 部署架构

### 两种部署方案

#### 方案1: 直接构建部署（`.github/workflows/deploy.yml`）

```
代码提交 → 运行测试 → 构建镜像 → SSH部署 → 服务器构建 → 启动容器
```

**特点**：
- 在服务器上直接构建 Docker 镜像
- 适合开发环境或私有部署
- 不需要 Docker Hub 账号

#### 方案2: Docker Hub 部署（`.github/workflows/deploy-dockerhub.yml`）

```
代码提交 → 运行测试 → 构建镜像 → 推送到Docker Hub → SSH部署 → 拉取镜像 → 启动容器
```

**特点**：
- 镜像推送到 Docker Hub
- 服务器只需拉取镜像，无需构建
- 适合生产环境，部署更快
- 需要 Docker Hub 账号

## 🔧 需要在 Git 中配置的内容

### 1. GitHub Secrets 配置（必需）

在 GitHub 仓库中配置以下 Secrets：

#### 方法1: 通过 GitHub Web 界面

1. 进入仓库：`Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret` 添加以下 Secrets：

| Secret 名称 | 说明 | 示例值 |
|------------|------|--------|
| `SSH_PRIVATE_KEY` | SSH 私钥（完整内容） | `-----BEGIN RSA PRIVATE KEY-----...` |
| `SERVER_HOST` | 服务器 IP 地址 | `43.143.139.197` |
| `SERVER_USER` | 服务器用户名 | `ubuntu` |
| `DOCKER_HUB_USERNAME` | Docker Hub 用户名（方案2需要） | `your-username` |
| `DOCKER_HUB_TOKEN` | Docker Hub Access Token（方案2需要） | `dckr_pat_...` |

#### 方法2: 使用 GitHub CLI（推荐）

```powershell
# 1. 安装 GitHub CLI（如果未安装）
# Windows: winget install GitHub.cli
# 或下载: https://cli.github.com/

# 2. 登录 GitHub
gh auth login

# 3. 配置 SSH 私钥
Get-Content enterprise_ai_platform.pem -Raw | gh secret set SSH_PRIVATE_KEY

# 4. 配置服务器信息
gh secret set SERVER_HOST --body "43.143.139.197"
gh secret set SERVER_USER --body "ubuntu"

# 5. 配置 Docker Hub（如果使用方案2）
gh secret set DOCKER_HUB_USERNAME --body "your-dockerhub-username"
gh secret set DOCKER_HUB_TOKEN --body "your-dockerhub-token"
```

#### 方法3: 使用自动配置脚本

项目已提供自动配置脚本：

```powershell
# 运行自动配置脚本
powershell -ExecutionPolicy Bypass -File scripts/setup-github-secrets.ps1
```

### 2. GitHub Actions 工作流文件（已配置）

项目已包含以下工作流文件，位于 `.github/workflows/` 目录：

- ✅ `deploy.yml` - 直接构建部署工作流
- ✅ `deploy-dockerhub.yml` - Docker Hub 部署工作流
- ✅ `test-suite.yml` - 测试套件
- ✅ `frontend-ci.yml` - 前端 CI
- ✅ `pr-checks.yml` - PR 检查

### 3. Docker Compose 配置文件

- ✅ `docker-compose.yml` - 开发环境配置
- ✅ `docker-compose.prod.yml` - 生产环境配置（使用 Docker Hub 镜像）

## 🚀 自动化部署流程

### 触发条件

部署工作流会在以下情况自动触发：

1. **Push 到 main 分支** - 自动部署到生产环境
2. **创建版本标签**（如 `v1.0.0`）- 自动部署
3. **手动触发** - 在 GitHub Actions 页面手动运行

### 部署流程步骤

#### 方案1: 直接构建部署流程

```yaml
1. 代码提交到 main 分支
   ↓
2. 运行测试（test, frontend-test）
   ↓
3. 构建 Docker 镜像（验证构建）
   ↓
4. SSH 连接到服务器
   ↓
5. 拉取最新代码
   ↓
6. 运行数据库迁移
   ↓
7. 备份当前容器状态
   ↓
8. 停止旧版本服务
   ↓
9. 构建新版本镜像
   ↓
10. 启动新版本容器
   ↓
11. 健康检查
   ↓
12. 部署完成
```

#### 方案2: Docker Hub 部署流程

```yaml
1. 代码提交到 main 分支
   ↓
2. 运行测试（test, frontend-test）
   ↓
3. 构建 Docker 镜像
   ↓
4. 推送镜像到 Docker Hub
   ↓
5. SSH 连接到服务器
   ↓
6. 拉取最新代码
   ↓
7. 拉取最新 Docker 镜像
   ↓
8. 运行数据库迁移
   ↓
9. 停止旧版本服务
   ↓
10. 启动新版本容器（使用拉取的镜像）
   ↓
11. 健康检查
   ↓
12. 部署完成
```

## 📝 详细配置步骤

### 步骤1: 配置 GitHub Secrets

#### 获取 SSH 私钥

SSH 私钥文件通常是 `enterprise_ai_platform.pem`，位置：
- 项目根目录：`./enterprise_ai_platform.pem`
- 用户目录：`~/.ssh/enterprise_ai_platform.pem`

**配置 SSH_PRIVATE_KEY**：

```powershell
# 读取密钥文件完整内容
$keyContent = Get-Content enterprise_ai_platform.pem -Raw

# 配置到 GitHub Secrets
$keyContent | gh secret set SSH_PRIVATE_KEY
```

#### 获取 Docker Hub Token（方案2需要）

1. 登录 Docker Hub：https://hub.docker.com
2. 进入 `Account Settings` → `Security` → `New Access Token`
3. 创建 Token，权限选择：`Read & Write`
4. 复制 Token（只显示一次）

**配置 Docker Hub Secrets**：

```powershell
gh secret set DOCKER_HUB_USERNAME --body "your-username"
gh secret set DOCKER_HUB_TOKEN --body "your-token"
```

### 步骤2: 服务器准备

#### 服务器端需要安装的软件

```bash
# SSH 登录服务器
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197

# 安装 Docker 和 Docker Compose
sudo apt update
sudo apt install -y docker.io docker-compose

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到 docker 组（避免每次使用 sudo）
sudo usermod -aG docker $USER
# 重新登录使权限生效

# 克隆项目（如果还没有）
cd /opt
sudo git clone https://github.com/your-username/enterprise-ai-platform.git
sudo chown -R ubuntu:ubuntu enterprise-ai-platform
cd enterprise-ai-platform
```

#### 配置服务器 Git 访问

```bash
# 如果使用私有仓库，配置 Git 凭据
git config --global credential.helper store

# 或者使用 SSH 密钥
ssh-keygen -t rsa -b 4096 -C "deploy@server"
# 将公钥添加到 GitHub
cat ~/.ssh/id_rsa.pub
```

### 步骤3: 配置 Docker Compose 生产环境

确保 `docker-compose.prod.yml` 配置正确：

```yaml
# 方案1: 使用本地构建
services:
  api-gateway:
    build:
      context: ./api-gateway
      dockerfile: Dockerfile.dev

# 方案2: 使用 Docker Hub 镜像
services:
  api-gateway:
    image: your-username/enterprise-ai-platform-api-gateway:latest
```

### 步骤4: 测试部署

#### 手动触发部署

1. 进入 GitHub 仓库
2. 点击 `Actions` 标签
3. 选择 `Deploy to Server` 或 `Build and Deploy to Docker Hub`
4. 点击 `Run workflow`
5. 选择环境（production/staging/development）
6. 点击 `Run workflow` 按钮

#### 查看部署日志

部署过程中可以：
- 在 GitHub Actions 页面查看实时日志
- SSH 到服务器查看容器状态：`docker-compose ps`
- 查看服务日志：`docker-compose logs -f api-gateway`

## 🔍 验证配置

### 验证 GitHub Secrets

```powershell
# 使用 GitHub CLI 查看 Secrets 列表
gh secret list

# 应该看到：
# SSH_PRIVATE_KEY
# SERVER_HOST
# SERVER_USER
# DOCKER_HUB_USERNAME (如果使用方案2)
# DOCKER_HUB_TOKEN (如果使用方案2)
```

### 验证 SSH 连接

```powershell
# 测试 SSH 连接
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197 "echo 'SSH连接成功'"
```

### 验证 Docker Hub 登录（方案2）

```bash
# 在服务器上测试 Docker Hub 登录
docker login -u your-username -p your-token
docker pull your-username/enterprise-ai-platform-api-gateway:latest
```

## 📊 工作流文件说明

### deploy.yml（直接构建部署）

**触发条件**：
- Push 到 `main` 分支
- 创建版本标签 `v*`
- 手动触发

**工作流程**：
1. `test` - 运行 Python 测试
2. `frontend-test` - 运行前端测试和构建
3. `build-images` - 验证 Docker 镜像构建
4. `deploy` - SSH 部署到服务器

### deploy-dockerhub.yml（Docker Hub 部署）

**触发条件**：
- Push 到 `main` 分支
- 创建版本标签 `v*`
- 手动触发（可选择跳过测试）

**工作流程**：
1. `test` - 运行 Python 测试
2. `frontend-test` - 运行前端测试和构建
3. `build-and-push` - 构建并推送镜像到 Docker Hub
4. `deploy` - SSH 部署到服务器，拉取镜像并启动

## 🛠️ 故障排查

### 问题1: SSH 连接失败

**错误**：`Permission denied (publickey)`

**解决方案**：
1. 检查 `SSH_PRIVATE_KEY` Secret 是否正确配置
2. 确保密钥文件格式正确（包含 `-----BEGIN` 和 `-----END`）
3. 测试 SSH 连接：`ssh -i key.pem user@host`

### 问题2: Docker 构建失败

**错误**：`docker build failed`

**解决方案**：
1. 检查 Dockerfile 是否存在
2. 查看构建日志中的具体错误
3. 确保所有依赖文件都在正确位置

### 问题3: 部署后服务无法启动

**错误**：`健康检查失败`

**解决方案**：
1. SSH 到服务器查看日志：`docker-compose logs service-name`
2. 检查环境变量配置
3. 检查端口是否被占用
4. 查看数据库连接是否正常

### 问题4: Docker Hub 推送失败

**错误**：`unauthorized: authentication required`

**解决方案**：
1. 检查 `DOCKER_HUB_USERNAME` 和 `DOCKER_HUB_TOKEN` 是否正确
2. 确保 Token 有 `Read & Write` 权限
3. 验证 Docker Hub 账号状态

## 📚 相关文档

- [GitHub Secrets 配置指南](./GITHUB_SECRETS_SETUP.md)
- [Docker Hub 部署指南](./docs/deployment/github-actions-dockerhub-deployment.md)
- [CI/CD 实施总结](./CI_CD_IMPLEMENTATION_SUMMARY.md)
- [部署指南](./docs/development-docs/DEPLOYMENT_GUIDE.md)

## 🎯 最佳实践

1. **使用环境分支**：
   - `main` → 生产环境
   - `develop` → 开发环境
   - `staging` → 预发布环境

2. **版本标签**：
   - 使用语义化版本：`v1.0.0`, `v1.1.0`
   - 创建标签触发部署：`git tag v1.0.0 && git push origin v1.0.0`

3. **回滚策略**：
   - 保留旧版本镜像
   - 使用 Git 标签快速回滚
   - 服务器上保留备份配置

4. **监控和告警**：
   - 配置部署通知（邮件/钉钉/企业微信）
   - 监控服务健康状态
   - 设置部署失败告警

## ✅ 配置检查清单

- [ ] GitHub Secrets 已配置（SSH_PRIVATE_KEY, SERVER_HOST, SERVER_USER）
- [ ] Docker Hub Secrets 已配置（如果使用方案2）
- [ ] 服务器已安装 Docker 和 Docker Compose
- [ ] 服务器已克隆项目代码
- [ ] SSH 连接测试通过
- [ ] GitHub Actions 工作流文件存在
- [ ] docker-compose.prod.yml 配置正确
- [ ] 测试部署流程成功

## 🚀 快速开始

### 步骤1: 配置 GitHub Secrets（5分钟）

**方法A: 使用自动配置脚本（推荐）**
```powershell
# 运行自动配置脚本
.\configure-github-secrets.ps1
```

**方法B: 手动配置**
```powershell
# PowerShell 正确语法（注意：不能使用 < 重定向）
Get-Content enterprise_ai_platform.pem -Raw | gh secret set SSH_PRIVATE_KEY
gh secret set SERVER_HOST --body "43.143.139.197"
gh secret set SERVER_USER --body "ubuntu"
```

⚠️ **重要提示**：在 PowerShell 中，不能使用 `<` 重定向操作符，必须使用 `Get-Content` 命令！

### 步骤2: 提交工作流文件到 GitHub

确保 `.github/workflows/` 目录下的工作流文件已提交到 GitHub：

```powershell
# 检查工作流文件是否存在
Get-ChildItem .github\workflows\*.yml

# 提交工作流文件
git add .github/workflows/
git commit -m "添加自动部署工作流"
git push origin main
```

### 步骤3: 验证工作流

1. 进入 GitHub 仓库页面
2. 点击 `Actions` 标签
3. 应该能看到以下工作流：
   - ✅ **🚀 自动部署到服务器** (auto-deploy.yml) - 推送代码自动触发
   - ✅ **Deploy to Server** (deploy.yml) - 完整测试后部署
   - ✅ **Deploy to Server (Simple)** (deploy-simple.yml) - 手动触发

### 步骤4: 测试自动部署

推送代码到 main 分支即可自动触发部署：

```powershell
# 做一个小改动（比如更新 README）
echo "# 测试自动部署" >> README.md
git add .
git commit -m "测试自动部署"
git push origin main
```

推送后，在 GitHub Actions 页面可以看到部署流程自动运行！

2. **准备服务器**（10分钟）
   ```bash
   # SSH 到服务器执行
   sudo apt install -y docker.io docker-compose
   cd /opt && git clone <your-repo-url>
   ```

3. **测试部署**（2分钟）
   - 在 GitHub Actions 页面手动触发部署
   - 查看部署日志
   - 验证服务是否正常

4. **自动部署**（完成）
   - 推送代码到 `main` 分支
   - 自动触发部署流程

---

**配置完成后，每次推送代码到 main 分支，系统会自动：**
1. ✅ 运行测试
2. ✅ 构建 Docker 镜像
3. ✅ 部署到服务器
4. ✅ 启动服务
5. ✅ 健康检查

**无需任何手动操作！** 🎉

