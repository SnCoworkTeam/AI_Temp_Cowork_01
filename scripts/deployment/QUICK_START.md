# 快速部署指南

## 📋 执行顺序

### 首次部署（新服务器）

```bash
# 1️⃣ 先执行：初始化服务器环境
sudo bash scripts/deployment/setup-server.sh --git-url https://github.com/PMLiuyubin/enterprise-ai-platform.git

# 2️⃣ 配置环境变量
cd /opt/enterprise-ai-platform
nano .env.production

# 3️⃣ 再执行：部署应用
bash scripts/deployment/deploy-server.sh --env production
```

### 日常更新（已有环境）

```bash
# 直接执行部署脚本（会自动拉取最新代码）
cd /opt/enterprise-ai-platform
bash scripts/deployment/deploy-server.sh --env production
```

---

## 🔧 如果Docker安装失败

如果 `setup-server.sh` 中Docker安装失败（网络问题），可以：

```bash
# 使用国内镜像源手动安装Docker
sudo bash scripts/deployment/install-docker-manual.sh
```

然后再继续执行 `deploy-server.sh`

---

## 📝 完整示例

### 示例1：首次部署

```bash
# SSH登录服务器
ssh user@your-server

# 步骤1：初始化环境
sudo bash /tmp/setup-server.sh \
  --git-url https://github.com/PMLiuyubin/enterprise-ai-platform.git \
  --branch main

# 步骤2：配置环境变量
cd /opt/enterprise-ai-platform
cp env.example .env.production
nano .env.production  # 编辑配置

# 步骤3：部署应用
bash scripts/deployment/deploy-server.sh --env production
```

### 示例2：日常更新

```bash
# SSH登录服务器
ssh user@your-server

# 直接部署（自动拉取最新代码）
cd /opt/enterprise-ai-platform
bash scripts/deployment/deploy-server.sh --env production
```

---

## ❓ 常见问题

### Q: 应该先执行哪个脚本？

**A:** 
- **首次部署**：先执行 `setup-server.sh`，再执行 `deploy-server.sh`
- **日常更新**：直接执行 `deploy-server.sh`

### Q: Docker安装失败怎么办？

**A:** 执行 `install-docker-manual.sh` 使用国内镜像源安装

### Q: 可以跳过setup-server.sh吗？

**A:** 如果服务器已经安装了Docker和Git，可以直接执行 `deploy-server.sh`

---

**总结：setup-server.sh（安装环境） → deploy-server.sh（部署应用）**

