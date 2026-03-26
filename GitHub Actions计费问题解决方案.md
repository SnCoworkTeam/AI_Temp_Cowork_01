# GitHub Actions 计费问题解决方案

## 🔍 问题原因

GitHub Actions 的免费额度：
- **公开仓库**：无限免费
- **私有仓库**：每月 2000 分钟免费
- **企业账户**：根据计划不同

当免费额度用完后，需要：
1. 升级付费计划
2. 或者优化工作流减少使用量

## ✅ 解决方案

### 方案1: 修复账户付款（推荐，如果需要持续使用）

1. **检查账户状态**
   - 进入：`https://github.com/settings/billing`
   - 检查付款方式是否有效
   - 检查是否有未付账单

2. **增加支出限制**
   - 进入：`Settings` → `Billing and plans`
   - 点击 `Spending limits`
   - 增加或移除支出限制

3. **升级计划**
   - 如果需要更多 Actions 分钟数
   - 考虑升级到付费计划

### 方案2: 优化工作流（节省费用）

#### 2.1 禁用自动触发的前端 CI

已修改 `frontend-ci.yml`，现在只支持手动触发：

```yaml
# 已禁用自动触发
# on:
#   push:
#     branches: [ main, develop ]

# 只允许手动触发
workflow_dispatch:
```

#### 2.2 使用轻量级部署工作流

已创建 `deploy-lightweight.yml`：
- ✅ 跳过测试步骤
- ✅ 限制运行时间（10分钟）
- ✅ 直接部署，节省 Actions 分钟数

#### 2.3 添加路径过滤

只在实际代码变更时触发：

```yaml
on:
  push:
    branches: [ main ]
    paths-ignore:
      - '**.md'          # 忽略文档变更
      - 'docs/**'        # 忽略文档目录
      - '.gitignore'     # 忽略配置文件
```

### 方案3: 使用自托管 Runner（完全免费）

在服务器上安装 GitHub Actions Runner，完全免费使用：

#### 步骤1: 在服务器上安装 Runner

```bash
# SSH 到服务器
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197

# 下载 Runner
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# 配置 Runner（需要从 GitHub 获取 token）
./config.sh --url https://github.com/PMLiuyubin/enterprise-ai-platform --token YOUR_TOKEN

# 安装为服务
sudo ./svc.sh install
sudo ./svc.sh start
```

#### 步骤2: 修改工作流使用自托管 Runner

```yaml
jobs:
  deploy:
    runs-on: self-hosted  # 使用自托管 runner
    # 或者指定标签
    # runs-on: [self-hosted, linux, x64]
```

**优势**：
- ✅ 完全免费
- ✅ 无时间限制
- ✅ 可以访问服务器资源
- ✅ 部署更快（无需 SSH）

**注意事项**：
- ⚠️ 需要服务器保持运行
- ⚠️ 需要配置网络安全
- ⚠️ 需要定期更新 Runner

### 方案4: 使用 Git Hooks + 服务器端脚本（完全免费）

不使用 GitHub Actions，直接在服务器上设置 Git Hook：

#### 步骤1: 在服务器上设置 Git Hook

```bash
# SSH 到服务器
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197

# 进入项目目录
cd /opt/enterprise-ai-platform

# 创建 post-receive hook
cat > .git/hooks/post-receive << 'EOF'
#!/bin/bash
cd /opt/enterprise-ai-platform
git pull origin main
docker-compose up -d --build
sleep 20
curl -f http://localhost:8080/health || exit 1
echo "✅ 自动部署完成"
EOF

chmod +x .git/hooks/post-receive
```

#### 步骤2: 配置 Git 推送触发

```bash
# 在本地配置推送后触发部署
git remote set-url origin ssh://ubuntu@43.143.139.197/opt/enterprise-ai-platform.git
```

## 📊 方案对比

| 方案 | 费用 | 复杂度 | 推荐度 |
|------|------|--------|--------|
| 修复付款/升级计划 | 付费 | 低 | ⭐⭐⭐⭐ |
| 优化工作流 | 免费 | 中 | ⭐⭐⭐⭐⭐ |
| 自托管 Runner | 免费 | 中 | ⭐⭐⭐⭐ |
| Git Hooks | 免费 | 高 | ⭐⭐⭐ |

## 🚀 快速修复（立即生效）

### 方法1: 使用轻量级部署工作流

已创建 `deploy-lightweight.yml`，现在可以：

1. **手动触发轻量级部署**：
   - 进入 GitHub Actions 页面
   - 选择 "🚀 轻量级自动部署（无测试）"
   - 点击 "Run workflow"

2. **或者推送代码触发**：
   ```powershell
   git add .
   git commit -m "使用轻量级部署"
   git push origin main
   ```

### 方法2: 禁用消耗大的工作流

已禁用 `frontend-ci.yml` 的自动触发，现在：
- ✅ 不会自动运行前端测试
- ✅ 可以手动触发（如果需要）
- ✅ 节省 Actions 分钟数

## 📝 后续建议

1. **监控 Actions 使用量**
   - 定期检查：`https://github.com/settings/billing`
   - 查看使用报告

2. **优化工作流**
   - 只在实际需要时运行
   - 使用缓存减少构建时间
   - 合并多个步骤

3. **考虑自托管 Runner**
   - 如果经常使用，自托管 Runner 更经济
   - 适合私有仓库

4. **使用条件触发**
   - 只在特定文件变更时触发
   - 使用 `paths` 和 `paths-ignore`

## ✅ 当前状态

- ✅ 已创建轻量级部署工作流（`deploy-lightweight.yml`）
- ✅ 已禁用前端 CI 自动触发
- ✅ 自动部署工作流（`auto-deploy.yml`）仍然可用
- ⚠️ 需要修复 GitHub 账户付款问题才能使用 Actions

## 🎯 推荐方案

**短期**：使用轻量级部署工作流（`deploy-lightweight.yml`）
- 跳过测试，直接部署
- 节省 Actions 分钟数

**长期**：设置自托管 Runner
- 完全免费
- 无时间限制
- 部署更快


