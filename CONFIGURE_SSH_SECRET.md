# 配置SSH_PRIVATE_KEY Secret

## 🔍 问题

工作流报错：`The ssh-private-key argument is empty`

**原因**: GitHub Secrets中缺少 `SSH_PRIVATE_KEY` 配置

## ✅ 解决方案

### 方法1: 使用GitHub CLI配置（推荐）

#### 步骤1: 找到密钥文件

密钥文件应该是 `enterprise_ai_platform.pem`，可能的位置：
- 项目根目录：`E:\enterprise-ai-platform\enterprise_ai_platform.pem`
- 用户SSH目录：`$env:USERPROFILE\.ssh\enterprise_ai_platform.pem`

#### 步骤2: 配置Secret

```powershell
# 如果密钥文件在项目根目录
if (Test-Path "enterprise_ai_platform.pem") {
    Get-Content enterprise_ai_platform.pem -Raw | gh secret set SSH_PRIVATE_KEY
    Write-Host "SSH_PRIVATE_KEY 配置成功！" -ForegroundColor Green
} else {
    Write-Host "未找到密钥文件，请手动指定路径" -ForegroundColor Red
}

# 或者使用完整路径
Get-Content "完整路径\enterprise_ai_platform.pem" -Raw | gh secret set SSH_PRIVATE_KEY
```

#### 步骤3: 验证配置

```powershell
# 查看所有secrets
gh secret list

# 应该看到 SSH_PRIVATE_KEY
```

### 方法2: 使用自动配置脚本

运行我创建的脚本：

```powershell
powershell -ExecutionPolicy Bypass -File setup-ssh-secret.ps1
```

脚本会自动：
1. 查找密钥文件
2. 验证格式
3. 配置到GitHub Secrets

### 方法3: 通过GitHub Web界面配置

如果CLI方式不行，使用Web界面：

1. **访问Secrets页面**：
   ```
   https://github.com/PMLiuyubin/enterprise-ai-platform/settings/secrets/actions
   ```

2. **添加新Secret**：
   - 点击 `New repository secret`
   - Name: `SSH_PRIVATE_KEY`
   - Secret: 打开 `enterprise_ai_platform.pem` 文件，复制**完整内容**（包括 `-----BEGIN` 和 `-----END` 行）
   - 点击 `Add secret`

## 📋 密钥文件内容格式

密钥文件应该类似这样：

```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
（多行内容）
...
-----END RSA PRIVATE KEY-----
```

或者：

```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn...
（多行内容）
...
-----END OPENSSH PRIVATE KEY-----
```

## ⚠️ 重要提示

1. **复制完整内容**：包括 `-----BEGIN` 和 `-----END` 行
2. **不要修改**：保持原样，不要添加或删除任何字符
3. **换行符**：确保保留所有换行符

## 🔍 如果找不到密钥文件

如果找不到 `enterprise_ai_platform.pem` 文件：

1. **检查其他位置**：
   ```powershell
   # 搜索整个系统
   Get-ChildItem -Path E:\ -Filter "*.pem" -Recurse -ErrorAction SilentlyContinue | Select-Object FullName
   ```

2. **联系服务器管理员**：获取新的SSH密钥

3. **生成新密钥**（如果需要）：
   ```powershell
   ssh-keygen -t rsa -b 4096 -f enterprise_ai_platform.pem -N '""'
   ```

## ✅ 验证配置

配置后，验证：

```powershell
# 1. 查看secrets列表
gh secret list

# 2. 重新触发工作流
gh workflow run deploy.yml --field environment=staging

# 3. 查看新运行，应该不再有SSH错误
```

---

**快速命令**（如果密钥文件在项目根目录）：
```powershell
Get-Content enterprise_ai_platform.pem -Raw | gh secret set SSH_PRIVATE_KEY
```





