# 🚀 继续测试和部署

## ✅ 代码已提交

现在可以触发完整的CI/CD测试和部署流程。

## 🎯 快速启动

### 方法1: 使用脚本（推荐）

```powershell
# 执行脚本自动触发并显示状态
powershell -ExecutionPolicy Bypass -File trigger-complete-test.ps1
```

### 方法2: 手动执行

```powershell
# 1. 触发完整测试和部署
gh workflow run deploy.yml --field environment=staging

# 2. 查看最新运行
gh run list --workflow="deploy.yml" --limit 1

# 3. 获取运行ID后查看详情
gh run view <运行ID>

# 4. 实时查看日志
gh run watch <运行ID>
```

## 📊 测试流程

### 阶段1: 后端测试 (test)
- ✅ 单元测试 - `tests/test-architecture`
- ✅ 集成测试 - `tests/test-integration`
- ✅ 前端API集成测试 - `tests/test_frontend_api_integration.py`
- ✅ E2E测试 - `tests/test_e2e_procurement.py`, `tests/test_complete_real_world.py`

### 阶段2: 前端测试 (frontend-test)
- ✅ Lint检查 - `npm run lint`
- ✅ 类型检查 - `npx tsc --noEmit`
- ✅ 构建测试 - `npm run build`

### 阶段3: 构建镜像 (build-images)
- ✅ api-gateway
- ✅ auth-service
- ✅ knowledge-base
- ✅ metadata-service
- ✅ workflow-engine
- ✅ web-ui

### 阶段4: 部署 (deploy)
- ✅ SSH连接到服务器
- ✅ 拉取最新代码
- ✅ 数据库迁移
- ✅ 蓝绿部署
- ✅ 健康检查
- ✅ 部署验证

## 🔍 监控测试进度

### 实时查看日志

```powershell
# 获取最新运行ID
$runId = (gh run list --workflow="deploy.yml" --limit 1 --json databaseId | ConvertFrom-Json).databaseId

# 实时查看日志
gh run watch $runId
```

### 查看特定作业

```powershell
# 查看test作业
gh run view <运行ID> --log --job=test

# 查看frontend-test作业
gh run view <运行ID> --log --job=frontend-test

# 查看build-images作业
gh run view <运行ID> --log --job=build-images

# 查看deploy作业
gh run view <运行ID> --log --job=deploy
```

### 在浏览器查看

访问GitHub Actions页面：
```
https://github.com/PMLiuyubin/enterprise-ai-platform/actions
```

## ⏱️ 预计时间

- **测试阶段**: 10-15分钟
- **构建阶段**: 10-15分钟
- **部署阶段**: 5-10分钟
- **总计**: 30-50分钟

## ✅ 测试完成后验证

### 1. 检查工作流状态

```powershell
gh run list --workflow="deploy.yml" --limit 1
```

### 2. 验证部署

访问服务器：
- 前端: `http://43.143.139.197:8080`
- 健康检查: `http://43.143.139.197:8080/health`

### 3. 测试功能

- ✅ 登录功能
- ✅ 知识库访问
- ✅ 工作流管理
- ✅ 监控面板
- ✅ 元数据管理

## 🐛 如果测试失败

### 查看失败详情

```powershell
# 查看失败作业的日志
gh run view <运行ID> --log --failed
```

### 常见问题

1. **测试失败但继续部署**
   - 测试使用 `continue-on-error: true`，不会阻止部署
   - 建议修复测试失败后再部署

2. **构建失败**
   - 检查Dockerfile配置
   - 检查依赖是否正确

3. **部署失败**
   - 检查SSH连接
   - 检查服务器资源
   - 查看部署日志

## 🚀 立即开始

执行以下命令：

```powershell
powershell -ExecutionPolicy Bypass -File trigger-complete-test.ps1
```

或手动执行：

```powershell
gh workflow run deploy.yml --field environment=staging
gh run watch
```

---

**状态**: ✅ 准备就绪，可以开始完整测试和部署！





