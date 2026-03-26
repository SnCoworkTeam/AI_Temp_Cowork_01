# 启动CI/CD - 快速指南

## ✅ 前提条件

1. ✅ GitHub CLI已安装
2. ✅ 已登录GitHub (`gh auth login`)
3. ✅ 密钥文件存在 (`enterprise_ai_platform.pem`)

## 🚀 快速启动步骤

### 步骤1: 配置GitHub Secrets

在新打开的PowerShell终端中运行：

```powershell
# 1. 配置SSH私钥
Get-Content enterprise_ai_platform.pem -Raw | gh secret set SSH_PRIVATE_KEY

# 2. 配置服务器信息
gh secret set SERVER_HOST --body "43.143.139.197"
gh secret set SERVER_USER --body "ubuntu"
gh secret set SERVER_URL --body "http://43.143.139.197:8080"

# 3. 验证配置
gh secret list
```

### 步骤2: 启动CI/CD工作流

```powershell
# 触发部署工作流（staging环境）
gh workflow run "Deploy to Server.yml" --field environment=staging

# 或触发到production环境
gh workflow run "Deploy to Server.yml" --field environment=production
```

### 步骤3: 查看运行状态

```powershell
# 列出最近的工作流运行
gh run list --workflow="Deploy to Server.yml" --limit 5

# 实时查看运行状态
gh run watch

# 查看特定运行的日志
gh run view <run-id> --log
```

## 📋 可用工作流

```powershell
# 列出所有工作流
gh workflow list

# 触发测试套件
gh workflow run "Test Suite.yml"

# 触发PR检查（需要Pull Request）
# 创建PR时会自动触发
```

## 🔍 故障排除

### 问题1: gh命令未找到

**解决方案**: 重启PowerShell终端

### 问题2: 未登录

**解决方案**: 
```powershell
gh auth login
```

### 问题3: Secrets配置失败

**解决方案**: 
- 检查是否有仓库写入权限
- 确认仓库名称正确
- 手动在GitHub Web界面配置

### 问题4: 工作流触发失败

**解决方案**:
1. 检查工作流文件是否存在: `.github/workflows/Deploy to Server.yml`
2. 在GitHub Web界面手动触发测试
3. 查看Actions标签页的错误信息

## 🌐 通过Web界面启动

如果CLI不可用，可以通过GitHub Web界面：

1. 进入GitHub仓库
2. 点击 `Actions` 标签
3. 选择 `Deploy to Server` 工作流
4. 点击 `Run workflow`
5. 选择环境（staging/production/development）
6. 点击 `Run workflow` 按钮

## 📊 监控CI/CD

### 查看工作流状态

```powershell
# 查看所有运行
gh run list

# 查看特定工作流
gh run list --workflow="Deploy to Server.yml"

# 查看失败的工作流
gh run list --status=failure
```

### 重新运行失败的工作流

```powershell
gh run rerun <run-id>
```

---

**创建时间**: 2025-12-03

