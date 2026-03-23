# 立即配置SSH_PRIVATE_KEY

## ✅ 密钥文件位置

密钥文件在项目根目录：`enterprise_ai_platform.pem`

## 🚀 立即执行以下命令

**在PowerShell中直接执行**（不要通过任何工具）：

```powershell
# 配置SSH_PRIVATE_KEY
Get-Content enterprise_ai_platform.pem -Raw | gh secret set SSH_PRIVATE_KEY

# 验证配置
gh secret list
```

## 📋 完整步骤

```powershell
# 步骤1: 确认文件存在
Test-Path enterprise_ai_platform.pem

# 步骤2: 配置Secret
Get-Content enterprise_ai_platform.pem -Raw | gh secret set SSH_PRIVATE_KEY

# 步骤3: 验证
gh secret list | Select-String "SSH_PRIVATE_KEY"

# 步骤4: 重新触发工作流（如果需要）
gh workflow run deploy.yml --field environment=staging
```

## ✅ 验证配置成功

如果看到以下输出，说明配置成功：

```
SSH_PRIVATE_KEY  ✓ Set 1 minute ago
```

## 🔍 如果配置失败

如果命令失败，检查：

1. **GitHub CLI是否已登录**：
   ```powershell
   gh auth status
   ```

2. **是否有仓库权限**：
   ```powershell
   gh repo view
   ```

3. **使用Web界面手动配置**：
   - 访问：`https://github.com/PMLiuyubin/enterprise-ai-platform/settings/secrets/actions`
   - 点击 `New repository secret`
   - Name: `SSH_PRIVATE_KEY`
   - Secret: 打开 `enterprise_ai_platform.pem`，复制全部内容
   - 点击 `Add secret`

---

**执行命令后告诉我结果，我会帮你验证！**





