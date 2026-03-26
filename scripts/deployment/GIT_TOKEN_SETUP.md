# Git Personal Access Token 配置指南

## ⚠️ 重要提示

**GitHub从2021年8月13日开始，不再支持密码认证！**

必须使用 **Personal Access Token (PAT)** 进行认证。

---

## 🔑 创建 Personal Access Token

### 步骤1: 登录GitHub并打开Token设置页面

**方法1：直接访问链接**
```
https://github.com/settings/tokens
```

**方法2：通过GitHub界面导航**
1. 登录GitHub：https://github.com
2. 点击右上角头像
3. 选择 **Settings**（设置）
4. 左侧菜单找到 **Developer settings**（开发者设置）
5. 点击 **Personal access tokens** → **Tokens (classic)**

### 步骤2: 生成新Token

1. **点击 "Generate new token"** → **"Generate new token (classic)"**
   - 如果看到"Fine-grained tokens"和"Tokens (classic)"两个选项，选择 **"Tokens (classic)"**

2. **填写Token信息**：
   - **Note（备注）**: 输入Token名称，例如：`enterprise-ai-platform-deploy`
   - **Expiration（过期时间）**: 选择过期时间
     - 建议：`90 days` 或 `1 year`（根据需求）
     - 也可以选择 `No expiration`（不过期，但不太安全）

3. **选择权限（Scopes）**：
   - ✅ **必须勾选**: `repo` - 完整仓库访问权限（包括私有仓库）
     - 这会自动勾选所有子权限：
       - `repo:status`
       - `repo_deployment`
       - `public_repo`
       - `repo:invite`
       - `security_events`
   - 如果仓库是私有的，必须勾选 `repo` 权限

4. **点击页面底部的 "Generate token"（绿色按钮）**

5. **⚠️ 重要：立即复制Token！**
   - Token只显示一次
   - 格式类似：`ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - 如果关闭页面，Token将无法再次查看
   - 只能删除后重新创建

---

## 📍 查看已创建的Token（无法查看完整Token）

### 查看Token列表

访问：https://github.com/settings/tokens

你可以看到：
- ✅ Token名称（Note）
- ✅ 创建时间
- ✅ 过期时间
- ✅ 最后使用时间
- ❌ **无法查看完整Token值**（只能看到部分字符）

### 如果Token丢失或忘记

**无法找回，只能重新创建：**

1. 删除旧Token（点击Token旁边的删除按钮）
2. 按照上面的步骤重新创建新Token
3. 更新所有使用该Token的地方

---

## 🔍 快速访问链接

### 创建Token
```
https://github.com/settings/tokens/new
```

### 查看Token列表
```
https://github.com/settings/tokens
```

### GitHub设置首页
```
https://github.com/settings/profile
```

---

## 📝 配置Token

### 方式1: 环境变量（推荐）

```bash
# 设置环境变量
export GIT_USERNAME="lyb-005@163.com"
export GIT_TOKEN="ghp_your_personal_access_token_here"

# 运行部署脚本
bash scripts/deployment/deploy-server.sh --env production
```

### 方式2: 命令行参数

```bash
bash scripts/deployment/deploy-server.sh \
  --env production \
  --git-username "lyb-005@163.com" \
  --git-token "ghp_your_personal_access_token_here"
```

### 方式3: 永久配置（推荐用于服务器）

```bash
# 编辑 ~/.bashrc 或 ~/.profile
nano ~/.bashrc

# 添加以下内容
export GIT_USERNAME="lyb-005@163.com"
export GIT_TOKEN="ghp_your_personal_access_token_here"

# 重新加载配置
source ~/.bashrc
```

### 方式4: 使用Git凭据存储

```bash
# 配置Git凭据存储
git config --global credential.helper store

# 创建凭据文件
echo "https://lyb-005@163.com:ghp_your_token_here@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
```

---

## 🔐 安全建议

1. **不要将Token提交到代码仓库**
   - 使用环境变量或配置文件（添加到.gitignore）

2. **定期更新Token**
   - 设置合理的过期时间
   - 定期轮换Token

3. **限制Token权限**
   - 只授予必要的权限（repo访问）
   - 不要授予不必要的权限

4. **保护凭据文件**
   ```bash
   chmod 600 ~/.git-credentials
   ```

---

## ❓ 常见问题

### Q: 如何检查Token是否有效？

```bash
# 使用curl测试
curl -H "Authorization: token ghp_your_token_here" https://api.github.com/user

# 如果返回用户信息，说明Token有效
```

### Q: Token过期了怎么办？

重新生成新的Token并更新环境变量或配置文件。

### Q: 可以使用SSH密钥吗？

可以！使用SSH方式更安全：

```bash
# 1. 生成SSH密钥
ssh-keygen -t ed25519 -C "lyb-005@163.com"

# 2. 添加SSH密钥到GitHub
cat ~/.ssh/id_ed25519.pub
# 复制公钥到: https://github.com/settings/keys

# 3. 使用SSH URL
GIT_URL="git@github.com:PMLiuyubin/enterprise-ai-platform.git"
```

---

## 📚 相关链接

- [GitHub Personal Access Tokens](https://github.com/settings/tokens)
- [GitHub Token 文档](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [Git 凭据存储](https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage)

---

**注意：请妥善保管你的Personal Access Token，不要泄露给他人！**

