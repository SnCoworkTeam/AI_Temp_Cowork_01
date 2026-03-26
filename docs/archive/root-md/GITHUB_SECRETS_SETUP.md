# GitHub Secrets 配置指南

## 📋 需要的Secrets

根据CI/CD工作流配置，需要在GitHub仓库中配置以下Secrets：

### 必需的Secrets

1. **SSH_PRIVATE_KEY** - SSH私钥
2. **SERVER_HOST** - 服务器地址
3. **SERVER_USER** - 服务器用户名
4. **SERVER_URL** - 服务器URL（可选，用于环境URL）

## 🔧 配置步骤

### 方法1: 通过GitHub Web界面配置

1. **进入仓库设置**
   - 打开GitHub仓库
   - 点击 `Settings` 标签
   - 在左侧菜单选择 `Secrets and variables` → `Actions`

2. **添加SSH_PRIVATE_KEY**
   - 点击 `New repository secret`
   - Name: `SSH_PRIVATE_KEY`
   - Secret: 粘贴 `enterprise_ai_platform.pem` 文件的完整内容
   - 点击 `Add secret`

3. **添加SERVER_HOST**
   - 点击 `New repository secret`
   - Name: `SERVER_HOST`
   - Secret: `43.143.139.197`
   - 点击 `Add secret`

4. **添加SERVER_USER**
   - 点击 `New repository secret`
   - Name: `SERVER_USER`
   - Secret: `ubuntu`
   - 点击 `Add secret`

5. **添加SERVER_URL** (可选)
   - 点击 `New repository secret`
   - Name: `SERVER_URL`
   - Secret: `http://43.143.139.197:8080`
   - 点击 `Add secret`

### 方法2: 使用GitHub CLI配置

```bash
# 安装GitHub CLI (如果未安装)
# Windows: winget install GitHub.cli
# Mac: brew install gh
# Linux: 参考 https://cli.github.com/

# 登录GitHub
gh auth login

# 设置Secrets
gh secret set SSH_PRIVATE_KEY < enterprise_ai_platform.pem
gh secret set SERVER_HOST --body "43.143.139.197"
gh secret set SERVER_USER --body "ubuntu"
gh secret set SERVER_URL --body "http://43.143.139.197:8080"
```

### 方法3: 使用PowerShell脚本自动配置

创建并运行以下脚本：

```powershell
# configure-github-secrets.ps1
$repo = "your-username/enterprise-ai-platform"  # 替换为你的仓库名
$keyFile = "enterprise_ai_platform.pem"

# 检查GitHub CLI是否安装
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI未安装，请先安装: winget install GitHub.cli" -ForegroundColor Red
    exit 1
}

# 检查是否已登录
gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Host "请先登录GitHub: gh auth login" -ForegroundColor Yellow
    exit 1
}

# 读取密钥文件
if (-not (Test-Path $keyFile)) {
    Write-Host "❌ 未找到密钥文件: $keyFile" -ForegroundColor Red
    exit 1
}

$keyContent = Get-Content $keyFile -Raw

# 设置Secrets
Write-Host "`n=== 配置GitHub Secrets ===" -ForegroundColor Cyan

Write-Host "设置 SSH_PRIVATE_KEY..." -ForegroundColor Yellow
$keyContent | gh secret set SSH_PRIVATE_KEY --repo $repo

Write-Host "设置 SERVER_HOST..." -ForegroundColor Yellow
gh secret set SERVER_HOST --body "43.143.139.197" --repo $repo

Write-Host "设置 SERVER_USER..." -ForegroundColor Yellow
gh secret set SERVER_USER --body "ubuntu" --repo $repo

Write-Host "设置 SERVER_URL..." -ForegroundColor Yellow
gh secret set SERVER_URL --body "http://43.143.139.197:8080" --repo $repo

Write-Host "`n✅ Secrets配置完成！" -ForegroundColor Green
```

## 🔍 验证配置

### 方法1: 通过GitHub Web界面验证

1. 进入 `Settings` → `Secrets and variables` → `Actions`
2. 确认以下Secrets已存在：
   - ✅ SSH_PRIVATE_KEY
   - ✅ SERVER_HOST
   - ✅ SERVER_USER
   - ✅ SERVER_URL

### 方法2: 使用GitHub CLI验证

```bash
gh secret list
```

### 方法3: 测试工作流

1. 进入 `Actions` 标签
2. 选择 `Deploy to Server` 工作流
3. 点击 `Run workflow`
4. 选择环境并运行
5. 查看日志确认Secrets是否正确读取

## ⚠️ 安全注意事项

1. **不要将密钥文件提交到Git仓库**
   - 确保 `.gitignore` 包含 `*.pem`
   - 如果已提交，立即撤销并轮换密钥

2. **密钥文件权限**
   - Linux/Mac: `chmod 600 enterprise_ai_platform.pem`
   - Windows: 右键 → 属性 → 安全 → 限制访问

3. **定期轮换密钥**
   - 建议每3-6个月轮换一次SSH密钥
   - 轮换后更新GitHub Secrets

4. **最小权限原则**
   - 使用专门的部署用户，不要使用root
   - 限制SSH密钥的权限范围

## 📝 密钥文件信息

根据 `remote.ssh` 配置：
- **密钥文件**: `enterprise_ai_platform.pem`
- **服务器地址**: `43.143.139.197`
- **用户名**: `ubuntu`
- **端口**: 22 (默认)

## 🚀 快速配置脚本

运行以下命令快速配置（需要GitHub CLI）：

```powershell
# 读取密钥并配置
$keyContent = Get-Content "enterprise_ai_platform.pem" -Raw
$keyContent | gh secret set SSH_PRIVATE_KEY
gh secret set SERVER_HOST --body "43.143.139.197"
gh secret set SERVER_USER --body "ubuntu"
gh secret set SERVER_URL --body "http://43.143.139.197:8080"
```

## ✅ 配置检查清单

- [ ] SSH_PRIVATE_KEY 已配置
- [ ] SERVER_HOST 已配置 (43.143.139.197)
- [ ] SERVER_USER 已配置 (ubuntu)
- [ ] SERVER_URL 已配置 (可选)
- [ ] 密钥文件未提交到Git
- [ ] 测试工作流运行成功

---

**创建时间**: 2025-12-03  
**密钥文件**: enterprise_ai_platform.pem

