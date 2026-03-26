# GitHub上传指南

## ⚠️ 重要安全提示

**GitHub已不再支持使用密码进行Git操作**。您需要使用以下方式之一：

1. **个人访问令牌（Personal Access Token，推荐）**
2. **SSH密钥**
3. **GitHub CLI**

## 📋 上传步骤

### 方法一：使用个人访问令牌（推荐）

#### 步骤1：创建个人访问令牌

1. 访问 GitHub: https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 设置令牌名称（如：`enterprise-ai-platform`）
4. 选择过期时间（建议选择较长时间或"无过期"）
5. 勾选以下权限：
   - `repo` (完整仓库访问权限)
   - `workflow` (如果需要CI/CD)
6. 点击 "Generate token"
7. **重要**：复制生成的令牌（只显示一次！）

#### 步骤2：在本地初始化Git仓库

```powershell
# 在项目根目录执行

# 1. 初始化Git仓库
git init

# 2. 配置用户信息
git config user.name "lyb-005"
git config user.email "lyb-005@163.com"

# 3. 添加所有文件
git add .

# 4. 创建初始提交
git commit -m "Initial commit: Enterprise AI Platform"

# 5. 添加远程仓库（先创建GitHub仓库后再执行）
git remote add origin https://github.com/lyb-005/enterprise-ai-platform.git

# 6. 推送到GitHub（使用令牌作为密码）
git push -u origin main
```

**注意**：当提示输入密码时，使用您的**个人访问令牌**，而不是GitHub密码。

#### 步骤3：在GitHub上创建私有仓库

1. 访问 https://github.com/new
2. 仓库名称：`enterprise-ai-platform`
3. 描述：`企业AI平台 - 基于业务流程自动化的企业AI平台`
4. **选择 "Private"（私有）**
5. **不要**勾选 "Initialize this repository with a README"
6. 点击 "Create repository"

### 方法二：使用SSH密钥（更安全）

#### 步骤1：生成SSH密钥

```powershell
# 生成SSH密钥（如果还没有）
ssh-keygen -t ed25519 -C "lyb-005@163.com"

# 按Enter使用默认路径
# 设置密码（可选，但推荐）
```

#### 步骤2：添加SSH密钥到GitHub

```powershell
# 查看公钥
cat ~/.ssh/id_ed25519.pub

# 复制输出的内容
```

1. 访问 https://github.com/settings/keys
2. 点击 "New SSH key"
3. 标题：`Enterprise AI Platform`
4. 密钥：粘贴刚才复制的公钥内容
5. 点击 "Add SSH key"

#### 步骤3：使用SSH URL

```powershell
# 添加远程仓库（使用SSH）
git remote add origin git@github.com:lyb-005/enterprise-ai-platform.git

# 推送代码
git push -u origin main
```

### 方法三：使用GitHub CLI（最简单）

#### 步骤1：安装GitHub CLI

```powershell
# 使用winget安装（Windows）
winget install GitHub.cli

# 或下载安装：https://cli.github.com/
```

#### 步骤2：登录GitHub

```powershell
# 登录GitHub
gh auth login

# 选择：
# - GitHub.com
# - HTTPS
# - 使用浏览器登录
```

#### 步骤3：创建并推送仓库

```powershell
# 初始化Git仓库
git init
git add .
git commit -m "Initial commit: Enterprise AI Platform"

# 创建私有仓库并推送
gh repo create enterprise-ai-platform --private --source=. --remote=origin --push
```

## 🔒 安全检查清单

在上传前，请确保：

- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 所有敏感信息（API密钥、密码等）已从代码中移除
- [ ] 数据库凭证未硬编码在代码中
- [ ] 个人访问令牌已安全保存（不要提交到代码库）
- [ ] 仓库设置为私有

## 📝 快速命令参考

### 如果使用HTTPS（个人访问令牌）

```powershell
git init
git config user.name "lyb-005"
git config user.email "lyb-005@163.com"
git add .
git commit -m "Initial commit: Enterprise AI Platform"
git remote add origin https://github.com/lyb-005/enterprise-ai-platform.git
git branch -M main
git push -u origin main
```

### 如果使用SSH

```powershell
git init
git config user.name "lyb-005"
git config user.email "lyb-005@163.com"
git add .
git commit -m "Initial commit: Enterprise AI Platform"
git remote add origin git@github.com:lyb-005/enterprise-ai-platform.git
git branch -M main
git push -u origin main
```

## 🆘 常见问题

### Q: 提示 "Authentication failed"
**A**: GitHub不再支持密码认证，请使用个人访问令牌或SSH密钥。

### Q: 如何保存令牌避免每次都输入？
**A**: 使用Git Credential Manager：
```powershell
git config --global credential.helper manager
```

### Q: 如何查看已配置的远程仓库？
**A**: 
```powershell
git remote -v
```

### Q: 如何更改远程仓库URL？
**A**: 
```powershell
git remote set-url origin https://github.com/lyb-005/enterprise-ai-platform.git
```

## 📚 相关资源

- [GitHub个人访问令牌文档](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub SSH密钥文档](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [GitHub CLI文档](https://cli.github.com/manual/)

---

**重要提示**：完成上传后，请删除本指南文件中的敏感信息，或将其添加到 `.gitignore`。







