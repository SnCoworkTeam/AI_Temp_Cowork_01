# Remote.SSH 部署指南

本指南将帮助您配置 VS Code Remote.SSH 并部署企业AI平台到云服务器。

## 📋 前置要求

1. ✅ VS Code 已安装 Remote.SSH 扩展
2. ✅ 云服务器信息：
   - IP: `43.143.139.197`
   - 用户名: `ubuntu`
   - 密码: `Liu@bner1983`
   - 密钥文件: `enterprise_ai_platform.pem`

## 🚀 快速开始

### 方法1：使用一键部署脚本（推荐）

```powershell
# 在项目根目录执行
.\scripts\deployment\deploy-remote.ps1
```

这个脚本会自动：
1. ✅ 上传代码到服务器
2. ✅ 初始化服务器环境（安装 Docker 等）
3. ✅ 配置环境变量
4. ✅ 部署并启动所有服务

### 方法2：分步执行

#### 步骤1：配置 Remote.SSH

1. **准备密钥文件**
   - 将 `enterprise_ai_platform.pem` 放置在 `C:\Users\YourUsername\.ssh\` 目录
   - 或者放在项目根目录

2. **配置 SSH Config**
   - 编辑 `C:\Users\YourUsername\.ssh\config`
   - 添加以下配置：
   ```
   Host enterprise-ai-server
       HostName 43.143.139.197
       User ubuntu
       IdentityFile C:\Users\YourUsername\.ssh\enterprise_ai_platform.pem
       StrictHostKeyChecking no
       ServerAliveInterval 60
       ServerAliveCountMax 3
   ```

3. **在 VS Code 中连接**
   - 按 `F1` → 输入 `Remote-SSH: Connect to Host`
   - 选择 `enterprise-ai-server`
   - 如果提示输入密码，输入：`Liu@bner1983`

#### 步骤2：上传代码

```powershell
# 使用上传脚本
.\scripts\deployment\upload-to-server.ps1
```

#### 步骤3：在服务器上部署

在 VS Code 的远程终端中执行：

```bash
# 首次部署：初始化服务器
sudo bash scripts/deployment/setup-server.sh

# 配置环境变量
cd /opt/enterprise-ai-platform
cp env.example .env.production
nano .env.production  # 编辑配置

# 执行部署
bash scripts/deployment/deploy-server.sh --env production
```

## 🔧 详细配置说明

### SSH 密钥文件位置

Windows 系统推荐位置：
- `C:\Users\YourUsername\.ssh\enterprise_ai_platform.pem`

设置密钥文件权限（PowerShell）：
```powershell
icacls enterprise_ai_platform.pem /inheritance:r
icacls enterprise_ai_platform.pem /grant:r "%USERNAME%:R"
```

### 测试 SSH 连接

```powershell
# 测试连接
ssh -i C:\Users\YourUsername\.ssh\enterprise_ai_platform.pem ubuntu@43.143.139.197

# 或者使用配置的 Host
ssh enterprise-ai-server
```

## 📝 常用命令

### 本地操作

```powershell
# 上传代码
.\scripts\deployment\upload-to-server.ps1

# 一键部署
.\scripts\deployment\deploy-remote.ps1

# 跳过上传，只部署
.\scripts\deployment\deploy-remote.ps1 -SkipUpload

# 跳过初始化，只部署
.\scripts\deployment\deploy-remote.ps1 -SkipSetup
```

### 远程操作（在 VS Code 远程终端中）

```bash
# 查看服务状态
cd /opt/enterprise-ai-platform
docker compose ps

# 查看日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f mcp-gateway

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 更新代码并重新部署
git pull
bash scripts/deployment/deploy-server.sh --env production
```

## 🌐 访问服务

部署成功后，可以通过以下地址访问：

- **Web UI**: http://43.143.139.197:3000
- **MCP Gateway**: http://43.143.139.197:8001
- **Workflow Engine**: http://43.143.139.197:8002
- **Auth Service**: http://43.143.139.197:8003
- **Knowledge Base**: http://43.143.139.197:8004

**注意：** 确保云服务器安全组已开放以下端口：
- 22 (SSH)
- 3000 (Web UI)
- 8001-8004 (后端服务)

## ❓ 故障排除

### 问题1：SSH 连接失败

**症状：** 无法连接到服务器

**解决方案：**
1. 检查服务器 IP 是否正确
2. 检查密钥文件路径是否正确
3. 检查云服务器安全组是否开放 22 端口
4. 尝试使用密码连接：`ssh ubuntu@43.143.139.197`

### 问题2：密钥文件权限错误

**症状：** SSH 提示 "Permissions too open"

**解决方案（PowerShell）：**
```powershell
icacls enterprise_ai_platform.pem /inheritance:r
icacls enterprise_ai_platform.pem /grant:r "%USERNAME%:R"
```

### 问题3：代码上传失败

**症状：** rsync 或 scp 命令失败

**解决方案：**
1. 确保已安装 Git for Windows（包含 scp）
2. 或安装 WSL（包含 rsync）
3. 检查网络连接
4. 检查服务器磁盘空间

### 问题4：Docker 镜像拉取失败

**症状：** 部署时 Docker 镜像拉取超时

**解决方案：**
```bash
# 在服务器上执行
sudo bash scripts/deployment/use-china-mirrors.sh
sudo systemctl restart docker
```

### 问题5：服务启动失败

**症状：** 容器启动后立即退出

**解决方案：**
```bash
# 查看详细日志
docker compose logs <service-name>

# 检查环境变量
cat .env.production

# 检查端口占用
netstat -tulpn | grep <port>
```

## 📚 相关文档

- [快速部署指南](QUICK_START.md)
- [服务器部署脚本说明](README.md)
- [环境变量配置](../env.example)

## 🔐 安全建议

1. **密钥文件安全**
   - 不要将密钥文件提交到 Git 仓库
   - 定期更换密钥
   - 使用强密码保护密钥文件

2. **服务器安全**
   - 定期更新系统
   - 配置防火墙规则
   - 使用 SSH 密钥认证而非密码
   - 限制 SSH 访问 IP

3. **环境变量安全**
   - 不要将 `.env` 文件提交到 Git
   - 使用强密码和密钥
   - 定期轮换 API 密钥

## 💡 提示

- 使用 VS Code Remote.SSH 可以直接在服务器上编辑代码和查看日志
- 建议在本地开发，在服务器上部署和测试
- 使用 Docker Compose 可以方便地管理多个服务
- 定期备份服务器数据

