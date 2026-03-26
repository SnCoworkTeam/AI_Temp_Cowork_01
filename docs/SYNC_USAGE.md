# 文件同步脚本使用说明

## 📋 概述

`sync.ps1` 和 `sync.bat` 是快速同步脚本，用于将本地修改的文件自动上传到服务器。

## 🚀 快速开始

### 1. 配置服务器信息

首先，需要创建 `remote.ssh` 配置文件（如果还没有的话）：

```bash
# 复制示例配置文件
cp remote.ssh.example remote.ssh
```

然后编辑 `remote.ssh` 文件，填入你的服务器信息：

```ssh
Host enterprise-ai-server
    HostName 你的服务器IP
    User ubuntu
    IdentityFile enterprise_ai_platform.pem
    StrictHostKeyChecking no
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### 2. 准备密钥文件

确保 `enterprise_ai_platform.pem` 密钥文件在以下位置之一：
- 项目根目录：`E:\enterprise-ai-platform\enterprise_ai_platform.pem`
- 用户目录：`C:\Users\YourUsername\.ssh\enterprise_ai_platform.pem`

### 3. 使用同步脚本

#### 方式1：使用批处理文件（推荐，避免执行策略问题）

```bash
# 在项目根目录执行
sync.bat
```

#### 方式2：使用 PowerShell 脚本

```powershell
# 在项目根目录执行
.\sync.ps1
```

如果遇到执行策略错误，使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\sync.ps1
```

## 📖 功能说明

脚本会自动：

1. ✅ **读取服务器配置**：从 `remote.ssh` 文件读取服务器地址、用户名等信息
2. ✅ **检测修改的文件**：自动检测 Git 工作区、暂存区和已提交但未推送的文件
3. ✅ **智能排除**：自动排除 `.env`、`.pem`、`node_modules` 等不需要上传的文件
4. ✅ **增量同步**：只上传修改的文件，节省时间和带宽
5. ✅ **进度显示**：显示上传进度和文件列表

## 🔧 高级用法

### 包含未跟踪的文件

```powershell
.\sync.ps1 -IncludeUntracked
```

### 上传所有文件（排除忽略项）

```powershell
.\sync.ps1 -All
```

### 预览模式（不实际上传）

```powershell
.\sync.ps1 -DryRun
```

### 指定远程路径

```powershell
.\sync.ps1 -RemotePath "/opt/my-project"
```

### 指定分支

```powershell
.\sync.ps1 -Branch "main"
```

## 📝 使用示例

### 日常开发流程

1. 修改代码文件
2. 执行 `sync.bat` 或 `.\sync.ps1`
3. 脚本自动检测修改的文件并上传到服务器
4. 在服务器上重启相关服务

### 完整示例

```powershell
# 1. 修改了文件
# 2. 执行同步
.\sync.ps1

# 输出示例：
# ==========================================
# 企业AI平台 - 自动同步脚本
# ==========================================
# 
# [1/6] 读取服务器配置...
# ✅ 找到配置文件: E:\enterprise-ai-platform\remote.ssh
# ✅ 找到密钥文件: E:\enterprise-ai-platform\enterprise_ai_platform.pem
# 服务器: ubuntu@43.143.139.197
# 远程路径: /opt/enterprise-ai-platform
# 
# [2/6] 检测 Git 变更...
# 当前分支: main
# 
# [3/6] 收集变更文件...
# ✅ 检测到 5 个文件需要同步
# 
# [4/6] 检查上传工具...
# ✅ 使用 rsync 上传（推荐，支持增量同步）
# 
# [5/6] 上传文件到服务器...
# 使用 rsync 同步文件...
# 
# [6/6] 验证上传结果...
# ✅ 同步完成！
```

## ⚠️ 注意事项

1. **首次使用**：确保 `remote.ssh` 配置文件存在并正确配置
2. **密钥文件**：确保密钥文件权限正确（脚本会自动设置）
3. **网络连接**：确保能够连接到服务器
4. **Git 仓库**：脚本需要在 Git 仓库中运行
5. **上传工具**：需要安装 `rsync`（推荐）或 `scp`（Git for Windows 包含）

## 🔍 故障排除

### 问题1：找不到配置文件

**错误**：`配置文件不存在: remote.ssh`

**解决**：
```bash
cp remote.ssh.example remote.ssh
# 然后编辑 remote.ssh 填入正确的服务器信息
```

### 问题2：找不到密钥文件

**错误**：`未找到密钥文件: enterprise_ai_platform.pem`

**解决**：将密钥文件放置在项目根目录或 `~/.ssh/` 目录

### 问题3：执行策略错误

**错误**：`无法加载文件，因为在此系统上禁止运行脚本`

**解决**：使用 `sync.bat` 或执行：
```powershell
powershell -ExecutionPolicy Bypass -File .\sync.ps1
```

### 问题4：找不到 rsync 或 scp

**错误**：`未找到 rsync 或 scp 命令`

**解决**：
- 安装 Git for Windows（包含 scp）
- 或安装 WSL（包含 rsync）

## 📚 相关文档

- 详细同步说明：`scripts/deployment/SYNC_README.md`
- 部署文档：`scripts/deployment/README.md`

