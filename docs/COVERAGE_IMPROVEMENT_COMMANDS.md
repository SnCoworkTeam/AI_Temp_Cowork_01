# 测试覆盖率80%目标 - 直接命令执行

本文档包含所有需要执行的命令，可以直接在命令行中运行。

## 前置检查

### 1. 检查SSH配置
```cmd
type remote.ssh
```

### 2. 测试SSH连接（限时10秒）
```cmd
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "echo 'Connection OK'"
```

## 服务处理流程

对每个服务，按以下顺序执行命令：

### 步骤1：检查当前覆盖率

```cmd
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "sudo docker exec enterprise-ai-{service} python3 -m pytest /app/tests --cov=/app/src --cov-report=json:/tmp/coverage.json --cov-report=term-missing 2>&1"
```

### 步骤2：下载覆盖率报告

```cmd
scp -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server:/tmp/coverage.json .coverage-reports\{service}-coverage.json
```

### 步骤3：查看覆盖率（需要Python解析JSON，或手动查看）

```cmd
py -c "import json; data=json.load(open('.coverage-reports\{service}-coverage.json')); print(f\"Coverage: {data['totals']['percent_covered']:.2f}%\")"
```

### 步骤4：如果覆盖率<80%，生成测试文件

```cmd
py scripts\test-coverage\improve-coverage.py --service {service}
```

### 步骤5：上传测试文件

```cmd
scp -F remote.ssh -o ConnectTimeout=10 {service}\tests\*.py enterprise-ai-server:/opt/enterprise-ai-platform/{service}/tests/
```

### 步骤6：重新运行测试

重复步骤1-3

## 各服务具体命令

### Database服务

```cmd
REM 步骤1: 运行测试
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "sudo docker exec enterprise-ai-postgres python3 -m pytest /database/tests --cov=/database/src --cov-report=json:/tmp/coverage.json --cov-report=term-missing 2>&1"

REM 步骤2: 下载报告
scp -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server:/tmp/coverage.json .coverage-reports\database-coverage.json

REM 步骤3: 检查覆盖率
py -c "import json; data=json.load(open('.coverage-reports\\database-coverage.json')); print(f\"Coverage: {data['totals']['percent_covered']:.2f}%\")"
```

### Auth Service

```cmd
REM 步骤1: 运行测试
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "sudo docker exec enterprise-ai-auth-service python3 -m pytest /app/tests --cov=/app/src --cov-report=json:/tmp/coverage.json --cov-report=term-missing 2>&1"

REM 步骤2: 下载报告
scp -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server:/tmp/coverage.json .coverage-reports\auth-service-coverage.json

REM 步骤3: 检查覆盖率
py -c "import json; data=json.load(open('.coverage-reports\\auth-service-coverage.json')); print(f\"Coverage: {data['totals']['percent_covered']:.2f}%\")"
```

### MCP Gateway

```cmd
REM 步骤1: 运行测试
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "sudo docker exec enterprise-ai-mcp-gateway python3 -m pytest /app/tests --cov=/app/src --cov-report=json:/tmp/coverage.json --cov-report=term-missing 2>&1"

REM 步骤2: 下载报告
scp -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server:/tmp/coverage.json .coverage-reports\mcp-gateway-coverage.json

REM 步骤3: 检查覆盖率
py -c "import json; data=json.load(open('.coverage-reports\\mcp-gateway-coverage.json')); print(f\"Coverage: {data['totals']['percent_covered']:.2f}%\")"
```

### Workflow Engine

```cmd
REM 步骤1: 运行测试
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "sudo docker exec enterprise-ai-workflow-engine python3 -m pytest /app/tests --cov=/app/src --cov-report=json:/tmp/coverage.json --cov-report=term-missing 2>&1"

REM 步骤2: 下载报告
scp -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server:/tmp/coverage.json .coverage-reports\workflow-engine-coverage.json

REM 步骤3: 检查覆盖率
py -c "import json; data=json.load(open('.coverage-reports\\workflow-engine-coverage.json')); print(f\"Coverage: {data['totals']['percent_covered']:.2f}%\")"
```

### Knowledge Base

```cmd
REM 步骤1: 运行测试
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "sudo docker exec enterprise-ai-knowledge-base python3 -m pytest /app/tests --cov=/app/src --cov-report=json:/tmp/coverage.json --cov-report=term-missing 2>&1"

REM 步骤2: 下载报告
scp -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server:/tmp/coverage.json .coverage-reports\knowledge-base-coverage.json

REM 步骤3: 检查覆盖率
py -c "import json; data=json.load(open('.coverage-reports\\knowledge-base-coverage.json')); print(f\"Coverage: {data['totals']['percent_covered']:.2f}%\")"
```

### Metadata Service

```cmd
REM 步骤1: 运行测试
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "sudo docker exec enterprise-ai-metadata-service python3 -m pytest /app/tests --cov=/app/src --cov-report=json:/tmp/coverage.json --cov-report=term-missing 2>&1"

REM 步骤2: 下载报告
scp -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server:/tmp/coverage.json .coverage-reports\metadata-service-coverage.json

REM 步骤3: 检查覆盖率
py -c "import json; data=json.load(open('.coverage-reports\\metadata-service-coverage.json')); print(f\"Coverage: {data['totals']['percent_covered']:.2f}%\")"
```

## 上传文件命令

### 上传测试文件

```cmd
REM Database
scp -F remote.ssh -o ConnectTimeout=10 database\tests\*.py enterprise-ai-server:/opt/enterprise-ai-platform/database/tests/

REM Auth Service
scp -F remote.ssh -o ConnectTimeout=10 auth-service\tests\*.py enterprise-ai-server:/opt/enterprise-ai-platform/auth-service/tests/

REM MCP Gateway
scp -F remote.ssh -o ConnectTimeout=10 mcp-gateway\tests\*.py enterprise-ai-server:/opt/enterprise-ai-platform/mcp-gateway/tests/

REM Workflow Engine
scp -F remote.ssh -o ConnectTimeout=10 workflow-engine\tests\*.py enterprise-ai-server:/opt/enterprise-ai-platform/workflow-engine/tests/

REM Knowledge Base
scp -F remote.ssh -o ConnectTimeout=10 knowledge-base\tests\*.py enterprise-ai-server:/opt/enterprise-ai-platform/knowledge-base/tests/

REM Metadata Service
scp -F remote.ssh -o ConnectTimeout=10 metadata-service\tests\*.py enterprise-ai-server:/opt/enterprise-ai-platform/metadata-service/tests/
```

## 注意事项

1. 所有SSH/SCP命令都设置了`-o ConnectTimeout=10`，连接限时10秒
2. 如果命令超时，需要重新执行
3. 每次执行命令后检查返回码（`echo %ERRORLEVEL%`）
4. 如果测试失败，查看输出中的错误信息，修复后重新上传和测试

