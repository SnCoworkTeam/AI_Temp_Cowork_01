# Agent Service - 智能体核心服务

智能体核心服务，提供智能体的创建、管理、执行等功能，使用 DeepSeek 作为大语言模型。

## 🚀 功能特性

- ✅ 智能体 CRUD 操作
- ✅ 智能体执行引擎
- ✅ DeepSeek LLM 集成
- ✅ 执行历史管理
- ✅ 模型管理接口
- ✅ 默认智能体（数据分析、文档处理、工作流编排）

## 📋 API 端点

### 智能体管理

- `POST /api/v1/agents` - 创建智能体
- `GET /api/v1/agents` - 获取智能体列表
- `GET /api/v1/agents/{agent_id}` - 获取智能体详情
- `PUT /api/v1/agents/{agent_id}` - 更新智能体
- `DELETE /api/v1/agents/{agent_id}` - 删除智能体
- `POST /api/v1/agents/{agent_id}/execute` - 执行智能体

### 执行管理

- `POST /api/v1/executions` - 创建执行任务
- `GET /api/v1/executions/{execution_id}` - 获取执行详情
- `GET /api/v1/executions` - 获取执行列表

### 模型管理

- `GET /api/v1/models` - 获取可用模型列表
- `POST /api/v1/models/{model_id}/chat` - 模型对话

### 健康检查

- `GET /api/v1/health` - 健康检查

## 🔧 环境变量

```bash
# 服务配置
HOST=0.0.0.0
PORT=8010
DEBUG=true
LOG_LEVEL=info

# DeepSeek LLM 配置
OPENAI_API_KEY=your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# 服务依赖
MCP_GATEWAY_URL=http://mcp-gateway:8001
WORKFLOW_ENGINE_URL=http://workflow-engine:8002
DAG_ORCHESTRATOR_URL=http://dag-orchestrator:8009
KNOWLEDGE_BASE_URL=http://knowledge-base:8004
```

## 🏗️ 项目结构

```
agent-service/
├── src/
│   ├── main.py              # 主应用入口
│   ├── routes/              # API 路由
│   │   ├── agents.py        # 智能体管理路由
│   │   ├── executions.py    # 执行管理路由
│   │   ├── models.py        # 模型管理路由
│   │   └── health.py        # 健康检查路由
│   ├── core/                # 核心逻辑
│   │   ├── agent_manager.py # 智能体管理器
│   │   └── llm_integration.py # DeepSeek LLM 集成
│   └── models/              # 数据模型
│       ├── agent_models.py  # 智能体模型
│       └── execution_models.py # 执行模型
├── requirements.txt         # Python 依赖
├── Dockerfile.dev          # 开发环境 Dockerfile
└── README.md               # 本文档
```

## 🚀 快速开始

### 使用 Docker Compose

```bash
# 启动服务
docker compose up agent-service

# 查看日志
docker compose logs -f agent-service

# 重启服务
docker compose restart agent-service
```

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export OPENAI_API_KEY=your-key
export LLM_BASE_URL=https://api.deepseek.com
export LLM_MODEL=deepseek-chat

# 启动服务
uvicorn src.main:app --host 0.0.0.0 --port 8010 --reload
```

## 📝 使用示例

### 创建智能体

```bash
curl -X POST http://localhost:8010/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "数据分析智能体",
    "description": "专门用于数据分析",
    "capabilities": ["data_analysis"],
    "system_prompt": "你是一个专业的数据分析专家"
  }'
```

### 执行智能体

```bash
curl -X POST http://localhost:8010/api/v1/agents/{agent_id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "分析销售数据并生成报告",
    "context": {"data_source": "sales.csv"},
    "parameters": {"temperature": 0.7}
  }'
```

## 🔗 相关服务

- **API Gateway**: `/api/agents/*` → `agent-service:8010`
- **Agent Orchestrator**: 智能体编排服务（待实现）
- **Agent Registry**: 智能体注册中心（待实现）

## 📚 技术栈

- **FastAPI**: Web 框架
- **LangChain**: LLM 集成
- **DeepSeek**: 大语言模型
- **Pydantic**: 数据验证
- **Uvicorn**: ASGI 服务器

## 🎯 后续计划

- [ ] 数据库持久化（当前使用内存存储）
- [ ] 流式响应支持
- [ ] 智能体能力扩展
- [ ] 与 MCP Gateway 集成
- [ ] 与 Workflow Engine 集成
- [ ] 与 DAG Orchestrator 集成

