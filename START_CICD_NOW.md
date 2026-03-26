# 启动CI/CD工作流 - 立即执行

## 🚀 方法1: 使用GitHub CLI启动（推荐）

### 步骤1: 验证登录状态

```powershell
# 如果未登录，先登录
gh auth login

# 或者使用token直接登录
echo "你的token" | gh auth login --with-token
```

### 步骤2: 查看可用的工作流

```powershell
# 列出所有工作流
gh workflow list
```

### 步骤3: 启动部署工作流

```powershell
# 启动到staging环境（推荐先测试）
gh workflow run "Deploy to Server.yml" --field environment=staging

# 或者启动到production环境
gh workflow run "Deploy to Server.yml" --field environment=production

# 或者启动到development环境
gh workflow run "Deploy to Server.yml" --field environment=development
```

### 步骤4: 查看运行状态

```powershell
# 查看最近的工作流运行
gh run list --workflow="Deploy to Server.yml" --limit 5

# 实时查看最新运行的日志
gh run watch

# 查看特定运行的详细信息
# 先获取run-id
gh run list --workflow="Deploy to Server.yml" --limit 1
# 然后查看日志（替换<run-id>为实际的ID）
gh run view <run-id> --log
```

## 🌐 方法2: 通过GitHub Web界面启动（如果CLI有问题）

1. **访问Actions页面**
   - 打开浏览器，访问：`https://github.com/PMLiuyubin/enterprise-ai-platform/actions`

2. **选择工作流**
   - 在左侧边栏找到 `Deploy to Server` 工作流
   - 点击进入

3. **运行工作流**
   - 点击右上角的 `Run workflow` 按钮
   - 选择环境（staging/production/development）
   - 点击绿色的 `Run workflow` 按钮

4. **查看运行状态**
   - 点击运行中的工作流查看详细日志
   - 实时查看每个步骤的执行情况

## 📋 其他可用的工作流

```powershell
# 运行测试套件
gh workflow run "Test Suite.yml"

# 运行PR检查
gh workflow run "PR Checks.yml"

# 运行前端CI
gh workflow run "Frontend CI.yml"

# 运行数据库迁移
gh workflow run "Database Migration.yml"
```

## 🔍 监控CI/CD状态

```powershell
# 查看所有运行
gh run list

# 查看特定工作流
gh run list --workflow="Deploy to Server.yml"

# 查看失败的工作流
gh run list --status=failure --limit 10

# 查看成功的工作流
gh run list --status=success --limit 10
```

## ⚡ 快速启动命令（一键执行）

```powershell
# 完整的一键启动脚本
Write-Host "🚀 启动CI/CD工作流..." -ForegroundColor Cyan

# 1. 启动到staging环境
gh workflow run "Deploy to Server.yml" --field environment=staging

# 2. 等待几秒
Start-Sleep -Seconds 3

# 3. 查看运行状态
Write-Host "`n📊 查看工作流状态..." -ForegroundColor Cyan
gh run list --workflow="Deploy to Server.yml" --limit 3

# 4. 实时监控（可选）
Write-Host "`n💡 提示: 使用 'gh run watch' 实时查看运行日志" -ForegroundColor Yellow
```

## 🎯 推荐流程

1. **首次启动**：使用 `staging` 环境测试
   ```powershell
   gh workflow run "Deploy to Server.yml" --field environment=staging
   ```

2. **验证staging**：确认部署成功后再部署到production
   ```powershell
   gh workflow run "Deploy to Server.yml" --field environment=production
   ```

3. **监控运行**：实时查看日志
   ```powershell
   gh run watch
   ```

## ⚠️ 注意事项

1. **Secrets配置**：确保已配置以下secrets：
   - `SERVER_HOST`
   - `SERVER_USER`
   - `SERVER_URL`
   - `SSH_PRIVATE_KEY`（如果使用SSH部署）

2. **权限检查**：确保token有 `workflow` 权限

3. **工作流文件**：确保 `.github/workflows/deploy.yml` 文件存在且正确

4. **分支要求**：某些工作流可能只在 `main` 分支上运行

---

**创建时间**: 2025-12-03
**状态**: 准备启动





