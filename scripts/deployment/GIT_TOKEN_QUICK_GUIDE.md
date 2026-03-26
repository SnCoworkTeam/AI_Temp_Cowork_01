# Git Token 快速指南

## 🚀 快速创建Token（3步）

### 1️⃣ 打开Token创建页面

**直接访问：**
```
https://github.com/settings/tokens/new
```

或者：
- 登录 GitHub → 点击头像 → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic)

### 2️⃣ 填写信息

- **Note**: `enterprise-ai-platform`（随便写个名字）
- **Expiration**: 选择过期时间（如90天）
- **勾选权限**: ✅ `repo`（完整仓库访问）

### 3️⃣ 生成并复制

- 点击 **"Generate token"**
- **立即复制Token**（格式：`ghp_xxxxxxxxxxxx`）
- 保存好，关闭页面后无法再查看

---

## 📝 使用Token

### 方式1：环境变量（推荐）

```bash
export GIT_USERNAME="lyb-005@163.com"
export GIT_TOKEN="ghp_your_token_here"

bash scripts/deployment/deploy-server.sh --env production
```

### 方式2：命令行参数

```bash
bash scripts/deployment/deploy-server.sh \
  --env production \
  --git-username "lyb-005@163.com" \
  --git-token "ghp_your_token_here"
```

---

## ❓ 常见问题

### Q: Token在哪里查看？

**A:** 访问 https://github.com/settings/tokens

**注意：** 只能看到Token列表，无法查看完整Token值。如果忘记了，只能重新创建。

### Q: Token格式是什么？

**A:** 通常以 `ghp_` 开头，例如：
```
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Q: Token过期了怎么办？

**A:** 重新创建一个新Token，然后更新环境变量或配置文件。

### Q: 如何测试Token是否有效？

```bash
# 替换为你的Token
curl -H "Authorization: token ghp_your_token_here" https://api.github.com/user

# 如果返回用户信息，说明Token有效
```

---

## 🔗 相关链接

- **创建Token**: https://github.com/settings/tokens/new
- **查看Token列表**: https://github.com/settings/tokens
- **GitHub文档**: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token

---

**记住：Token创建后立即复制保存，关闭页面后无法再查看！**

