# 部署脚本使用指南

## 📋 脚本说明

本目录包含企业AI平台的完整部署脚本，支持从Git拉取代码并自动部署到服务器。

### 脚本列表

1. **`setup-server.sh`** - 服务器初始化脚本（首次部署时先执行，安装Docker、Git等）
2. **`deploy-server.sh`** - 主部署脚本（日常部署使用，会自动拉取代码并部署）
3. **`install-docker-manual.sh`** - 手动安装Docker脚本（当setup-server.sh中Docker安装失败时使用）
4. **`../test-deployment.sh`** - 部署验证测试脚本

### 执行顺序

```
首次部署流程：
setup-server.sh (安装环境) 
    ↓
配置环境变量 (.env.production)
    ↓
deploy-server.sh (部署应用)
```

```
日常更新流程：
deploy-server.sh (自动拉取代码并部署)
```

---

## 🚀 快速开始

### 执行顺序说明

**重要：请按以下顺序执行脚本**

1. **首次部署**（新服务器）：
   - 先执行 `setup-server.sh` → 安装Docker、Git等基础环境
   - 再执行 `deploy-server.sh` → 部署应用

2. **日常更新**（已有环境）：
   - 直接执行 `deploy-server.sh` → 自动拉取代码并部署

3. **Docker安装失败时**：
   - 如果 `setup-server.sh` 中Docker安装失败，可以单独执行 `install-docker-manual.sh`

---

### 首次部署（在新服务器上）

#### 步骤1: 上传初始化脚本到服务器

```bash
# 将脚本上传到服务器
scp scripts/deployment/setup-server.sh user@your-server:/tmp/
scp scripts/deployment/deploy-server.sh user@your-server:/tmp/
```

#### 步骤2: 在服务器上运行初始化（先执行这个）

```bash
# SSH登录服务器
ssh user@your-server

# 运行初始化脚本（安装Docker、Git等）
sudo bash /tmp/setup-server.sh --git-url https://github.com/PMLiuyubin/enterprise-ai-platform.git --branch main
```

**如果Docker安装失败（网络问题），可以手动安装：**

```bash
# 使用国内镜像源手动安装Docker
sudo bash /tmp/install-docker-manual.sh
```

这个脚本会：
- ✅ 安装Docker和Docker Compose
- ✅ 安装Git和其他必要工具
- ✅ 从Git克隆项目代码
- ✅ 配置防火墙规则（可选）

#### 步骤3: 配置环境变量

```bash
# 进入项目目录
cd /opt/enterprise-ai-platform

# 编辑环境变量文件
nano .env.production
```

必需配置：
- `DATABASE_URL` - 数据库连接
- `REDIS_HOST` - Redis地址
- `JWT_SECRET_KEY` - JWT密钥
- `OPENAI_API_KEY` - LLM API密钥
- `LLM_BASE_URL` - LLM服务地址（DeepSeek使用：https://api.deepseek.com/v1）

#### 步骤4: 运行部署脚本（再执行这个）

```bash
# 进入项目目录
cd /opt/enterprise-ai-platform

# 运行部署脚本（从Git拉取代码并部署）
bash scripts/deployment/deploy-server.sh --env production
```

**注意：** 如果步骤2中已经通过 `--git-url` 参数克隆了代码，步骤4会自动更新代码；如果没有，步骤4会尝试从Git拉取。

---

### 日常更新部署

#### 方法1: 直接运行部署脚本（推荐）

```bash
# SSH登录服务器
ssh user@your-server

# 进入项目目录
cd /opt/enterprise-ai-platform

# 运行部署脚本（会自动拉取最新代码）
bash scripts/deployment/deploy-server.sh --env production
```

#### 方法2: 指定Git分支

```bash
# 部署特定分支
bash scripts/deployment/deploy-server.sh --env production --branch develop
```

---

## 📖 详细使用说明

### `deploy-server.sh` - 主部署脚本

#### 基本用法

```bash
bash scripts/deployment/deploy-server.sh [选项]
```

#### 可用选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--git-url <url>` | Git仓库地址（首次部署时使用） | - |
| `--env <env>` | 部署环境 (production\|staging\|development) | production |
| `--branch <branch>` | Git分支 | main |
| `--skip-tests` | 跳过测试 | false |
| `--skip-backup` | 跳过备份 | false |
| `--skip-migration` | 跳过数据库迁移 | false |
| `--force` | 强制重新构建镜像 | false |
| `--project-dir <dir>` | 项目目录 | /opt/enterprise-ai-platform |
| `--git-username <user>` | Git用户名（可选） | 从环境变量GIT_USERNAME读取 |
| `--git-token <token>` | Git Personal Access Token（必需） | 从环境变量GIT_TOKEN读取 |
| | | **注意：GitHub不再支持密码认证，必须使用Token** |

#### 使用示例

```bash
# 基本部署（生产环境）
bash scripts/deployment/deploy-server.sh --env production

# 部署到预发布环境
bash scripts/deployment/deploy-server.sh --env staging

# 强制重新构建并跳过测试
bash scripts/deployment/deploy-server.sh --env production --force --skip-tests

# 首次部署（从Git克隆）
bash scripts/deployment/deploy-server.sh \
  --git-url https://github.com/PMLiuyubin/enterprise-ai-platform.git \
  --branch main \
  --env production

# 跳过备份和迁移（快速部署）
bash scripts/deployment/deploy-server.sh \
  --env production \
  --skip-backup \
  --skip-migration
```

---

### `setup-server.sh` - 服务器初始化脚本

#### 基本用法

```bash
sudo bash scripts/deployment/setup-server.sh [选项]
```

#### 可用选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--git-url <url>` | Git仓库地址 | - |
| `--branch <branch>` | Git分支 | main |
| `--project-dir <dir>` | 项目目录 | /opt/enterprise-ai-platform |

#### 使用示例

```bash
# 初始化服务器并从Git克隆项目
sudo bash scripts/deployment/setup-server.sh \
  --git-url https://github.com/PMLiuyubin/enterprise-ai-platform.git \
  --branch main
```

---

## 🔄 部署流程

部署脚本按以下顺序执行：

1. ✅ **检查Docker环境** - 验证Docker和Docker Compose是否安装
2. ✅ **准备项目目录** - 从Git拉取/更新代码
3. ✅ **检查环境变量** - 验证环境变量文件是否存在
4. ✅ **备份数据** - 备份现有数据（可选）
5. ✅ **停止现有服务** - 优雅停止正在运行的服务
6. ✅ **启动数据库** - 启动PostgreSQL和Redis
7. ✅ **构建镜像** - 构建所有服务的Docker镜像
8. ✅ **按顺序启动服务**：
   - Redis（基础服务）
   - MCP Gateway（基础服务）
   - Auth Service
   - Knowledge Base
   - Workflow Engine（依赖MCP Gateway）
   - Web UI（最后启动，依赖所有后端服务）
9. ✅ **运行数据库迁移** - 执行Alembic迁移
10. ✅ **验证部署** - 运行健康检查和测试
11. ✅ **显示状态** - 显示所有服务状态
12. ✅ **显示信息** - 显示服务地址和常用命令

---

## 🛠️ 故障排查

### 问题1: Docker未安装

```bash
# 解决方案：运行初始化脚本
sudo bash scripts/deployment/setup-server.sh
```

### 问题2: Git拉取失败

**可能原因1: GitHub认证问题**

GitHub从2021年8月13日开始不再支持密码认证，必须使用Personal Access Token。

```bash
# 1. 创建Personal Access Token
# 访问: https://github.com/settings/tokens/new
# 生成新Token，至少需要repo权限

# 2. 配置Token（方式1：环境变量）
export GIT_USERNAME="lyb-005@163.com"
export GIT_TOKEN="ghp_your_token_here"

# 或方式2：命令行参数
bash scripts/deployment/deploy-server.sh \
  --git-username "lyb-005@163.com" \
  --git-token "ghp_your_token_here"

# 详细说明请查看: scripts/deployment/GIT_TOKEN_SETUP.md
```

**可能原因2: 防火墙阻止443端口**

```bash
# 1. 检查443端口
timeout 3 bash -c "echo >/dev/tcp/github.com/443" || echo "443端口被阻止"

# 2. 自动配置防火墙
sudo bash scripts/deployment/configure-firewall.sh

# 或手动配置（Ubuntu/Debian）
sudo ufw allow 443/tcp
sudo ufw reload

# 详细说明请查看: scripts/deployment/FIREWALL_FIX.md
```

**可能原因3: 网络连接问题**

```bash
# 检查网络连接
ping github.com

# 检查DNS
nslookup github.com

# 测试GitHub API
curl -I https://api.github.com
```

### 问题3: 服务启动失败

```bash
# 查看日志
docker-compose -f docker-compose.production.yml logs [service-name]

# 检查服务状态
docker-compose -f docker-compose.production.yml ps

# 重启服务
docker-compose -f docker-compose.production.yml restart [service-name]
```

### 问题4: 数据库连接失败

```bash
# 检查数据库服务
docker-compose -f docker-compose.db.yml ps

# 测试数据库连接
docker-compose -f docker-compose.db.yml exec postgres psql -U postgres -c "SELECT 1"
```

---

## 📝 环境变量配置

### 必需的环境变量

创建 `.env.production` 文件：

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@postgres:5432/enterprise_ai
REDIS_HOST=redis
REDIS_PORT=6379

# 安全配置
JWT_SECRET_KEY=your-super-secret-jwt-key-here
ENCRYPTION_KEY=your-encryption-key-here

# LLM配置（DeepSeek）
OPENAI_API_KEY=sk-your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 服务端口
MCP_GATEWAY_PORT=8001
WORKFLOW_ENGINE_PORT=8002
AUTH_SERVICE_PORT=8003
KNOWLEDGE_BASE_PORT=8004
WEB_UI_PORT=3000

# 日志级别
LOG_LEVEL=INFO
```

---

## 🔐 安全建议

1. **保护环境变量文件**
   ```bash
   chmod 600 .env.production
   ```

2. **使用强密码**
   - JWT密钥至少32字符
   - 数据库密码使用复杂密码

3. **配置防火墙**
   ```bash
   # 只允许必要的端口
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp    # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   ```

4. **定期更新**
   ```bash
   # 更新系统
   sudo apt-get update && sudo apt-get upgrade
   
   # 更新Docker镜像
   docker-compose -f docker-compose.production.yml pull
   ```

---

## 📞 获取帮助

如果遇到问题：

1. 查看日志：`docker-compose logs -f`
2. 检查服务状态：`docker-compose ps`
3. 查看部署文档：`docs/development-docs/DEPLOYMENT_GUIDE.md`
4. 运行测试：`bash scripts/test-deployment.sh`

---

## ✅ 部署检查清单

部署完成后，检查：

- [ ] 所有服务正常运行
- [ ] 健康检查通过
- [ ] 数据库迁移完成
- [ ] API端点可访问
- [ ] 前端界面可访问
- [ ] 自动化调试系统启用
- [ ] 日志收集正常

---

**祝你部署顺利！🚀**

