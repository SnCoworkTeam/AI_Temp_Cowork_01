# 快速开始指南

本指南将帮助您快速启动和运行企业AI平台。

## 前置要求

### 必需软件

- **Docker** 20.10+ 和 **Docker Compose** 2.0+
- **Python** 3.11+ (本地开发)
- **Node.js** 20+ 和 **npm** 9+ (本地开发)
- **Git** 2.30+

### 可选软件

- **PostgreSQL客户端** (如pgAdmin、DBeaver)
- **Redis客户端** (如RedisInsight)
- **代码编辑器** (推荐VS Code)

## 快速启动（推荐）

### 1. 克隆项目

```bash
git clone <repository-url>
cd enterprise-ai-platform
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，至少配置以下内容：
# - OPENAI_API_KEY (如果使用OpenAI)
# - LANGCHAIN_API_KEY (如果使用LangChain)
# - 数据库密码
# - Redis密码（可选）
```

### 3. 启动所有服务

```bash
# 启动所有服务（开发模式，支持热重载）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f mcp-gateway
```

### 4. 验证服务运行

访问以下端点验证服务：

- **MCP Gateway**: http://localhost:8001/api/health
- **Workflow Engine**: http://localhost:8002/api/health
- **Auth Service**: http://localhost:8003/api/health
- **Knowledge Base**: http://localhost:8004/api/health
- **Web UI**: http://localhost:3000

### 5. 访问API文档

- **MCP Gateway Swagger**: http://localhost:8001/api/docs
- **Workflow Engine Swagger**: http://localhost:8002/api/docs
- **Auth Service Swagger**: http://localhost:8003/api/docs
- **Knowledge Base Swagger**: http://localhost:8004/api/docs

## 本地开发

### 1. 启动基础设施

```bash
# 只启动数据库和Redis
docker-compose up -d redis postgres
```

### 2. 启动后端服务

#### MCP Gateway

```bash
cd mcp-gateway
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m src.main
```

服务将在 `http://localhost:8001` 启动

#### Workflow Engine

```bash
cd workflow-engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

服务将在 `http://localhost:8002` 启动

#### Auth Service

```bash
cd auth-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

服务将在 `http://localhost:8003` 启动

#### Knowledge Base

```bash
cd knowledge-base
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

服务将在 `http://localhost:8004` 启动

### 3. 启动前端

```bash
cd web-ui
npm install
npm run dev
```

前端将在 `http://localhost:3000` 启动

## 配置自动化调试系统

### 1. 配置平台集成

编辑 `config/platform_integration.yaml`：

```yaml
service_monitoring:
  mcp-gateway:
    base_url: "http://localhost:8001"
  workflow-engine:
    base_url: "http://localhost:8002"
  # ... 其他服务配置
```

### 2. 配置监控系统（可选）

如果使用Prometheus、Grafana、Loki：

```yaml
monitoring_integration:
  prometheus:
    enabled: true
    url: "http://localhost:9090"
  grafana:
    enabled: true
    url: "http://localhost:3000"
  loki:
    enabled: true
    url: "http://localhost:3100"
```

### 3. 使用自动化调试系统

```python
from src.auto_debug import (
    get_error_analyzer,
    get_fix_strategy_manager,
    get_debug_orchestrator
)

# 分析错误
analyzer = get_error_analyzer()
analysis = await analyzer.analyze_error(
    error_message="MCP tool timeout",
    context={"service": "mcp-gateway"}
)

# 应用修复
manager = get_fix_strategy_manager()
result = await manager.apply_fix(
    error_category=analysis.error_category,
    error_type=analysis.error_type
)

# 协调调试
orchestrator = get_debug_orchestrator()
task = await orchestrator.submit_error_report(
    error_message="...",
    context={...}
)
```

## 运行测试

### 后端测试

```bash
# 运行所有测试
pytest

# 运行特定服务测试
cd mcp-gateway && pytest
cd workflow-engine && pytest

# 运行自动化调试系统测试
pytest tests/test_auto_debug/ -v

# 检查覆盖率
pytest --cov=src --cov-report=html
```

### 前端测试

```bash
cd web-ui
npm test
```

## 开发工作流

### 1. 创建功能分支

```bash
git checkout -b feature/my-feature
```

### 2. 开发功能

- 遵循编码规范（见 `docs/development-docs/coding-standards/`）
- 编写测试（覆盖率目标 >= 80%）
- 更新文档

### 3. 代码审查前检查

```bash
# 运行架构守护
python scripts/architecture_guard.py --check

# 运行测试
pytest

# 检查代码质量
python scripts/code-health/check-all.sh
```

### 4. 提交代码

```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature
```

### 5. 创建Pull Request

在GitHub上创建PR，确保：
- [ ] 所有测试通过
- [ ] 代码审查通过
- [ ] 文档已更新
- [ ] 架构合规性检查通过

## 常见问题

### 服务无法启动

1. 检查端口是否被占用
2. 检查环境变量配置
3. 查看服务日志：`docker-compose logs <service-name>`

### 数据库连接失败

1. 确认PostgreSQL容器正在运行：`docker-compose ps postgres`
2. 检查数据库配置：`docker-compose logs postgres`
3. 验证连接字符串：`env.example`

### Redis连接失败

1. 确认Redis容器正在运行：`docker-compose ps redis`
2. 检查Redis日志：`docker-compose logs redis`
3. 测试连接：`docker-compose exec redis redis-cli ping`

### 前端无法连接后端

1. 检查后端服务是否运行
2. 检查CORS配置
3. 检查环境变量：`NEXT_PUBLIC_*` 变量是否正确

### 自动化调试系统不工作

1. 检查配置文件：`config/platform_integration.yaml`
2. 检查服务端点是否可访问
3. 查看调试协调器日志

## 下一步

- 阅读 [编码规范](coding-standards/python-standards.md)
- 了解 [系统架构](../architecture-docs/system-overview/system-architecture.md)
- 学习 [自动化调试系统](auto-debug-system.md)
- 查看 [API文档](../api-docs/README.md)

## 获取帮助

- 查看 [故障排查指南](setup-guide/troubleshooting.md)
- 提交 Issue
- 查看项目文档：`docs/`

