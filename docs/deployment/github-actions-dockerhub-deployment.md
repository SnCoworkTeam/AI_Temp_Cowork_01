# GitHub Actions + Docker Hub 自动化部署方案

## 📋 方案概述

这是一个专业的CI/CD自动化部署方案，实现：
- **代码提交** → 自动触发构建
- **构建Docker镜像** → 推送到Docker Hub
- **SSH远程部署** → 服务器自动拉取镜像并重启服务

## 🎯 方案优势

1. **自动化程度高**：代码提交即自动部署，无需手动操作
2. **质量保证**：构建前自动运行测试，确保代码质量
3. **版本管理**：每个镜像都有版本标签，便于回滚
4. **专业标准**：符合DevOps最佳实践
5. **减少错误**：避免手动部署的人为错误

## 🏗️ 架构流程

```
开发者提交代码
    ↓
GitHub Actions 触发
    ↓
运行测试（test, frontend-test）
    ↓
构建Docker镜像（并行构建所有服务）
    ↓
推送镜像到Docker Hub
    ↓
SSH连接到服务器
    ↓
执行 docker-compose pull
    ↓
执行 docker-compose up -d
    ↓
健康检查
    ↓
部署完成
```

## 📝 实施步骤

### 步骤1：配置Docker Hub

1. **注册Docker Hub账号**（如果还没有）
   - 访问 https://hub.docker.com
   - 注册账号并登录

2. **创建Access Token**
   - 登录Docker Hub
   - 进入 Account Settings → Security → New Access Token
   - 创建Token，权限选择：Read & Write
   - 保存Token（只显示一次）

3. **配置GitHub Secrets**
   - 进入GitHub仓库 → Settings → Secrets and variables → Actions
   - 添加以下Secrets：
     - `DOCKER_HUB_USERNAME`: Docker Hub用户名
     - `DOCKER_HUB_TOKEN`: Docker Hub Access Token
     - `SSH_PRIVATE_KEY`: SSH私钥（服务器部署用）
     - `SERVER_HOST`: 服务器IP（如：43.143.139.197）
     - `SERVER_USER`: 服务器用户名（如：root）

### 步骤2：创建生产环境docker-compose.yml

创建 `docker-compose.prod.yml`，使用Docker Hub镜像而不是本地构建：

```yaml
version: '3.8'

services:
  # 使用Docker Hub镜像
  api-gateway:
    image: ${DOCKER_HUB_USERNAME}/enterprise-ai-api-gateway:${IMAGE_TAG:-latest}
    # ... 其他配置
```

### 步骤3：创建GitHub Actions Workflow

创建 `.github/workflows/deploy-dockerhub.yml`，实现完整的CI/CD流程。

### 步骤4：服务器端配置

在服务器上：
1. 确保Docker和Docker Compose已安装
2. 配置SSH密钥认证
3. 创建项目目录并初始化git仓库
4. 配置生产环境变量文件

## 🔧 详细配置

### GitHub Secrets配置清单

| Secret名称 | 说明 | 示例值 |
|-----------|------|--------|
| `DOCKER_HUB_USERNAME` | Docker Hub用户名 | `your-username` |
| `DOCKER_HUB_TOKEN` | Docker Hub Access Token | `dckr_pat_xxxxx` |
| `SSH_PRIVATE_KEY` | SSH私钥内容 | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SERVER_HOST` | 服务器IP地址 | `43.143.139.197` |
| `SERVER_USER` | 服务器用户名 | `root` |

### 服务器目录结构

```
/opt/enterprise-ai-platform/
├── docker-compose.prod.yml    # 生产环境配置
├── .env.prod                  # 生产环境变量
├── .env                       # 环境变量（从.env.prod复制）
└── logs/                      # 日志目录
```

## 🚀 使用流程

1. **开发完成**：提交代码到main分支
2. **自动触发**：GitHub Actions自动运行
3. **构建镜像**：所有服务镜像并行构建
4. **推送镜像**：自动推送到Docker Hub
5. **自动部署**：SSH到服务器执行部署命令
6. **健康检查**：自动验证部署是否成功

## 📊 监控和日志

- GitHub Actions提供详细的构建和部署日志
- 服务器端可以通过 `docker-compose logs` 查看服务日志
- 部署失败会自动通知（可配置）

## ⚠️ 注意事项

1. **首次部署**：需要手动在服务器上初始化项目目录
2. **数据库迁移**：部署前会自动运行数据库迁移
3. **回滚机制**：可以通过GitHub Actions手动触发回滚
4. **安全考虑**：所有敏感信息都存储在GitHub Secrets中

## 🔄 回滚方案

如果部署失败，可以：
1. 在GitHub Actions中查看失败原因
2. 手动SSH到服务器执行回滚命令
3. 或使用GitHub Actions的rollback workflow




