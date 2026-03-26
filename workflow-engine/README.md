# Workflow Engine 服务

企业AI平台的工作流引擎服务，基于LangGraph和LangChain提供智能工作流编排和执行能力。

## 功能特性

- 🔄 **工作流编排**: 基于LangGraph的可视化工作流设计
- 🤖 **AI集成**: 深度集成大语言模型（支持OpenAI和DeepSeek）
- 📊 **执行管理**: 工作流执行状态跟踪和历史记录
- 🔍 **版本控制**: 工作流版本管理和回滚
- 📈 **性能监控**: 工作流执行性能指标和统计
- 🎨 **设计器支持**: 与前端工作流设计器集成

## 技术栈

- **框架**: FastAPI
- **工作流引擎**: LangGraph + LangChain
- **AI模型**: OpenAI / DeepSeek
- **数据库**: PostgreSQL (通过database模块)
- **缓存**: Redis
- **Python版本**: 3.11+

## API端点

### 工作流管理

- `POST /api/workflows` - 创建工作流
- `GET /api/workflows` - 获取工作流列表（支持分页、过滤、搜索）
- `GET /api/workflows/{id}` - 获取工作流详情
- `PUT /api/workflows/{id}` - 更新工作流
- `DELETE /api/workflows/{id}` - 删除工作流

### 工作流设计器

- `GET /api/workflows/{id}/designer` - 获取设计器元数据
- `POST /api/workflows/{id}/save` - 保存工作流设计
- `GET /api/workflows/{id}/nodes` - 获取节点列表
- `POST /api/workflows/{id}/nodes` - 添加节点
- `PUT /api/workflows/{id}/nodes/{node_id}` - 更新节点
- `DELETE /api/workflows/{id}/nodes/{node_id}` - 删除节点

### 工作流执行

- `POST /api/workflows/{id}/execute` - 执行工作流
- `GET /api/executions/{execution_id}` - 获取执行状态
- `GET /api/executions` - 获取执行历史列表
- `POST /api/executions/{execution_id}/cancel` - 取消执行

### 版本管理

- `GET /api/workflows/{id}/versions` - 获取版本列表
- `GET /api/workflows/{id}/versions/{version}` - 获取指定版本
- `POST /api/workflows/{id}/versions/{version}/restore` - 恢复版本

### 性能监控

- `GET /api/metrics/workflows/{id}` - 获取工作流性能指标
- `GET /api/metrics/executions` - 获取执行统计
- `GET /api/metrics/nodes/{node_id}` - 获取节点性能指标

### 健康检查

- `GET /api/health` - 健康检查
- `GET /api/health/ready` - 就绪检查
- `GET /api/health/live` - 存活检查

## 配置

### 环境变量

```bash
# 服务配置
HOST=0.0.0.0
PORT=8002
DEBUG=false

# CORS配置（逗号分隔）
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# LangChain配置
OPENAI_API_KEY=your_openai_api_key
# 使用 DeepSeek API 时设置:
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
LANGCHAIN_API_KEY=your_langchain_api_key
LANGCHAIN_TRACING_V2=false

# MCP Gateway配置
MCP_GATEWAY_URL=http://mcp-gateway:8001

# 知识库服务配置
KNOWLEDGE_BASE_URL=http://knowledge-base:8004

# 元数据服务配置
METADATA_SERVICE_URL=http://metadata-service:8005

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# 日志配置
LOG_LEVEL=info  # 注意：uvicorn需要小写
```

## 使用示例

### 1. 创建工作流

```bash
curl -X POST "http://localhost:8002/api/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "数据处理流程",
    "description": "处理客户数据的工作流",
    "nodes": [
      {
        "id": "node1",
        "type": "start",
        "position": {"x": 100, "y": 100}
      },
      {
        "id": "node2",
        "type": "llm",
        "config": {
          "prompt": "分析以下数据：{{input}}"
        },
        "position": {"x": 300, "y": 100}
      }
    ],
    "connections": [
      {
        "from": "node1",
        "to": "node2"
      }
    ]
  }'
```

### 2. 执行工作流

```bash
curl -X POST "http://localhost:8002/api/workflows/{workflow_id}/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "data": "客户数据示例"
    },
    "context": {
      "user_id": "user123"
    }
  }'
```

### 3. 获取执行状态

```bash
curl -X GET "http://localhost:8002/api/executions/{execution_id}"
```

### 4. 获取工作流列表

```bash
curl -X GET "http://localhost:8002/api/workflows?page=1&page_size=20"
```

## 开发

### 本地运行

```bash
cd workflow-engine
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8002
```

### Docker开发

```bash
# 构建开发镜像
docker build -f Dockerfile.dev -t workflow-engine:dev .

# 运行容器
docker run -p 8002:8002 -v $(pwd):/app workflow-engine:dev
```

### Docker Compose

```bash
# 启动服务
docker-compose up workflow-engine

# 查看日志
docker-compose logs -f workflow-engine
```

## 工作流节点类型

支持以下节点类型：

- `start` - 开始节点
- `end` - 结束节点
- `llm` - 大语言模型节点
- `tool` - 工具调用节点
- `condition` - 条件判断节点
- `transform` - 数据转换节点
- `parallel` - 并行执行节点
- `custom` - 自定义节点

## 工作流执行流程

1. **工作流定义**: 通过设计器或API创建工作流定义
2. **工作流保存**: 保存工作流到数据库
3. **工作流执行**: 通过API触发工作流执行
4. **状态跟踪**: 实时跟踪执行状态和节点结果
5. **结果返回**: 返回执行结果和元数据

## 数据库集成

服务使用 `database` 模块进行数据持久化：

- **WorkflowDefinition**: 工作流定义
- **WorkflowNode**: 工作流节点
- **WorkflowConnection**: 节点连接
- **WorkflowExecution**: 工作流执行历史

## AI模型支持

### OpenAI

```bash
OPENAI_API_KEY=your_openai_api_key
LLM_MODEL=gpt-4
```

### DeepSeek

```bash
OPENAI_API_KEY=your_deepseek_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

## 监控和日志

- 所有API请求都会记录日志
- 工作流执行统计存储在数据库中
- 支持通过监控端点查询性能指标

## 依赖

主要依赖项：
- `fastapi>=0.104.1` - Web框架
- `uvicorn[standard]>=0.24.0` - ASGI服务器
- `pydantic>=2.5.0` - 数据验证
- `langchain==0.1.0` - LangChain框架
- `langgraph==0.0.20` - LangGraph工作流引擎
- `langchain-openai==0.0.2` - OpenAI集成
- `redis>=5.0.1` - Redis客户端

## 端口说明

⚠️ **注意**: 默认使用端口 **8002**。确保该端口未被其他服务占用。

## 相关文档

- [项目主文档](../../README.md)
- [数据库模块文档](../database/README.md)
- [MCP Gateway文档](../mcp-gateway/README.md)
- [API文档](../../docs/api-docs/README.md)
- [DeepSeek设置指南](../../docs/development-docs/DEEPSEEK_SETUP.md)

