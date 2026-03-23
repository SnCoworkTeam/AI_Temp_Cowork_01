# 中化国际AIOS平台

基于业务流程自动化的中化国际AIOS平台，提供MCP工具网关、工作流引擎、智能体服务和现代化Web界面。

## ✨ 核心特性

- 🤖 **智能体服务**: 完整的智能体管理系统，支持对话理解、任务分类、智能路由和流式执行
  - **动态工作流**: 基于LLM的智能工作流设计，自动分析任务并生成最优执行网络
  - **多智能体协作**: 支持多个智能体协同工作，自动编排执行顺序
  - **流式执行**: 实时返回执行过程和结果，支持SSE流式响应
- 🔀 **智能路由**: 基于内容的自动路由，自动识别用户意图并路由到最佳服务
- 📡 **流式能力**: 完整的Server-Sent Events (SSE)支持，实时返回执行过程和结果
- 🔧 **MCP工具网关**: 统一的工具调用接口，支持多种MCP工具
  - **参数智能映射**: 自动将常见参数名映射到工具所需参数（如邮件发送、SAP查询等）
  - **工具发现**: 动态发现和注册MCP工具
- 📊 **工作流引擎**: 基于LangGraph的工作流编排和执行
- 📚 **知识库服务**: 文档管理、语义搜索和知识图谱
- 📋 **元数据管理**: 完整的企业元数据管理，支持数据资产、AI模型、业务实体和工作流元数据
- 🏢 **SAP集成**: SAP ERP深度集成
  - **SAP OData MCP Server**: 将SAP OData服务转换为MCP工具
  - **SAP元数据自动发现**: 自动发现和构建SAP ERP元数据（48,000+数据资产）
  - **SAP数据查询智能体**: 智能查询SAP数据，支持服务发现、实体发现和数据操作
- 🔐 **统一认证**: JWT认证和SSO单点登录
- 🌐 **微服务架构**: 完整的服务注册、发现、网关和配置管理

## 🏗️ 项目架构

本项目采用完整的微服务架构，包含以下核心服务：

### 核心架构层
- **registry-service**: 服务注册与发现中心（FastAPI，端口: 8000）
- **api-gateway**: 统一API网关（FastAPI，端口: 8080）
- **config-center**: 配置管理中心（FastAPI，端口: 8090）

### 业务服务层
- **sap-mcp-server**: SAP OData to MCP 服务（Node.js，端口: 3001）- 将SAP OData服务转换为MCP工具
- **mcp-gateway**: MCP工具网关服务（FastAPI，端口: 8001）
- **workflow-engine**: 工作流引擎服务（LangGraph + LangChain，端口: 8002）
- **auth-service**: 认证和授权服务（FastAPI，端口: 8003）
- **knowledge-base**: 知识库服务（FastAPI，端口: 8004）
- **metadata-service**: 元数据管理服务（FastAPI，端口: 8005）- 数据资产、AI模型、业务实体、工作流元数据管理
- **sap-metadata-agent**: SAP元数据代理服务（FastAPI，端口: 8015）- 自动发现和构建SAP ERP元数据 ⭐NEW
- **chat-service**: AI对话服务（FastAPI，端口: 8006）
- **joyagent-adapter**: JoyAgent适配器服务（端口: 8007）- 集成JoyAgent能力
- **dag-orchestrator**: 智能任务分解与编排服务（FastAPI，端口: 8009）
- **agent-service**: 智能体核心服务（FastAPI，端口: 8010）
- **agent-orchestrator**: 智能体编排服务（FastAPI，端口: 8011）
- **agent-registry**: 智能体注册中心（FastAPI，端口: 8012）
- **memory-service**: 记忆服务（FastAPI，端口: 8013）- 智能体长期记忆管理

### 基础设施层
- **postgres**: PostgreSQL数据库（端口: 5432）
- **redis**: Redis缓存服务（端口: 6379）
- **redis-commander**: Redis管理界面（端口: 8081）
- **qdrant**: 向量数据库（端口: 6333/6334）- 用于知识库和记忆服务的向量存储

### 前端与工具
- **web-ui**: 前端界面（Next.js + TypeScript，端口: 3000）
- **shared-libs**: 共享库（通用工具和数据模型）
- **database**: 共享数据库模块（SQLAlchemy模型和迁移）

### 架构特性
✅ **服务发现**: 动态服务注册与发现，消除硬编码URL
✅ **统一网关**: 单一入口点，统一路由和认证
✅ **智能路由**: 基于内容自动路由到最佳服务（LLM+规则混合）⭐NEW
✅ **流式能力**: 完整的Server-Sent Events (SSE)流式响应支持⭐NEW
✅ **配置管理**: 集中式配置，支持多环境和版本控制
✅ **服务治理**: 限流、熔断、负载均衡、请求重试
✅ **可观测性**: Prometheus指标、健康检查、监控中间件

## 📋 技术栈

### 后端
- **Python 3.11+**: 主要后端语言
- **Node.js 20+**: SAP MCP Server使用
- **FastAPI**: 高性能异步Web框架
- **LangGraph**: 工作流编排框架
- **LangChain**: AI应用开发框架
- **Pydantic v2**: 数据验证和设置管理
- **SQLAlchemy 2.0**: ORM框架
- **Alembic**: 数据库迁移工具
- **Redis 7**: 缓存和会话存储
- **PostgreSQL 15**: 业务数据存储
- **Qdrant**: 向量数据库（用于知识库和记忆服务）

### 前端
- **Next.js 14**: React框架（App Router）
- **TypeScript 5+**: 类型安全的JavaScript
- **TailwindCSS 3+**: 实用优先的CSS框架
- **React 18**: UI组件库

### AI/ML
- **OpenAI API**: 支持OpenAI兼容的API（包括DeepSeek）
- **LangChain**: AI应用开发框架
- **Sentence Transformers**: 文本嵌入模型
- **ChromaDB**: 向量存储（可选，知识库使用）

### 部署
- **Docker**: 容器化
- **Docker Compose**: 开发环境编排
- **热重载**: 开发模式支持代码热重载

## 📊 服务状态

### 当前运行的服务（共22个）

**基础设施层（4个）**:
- ✅ postgres (5432) - PostgreSQL数据库
- ✅ redis (6379) - Redis缓存
- ✅ redis-commander (8081) - Redis管理界面
- ✅ qdrant (6333/6334) - 向量数据库

**核心架构层（3个）**:
- ✅ registry-service (8000) - 服务注册与发现中心
- ✅ api-gateway (8080) - 统一API网关
- ✅ config-center (8090) - 配置管理中心

**业务服务层（14个）**:
- ✅ sap-mcp-server (3001) - SAP OData to MCP服务
- ✅ mcp-gateway (8001) - MCP工具网关
- ✅ workflow-engine (8002) - 工作流引擎
- ✅ auth-service (8003) - 认证服务
- ✅ knowledge-base (8004) - 知识库服务
- ✅ metadata-service (8005) - 元数据服务
- ✅ sap-metadata-agent (8015) - SAP元数据代理服务 ⭐NEW
- ✅ chat-service (8006) - 聊天服务
- ✅ joyagent-adapter (8007) - JoyAgent适配器
- ✅ dag-orchestrator (8009) - DAG编排服务
- ✅ agent-service (8010) - 智能体核心服务
- ✅ agent-orchestrator (8011) - 智能体编排服务
- ✅ agent-registry (8012) - 智能体注册中心
- ✅ memory-service (8013) - 记忆服务

**前端层（1个）**:
- ✅ web-ui (3000) - Next.js前端界面

**开发模式特性**:
- ✅ 热重载：所有服务支持代码热重载，修改后自动同步
- ✅ Volume挂载：源代码实时同步到容器
- ✅ 健康检查：所有服务配置了健康检查机制

## 🚀 快速开始

### 前置要求

- Docker 和 Docker Compose
- Python 3.11+（本地开发）
- Node.js 20+（本地开发）

### 使用Docker Compose启动（推荐）

```bash
# 1. 复制环境变量文件
cp .env.example .env

# 2. 编辑 .env 文件，填入必要的配置（如OPENAI_API_KEY或DeepSeek API Key）
#    支持 OpenAI 或 DeepSeek API（DeepSeek完全兼容OpenAI API格式）
#    使用 DeepSeek: 设置 OPENAI_API_KEY 为 DeepSeek API Key，LLM_BASE_URL=https://api.deepseek.com

# 3. 启动所有服务（开发模式，支持热重载）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f mcp-gateway

# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

**开发模式特性：**
- ✅ 热重载：代码修改自动重启
- ✅ Volume挂载：源代码实时同步
- ✅ 调试工具：包含ipython、ipdb、vim等
- ✅ 快速迭代：无需重建镜像

**生产环境：**
```bash
# 使用生产配置
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 本地开发

#### 1. 启动基础设施

```bash
# 启动Redis和PostgreSQL
docker-compose up -d redis postgres
```

#### 2. 启动MCP Gateway

```bash
cd mcp-gateway
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m src.main
```

服务将在 `http://localhost:8001` 启动

#### 3. 启动Workflow Engine

```bash
cd workflow-engine
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m src.main
```

服务将在 `http://localhost:8002` 启动

#### 4. 启动Web UI

```bash
cd web-ui
npm install
npm run dev
```

服务将在 `http://localhost:3000` 启动

## 📡 API端点

### 架构服务

#### API Gateway (统一入口)
- **根路径**: `http://localhost:8080/`
- **健康检查**: `GET http://localhost:8080/health`
- **指标收集**: `GET http://localhost:8080/metrics` (Prometheus格式)

所有业务API通过网关访问：
- `/api/workflows/*` → Workflow Engine
- `/api/mcp/*` → MCP Gateway
- `/api/auth/*` → Auth Service
- `/api/knowledge/*` → Knowledge Base
- `/api/metadata/*` → Metadata Service
- `/api/sap-metadata/*` → SAP Metadata Agent（SAP元数据发现和构建）⭐NEW
- `/api/chat/*` → Chat Service
- `/api/chat/intelligent` → 智能路由对话（自动路由到最佳服务）⭐NEW
- `/api/chat/intelligent/stream` → 流式智能对话（实时返回执行过程）⭐NEW
- `/api/agents/*` → Agent Service（智能体管理）⭐NEW
- `/api/dag/*` → DAG Orchestrator
- `/api/joyagent/*` → JoyAgent Adapter
- `/api/registry/*` → Registry Service

#### Registry Service (服务注册中心)
- `POST /api/register` - 注册服务
- `DELETE /api/unregister/{service_id}` - 注销服务
- `POST /api/heartbeat/{service_id}` - 发送心跳
- `GET /api/discover/{service_name}` - 服务发现
- `GET /api/services` - 列出所有服务

#### Config Center (配置管理)
- `GET /api/config/{key}` - 获取配置
- `POST /api/config` - 创建/更新配置
- `DELETE /api/config/{key}` - 删除配置
- `GET /api/configs` - 列出所有配置
- `GET /api/configs/all` - 获取扁平化配置

### 业务服务（通过API Gateway访问）

#### MCP Gateway API
- `GET /api/tools` - 获取可用工具列表
- `POST /api/tools/execute` - 执行工具
- `GET /api/tools/{tool_name}` - 获取工具详情

#### Workflow Engine API
- `GET /api/workflows` - 获取工作流列表
- `POST /api/workflows/execute` - 执行工作流
- `GET /api/workflows/{workflow_name}` - 获取工作流详情
- `GET /api/workflows/executions/{execution_id}` - 获取执行状态
- `POST /api/workflows/{workflow_id}/start` - 启动工作流
- `POST /api/workflows/advance` - 推进工作流到下一个节点

#### Agent Service API（智能体核心服务）
- `GET /api/v1/agents` - 获取智能体列表
- `POST /api/v1/agents` - 创建智能体
- `GET /api/v1/agents/{agent_id}` - 获取智能体详情
- `PUT /api/v1/agents/{agent_id}` - 更新智能体
- `DELETE /api/v1/agents/{agent_id}` - 删除智能体
- `POST /api/v1/agents/{agent_id}/execute` - 执行智能体
- `POST /api/v1/agents/{agent_id}/execute/stream` - 流式执行智能体
- `GET /api/v1/agents/{agent_id}/executions` - 获取执行历史
- `POST /api/v1/chat` - 智能对话（非流式）
- `POST /api/v1/chat/stream` - 流式智能对话（实时返回执行过程）
- `POST /api/dynamic-workflow/execute` - 执行动态工作流（流式）⭐NEW
- `POST /api/agent/continue` - 继续工作流执行

**智能对话功能**:
- ✅ **对话理解**: 自动分析用户意图和上下文，支持LLM和规则两种模式
- ✅ **任务分类**: 智能识别任务类型（简单对话、工具执行、工作流、DAG编排、知识搜索、多智能体协调）
- ✅ **智能路由**: 自动路由到最佳服务执行（chat-service、agent-service、workflow-engine、dag-orchestrator、knowledge-base）
- ✅ **流式响应**: 实时返回执行过程和结果（Server-Sent Events）
- ✅ **状态管理**: 完整的执行状态跟踪和记录
- ✅ **服务集成**: 统一调用MCP工具、工作流、知识库、DAG编排等服务

**动态工作流功能** ⭐NEW:
- ✅ **智能工作流设计**: 基于LLM自动分析任务并设计最优执行网络
- ✅ **多智能体编排**: 自动识别需要的智能体并编排执行顺序
- ✅ **执行层管理**: 智能识别依赖关系，按层执行智能体
- ✅ **实时进度反馈**: 流式返回设计过程、执行进度和最终结果
- ✅ **结果合成**: 自动聚合所有智能体的执行结果
- ✅ **错误处理**: 智能错误处理和降级策略

**智能路由端点**（通过API Gateway）:
- `POST /api/chat/intelligent` - 智能路由对话（非流式）
- `POST /api/chat/intelligent/stream` - 流式智能路由对话（实时返回执行过程）

#### DAG Orchestrator API（智能任务分解与编排）
- `POST /api/v1/tasks/execute` - 执行复杂任务（自动分解并执行）
- `POST /api/v1/tasks/decompose` - 仅分解任务（不执行）
- `GET /api/v1/executions/{execution_id}` - 获取执行状态
- `GET /api/v1/executions/{execution_id}/status` - 获取执行状态详情
- `POST /api/v1/executions/{execution_id}/cancel` - 取消执行
- `GET /api/v1/health` - 健康检查

**功能特性**:
- 智能任务分解：使用LLM将自然语言任务分解为可执行的DAG计划
- 多服务编排：协调MCP工具、工作流引擎、知识库等微服务协同工作
- 并行执行：支持无依赖任务的并行执行
- 状态管理：完整的执行状态跟踪和监控

#### Metadata Service API
- `GET /api/data-assets` - 列出数据资产（支持分页、搜索、分类过滤）
- `POST /api/data-assets` - 创建数据资产
- `GET /api/data-assets/{id}` - 获取数据资产详情
- `GET /api/workflows` - 列出工作流元数据
- `GET /api/ai-models` - 列出AI模型元数据
- `GET /api/business-entities` - 列出业务实体元数据
- `GET /api/search` - 全局元数据搜索
- `GET /api/lineage` - 数据血缘查询

#### SAP Metadata Agent API ⭐NEW
- `POST /api/sap-metadata/discover` - 发现和构建SAP元数据
- `GET /api/sap-metadata/assets` - 获取发现的SAP数据资产
- `GET /api/sap-metadata/entities` - 获取提取的业务实体
- `GET /api/sap-metadata/processes` - 获取业务流程信息
- `GET /api/sap-metadata/build-status` - 获取构建状态和进度

**功能特性**:
- OData服务发现：自动从SAP OData服务发现所有实体和接口
- 数据库表发现：直接从SAP HANA/SQL Server数据库发现表结构
- 业务实体提取：自动识别客户、供应商、物料等业务实体
- 业务流程分析：分析业务过程和数据血缘关系
- 语义索引构建：为元数据构建语义搜索索引
- 批量处理：支持大规模元数据的分批构建

#### JoyAgent Adapter API
- `POST /api/joyagent/tasks` - 创建JoyAgent任务
- `GET /api/joyagent/tasks/{task_id}` - 获取任务状态
- `GET /api/joyagent/tasks` - 获取任务列表（支持分页）
- `DELETE /api/joyagent/tasks/{task_id}` - 取消任务
- `GET /api/joyagent/status` - 获取服务状态和能力
- `GET /api/joyagent/health` - 健康检查
- `POST /api/joyagent/integrations/workflow` - 工作流集成
- `POST /api/joyagent/integrations/knowledge` - 知识增强集成
- `POST /api/joyagent/integrations/mcp` - MCP工具集成

## 🔧 配置

### 环境变量

创建 `.env` 文件（各服务目录下）：

```bash
# MCP Gateway
HOST=0.0.0.0
PORT=8001
DEBUG=true
REDIS_HOST=localhost
REDIS_PORT=6379
WORKFLOW_ENGINE_URL=http://localhost:8002

# Workflow Engine
HOST=0.0.0.0
PORT=8002
DEBUG=true
OPENAI_API_KEY=your_openai_api_key
# 使用 DeepSeek API 时设置:
# LLM_BASE_URL=https://api.deepseek.com
# LLM_MODEL=deepseek-chat
LANGCHAIN_API_KEY=your_langchain_api_key
REDIS_HOST=localhost
REDIS_PORT=6379
MCP_GATEWAY_URL=http://localhost:8001

# DAG Orchestrator
HOST=0.0.0.0
PORT=8009
DEBUG=true
MCP_GATEWAY_URL=http://localhost:8001
WORKFLOW_ENGINE_URL=http://localhost:8002
KNOWLEDGE_BASE_URL=http://localhost:8004
CHAT_SERVICE_URL=http://localhost:8006
OPENAI_API_KEY=your_openai_api_key
LLM_BASE_URL=https://api.deepseek.com  # 可选，使用DeepSeek时设置
LLM_MODEL=deepseek-chat

# Web UI
NEXT_PUBLIC_MCP_GATEWAY_URL=http://localhost:8001
NEXT_PUBLIC_WORKFLOW_ENGINE_URL=http://localhost:8002
NEXT_PUBLIC_DAG_ORCHESTRATOR_URL=http://localhost:8009
```

## 📁 项目结构

```
enterprise-ai-platform/
├── registry-service/     # 服务注册与发现中心 ⭐NEW
│   ├── src/
│   │   ├── main.py       # FastAPI主应用
│   │   ├── routes/       # API路由
│   │   ├── services/     # 注册服务逻辑
│   │   └── models/       # 数据模型
│   ├── requirements.txt
│   └── Dockerfile
│
├── api-gateway/          # 统一API网关 ⭐NEW
│   ├── src/
│   │   ├── main.py       # FastAPI主应用
│   │   ├── core/         # 核心功能（服务发现、代理）
│   │   ├── middleware/   # 中间件（限流、监控）
│   │   └── config.py     # 配置
│   ├── requirements.txt
│   └── Dockerfile
│
├── config-center/        # 配置管理中心 ⭐NEW
│   ├── src/
│   │   ├── main.py       # FastAPI主应用
│   │   ├── core/         # 配置服务
│   │   └── models/       # 配置模型
│   ├── requirements.txt
│   └── Dockerfile
│
├── mcp-gateway/          # MCP工具网关服务
│   ├── src/
│   │   ├── main.py       # FastAPI主应用
│   │   ├── routes/       # API路由
│   │   ├── core/         # 核心功能
│   │   └── models/       # Pydantic模型
│   ├── tests/           # 测试文件
│   ├── requirements.txt # Python依赖
│   └── Dockerfile       # 容器配置
│
├── workflow-engine/      # 工作流引擎服务
│   ├── src/
│   │   ├── main.py       # LangGraph主应用
│   │   ├── workflows/    # 业务流程定义
│   │   ├── nodes/         # 工作流节点
│   │   └── core/         # 核心引擎
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── auth-service/         # 认证和授权服务
│   ├── src/
│   │   ├── main.py       # FastAPI主应用
│   │   ├── routes/       # API路由
│   │   ├── services/     # 业务服务
│   │   └── sso/          # SSO集成
│   ├── tests/
│   └── requirements.txt
│
├── knowledge-base/       # 知识库服务
│   ├── src/
│   │   ├── main.py       # FastAPI主应用
│   │   ├── services/     # 知识库服务
│   │   └── models/       # 数据模型
│   ├── tests/
│   └── requirements.txt
│
├── metadata-service/       # 元数据管理服务
│   ├── src/
│   │   ├── main.py       # FastAPI主应用
│   │   ├── services/     # 元数据目录服务
│   │   ├── api/          # API路由
│   │   └── models/       # 数据模型
│   ├── tests/
│   └── requirements.txt
│
├── sap-metadata-agent/     # SAP元数据代理服务 ⭐NEW
│   ├── src/
│   │   ├── main.py       # FastAPI主应用
│   │   ├── core/         # 核心功能（元数据编排、发现、提取）
│   │   ├── services/     # 服务层（数据库客户端、MCP客户端）
│   │   └── routes/       # API路由
│   ├── tests/
│   └── requirements.txt
│
├── chat-service/         # AI对话服务
│   ├── src/
│   │   ├── main.py       # FastAPI主应用
│   │   ├── services/     # 对话服务
│   │   └── models/       # 数据模型
│   ├── tests/
│   └── requirements.txt
│
├── agent-service/        # 智能体核心服务 ⭐NEW
│   ├── src/
│   │   ├── main.py       # FastAPI主应用
│   │   ├── routes/       # API路由（agents, chat, stream_executions）
│   │   ├── core/         # 核心功能
│   │   │   ├── conversation_agent.py  # 对话理解
│   │   │   ├── task_classifier.py     # 任务分类
│   │   │   ├── service_integration.py # 服务集成
│   │   │   ├── stream_executor.py     # 流式执行
│   │   │   ├── agent_manager.py       # 智能体管理
│   │   │   └── state_manager.py       # 状态管理
│   │   └── services/     # 服务客户端（MCP, Workflow, Knowledge, DAG）
│   ├── tests/
│   └── requirements.txt
│
├── agent-orchestrator/   # 智能体编排服务 ⭐NEW
│   ├── src/
│   │   ├── main.py       # FastAPI主应用
│   │   ├── routes/       # API路由
│   │   ├── core/         # 核心引擎（编排器、结果聚合器）
│   │   └── models/       # 数据模型
│   ├── tests/
│   └── requirements.txt
│
├── dag-orchestrator/     # 智能任务分解与编排服务
│   ├── src/
│   │   ├── main.py       # FastAPI主应用
│   │   ├── routes/       # API路由
│   │   ├── core/         # 核心引擎（DAG引擎、任务分解器）
│   │   ├── services/     # 服务集成（LLM、后端客户端）
│   │   └── models/       # 数据模型
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── web-ui/              # 前端界面
│   ├── src/
│   │   ├── app/         # Next.js App Router
│   │   │   ├── agents/  # 智能体管理页面
│   │   │   ├── chat/    # AI助手聊天页面
│   │   │   ├── workflows/ # 工作流页面
│   │   │   └── knowledge-bases/ # 知识库页面
│   │   ├── components/  # React组件
│   │   │   ├── AgentWorkflowInterface/ # 智能体工作流界面组件
│   │   │   ├── Layout/  # 布局组件（导航栏、侧边栏）
│   │   │   └── ...      # 其他组件
│   │   ├── types/       # TypeScript类型定义
│   │   │   └── agent-protocol.ts # 前端与智能体交互协议类型
│   │   └── lib/         # 工具函数
│   ├── package.json
│   └── Dockerfile
│
├── shared-libs/         # 共享库（Python）
│   ├── common/          # 共享工具函数
│   └── schemas/         # 共享数据模型
│
├── database/            # 数据库模块（共享）
│   ├── src/
│   │   ├── models/      # SQLAlchemy模型
│   │   ├── repositories/# 数据访问层
│   │   └── migrations/  # Alembic迁移
│   └── requirements.txt
│
├── src/                 # 项目级模块
│   └── auto_debug/      # 自动化调试系统
│       ├── platform_error_analyzer.py
│       ├── platform_fix_strategies.py
│       ├── debug_orchestrator.py
│       ├── platform_test_validator.py
│       ├── platform_deployment.py
│       └── platform_monitor.py
│
├── config/              # 配置文件
│   ├── platform_integration.yaml
│   ├── debug_workflows.yaml
│   └── decision_rules.yaml
│
├── docs/                # 项目文档
│   ├── api-docs/        # API文档
│   ├── architecture-docs/# 架构文档
│   └── development-docs/# 开发文档
│
├── scripts/             # 工具脚本
│   ├── architecture_guard.py
│   ├── backup/          # 备份恢复
│   ├── code-health/     # 代码健康度
│   └── release/         # 发布管理
│
├── tests/               # 项目级测试
├── docker-compose.yml   # 开发环境编排
├── docker-compose.prod.yml # 生产环境
├── ARCHITECTURE_IMPLEMENTATION.md # 架构实现详细文档 ⭐NEW
├── .project_constitution.md # 项目宪法
└── README.md
```

## 🤖 智能体功能

### 智能体管理

中化国际AIOS平台提供了完整的智能体管理系统，支持智能体的创建、管理和执行。

#### 前端功能

1. **智能体列表页面** (`/agents`)
   - 智能体列表展示
   - 搜索和筛选功能
   - 状态显示（运行中、已停用、错误、更新中）
   - 基本操作（执行、编辑、删除）

2. **智能体工作流界面组件** (`AgentWorkflowInterface`)
   - 整合智能体聊天和工作流可视化
   - 实时状态同步
   - 工作流进度可视化
   - 错误处理和恢复

3. **导航栏集成**
   - 顶部导航栏：AI助手 | 智能体 | 工作流 | 知识库
   - 侧边栏：智能体菜单项

#### 前端与智能体交互协议

项目实现了完整的前端与智能体工作流交互协议（任务4.1）：

- **WebSocket实时通信**：支持双向消息传递
- **TypeScript类型定义**：完整的类型安全（`web-ui/src/types/agent-protocol.ts`）
- **消息格式规范**：标准化的消息结构和类型
- **状态同步机制**：前后端状态实时同步
- **错误处理体系**：完整的错误码和恢复策略

详细文档：
- [前端交互协议设计](docs/frontend-agent-protocol.md)
- [API使用指南](docs/frontend-api-usage-guide.md)
- [组件使用文档](web-ui/src/components/AgentWorkflowInterface/README.md)

#### 组件架构

```
AgentWorkflowInterface/
├── AgentWorkflowInterface.tsx  # 主组件（整合聊天和工作流）
├── WorkflowVisualizer.tsx      # 工作流可视化组件
├── AgentChat.tsx               # 智能体聊天组件
└── index.ts                    # 导出文件
```

#### 使用示例

```tsx
import { AgentWorkflowInterface } from '@/components/AgentWorkflowInterface'

function MyPage() {
  return (
    <AgentWorkflowInterface
      workflowId="workflow-123"
      agentId="agent-456"
      initialInput="请帮我分析这个文档"
      autoStart={true}
      onError={(error) => console.error('Error:', error)}
      onWorkflowComplete={(result) => console.log('Complete:', result)}
    />
  )
}
```

## 🔐 认证功能

### 支持的登录方式

1. **用户名密码登录**
   - 用户注册：`POST /api/auth/register`
   - 用户登录：`POST /api/auth/login`
   - 支持用户名或邮箱登录
   - 密码强度验证
   - 自动令牌刷新

2. **SSO单点登录**
   - OAuth 2.0/OpenID Connect集成
   - 支持企业SSO提供者
   - 自动令牌管理

### 认证API端点

- `POST /api/auth/register` - 用户注册（用户名、邮箱、密码）
- `POST /api/auth/login` - 用户名密码登录
- `POST /api/auth/refresh` - 刷新访问令牌
- `POST /api/auth/logout` - 登出
- `POST /api/auth/change-password` - 修改密码
- `GET /api/auth/sso/login` - 发起SSO登录
- `GET /api/auth/sso/callback` - SSO回调处理

详细API文档请参考：`docs/api-docs/API_REFERENCE.md`

## 🧪 测试

### 测试覆盖

项目已实现全面的测试覆盖，当前覆盖率 **65%+**，目标覆盖率达到 **80%+**：

- **单元测试**：所有服务的主要功能
- **集成测试**：API集成、数据库集成、完整流程测试
- **性能测试**：API性能、数据库性能测试
- **安全测试**：认证、授权、输入验证测试
- **Mock测试**：外部依赖使用mock测试

### 覆盖率现状

| 服务 | 当前覆盖率 | 目标覆盖率 | 状态 |
|------|----------|----------|------|
| auth-service | ~70% | 80% | 🟡 进行中 |
| metadata-service | ~60% | 80% | 🟡 进行中 |
| workflow-engine | ~55% | 80% | 🟡 进行中 |
| database | ~65% | 80% | 🟡 进行中 |
| mcp-gateway | ~50% | 80% | 🟡 待提升 |
| knowledge-base | ~50% | 80% | 🟡 待提升 |

**改进计划**: 优先提升 mcp-gateway 和 knowledge-base 的覆盖率，目标在下一季度达到80%+

### Python服务测试

```bash
# 运行所有测试
cd tests
bash run-all-tests.sh all

# 运行特定服务测试
cd metadata-service
pytest tests/

# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

### 测试覆盖率检查

```bash
# 检查测试覆盖率
bash tests/check-test-coverage.sh

# 在服务器上运行测试
bash tests/run-all-tests-server.sh
```

### 测试-修复循环

使用自动化脚本进行测试-修复-上传循环：

```powershell
# Windows PowerShell
.\scripts\deployment\test-and-fix.ps1
```

### 前端测试

```bash
cd web-ui
npm test
```

## 📝 开发规范

### 代码质量要求

- 所有API必须包含完整的OpenAPI文档
- 关键业务逻辑必须有单元测试（覆盖率>=80%）
- 使用Pydantic进行数据验证
- 统一的错误处理中间件
- 生产环境不泄露敏感信息（数据库凭证、SQL语句等）
- 使用类型提示提高代码可读性

### 代码质量工具

**Python**:
- `black` - 代码格式化
- `flake8` - 代码风格检查
- `mypy` - 类型检查
- `pylint` - 代码质量分析

**TypeScript**:
- `eslint` - 代码检查
- `prettier` - 代码格式化
- `typescript` - 类型检查

**建议**: 配置 pre-commit hooks 自动运行代码质量检查

### 日志格式

所有服务使用统一的日志格式：

```
YYYY-MM-DD HH:MM:SS - logger_name - LEVEL - message
```

### 错误处理

使用统一的错误响应格式：

```json
{
  "success": false,
  "error": {
    "message": "错误消息",
    "status_code": 500,
    "request_id": "uuid-request-id",
    "details": "错误详情（仅开发环境）"
  }
}
```

**安全要求**:
- 生产环境不返回敏感错误信息（数据库凭证、SQL语句、系统架构）
- 所有错误必须有唯一请求ID用于追踪
- 错误详情记录到日志但不返回给客户端

## 🔐 安全

### 安全要求

- ✅ 使用环境变量管理敏感信息
- ✅ 生产环境错误响应不泄露敏感信息
- ✅ 所有错误都有唯一请求ID用于追踪
- ⚠️ 所有API端点应包含适当的身份验证（部分实现）
- ⚠️ 使用HTTPS在生产环境中（待实现）

### 安全最佳实践

- 定期进行依赖安全扫描（`pip-audit`, `npm audit`）
- 使用强密码策略和bcrypt加密
- 实现速率限制防止暴力攻击
- 配置CORS策略限制跨域访问
- 输入验证和清理防止注入攻击

## 📚 文档

### API文档

- **Swagger UI**:
  - API Gateway: `http://localhost:8000/docs` ⭐NEW - 统一搜索、知识图谱搜索、自然语言查询
  - MCP Gateway: `http://localhost:8001/api/docs`
  - Workflow Engine: `http://localhost:8002/api/docs`
  - Auth Service: `http://localhost:8003/api/docs`
  - Knowledge Base: `http://localhost:8004/docs` ⭐UPDATED
  - Metadata Service: `http://localhost:8005/docs` ⭐UPDATED - 知识图谱、本体、智能推荐
  - Vector Coordinator: `http://localhost:8020/docs` ⭐NEW - 向量协调服务
  - SAP Metadata Agent: `http://localhost:8015/api/docs`
  - Chat Service: `http://localhost:8006/api/docs`
  - DAG Orchestrator: `http://localhost:8009/api/v1/docs`

### 项目文档

- **项目宪法**: [.project_constitution.md](.project_constitution.md) - 项目核心规范和原则
- **架构文档**: [docs/architecture-docs/](docs/architecture-docs/) - 系统架构和设计决策
- **开发文档**: [docs/development-docs/](docs/development-docs/) - 开发指南和最佳实践
- **自动化调试系统**: [docs/development-docs/auto-debug-system.md](docs/development-docs/auto-debug-system.md) - 自动化调试系统完整文档

### 智能体相关文档

- **前端交互协议设计**: [docs/frontend-agent-protocol.md](docs/frontend-agent-protocol.md) - 前端与智能体工作流交互协议（任务4.1）
- **API使用指南**: [docs/frontend-api-usage-guide.md](docs/frontend-api-usage-guide.md) - 前端智能体交互协议API使用文档
- **组件使用文档**: [web-ui/src/components/AgentWorkflowInterface/README.md](web-ui/src/components/AgentWorkflowInterface/README.md) - AgentWorkflowInterface组件使用说明（任务4.2）

### 阶段1-4实施文档

- [阶段1-4最终总结](../STAGES_1-4_FINAL_SUMMARY.md) - 阶段1-4完整实施总结
- [SAP MM知识库访问指南](../SAP_MM_KNOWLEDGE_BASE_ACCESS_GUIDE.md) - 知识库和元数据访问指南
- [阶段1实施报告](../STAGE1_COMPLETE_SUMMARY_FINAL.md) - 向量协调服务与统一搜索
- [阶段2实施报告](../STAGE2_FINAL_SUMMARY.md) - 业务本体功能迁移
- [阶段3实施报告](../STAGE3_TEST_COMPLETE_FINAL.md) - 统一实体标识与知识图谱
- [阶段4实施报告](../STAGE4_TEST_COMPLETE_FINAL.md) - 智能化提升

### 快速链接

- [快速开始指南](docs/development-docs/setup-guide/development-environment.md)
- [编码规范](docs/development-docs/coding-standards/)
- [测试指南](docs/development-docs/testing-guide/getting-started.md)
- [部署指南](docs/development-docs/deployment-guide/production-deployment.md)

## 🔍 架构守护

项目包含架构守护脚本，用于确保代码质量和不偏离设计理念。

### 使用架构守护

```bash
# 检查项目结构
python scripts/architecture_guard.py --check

# 验证特定文件的导入
python scripts/architecture_guard.py --validate-imports mcp-gateway/src/main.py

# 生成健康报告
python scripts/architecture_guard.py --report --output architecture_report.json

# 自动修复可修复的违规
python scripts/architecture_guard.py --auto-fix
```

### 安装预提交钩子

```bash
# 安装git预提交钩子
python scripts/pre-commit-hook.py --install
```

预提交钩子会在每次 `git commit` 时自动运行架构检查，确保代码符合规范。

详细说明请查看 `scripts/README.md`。

## 🤝 贡献

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

**注意**: 提交代码前请确保通过架构守护检查。

## 📝 变更日志

详细的变更记录请查看 [CHANGELOG.md](CHANGELOG.md) 或 [变更日志指南](docs/development-docs/CHANGELOG_GUIDE.md)。

### 最新更新

#### 阶段1-4架构优化完成 (2025-11) ⭐NEW
- ✅ **阶段1: 向量协调服务与统一搜索优化**: Qdrant集成、多级缓存、批量写入、性能提升44x
- ✅ **阶段2: 业务本体功能迁移**: 从knowledge-base迁移到metadata-service，服务边界清晰
- ✅ **阶段3: 统一实体标识与知识图谱增强**: EntityURI系统、混合关系发现、文档实体关联
- ✅ **阶段4: 智能化提升**: 智能推荐、决策支持、自然语言查询、知识图谱可视化
- ✅ **SAP MM知识库构建**: 2734个实体、712个知识图谱节点、84个关系、21个文档、447个chunks

#### 动态工作流和SAP集成增强 (2025-11)
- ✅ **动态工作流引擎**: 实现基于LLM的智能工作流设计，自动分析任务并生成最优执行网络
- ✅ **SAP数据查询智能体**: 实现SAP OData智能体，支持服务发现、实体发现和数据操作
- ✅ **参数智能映射**: MCP工具网关支持参数自动映射（如邮件发送、SAP查询等）
- ✅ **流式消息显示优化**: 修复流式响应后消息消失问题，确保最终结果正确显示
- ✅ **SAP OData MCP Server**: 完善SAP OData到MCP的转换，支持5个核心服务顺序执行

#### SAP元数据管理 (2025-11)
- ✅ **SAP元数据代理**: SAP Metadata Agent服务实现，自动发现和构建SAP ERP元数据
- ✅ **OData元数据发现**: 自动从SAP OData服务发现实体和接口元数据（已发现48,000+数据资产）
- ✅ **数据库表元数据**: 支持直接从SAP HANA/SQL Server数据库发现表结构
- ✅ **业务实体提取**: 自动识别业务实体（客户、供应商、物料等）
- ✅ **业务流程分析**: 分析业务过程和数据血缘关系
- ✅ **语义索引构建**: 为发现的元数据构建语义搜索索引
- ✅ **元数据同步**: 自动同步到元数据服务，支持大规模数据资产管理
- ✅ **元数据管理界面**: 完整的元数据管理页面，支持分页、搜索、分类筛选

#### 平台完善 (2025-11)
- ✅ **记忆服务**: Memory Service实现，支持智能体长期记忆管理
- ✅ **向量数据库**: Qdrant集成，用于知识库和记忆服务的向量存储
- ✅ **SAP集成**: SAP OData to MCP Server，将SAP系统集成到平台
- ✅ **智能体注册中心**: Agent Registry实现，智能体能力注册和发现
- ✅ **代码修复**: 修复了agent-service、chat-service、mcp-gateway的关键错误
- ✅ **热重载优化**: 所有服务支持开发模式热重载，提升开发效率
- ✅ **Docker网络优化**: 修复了容器间服务连接问题，优化了元数据服务访问

#### 微服务架构完善 (2025-01)
- ✅ **服务注册中心**: Registry Service实现，消除硬编码URL
- ✅ **统一API网关**: API Gateway实现，提供单一入口
- ✅ **配置管理中心**: Config Center实现，集中式配置管理
- ✅ **服务治理**: 限流、熔断、负载均衡、请求重试
- ✅ **可观测性**: Prometheus指标、健康检查、监控中间件

详细文档: [ARCHITECTURE_IMPLEMENTATION.md](ARCHITECTURE_IMPLEMENTATION.md)

#### 智能路由和流式能力 (2025-01)
- ✅ **智能路由**: API Gateway实现基于内容的智能路由，自动识别用户意图并路由到最佳服务
- ✅ **流式能力**: 完整的Server-Sent Events (SSE)流式响应支持，实时返回执行过程
- ✅ **Agent Service**: 智能体核心服务，提供对话理解、任务分类、服务集成等功能
- ✅ **Agent Orchestrator**: 智能体编排服务，支持多智能体协调和结果聚合
- ✅ **智能对话**: 统一的智能对话接口，自动理解意图、分类任务、路由执行
- ✅ **动态工作流**: 基于LLM的智能工作流设计，自动分析任务并生成最优执行网络

详细文档: 
- [STREAMING_IMPLEMENTATION.md](STREAMING_IMPLEMENTATION.md) - 流式能力实现
- [IMPLEMENTATION_COMPLETE_REPORT.md](IMPLEMENTATION_COMPLETE_REPORT.md) - 智能体执行链路实现
- [SAP_MCP_SERVER_5_SERVICES_ANALYSIS.md](SAP_MCP_SERVER_5_SERVICES_ANALYSIS.md) - SAP MCP Server服务分析

#### 任务4.1 - 前端与智能体工作流交互协议设计 ✅
- 完成WebSocket消息格式设计
- 实现TypeScript类型定义（`web-ui/src/types/agent-protocol.ts`）
- 设计实时通信API和状态同步机制
- 创建完整的协议文档和使用指南

#### 任务4.2 - 前端组件实现 ✅
- 实现 `AgentWorkflowInterface` 主组件
- 实现 `WorkflowVisualizer` 工作流可视化组件
- 实现 `AgentChat` 智能体聊天组件
- 完成状态管理、错误处理和API调用逻辑
- 添加完整的使用文档

#### 智能体导航栏集成 ✅
- 在顶部导航栏添加智能体菜单项
- 在侧边栏添加智能体菜单项
- 创建智能体列表页面（`/agents`）
- 支持搜索、筛选和基本操作功能

#### 项目可持续性评估 (2025-01) ⭐NEW
- ✅ **项目结构**: 8/10 - 清晰的微服务架构
- ✅ **代码质量**: 7/10 - 统一的错误处理框架
- 🟡 **测试覆盖**: 6/10 - 当前65%+，目标80%
- ✅ **类型安全**: 8/10 - TypeScript严格模式，Python类型提示
- ✅ **CI/CD**: 8/10 - 自动部署配置完善，支持热重载
- 🟡 **技术债务**: 5/10 - 23项债务，95-121小时修复时间

**综合评分**: 6.9/10 - **可持续，但需要持续改进**

详细报告: [PROJECT_SUSTAINABILITY_REPORT.md](PROJECT_SUSTAINABILITY_REPORT.md)

#### 技术债务管理 (2025-01) ⭐NEW
- 🔴 **P0关键问题**: 12项（安全漏洞、数据库问题、HTTP状态码）
- 🟡 **P1高优先级**: 8项（API规范、错误处理）
- 🟢 **P2中优先级**: 3项（测试覆盖、文档完善）

**改进路线图**: 详见 [TECHNICAL_DEBT_BOARD.md](TECHNICAL_DEBT_BOARD.md)

## 📄 许可证

本项目采用 MIT 许可证。

## 🙋 支持

- **问题反馈**: 提交 [Issue](../../issues)
- **功能请求**: 提交 [Feature Request](../../issues/new?template=feature_request.md)
- **文档问题**: 提交 [Documentation Issue](../../issues/new?template=documentation.md)
- **安全漏洞**: 请通过安全渠道报告，不要公开披露

## 🔄 项目迭代

- 查看 [项目迭代指南](docs/development-docs/ITERATION_GUIDE.md) 了解如何参与项目迭代
- 查看 [项目宪法](.project_constitution.md) 了解项目核心规范和原则


## 自动部署测试 - 12/26/2025 18:04:38
