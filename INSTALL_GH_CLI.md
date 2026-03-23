# GitHub CLI 安装指南

## 🚀 快速安装

### 方法1: 使用安装脚本（推荐）

运行以下PowerShell命令：

```powershell
# 下载并安装GitHub CLI
$url = "https://github.com/cli/cli/releases/latest/download/gh_windows_amd64.msi"
$installer = "$env:TEMP\gh_installer.msi"
Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
Start-Process msiexec.exe -ArgumentList "/i `"$installer`" /quiet /norestart" -Wait
```

安装完成后，**重启PowerShell终端**，然后运行：

```powershell
gh --version
gh auth login
```

### 方法2: 手动下载安装

1. 访问 https://cli.github.com/
2. 下载 Windows 安装包 (gh_windows_amd64.msi)
3. 运行安装程序
4. 重启PowerShell终端
5. 验证安装：`gh --version`

### 方法3: 使用Chocolatey（如果已安装）

```powershell
choco install gh -y
```

### 方法4: 使用Scoop（如果已安装）

```powershell
scoop install gh
```

## ✅ 安装后配置

### 1. 登录GitHub

```powershell
gh auth login
```

按照提示选择：
- GitHub.com
- HTTPS
- 登录方式（浏览器或token）

### 2. 验证登录

```powershell
gh auth status
```

### 3. 配置Secrets

```powershell
# 配置SSH私钥
Get-Content enterprise_ai_platform.pem -Raw | gh secret set SSH_PRIVATE_KEY

# 配置服务器信息
gh secret set SERVER_HOST --body "43.143.139.197"
gh secret set SERVER_USER --body "ubuntu"
gh secret set SERVER_URL --body "http://43.143.139.197:8080"
```

### 4. 验证Secrets

```powershell
gh secret list
```

## 🚀 启动CI/CD

### 触发部署工作流

```powershell
gh workflow run "Deploy to Server.yml" --field environment=staging
```

### 查看工作流状态

```powershell
# 列出最近的工作流运行
gh run list --workflow="Deploy to Server.yml" --limit 5

# 实时查看运行状态
gh run watch

# 查看特定运行的日志
gh run view <run-id> --log
```

## 📝 常用命令

```powershell
# 查看工作流列表
gh workflow list

# 触发工作流
gh workflow run <workflow-name>

# 查看运行列表
gh run list

# 查看运行详情
gh run view <run-id>

# 重新运行失败的工作流
gh run rerun <run-id>
```

## ⚠️ 故障排除

### 问题1: 命令未找到

**解决方案**: 重启PowerShell终端，或手动添加到PATH

### 问题2: 登录失败

**解决方案**: 
- 检查网络连接
- 使用token方式登录：`gh auth login --with-token < token.txt`

### 问题3: 权限不足

**解决方案**: 
- 确保有仓库的写入权限
- 检查GitHub token权限

---

**创建时间**: 2025-12-03

