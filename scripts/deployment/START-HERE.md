# 🚀 快速开始 - Remote.SSH 部署

## 📋 准备工作

1. **准备密钥文件**
   - 将 `enterprise_ai_platform.pem` 放在 `C:\Users\YourUsername\.ssh\` 目录
   - 或放在项目根目录

2. **配置 SSH（推荐）**
   - 编辑 `C:\Users\YourUsername\.ssh\config`
   - 参考 `.ssh-config.example` 文件

## ⚡ 一键部署

在 PowerShell 中（项目根目录）：

```powershell
.\scripts\deployment\deploy-remote.ps1
```

## 📝 分步执行

### 步骤1：上传代码

```powershell
.\scripts\deployment\upload-to-server.ps1
```

### 步骤2：在 VS Code 中连接服务器

1. 按 `F1` → `Remote-SSH: Connect to Host`
2. 选择 `enterprise-ai-server` 或输入 `ubuntu@43.143.139.197`
3. 输入密码：`Liu@bner1983`

### 步骤3：在远程终端中部署

```bash
cd /opt/enterprise-ai-platform
sudo bash scripts/deployment/setup-server.sh
cp env.example .env.production
nano .env.production  # 编辑配置
bash scripts/deployment/deploy-server.sh --env production
```

## 🌐 访问服务

- Web UI: http://43.143.139.197:3000
- API: http://43.143.139.197:8001/api/docs

## 📚 详细文档

- [完整部署指南](README-REMOTE-SSH.md)
- [快速部署指南](../DEPLOYMENT-QUICK-START.md)

