# 自动同步脚本使用说明

## 📋 概述

`sync-to-server.ps1` 是一个智能的文件同步脚本，能够自动检测 Git 变更的文件并同步到远程服务器。

## 🚀 快速开始

### 1. 配置服务器信息

创建 `remote.ssh` 配置文件（或复制 `remote.ssh.example`）：

```ssh
Host enterprise-ai-server
    HostName 43.143.139.197
    User ubuntu
    IdentityFile enterprise_ai_platform.pem
    StrictHostKeyChecking no
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### 2. 准备密钥文件

将 `enterprise_ai_platform.pem` 放置在以下位置之一：
- 项目根目录：`E:\enterprise-ai-platform\enterprise_ai_platform.pem`
- 用户目录：`C:\Users\YourUsername\.ssh\enterprise_ai_platform.pem`

### 3. 使用同步脚本

#### 方式1：使用快捷脚本（推荐）

```powershell
# 在项目根目录执行
.\sync.ps1
```

#### 方式2：直接调用脚本

```powershell
.\scripts\deployment\sync-to-server.ps1
```

## 📖 参数说明

### 基本参数

```powershell
# 指定配置文件
.\sync.ps1 -ConfigFile "remote.ssh"

# 指定密钥文件
.\sync.ps1 -KeyFile "enterprise_ai_platform.pem"

# 指定远程路径
.\sync.ps1 -RemotePath "/opt/enterprise-ai-platform"

# 指定分支
.\sync.ps1 -Branch "main"
```

### 高级参数

```powershell
# 包含未跟踪的文件
.\sync.ps1 -IncludeUntracked

# 上传所有文件（排除 .git, node_modules 等）
.\sync.ps1 -All

# 预览模式（不实际上传）
.\sync.ps1 -DryRun
```

## 🔍 功能特性

### 自动检测变更

脚本会自动检测以下类型的变更：

1. **工作区修改**：已修改但未暂存的文件
2. **暂存区文件**：已暂存但未提交的文件
3. **已提交未推送**：已提交但未推送到远程的文件
4. **未跟踪文件**：使用 `-IncludeUntracked` 参数包含

### 智能排除

自动排除以下文件/目录：
- `.git/` - Git 目录
- `node_modules/` - Node 模块
- `__pycache__/` - Python 缓存
- `.env*` - 环境变量文件
- `*.pem` - 密钥文件
- `*.log` - 日志文件
- `.venv/`, `venv/` - 虚拟环境
- `.next/`, `dist/`, `build/` - 构建输出
- `.vscode/`, `.idea/` - IDE 配置

### 增量同步

- 使用 `rsync`（如果可用）进行增量同步，只传输变更的部分
- 使用 `scp` 作为备选方案

## 📝 使用示例

### 示例1：同步修改的文件

```powershell
# 修改了 knowledge-base/requirements.txt 后
.\sync.ps1
```

输出：
```
==========================================
企业AI平台 - 自动同步脚本
==========================================

[1/6] 读取服务器配置...
✅ 找到配置文件: E:\enterprise-ai-platform\remote.ssh
✅ 使用密钥文件: E:\enterprise-ai-platform\enterprise_ai_platform.pem
服务器: ubuntu@43.143.139.197
远程路径: /opt/enterprise-ai-platform

[2/6] 检测 Git 变更...
当前分支: main

[3/6] 收集变更文件...
✅ 检测到 1 个文件需要同步

文件列表（前 20 个）：
  - knowledge-base/requirements.txt

[4/6] 检查上传工具...
✅ 使用 rsync 上传（推荐，支持增量同步）

[5/6] 上传文件到服务器...
使用 rsync 同步文件...
执行 rsync 命令...

[6/6] 验证上传结果...

==========================================
✅ 同步完成！
==========================================

统计信息：
  - 上传文件数: 1
  - 耗时: 2.35 秒
  - 服务器: ubuntu@43.143.139.197
  - 远程路径: /opt/enterprise-ai-platform

下一步操作：
  1. SSH 连接: ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" ubuntu@43.143.139.197
  2. 进入目录: cd /opt/enterprise-ai-platform
  3. 重启服务: sudo docker compose restart <service-name>

💡 提示：修改 requirements.txt 后，需要重新构建 Docker 镜像
```

### 示例2：预览模式

```powershell
# 查看将要上传的文件，不实际上传
.\sync.ps1 -DryRun
```

### 示例3：包含未跟踪的文件

```powershell
# 同步修改的文件和未跟踪的新文件
.\sync.ps1 -IncludeUntracked
```

### 示例4：上传所有文件

```powershell
# 上传所有文件（排除忽略项）
.\sync.ps1 -All
```

## 🔧 常见问题

### Q1: 找不到密钥文件

**问题**：脚本提示找不到 `enterprise_ai_platform.pem`

**解决**：
1. 确认密钥文件在项目根目录或 `~/.ssh/` 目录
2. 使用 `-KeyFile` 参数指定完整路径

```powershell
.\sync.ps1 -KeyFile "C:\path\to\enterprise_ai_platform.pem"
```

### Q2: 找不到 rsync 或 scp

**问题**：脚本提示未找到上传工具

**解决**：
1. 安装 Git for Windows（包含 scp）
2. 或安装 WSL（包含 rsync）
3. 或使用 Cygwin

### Q3: 连接超时

**问题**：SSH 连接超时

**解决**：
1. 检查服务器 IP 是否正确
2. 检查网络连接
3. 检查服务器防火墙设置
4. 确认密钥文件权限正确

### Q4: 某些文件没有上传

**问题**：修改了文件但没有被检测到

**解决**：
1. 确认文件已添加到 Git（`git add`）
2. 或使用 `-IncludeUntracked` 参数
3. 或使用 `-All` 参数上传所有文件

## 💡 最佳实践

### 1. 工作流程

```powershell
# 1. 修改代码
# 2. 提交到 Git（可选）
git add .
git commit -m "修复依赖问题"

# 3. 同步到服务器
.\sync.ps1

# 4. SSH 到服务器重启服务
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform
sudo docker compose restart knowledge-base
```

### 2. 修改 requirements.txt 后

```powershell
# 1. 同步文件
.\sync.ps1

# 2. SSH 到服务器重新构建
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform
sudo docker compose up -d --build knowledge-base
```

### 3. 批量修改后

```powershell
# 使用预览模式先查看
.\sync.ps1 -DryRun

# 确认无误后上传
.\sync.ps1
```

## 📚 相关脚本

- `upload-to-server.ps1` - 完整上传脚本（上传所有文件）
- `upload-changes-only.ps1` - 增量上传脚本（旧版本）
- `deploy-remote.ps1` - 一键部署脚本（包含上传和部署）

## 🔐 安全提示

1. **密钥文件安全**
   - 不要将密钥文件提交到 Git
   - 定期更换密钥
   - 使用强密码保护密钥文件

2. **配置文件安全**
   - `remote.ssh` 文件包含服务器信息，不要提交到公开仓库
   - 建议添加到 `.gitignore`

3. **环境变量文件**
   - `.env` 文件不会被上传（自动排除）
   - 确保服务器上的 `.env` 文件已正确配置

## 📞 支持

如有问题，请查看：
- [部署文档](../README.md)
- [故障排除指南](../../docs/troubleshooting/)

