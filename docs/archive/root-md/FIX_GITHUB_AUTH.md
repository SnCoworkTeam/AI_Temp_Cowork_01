# 修复GitHub CLI认证问题

## 🔍 问题：Token无效 (401 Bad credentials)

当前token无效，需要重新认证。

## ✅ 解决方案

### 方案1: 清除环境变量并使用交互式登录（推荐）

```powershell
# 1. 清除环境变量中的token
Remove-Item Env:\GITHUB_TOKEN -ErrorAction SilentlyContinue

# 2. 使用交互式登录（会打开浏览器）
gh auth login

# 按照提示选择：
# - GitHub.com
# - HTTPS
# - 登录方式：选择 "Login with a web browser" 或 "Paste an authentication token"
```

### 方案2: 使用新的Token直接登录

如果你有新的有效token：

```powershell
# 1. 清除旧的token
Remove-Item Env:\GITHUB_TOKEN -ErrorAction SilentlyContinue

# 2. 使用新token登录（通过管道输入）
echo "你的新token" | gh auth login --with-token

# 或者设置环境变量后登录
$env:GITHUB_TOKEN = "你的新token"
gh auth refresh -h github.com
```

### 方案3: 手动写入配置文件

如果交互式登录有问题，可以手动配置：

```powershell
# 1. 找到配置文件位置
$ghConfigPath = "$env:USERPROFILE\.config\gh\hosts.yml"

# 2. 创建配置目录（如果不存在）
$configDir = Split-Path $ghConfigPath
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# 3. 创建配置文件内容（替换为你的token）
$configContent = @"
github.com:
    oauth_token: 你的新token
    git_protocol: https
    user: 你的用户名
"@

# 4. 写入配置文件
$configContent | Out-File -FilePath $ghConfigPath -Encoding utf8 -Force
```

## 🔑 获取新的GitHub Token

如果token已过期，需要创建新的：

1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 设置名称：`CI/CD Token`
4. 选择权限：
   - ✅ `repo` (完整仓库访问)
   - ✅ `workflow` (工作流权限)
   - ✅ `admin:repo_hook` (仓库webhooks)
5. 点击 "Generate token"
6. **立即复制token**（只显示一次）

## 📝 快速修复命令

```powershell
# 步骤1: 清除无效token
Remove-Item Env:\GITHUB_TOKEN -ErrorAction SilentlyContinue

# 步骤2: 重新登录（选择一种方式）
# 方式A: 交互式登录（推荐）
gh auth login

# 方式B: 使用新token
echo "你的新token" | gh auth login --with-token

# 步骤3: 验证登录
gh auth status

# 步骤4: 测试连接
gh repo view

# 步骤5: 配置secrets
gh secret set SERVER_HOST --body "43.143.139.197"
gh secret set SERVER_USER --body "ubuntu"
gh secret set SERVER_URL --body "http://43.143.139.197:8080"
```

## ⚠️ 注意事项

1. **Token权限**：确保token有 `repo` 和 `workflow` 权限
2. **Token有效期**：Classic token可以设置过期时间，注意及时更新
3. **安全**：不要将token提交到Git仓库
4. **环境变量**：如果使用环境变量，确保在每次新会话中重新设置

---

**当前状态**：Token无效，需要重新认证





