# 测试覆盖率80%目标 - 命令执行计划

## 目标
所有服务测试覆盖率达到80%，使用命令直接执行，不使用脚本。

## 服务列表
1. auth-service (容器: enterprise-ai-auth-service)
2. knowledge-base (容器: enterprise-ai-knowledge-base)
3. metadata-service (容器: enterprise-ai-metadata-service)
4. workflow-engine (容器: enterprise-ai-workflow-engine)
5. mcp-gateway (容器: enterprise-ai-mcp-gateway)
6. database (容器: enterprise-ai-postgres)

## SSH配置信息
- Host: enterprise-ai-server
- HostName: 43.143.139.197
- User: ubuntu
- IdentityFile: enterprise_ai_platform.pem
- ConnectTimeout: 10秒

## 重要规则
1. **所有命令必须加10秒超时限制**
2. **Windows不能用&&，要用分号或分开执行**
3. **所有命令直接在对话框执行，不用脚本**
4. **每次连接服务器限时10秒**
5. **按to-dos任务清单逐个进行**

## 命令执行模板

### Windows命令超时处理
Windows下使用`timeout`命令或PowerShell的`Start-Process -Timeout`，但为了简单，我们使用SSH的`-o ConnectTimeout=10`参数。

### 基础命令结构
```powershell
# SSH连接测试（10秒超时）
ssh -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server "命令"

# SCP上传文件（10秒超时）
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "本地文件" enterprise-ai-server:"远程路径"

# SCP下载文件（10秒超时）
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server:"远程文件" "本地路径"
```

## 执行流程

### 阶段1: 初始化检查
**任务1.1: 检查SSH连接**
```powershell
ssh -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server "echo 'SSH连接成功'"
```

**任务1.2: 检查Docker容器状态**
```powershell
ssh -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server "docker ps --format 'table {{.Names}}\t{{.Status}}'"
```

**任务1.3: 检查项目路径**
```powershell
ssh -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server "ls -la /opt/enterprise-ai-platform"
```

### 阶段2: 循环处理每个服务

对每个服务执行以下循环，直到覆盖率达到80%：

#### 步骤1: 检查当前覆盖率
```powershell
# 在服务器Docker容器中运行测试并生成覆盖率报告
ssh -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server "docker exec enterprise-ai-auth-service pytest /app/tests --cov=/app/src --cov-report=json:/tmp/coverage.json --cov-report=term 2>&1"
```

#### 步骤2: 下载覆盖率报告
```powershell
# 从服务器下载覆盖率JSON文件
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server:/tmp/coverage.json .coverage-reports/auth-service-coverage.json
```

#### 步骤3: 解析覆盖率（手动检查）
查看`.coverage-reports/auth-service-coverage.json`文件中的`totals.percent_covered`字段。

#### 步骤4: 如果覆盖率<80%，创建/修改测试文件
```powershell
# 创建测试文件（示例）
# 在本地创建测试文件，然后上传到服务器
```

#### 步骤5: 上传测试文件到服务器
```powershell
# 上传测试文件
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "auth-service/tests/test_new.py" enterprise-ai-server:/opt/enterprise-ai-platform/auth-service/tests/test_new.py
```

#### 步骤6: 在服务器Docker中运行测试
```powershell
# 运行测试
ssh -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server "docker exec enterprise-ai-auth-service pytest /app/tests/test_new.py -v"
```

#### 步骤7: 如果测试失败，修复bug
- 查看测试输出，定位问题
- 修改源代码文件
- 上传修改后的文件到服务器
- 重新运行测试

#### 步骤8: 重新检查覆盖率
重复步骤1-3，直到覆盖率达到80%

## 服务特定命令

### auth-service
```powershell
# 容器名: enterprise-ai-auth-service
# 测试路径: /app/tests
# 源码路径: /app/src
# 远程路径: /opt/enterprise-ai-platform/auth-service

# 运行测试
ssh -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server "docker exec enterprise-ai-auth-service pytest /app/tests --cov=/app/src --cov-report=json:/tmp/coverage.json --cov-report=term 2>&1"

# 上传测试文件
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "auth-service/tests/test_*.py" enterprise-ai-server:/opt/enterprise-ai-platform/auth-service/tests/

# 上传源码文件（修复bug后）
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "auth-service/src/*.py" enterprise-ai-server:/opt/enterprise-ai-platform/auth-service/src/
```

### knowledge-base
```powershell
# 容器名: enterprise-ai-knowledge-base
# 测试路径: /app/tests
# 源码路径: /app/src
# 远程路径: /opt/enterprise-ai-platform/knowledge-base

# 运行测试
ssh -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server "docker exec enterprise-ai-knowledge-base pytest /app/tests --cov=/app/src --cov-report=json:/tmp/coverage.json --cov-report=term 2>&1"

# 上传测试文件
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "knowledge-base/tests/test_*.py" enterprise-ai-server:/opt/enterprise-ai-platform/knowledge-base/tests/

# 上传源码文件
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "knowledge-base/src/*.py" enterprise-ai-server:/opt/enterprise-ai-platform/knowledge-base/src/
```

### metadata-service
```powershell
# 容器名: enterprise-ai-metadata-service
# 测试路径: /app/tests
# 源码路径: /app/src
# 远程路径: /opt/enterprise-ai-platform/metadata-service

# 运行测试
ssh -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server "docker exec enterprise-ai-metadata-service pytest /app/tests --cov=/app/src --cov-report=json:/tmp/coverage.json --cov-report=term 2>&1"

# 上传测试文件
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "metadata-service/tests/test_*.py" enterprise-ai-server:/opt/enterprise-ai-platform/metadata-service/tests/

# 上传源码文件
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "metadata-service/src/*.py" enterprise-ai-server:/opt/enterprise-ai-platform/metadata-service/src/
```

### workflow-engine
```powershell
# 容器名: enterprise-ai-workflow-engine
# 测试路径: /app/tests
# 源码路径: /app/src
# 远程路径: /opt/enterprise-ai-platform/workflow-engine

# 运行测试
ssh -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server "docker exec enterprise-ai-workflow-engine pytest /app/tests --cov=/app/src --cov-report=json:/tmp/coverage.json --cov-report=term 2>&1"

# 上传测试文件
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "workflow-engine/tests/test_*.py" enterprise-ai-server:/opt/enterprise-ai-platform/workflow-engine/tests/

# 上传源码文件
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "workflow-engine/src/*.py" enterprise-ai-server:/opt/enterprise-ai-platform/workflow-engine/src/
```

### mcp-gateway
```powershell
# 容器名: enterprise-ai-mcp-gateway
# 测试路径: /app/tests
# 源码路径: /app/src
# 远程路径: /opt/enterprise-ai-platform/mcp-gateway

# 运行测试
ssh -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server "docker exec enterprise-ai-mcp-gateway pytest /app/tests --cov=/app/src --cov-report=json:/tmp/coverage.json --cov-report=term 2>&1"

# 上传测试文件
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "mcp-gateway/tests/test_*.py" enterprise-ai-server:/opt/enterprise-ai-platform/mcp-gateway/tests/

# 上传源码文件
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "mcp-gateway/src/*.py" enterprise-ai-server:/opt/enterprise-ai-platform/mcp-gateway/src/
```

### database
```powershell
# 容器名: enterprise-ai-postgres
# 测试路径: /database/tests
# 源码路径: /database/src
# 远程路径: /opt/enterprise-ai-platform/database

# 运行测试（注意：postgres容器可能没有pytest，需要特殊处理）
ssh -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server "docker exec enterprise-ai-postgres pytest /database/tests --cov=/database/src --cov-report=json:/tmp/coverage.json --cov-report=term 2>&1"

# 上传测试文件
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "database/tests/test_*.py" enterprise-ai-server:/opt/enterprise-ai-platform/database/tests/

# 上传源码文件
scp -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "database/src/*.py" enterprise-ai-server:/opt/enterprise-ai-platform/database/src/
```

## 覆盖率解析命令

### 从JSON文件提取覆盖率（Windows PowerShell）
```powershell
# 读取JSON并提取覆盖率
$json = Get-Content .coverage-reports/auth-service-coverage.json | ConvertFrom-Json
$coverage = $json.totals.percent_covered
Write-Host "覆盖率: $coverage%"
```

### 从测试输出提取覆盖率（手动查看）
测试输出中会包含类似这样的行：
```
TOTAL    1234    987    80%
```
或者
```
Coverage: 80.5%
```

## 循环执行逻辑

### 主循环结构（概念性，实际用命令逐个执行）

1. **初始化**
   - 检查SSH连接
   - 检查所有容器状态
   - 创建本地覆盖率报告目录

2. **对每个服务循环**
   - 检查当前覆盖率
   - 如果 < 80%:
     - 分析缺失的测试
     - 创建/修改测试文件
     - 上传测试文件
     - 运行测试
     - 如果测试失败，修复bug并重新上传
     - 重新检查覆盖率
   - 如果 >= 80%:
     - 标记服务完成
     - 继续下一个服务

3. **所有服务完成后**
   - 生成最终报告
   - 验证所有服务都达到80%

## 错误处理

### SSH连接超时
如果SSH命令超过10秒，命令会自动失败。重新执行相同命令。

### 容器不存在或未运行
```powershell
# 检查容器状态
ssh -F remote.ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no enterprise-ai-server "docker ps -a | grep enterprise-ai-auth-service"
```

### 测试失败
1. 查看测试输出，找到失败原因
2. 修复源代码中的bug
3. 上传修复后的文件
4. 重新运行测试

### 文件上传失败
1. 检查文件路径是否正确
2. 检查服务器目录权限
3. 检查SSH连接是否正常
4. 重新执行上传命令

## 进度跟踪

### 创建进度文件
```powershell
# 创建进度跟踪文件
@"
{
  "services": {
    "auth-service": {"coverage": 0, "target": 80, "status": "pending"},
    "knowledge-base": {"coverage": 0, "target": 80, "status": "pending"},
    "metadata-service": {"coverage": 0, "target": 80, "status": "pending"},
    "workflow-engine": {"coverage": 0, "target": 80, "status": "pending"},
    "mcp-gateway": {"coverage": 0, "target": 80, "status": "pending"},
    "database": {"coverage": 0, "target": 80, "status": "pending"}
  }
}
"@ | Out-File -FilePath .coverage-progress.json -Encoding UTF8
```

### 更新进度
手动更新`.coverage-progress.json`文件，记录每个服务的当前覆盖率和状态。

## 注意事项

1. **Windows命令分隔符**: 不能使用`&&`，使用分号`;`或分开执行
2. **路径分隔符**: Windows使用反斜杠`\`，但SSH命令中使用正斜杠`/`
3. **文件路径**: 使用引号包裹包含空格的路径
4. **超时处理**: 所有SSH/SCP命令都使用`-o ConnectTimeout=10`
5. **错误重试**: 如果命令失败，直接重新执行，不要使用循环脚本

## 执行顺序

按照以下顺序逐个处理服务：
1. auth-service
2. knowledge-base
3. metadata-service
4. workflow-engine
5. mcp-gateway
6. database

每个服务完成后，再进行下一个服务。

