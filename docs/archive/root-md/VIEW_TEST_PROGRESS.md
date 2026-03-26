# 📊 查看测试进度和日志

## 🚀 第一步：触发完整测试和部署

如果还没有触发，执行：

```powershell
gh workflow run deploy.yml --field environment=staging
```

## 📊 查看测试进度

### 方法1: 查看最新运行状态（推荐）

```powershell
# 查看最新运行
gh run list --workflow="deploy.yml" --limit 1

# 获取运行ID后查看详情
gh run view <运行ID>
```

### 方法2: 实时查看日志

```powershell
# 获取最新运行ID并实时查看
$runId = (gh run list --workflow="deploy.yml" --limit 1 --json databaseId | ConvertFrom-Json).databaseId
gh run watch $runId
```

### 方法3: 查看特定作业的日志

```powershell
# 获取运行ID
$runId = (gh run list --workflow="deploy.yml" --limit 1 --json databaseId | ConvertFrom-Json).databaseId

# 查看test作业（后端测试）
gh run view $runId --log --job=test

# 查看frontend-test作业（前端测试）
gh run view $runId --log --job=frontend-test

# 查看build-images作业（构建镜像）
gh run view $runId --log --job=build-images

# 查看deploy作业（部署）
gh run view $runId --log --job=deploy
```

## 🌐 在浏览器中查看（最直观）

访问GitHub Actions页面：
```
https://github.com/PMLiuyubin/enterprise-ai-platform/actions
```

点击最新的运行，可以看到：
- ✅ 每个作业的状态（进行中/成功/失败）
- ✅ 实时日志输出
- ✅ 测试结果
- ✅ 构建状态

## 📋 工作流执行阶段

### 阶段1: test (后端测试)
- 单元测试
- 集成测试
- 前端API集成测试
- E2E测试

### 阶段2: frontend-test (前端测试)
- Lint检查
- 类型检查
- 构建测试

### 阶段3: build-images (构建镜像)
- 构建所有服务的Docker镜像

### 阶段4: deploy (部署)
- SSH连接
- 代码拉取
- 数据库迁移
- 蓝绿部署
- 健康检查

## ⏱️ 预计时间

- **测试阶段**: 10-15分钟
- **构建阶段**: 10-15分钟
- **部署阶段**: 5-10分钟
- **总计**: 30-50分钟

## 🔍 快速检查脚本

创建一个快速检查脚本：

```powershell
# 快速检查状态
$runs = gh run list --workflow="deploy.yml" --limit 1 --json databaseId,status,conclusion,displayTitle,createdAt,url | ConvertFrom-Json

if ($runs) {
    $run = $runs[0]
    Write-Host "运行ID: $($run.databaseId)" -ForegroundColor Green
    Write-Host "状态: $($run.status)" -ForegroundColor $(if ($run.status -eq "completed") { "Green" } elseif ($run.status -eq "in_progress") { "Yellow" } else { "Cyan" })
    if ($run.conclusion) {
        Write-Host "结果: $($run.conclusion)" -ForegroundColor $(if ($run.conclusion -eq "success") { "Green" } else { "Red" })
    }
    Write-Host "查看: $($run.url)" -ForegroundColor Yellow
}
```

## ✅ 测试完成后的验证

### 1. 检查工作流状态

```powershell
gh run list --workflow="deploy.yml" --limit 1
```

### 2. 验证部署

- 前端: `http://43.143.139.197:8080`
- 健康检查: `http://43.143.139.197:8080/health`

### 3. 测试功能

- 登录功能
- 知识库访问
- 工作流管理
- 监控面板

---

**立即执行**: `gh run list --workflow="deploy.yml" --limit 1` 查看最新状态





