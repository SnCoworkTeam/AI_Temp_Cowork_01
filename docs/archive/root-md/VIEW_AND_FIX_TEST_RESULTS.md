# 📊 查看测试结果和修复代码指南

## 🔍 查看测试结果

### 方法1: 在浏览器中查看（推荐）

1. 访问GitHub Actions页面：
   ```
   https://github.com/PMLiuyubin/enterprise-ai-platform/actions
   ```

2. 点击最新的运行（最上面的）

3. 查看各个作业的状态：
   - ✅ **绿色** = 成功
   - ❌ **红色** = 失败
   - 🟡 **黄色** = 进行中
   - ⚪ **灰色** = 未开始/跳过

4. 点击失败的作业查看详细日志

### 方法2: 使用GitHub CLI

```powershell
# 获取最新运行ID
$runId = (gh run list --workflow="deploy.yml" --limit 1 --json databaseId | ConvertFrom-Json).databaseId

# 查看运行状态
gh run view $runId

# 查看所有作业状态
gh run view $runId --json jobs --jq '.jobs[] | {name: .name, status: .status, conclusion: .conclusion}'

# 查看失败的作业
gh run view $runId --json jobs --jq '.jobs[] | select(.conclusion == "failure") | {name: .name, id: .databaseId}'

# 查看特定作业的日志
gh run view $runId --log --job=<作业名>
```

### 方法3: 使用检查脚本

```powershell
# 运行检查脚本
powershell -ExecutionPolicy Bypass -File check-test-status.ps1
```

## 📋 测试结果分析

### 1. test 作业（后端测试）

**查看日志**：
```powershell
gh run view <运行ID> --log --job=test
```

**常见失败原因**：
- ❌ 单元测试失败 → 检查 `tests/test-architecture/`
- ❌ 集成测试失败 → 检查 `tests/test-integration/`
- ❌ 前端API集成测试失败 → 检查 `tests/test_frontend_api_integration.py`
- ❌ E2E测试失败 → 检查 `tests/test_e2e_procurement.py`

**修复步骤**：
1. 查看失败测试的详细错误信息
2. 在本地运行失败的测试：
   ```powershell
   pytest tests/test-architecture/test_imports.py -v
   pytest tests/test-integration/test_api_integration.py -v
   ```
3. 修复代码后重新运行测试
4. 提交修复并重新触发工作流

### 2. frontend-test 作业（前端测试）

**查看日志**：
```powershell
gh run view <运行ID> --log --job=frontend-test
```

**常见失败原因**：
- ❌ Lint错误 → 运行 `cd web-ui && npm run lint`
- ❌ 类型错误 → 运行 `cd web-ui && npx tsc --noEmit`
- ❌ 构建失败 → 检查 `web-ui/package.json` 和依赖

**修复步骤**：
1. 进入前端目录：
   ```powershell
   cd web-ui
   ```

2. 修复Lint错误：
   ```powershell
   npm run lint -- --fix
   ```

3. 修复类型错误：
   ```powershell
   npx tsc --noEmit
   # 根据错误信息修复TypeScript类型问题
   ```

4. 测试构建：
   ```powershell
   npm run build
   ```

5. 提交修复并重新触发工作流

### 3. build-images 作业（构建镜像）

**查看日志**：
```powershell
gh run view <运行ID> --log --job=build-images
```

**常见失败原因**：
- ❌ Dockerfile路径错误
- ❌ 依赖安装失败
- ❌ 构建上下文错误
- ❌ 内存不足

**修复步骤**：
1. 查看具体哪个服务构建失败
2. 检查该服务的Dockerfile路径是否正确
3. 在本地测试构建：
   ```powershell
   # 例如测试api-gateway
   docker build -f api-gateway/Dockerfile.dev -t test-api-gateway ./api-gateway
   ```
4. 修复Dockerfile或构建配置
5. 提交修复并重新触发工作流

### 4. deploy 作业（部署）

**查看日志**：
```powershell
gh run view <运行ID> --log --job=deploy
```

**常见失败原因**：
- ❌ SSH连接失败 → 检查SSH密钥配置
- ❌ 服务器资源不足
- ❌ 健康检查失败 → 检查服务是否正常启动
- ❌ 数据库迁移失败

**修复步骤**：
1. 检查SSH连接：
   ```powershell
   ssh ubuntu@43.143.139.197
   ```

2. 检查服务器资源：
   ```powershell
   ssh ubuntu@43.143.139.197 "df -h && free -h"
   ```

3. 检查服务状态：
   ```powershell
   ssh ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && docker-compose ps"
   ```

4. 手动测试部署：
   ```powershell
   ssh ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && docker-compose up -d"
   ```

## 🔧 修复代码流程

### 1. 识别问题

```powershell
# 获取失败作业列表
gh run view <运行ID> --json jobs --jq '.jobs[] | select(.conclusion == "failure") | .name'
```

### 2. 查看详细错误

```powershell
# 查看失败作业的完整日志
gh run view <运行ID> --log --job=<失败作业名> > error.log
```

### 3. 本地复现问题

```powershell
# 对于测试失败
pytest tests/<失败的测试文件> -v

# 对于构建失败
docker build -f <服务>/Dockerfile.dev -t test-<服务> ./<服务>

# 对于前端问题
cd web-ui
npm run lint
npx tsc --noEmit
npm run build
```

### 4. 修复代码

根据错误信息修复代码：
- 测试失败 → 修复测试或代码逻辑
- 类型错误 → 修复TypeScript类型
- 构建失败 → 修复Dockerfile或依赖
- 部署失败 → 检查配置和服务器状态

### 5. 验证修复

```powershell
# 运行相关测试
pytest tests/<相关测试> -v

# 构建相关服务
docker build -f <服务>/Dockerfile.dev -t test-<服务> ./<服务>
```

### 6. 提交并重新触发

```powershell
# 提交修复
git add .
git commit -m "fix: 修复<问题描述>"
git push origin main

# 重新触发工作流
gh workflow run deploy.yml --field environment=staging
```

## 📊 测试报告下载

### 下载测试结果Artifacts

```powershell
# 列出所有Artifacts
gh run view <运行ID> --json artifacts --jq '.artifacts[] | {name: .name, id: .databaseId}'

# 下载Artifacts（需要在浏览器中操作）
# 访问运行页面，点击Artifacts下载
```

## 🎯 快速修复脚本

创建 `fix-and-retry.ps1`：

```powershell
# 获取最新失败运行
$runs = gh run list --workflow="deploy.yml" --limit 5 --json databaseId,conclusion,status | ConvertFrom-Json
$failedRun = $runs | Where-Object { $_.conclusion -eq "failure" } | Select-Object -First 1

if ($failedRun) {
    Write-Host "找到失败运行: $($failedRun.databaseId)" -ForegroundColor Red
    Write-Host "查看日志: gh run view $($failedRun.databaseId) --log" -ForegroundColor Yellow
} else {
    Write-Host "没有找到失败的运行" -ForegroundColor Green
}
```

## 📝 常见问题解决

### 问题1: 测试超时

**解决方案**：
- 增加测试超时时间
- 优化测试性能
- 使用 `--maxfail=1` 快速失败

### 问题2: 构建超时

**解决方案**：
- 优化Dockerfile，使用多阶段构建
- 使用缓存加速构建
- 减少不必要的依赖

### 问题3: 内存不足

**解决方案**：
- 增加GitHub Actions运行器资源
- 优化构建过程
- 分批构建服务

---

**提示**: 每次修复后，记得提交代码并重新触发工作流！





