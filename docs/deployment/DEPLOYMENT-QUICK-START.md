# 🚀 快速部署指南 - Remote.SSH

本指南将帮助您快速配置 Remote.SSH 并部署企业AI平台到云服务器。

## 📋 服务器信息

- **IP地址**: `43.143.139.197`
- **用户名**: `ubuntu`
- **密码**: `Liu@bner1983`
- **密钥文件**: `enterprise_ai_platform.pem`

## ⚡ 一键部署（最简单）

### 步骤1：准备密钥文件

将 `enterprise_ai_platform.pem` 放置在以下位置之一：
- `C:\Users\YourUsername\.ssh\enterprise_ai_platform.pem`（推荐）
- 项目根目录：`E:\enterprise-ai-platform\enterprise_ai_platform.pem`

### 步骤2：配置 SSH（可选，但推荐）

编辑 `C:\Users\YourUsername\.ssh\config`，添加：

```
Host enterprise-ai-server
    HostName 43.143.139.197
    User ubuntu
    IdentityFile C:\Users\YourUsername\.ssh\enterprise_ai_platform.pem
    StrictHostKeyChecking no
    ServerAliveInterval 60
```

**注意：** 将路径替换为您的实际密钥文件路径。

### 步骤3：执行一键部署

在 PowerShell 中（项目根目录）：

```powershell
.\scripts\deployment\deploy-remote.ps1
```

这个脚本会自动完成：
1. ✅ 上传代码到服务器
2. ✅ 初始化服务器环境（安装 Docker、Git 等）
3. ✅ 配置环境变量
4. ✅ 构建并启动所有服务

### 步骤4：访问服务

部署成功后，访问：
- **Web UI**: http://43.143.139.197:3000
- **API 文档**: http://43.143.139.197:8001/api/docs

---

## 🔧 手动部署（分步执行）

### 方法1：使用 VS Code Remote.SSH

#### 1. 配置 Remote.SSH

1. 按 `F1` → 输入 `Remote-SSH: Connect to Host`
2. 选择 `enterprise-ai-server`（如果已配置 SSH config）
3. 或选择 `Add New SSH Host` → 输入 `ubuntu@43.143.139.197`
4. 选择配置文件位置（默认即可）
5. 如果提示输入密码，输入：`Liu@bner1983`

#### 2. 上传代码

在本地 PowerShell 中：

```powershell
.\scripts\deployment\upload-to-server.ps1
```

#### 3. 在远程终端中部署

在 VS Code 的远程终端中执行：

```bash
# 首次部署：初始化服务器
sudo bash scripts/deployment/setup-server.sh

# 配置环境变量
cd /opt/enterprise-ai-platform
cp env.example .env.production
nano .env.production  # 编辑配置，至少设置 OPENAI_API_KEY

# 执行部署
bash scripts/deployment/deploy-server.sh --env production
```

### 方法2：直接 SSH 连接

#### 1. 测试连接

```powershell
# 使用密钥文件
ssh -i C:\Users\YourUsername\.ssh\enterprise_ai_platform.pem ubuntu@43.143.139.197

# 或使用密码
ssh ubuntu@43.143.139.197
# 密码: Liu@bner1983
```

#### 2. 上传代码

```powershell
.\scripts\deployment\upload-to-server.ps1
```

#### 3. 部署

在服务器上执行：

```bash
cd /opt/enterprise-ai-platform
sudo bash scripts/deployment/setup-server.sh
cp env.example .env.production
nano .env.production  # 编辑配置
bash scripts/deployment/deploy-server.sh --env production
```

---

## 📝 环境变量配置

编辑 `.env.production` 文件，至少配置以下变量：

```bash
# AI 服务配置（必需）
OPENAI_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=gpt-4

# 数据库配置（如果使用外部数据库）
DB_HOST=postgres
DB_PORT=5432
DB_USER=ai_user
DB_PASSWORD=ai_password
DB_NAME=ai_platform

# Redis 配置
REDIS_HOST=redis
REDIS_PORT=6379
```

---

## 🔍 验证部署

### 检查服务状态

```bash
# 在服务器上执行
cd /opt/enterprise-ai-platform
docker compose ps
```

应该看到所有服务都在运行：
- ✅ redis
- ✅ mcp-gateway
- ✅ workflow-engine
- ✅ auth-service
- ✅ knowledge-base
- ✅ web-ui

### 检查服务健康

```bash
# 测试各个服务
curl http://localhost:8001/api/health  # MCP Gateway
curl http://localhost:8002/api/health  # Workflow Engine
curl http://localhost:8003/health      # Auth Service
curl http://localhost:8004/api/health  # Knowledge Base
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f mcp-gateway
docker compose logs -f web-ui
```

---

## 🛠️ 常用操作

### 更新代码

```powershell
# 本地：上传最新代码
.\scripts\deployment\upload-to-server.ps1

# 远程：重新部署
cd /opt/enterprise-ai-platform
git pull  # 如果使用 Git
bash scripts/deployment/deploy-server.sh --env production
```

### 重启服务

```bash
cd /opt/enterprise-ai-platform
docker compose restart
```

### 停止服务

```bash
cd /opt/enterprise-ai-platform
docker compose down
```

### 查看资源使用

```bash
docker stats
```

---

## ❓ 常见问题

### Q1: 密钥文件权限错误

**A:** 在 PowerShell 中执行：
```powershell
icacls enterprise_ai_platform.pem /inheritance:r
icacls enterprise_ai_platform.pem /grant:r "%USERNAME%:R"
```

### Q2: 无法连接到服务器

**A:** 检查：
1. 服务器 IP 是否正确
2. 云服务器安全组是否开放 22 端口
3. 服务器是否运行中
4. 网络连接是否正常

### Q3: Docker 镜像拉取失败

**A:** 在服务器上执行：
```bash
sudo bash scripts/deployment/use-china-mirrors.sh
sudo systemctl restart docker
```

### Q4: 服务启动失败

**A:** 查看详细日志：
```bash
docker compose logs <service-name>
```

检查环境变量配置是否正确。

---

## 📚 更多文档

- [详细部署文档](scripts/deployment/README-REMOTE-SSH.md)
- [服务器部署脚本说明](scripts/deployment/README.md)
- [快速部署指南](scripts/deployment/QUICK_START.md)

---

## 🎉 完成！

部署成功后，您可以通过以下地址访问服务：

- 🌐 **Web UI**: http://43.143.139.197:3000
- 📡 **MCP Gateway API**: http://43.143.139.197:8001
- ⚙️ **Workflow Engine API**: http://43.143.139.197:8002
- 🔐 **Auth Service API**: http://43.143.139.197:8003
- 📚 **Knowledge Base API**: http://43.143.139.197:8004

**注意：** 确保云服务器安全组已开放相应端口！

