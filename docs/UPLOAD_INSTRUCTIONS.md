# 上传文件到服务器 - 使用说明

## 快速上传命令

### 方法1：直接使用 scp 命令（推荐）

在 PowerShell 或 CMD 中执行：

```bash
# 如果密钥文件在项目根目录
scp -i enterprise_ai_platform.pem -o StrictHostKeyChecking=no knowledge-base/requirements.txt ubuntu@43.143.139.197:/opt/enterprise-ai-platform/knowledge-base/requirements.txt

# 如果密钥文件在 ~/.ssh/ 目录
scp -i %USERPROFILE%\.ssh\enterprise_ai_platform.pem -o StrictHostKeyChecking=no knowledge-base/requirements.txt ubuntu@43.143.139.197:/opt/enterprise-ai-platform/knowledge-base/requirements.txt
```

### 方法2：使用批处理文件

直接双击运行：`upload-files.bat`

### 方法3：使用 PowerShell 脚本

```powershell
powershell -ExecutionPolicy Bypass -File .\upload-simple.ps1
```

## 上传多个文件

如果需要上传多个修改的文件，可以逐个上传：

```bash
# 上传 requirements.txt
scp -i enterprise_ai_platform.pem knowledge-base/requirements.txt ubuntu@43.143.139.197:/opt/enterprise-ai-platform/knowledge-base/

# 上传其他文件（示例）
scp -i enterprise_ai_platform.pem knowledge-base/src/core/vector_store.py ubuntu@43.143.139.197:/opt/enterprise-ai-platform/knowledge-base/src/core/
```

## 上传后操作

文件上传成功后，SSH 到服务器并重新构建服务：

```bash
# 1. SSH 连接到服务器
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197

# 2. 进入项目目录
cd /opt/enterprise-ai-platform

# 3. 重新构建 knowledge-base 服务（因为修改了 requirements.txt）
sudo docker compose up -d --build knowledge-base

# 4. 查看日志确认
sudo docker compose logs -f knowledge-base
```

## 从 remote.ssh 读取配置

如果创建了 `remote.ssh` 配置文件，可以手动读取配置：

```bash
# 查看配置
cat remote.ssh

# 根据配置中的 HostName 和 User 修改上传命令
# 例如：HostName 43.143.139.197, User ubuntu
scp -i enterprise_ai_platform.pem knowledge-base/requirements.txt ubuntu@43.143.139.197:/opt/enterprise-ai-platform/knowledge-base/requirements.txt
```

## 常见问题

### 1. 找不到密钥文件

确保 `enterprise_ai_platform.pem` 在以下位置之一：
- 项目根目录：`E:\enterprise-ai-platform\enterprise_ai_platform.pem`
- 用户目录：`C:\Users\YourUsername\.ssh\enterprise_ai_platform.pem`

### 2. 连接超时

- 检查服务器 IP 是否正确
- 检查网络连接
- 检查服务器防火墙设置

### 3. 权限错误

确保密钥文件权限正确（Windows 上通常不是问题）

## 最简单的上传方式

**直接复制粘贴这个命令到 PowerShell：**

```powershell
scp -i enterprise_ai_platform.pem -o StrictHostKeyChecking=no knowledge-base/requirements.txt ubuntu@43.143.139.197:/opt/enterprise-ai-platform/knowledge-base/requirements.txt
```

如果密钥文件不在当前目录，使用完整路径：

```powershell
scp -i "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem" -o StrictHostKeyChecking=no knowledge-base/requirements.txt ubuntu@43.143.139.197:/opt/enterprise-ai-platform/knowledge-base/requirements.txt
```

