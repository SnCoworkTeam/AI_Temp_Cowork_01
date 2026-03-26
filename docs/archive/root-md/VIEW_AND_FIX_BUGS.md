# 🔍 查看测试结果并修复Bug

## 📊 查看工作流运行状态

### 方法1: 使用GitHub CLI（推荐）

```powershell
# 1. 获取最新运行ID
$runId = (gh run list --workflow="deploy.yml" --limit 1 --json databaseId | ConvertFrom-Json).databaseId
Write-Host "运行ID: $runId" -ForegroundColor Green

# 2. 查看运行状态
gh run view $runId

# 3. 查看所有作业状态
gh run view $runId --json jobs --jq '.jobs[] | {name: .name, status: .status, conclusion: .conclusion}'
```

### 方法2: 在浏览器中查看（最直观）

访问：`https://github.com/PMLiuyubin/enterprise-ai-platform/actions`

点击最新的运行，可以看到：
- ✅ 绿色 = 成功
- ❌ 红色 = 失败
- 🟡 黄色 = 进行中

## 🔍 查看测试结果

### 查看所有作业的日志

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

### 查看失败的作业

```powershell
# 获取失败作业列表
gh run view $runId --json jobs --jq '.jobs[] | select(.conclusion == "failure") | {name: .name, id: .databaseId}'

# 查看特定失败作业的日志
gh run view $runId --log --job=<失败作业名>
```

### 实时查看日志

```powershell
# 实时查看整个运行
gh run watch $runId

# 实时查看特定作业
gh run view $runId --log --job=<作业名> --follow
```

## 🐛 根据测试结果修复Bug

### 步骤1: 识别失败类型

#### A. 测试失败

```powershell
# 查看测试失败详情
gh run view $runId --log --job=test | Select-String -Pattern "FAILED|ERROR|AssertionError" -Context 5
```

**常见失败原因**：
- 单元测试失败 → 检查 `tests/test-architecture/`
- 集成测试失败 → 检查 `tests/test-integration/`
- 前端API测试失败 → 检查 `tests/test_frontend_api_integration.py`
- E2E测试失败 → 检查 `tests/test_e2e_procurement.py`

#### B. 前端构建失败

```powershell
# 查看前端构建失败详情
gh run view $runId --log --job=frontend-test | Select-String -Pattern "error|Error|failed" -Context 5
```

**常见失败原因**：
- Lint错误 → 代码格式问题
- 类型错误 → TypeScript类型问题
- 构建错误 → 依赖或配置问题

#### C. Docker构建失败

```powershell
# 查看构建失败详情
gh run view $runId --log --job=build-images | Select-String -Pattern "error|Error|failed|ERROR" -Context 10
```

**常见失败原因**：
- Dockerfile路径错误
- 依赖安装失败
- 构建上下文错误

#### D. 部署失败

```powershell
# 查看部署失败详情
gh run view $runId --log --job=deploy | Select-String -Pattern "error|Error|failed|ERROR" -Context 10
```

**常见失败原因**：
- SSH连接失败
- 服务启动失败
- 健康检查失败

### 步骤2: 本地复现问题

#### 对于测试失败

```powershell
# 进入项目目录
cd E:\enterprise-ai-platform

# 安装依赖
pip install -r tests/requirements.txt

# 运行失败的测试
pytest tests/test-architecture/test_imports.py -v
pytest tests/test-integration/test_api_integration.py -v
pytest tests/test_frontend_api_integration.py -v
```

#### 对于前端问题

```powershell
# 进入前端目录
cd web-ui

# 安装依赖
npm ci --legacy-peer-deps

# 运行Lint
npm run lint

# 运行类型检查
npx tsc --noEmit

# 尝试构建
npm run build
```

#### 对于Docker构建失败

```powershell
# 测试构建特定服务
docker build -f api-gateway/Dockerfile.dev -t test-api-gateway ./api-gateway

# 查看构建日志
docker build -f <服务>/Dockerfile.dev -t test-<服务> ./<服务> 2>&1 | tee build.log
```

### 步骤3: 修复Bug

#### 修复测试失败

1. **查看具体错误信息**
   ```powershell
   # 运行测试并查看详细输出
   pytest tests/<失败的测试文件> -v --tb=short
   ```

2. **修复代码或测试**
   - 如果是代码问题 → 修复源代码
   - 如果是测试问题 → 修复测试用例
   - 如果是环境问题 → 检查配置

3. **验证修复**
   ```powershell
   # 重新运行测试
   pytest tests/<修复的测试文件> -v
   ```

#### 修复前端问题

1. **修复Lint错误**
   ```powershell
   cd web-ui
   npm run lint -- --fix
   ```

2. **修复类型错误**
   ```powershell
   # 查看类型错误
   npx tsc --noEmit
   # 根据错误信息修复TypeScript类型
   ```

3. **验证修复**
   ```powershell
   npm run lint
   npx tsc --noEmit
   npm run build
   ```

#### 修复Docker构建问题

1. **检查Dockerfile**
   ```powershell
   # 查看Dockerfile内容
   Get-Content <服务>/Dockerfile.dev
   ```

2. **修复构建问题**
   - 检查Dockerfile路径
   - 检查依赖安装
   - 检查构建上下文

3. **验证修复**
   ```powershell
   docker build -f <服务>/Dockerfile.dev -t test-<服务> ./<服务>
   ```

### 步骤4: 提交并重新测试

```powershell
# 1. 检查更改
git status

# 2. 添加修复的文件
git add <修复的文件>

# 3. 提交
git commit -m "fix: 修复<问题描述>

- 修复<具体问题>
- 修复<另一个问题>"

# 4. 推送
git push origin main

# 5. 等待并触发新工作流
Start-Sleep -Seconds 5
gh workflow run deploy.yml --field environment=staging

# 6. 监控新运行
gh run watch
```

## 📋 快速诊断脚本

创建 `diagnose-failures.ps1`：

```powershell
# 获取最新运行
$runId = (gh run list --workflow="deploy.yml" --limit 1 --json databaseId | ConvertFrom-Json).databaseId

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "诊断工作流失败" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "运行ID: $runId" -ForegroundColor Green
Write-Host ""

# 获取失败作业
$failedJobs = gh run view $runId --json jobs --jq '.jobs[] | select(.conclusion == "failure") | .name' | ConvertFrom-Json

if ($failedJobs) {
    Write-Host "失败的作业:" -ForegroundColor Red
    $failedJobs | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    Write-Host ""
    
    foreach ($job in $failedJobs) {
        Write-Host "==========================================" -ForegroundColor Cyan
        Write-Host "作业: $job" -ForegroundColor Cyan
        Write-Host "==========================================" -ForegroundColor Cyan
        
        # 提取错误信息
        $log = gh run view $runId --log --job=$job 2>&1
        $errors = $log | Select-String -Pattern "error|Error|ERROR|failed|Failed|FAILED" -Context 3
        
        if ($errors) {
            Write-Host "错误摘要:" -ForegroundColor Yellow
            $errors | Select-Object -First 10 | ForEach-Object { 
                Write-Host $_.Line -ForegroundColor Red 
            }
        }
        
        Write-Host ""
        Write-Host "查看完整日志:" -ForegroundColor Gray
        Write-Host "  gh run view $runId --log --job=$job" -ForegroundColor White
        Write-Host ""
    }
} else {
    Write-Host "✅ 没有失败的作业" -ForegroundColor Green
}
```

## 🎯 常见问题修复指南

### 问题1: 测试超时

**解决方案**：
```python
# 在测试文件中增加超时
@pytest.mark.asyncio
@pytest.mark.timeout(60)  # 60秒超时
async def test_something():
    ...
```

### 问题2: 依赖冲突

**解决方案**：
```powershell
# 更新requirements.txt
pip install --upgrade <冲突的包>

# 或使用特定版本
pip install <包名>==<版本号>
```

### 问题3: 端口冲突

**解决方案**：
```yaml
# 在docker-compose.yml中修改端口
ports:
  - "8081:8080"  # 改为其他端口
```

### 问题4: 环境变量缺失

**解决方案**：
```yaml
# 在工作流中添加环境变量
env:
  REQUIRED_VAR: ${{ secrets.REQUIRED_VAR }}
```

## 📝 修复流程总结

1. **查看运行状态** → 识别失败的作业
2. **查看日志** → 找到具体错误
3. **本地复现** → 在本地环境重现问题
4. **修复代码** → 根据错误信息修复
5. **本地验证** → 确保修复有效
6. **提交推送** → 提交修复并触发新工作流
7. **验证修复** → 检查新运行是否通过

---

**提示**: 使用 `gh run watch` 可以实时查看工作流进度！





