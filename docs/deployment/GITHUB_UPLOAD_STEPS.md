# GitHub上传步骤 - 快速指南

## 📋 需要执行的命令（按顺序）

### 步骤1：检查并初始化Git仓库

```powershell
# 检查是否已初始化
git status

# 如果报错"not a git repository"，执行：
git init
```

### 步骤2：配置Git用户信息

```powershell
git config user.name "lyb-005"
git config user.email "lyb-005@163.com"
```

### 步骤3：添加所有文件并提交

```powershell
# 添加所有文件
git add .

# 创建初始提交
git commit -m "Initial commit: Enterprise AI Platform"
```

### 步骤4：设置主分支名称

```powershell
git branch -M main
```

### 步骤5：在GitHub网站创建仓库（必须手动）

1. 访问：https://github.com/new
2. 仓库名称：`enterprise-ai-platform`
3. 描述：`企业AI平台 - 基于业务流程自动化的企业AI平台`
4. **重要**：选择 **"Private"（私有）**
5. **不要**勾选任何初始化选项（README、.gitignore、license）
6. 点击 **"Create repository"**

### 步骤6：添加远程仓库并推送

创建仓库后，GitHub会显示命令。选择以下方式之一：

#### 方式A：使用HTTPS（需要个人访问令牌）

```powershell
# 添加远程仓库
git remote add origin https://github.com/lyb-005/enterprise-ai-platform.git

# 推送代码
git push -u origin main
```

**重要**：当提示输入密码时，使用**个人访问令牌**（不是GitHub密码）

#### 方式B：使用SSH（如果已配置SSH密钥）

```powershell
# 添加远程仓库
git remote add origin git@github.com:lyb-005/enterprise-ai-platform.git

# 推送代码
git push -u origin main
```

---

## 🔑 如何获取个人访问令牌（如果使用HTTPS）

1. 访问：https://github.com/settings/tokens
2. 点击："Generate new token" → "Generate new token (classic)"
3. 设置：
   - 名称：`enterprise-ai-platform`
   - 过期时间：选择较长时间或"无过期"
   - 权限：勾选 `repo`（完整仓库访问权限）
4. 点击："Generate token"
5. **立即复制令牌**（只显示一次！）

---

## 📝 完整命令序列（复制粘贴）

如果Git仓库已初始化，直接执行：

```powershell
# 1. 配置用户信息（如果还没配置）
git config user.name "lyb-005"
git config user.email "lyb-005@163.com"

# 2. 添加所有文件
git add .

# 3. 创建提交
git commit -m "Initial commit: Enterprise AI Platform"

# 4. 设置主分支
git branch -M main

# 5. 添加远程仓库（HTTPS方式）
git remote add origin https://github.com/lyb-005/enterprise-ai-platform.git

# 6. 推送代码
git push -u origin main
```

---

## ⚠️ 常见问题

### Q: 提示 "Authentication failed"
**解决**：GitHub不再支持密码，必须使用个人访问令牌
- 访问 https://github.com/settings/tokens 创建令牌
- 推送时使用令牌作为密码

### Q: 提示 "remote origin already exists"
**解决**：删除后重新添加
```powershell
git remote remove origin
git remote add origin https://github.com/lyb-005/enterprise-ai-platform.git
```

### Q: 提示 "failed to push some refs"
**解决**：可能是远程仓库有内容，先拉取
```powershell
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Q: 提示 "Failed to connect to github.com port 443" 或连接超时
**原因**：网络连接问题，GitHub 443端口无法访问

**解决方案1：配置代理（推荐）**
如果你有代理服务（如 Clash、V2Ray 等），配置 Git 使用代理：
```powershell
# 设置 HTTP/HTTPS 代理（根据你的代理端口调整）
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 如果使用 SOCKS5 代理
git config --global http.proxy socks5://127.0.0.1:1080
git config --global https.proxy socks5://127.0.0.1:1080

# 取消代理设置（如果不需要）
git config --global --unset http.proxy
git config --global --unset https.proxy
```

**解决方案2：使用 SSH 方式（更稳定）**
SSH 方式通常比 HTTPS 更稳定，使用 22 端口：
```powershell
# 1. 检查是否已有 SSH 密钥
ls ~/.ssh

# 2. 如果没有，生成 SSH 密钥
ssh-keygen -t ed25519 -C "lyb-005@163.com"
# 按回车使用默认路径和空密码

# 3. 复制公钥内容
cat ~/.ssh/id_ed25519.pub

# 4. 在 GitHub 添加 SSH 密钥：
#    访问：https://github.com/settings/keys
#    点击 "New SSH key"，粘贴公钥内容

# 5. 测试 SSH 连接
ssh -T git@github.com

# 6. 修改远程仓库地址为 SSH
git remote set-url origin git@github.com:PMLiuyubin/enterprise-ai-platform.git

# 7. 再次推送
git push -u origin main
```

**解决方案3：临时使用镜像或 VPN**
- 使用 VPN 服务
- 或使用 GitHub 镜像站点（不推荐用于推送）

---

## ✅ 验证上传成功

上传完成后，访问：
https://github.com/lyb-005/enterprise-ai-platform

应该能看到所有项目文件。


