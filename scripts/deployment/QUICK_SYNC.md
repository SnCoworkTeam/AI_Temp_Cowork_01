# 快速同步指南

## 🚀 一键同步修改的文件到服务器

### 最简单的使用方法

```powershell
# 在项目根目录执行
.\sync.ps1
```

就这么简单！脚本会自动：
1. ✅ 检测你修改的文件
2. ✅ 读取服务器配置（从 `remote.ssh`）
3. ✅ 只上传修改的文件
4. ✅ 显示上传结果

## 📝 使用场景

### 场景1：修改了 requirements.txt

```powershell
# 1. 修改 knowledge-base/requirements.txt
# 2. 执行同步
.\sync.ps1

# 3. SSH 到服务器重新构建
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform
sudo docker compose up -d --build knowledge-base
```

### 场景2：修改了代码文件

```powershell
# 1. 修改代码（例如：knowledge-base/src/core/vector_store.py）
# 2. 执行同步
.\sync.ps1

# 3. SSH 到服务器重启服务
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform
sudo docker compose restart knowledge-base
```

### 场景3：预览要上传的文件

```powershell
# 先看看会上传哪些文件（不实际上传）
.\sync.ps1 -DryRun
```

## ⚙️ 首次使用配置

### 1. 创建 remote.ssh 配置文件

复制示例文件并修改：

```powershell
# 复制示例文件
Copy-Item remote.ssh.example remote.ssh

# 编辑配置文件（根据实际情况修改）
notepad remote.ssh
```

`remote.ssh` 内容示例：

```
Host enterprise-ai-server
    HostName 43.143.139.197
    User ubuntu
    IdentityFile enterprise_ai_platform.pem
    StrictHostKeyChecking no
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### 2. 准备密钥文件

将 `enterprise_ai_platform.pem` 放在项目根目录：

```
E:\enterprise-ai-platform\
  ├── enterprise_ai_platform.pem  ← 放在这里
  ├── remote.ssh
  └── sync.ps1
```

## 🎯 常用命令

```powershell
# 基本同步（只上传修改的文件）
.\sync.ps1

# 包含未跟踪的新文件
.\sync.ps1 -IncludeUntracked

# 上传所有文件（排除 .git, node_modules 等）
.\sync.ps1 -All

# 预览模式（不实际上传）
.\sync.ps1 -DryRun

# 指定分支
.\sync.ps1 -Branch "develop"
```

## 💡 提示

1. **修改 requirements.txt 后**：需要重新构建 Docker 镜像
   ```bash
   sudo docker compose up -d --build <service-name>
   ```

2. **修改代码后**：通常只需要重启服务
   ```bash
   sudo docker compose restart <service-name>
   ```

3. **批量修改后**：建议先用 `-DryRun` 预览

4. **首次同步**：可以使用 `-All` 上传所有文件

## ❓ 常见问题

**Q: 找不到密钥文件？**  
A: 确保 `enterprise_ai_platform.pem` 在项目根目录或 `~/.ssh/` 目录

**Q: 连接失败？**  
A: 检查 `remote.ssh` 中的服务器 IP 和用户名是否正确

**Q: 某些文件没上传？**  
A: 使用 `-IncludeUntracked` 包含未跟踪的文件，或使用 `-All` 上传所有文件

## 📚 更多信息

详细文档请查看：`scripts/deployment/SYNC_README.md`

