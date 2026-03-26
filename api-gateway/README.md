# API Gateway

企业AI平台的统一API网关服务，提供路由、负载均衡、限流、熔断、统一搜索、知识图谱搜索、自然语言查询和智能助手等功能。

## 📋 功能特性

### 核心功能
- ✅ **统一路由**: 所有业务API通过网关统一访问
- ✅ **服务发现**: 动态服务注册与发现，消除硬编码URL
- ✅ **负载均衡**: 支持多种负载均衡策略
- ✅ **限流保护**: 基于Redis的分布式限流
- ✅ **熔断保护**: 防止服务雪崩
- ✅ **智能路由**: 基于LLM的智能路由，自动识别用户意图并路由到最佳服务
- ✅ **流式代理**: 完整的Server-Sent Events (SSE)流式响应支持
- ✅ **WebSocket代理**: WebSocket连接代理支持

### 统一搜索功能
- ✅ **统一搜索**: 整合knowledge-base、metadata-service和vector-coordinator-service的搜索能力
- ✅ **向量搜索**: 集成向量相似度搜索
- ✅ **结果融合**: 智能合并和去重搜索结果
- ✅ **多级缓存**: L1内存缓存 + L2 Redis缓存
- ✅ **知识图谱搜索**: 基于知识图谱的语义搜索

### 智能功能
- ✅ **自然语言查询**: LLM驱动的自然语言到结构化查询转换
- ✅ **智能助手**: 上下文感知的多轮对话AI助手
- ✅ **智能监控**: AI驱动的性能分析和优化建议

## 🏗️ 架构

### 核心组件

1. **服务发现** (`src/core/service_discovery.py`)
   - 动态服务注册与发现
   - 健康检查和服务状态监控

2. **网关代理** (`src/core/proxy.py`)
   - HTTP请求代理
   - 负载均衡
   - 请求重试

3. **智能路由器** (`src/core/intelligent_router.py`)
   - 基于LLM的智能路由
   - 意图识别
   - 服务选择

4. **流式代理** (`src/core/stream_proxy.py`)
   - SSE流式响应代理
   - 实时数据传输

5. **统一搜索服务** (`src/services/unified_search_service.py`)
   - 整合多个服务的搜索能力
   - 结果融合和排序
   - 缓存管理

6. **知识图谱搜索服务** (`src/services/knowledge_graph_search.py`)
   - 知识图谱查询
   - 实体关系搜索

7. **自然语言查询服务** (`src/services/nl_query_service.py`)
   - NLQ解析
   - 查询转换

8. **智能助手服务** (`src/services/assistant_service.py`)
   - 对话管理
   - 上下文维护

## 📡 API端点

### 统一搜索

- `GET /api/unified/search` - 统一搜索（GET方式）
  - 参数: `q` (查询文本), `limit` (结果数量), `use_vector_search` (是否使用向量搜索), `use_cache` (是否使用缓存)
- `POST /api/unified/search` - 统一搜索（POST方式，支持更多参数）
  - 请求体: `query`, `limit`, `use_vector_search`, `use_cache`, `filters`

### 知识图谱搜索

- `GET /api/knowledge-graph/search` - 知识图谱搜索
  - 参数: `q` (查询文本), `node_type` (节点类型), `limit` (结果数量)
- `POST /api/knowledge-graph/search` - 知识图谱搜索（POST方式）

### 自然语言查询

- `POST /api/nl-query/parse` - 解析自然语言查询
- `POST /api/nl-query/search` - 自然语言搜索
- `POST /api/nl-query/answer` - 自然语言问答

### 智能助手

- `POST /api/assistant/chat/{session_id}` - 与智能助手对话
- `POST /api/assistant/ask` - 向智能助手提问
- `POST /api/assistant/clear-context/{session_id}` - 清除对话上下文

### 智能监控

- `POST /api/intelligent-monitoring/analyze-performance` - 分析系统性能
- `POST /api/intelligent-monitoring/detect-anomalies` - 检测异常
- `GET /api/intelligent-monitoring/optimization-suggestions` - 获取优化建议

### 缓存管理

- `GET /api/unified/cache/stats` - 获取缓存统计
- `DELETE /api/unified/cache` - 清除缓存

### 健康检查

- `GET /health` - 健康检查
- `GET /health/ready` - 就绪检查
- `GET /health/live` - 存活检查
- `GET /metrics` - Prometheus指标

### 代理路由

所有业务API通过网关代理访问：
- `/api/workflows/*` → Workflow Engine
- `/api/mcp/*` → MCP Gateway
- `/api/auth/*` → Auth Service
- `/api/knowledge/*` → Knowledge Base
- `/api/metadata/*` → Metadata Service
- `/api/chat/*` → Chat Service
- `/api/agents/*` → Agent Service
- `/api/dag/*` → DAG Orchestrator

## 🔧 配置

### 环境变量

```bash
# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# 服务发现配置
REGISTRY_SERVICE_URL=http://registry-service:8000
SERVICE_NAME=api-gateway
SERVICE_VERSION=1.0.0

# 限流配置
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# 熔断配置
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Redis配置（用于限流和缓存）
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 统一搜索配置
UNIFIED_SEARCH_CACHE_ENABLED=true
UNIFIED_SEARCH_CACHE_TTL=300
VECTOR_COORDINATOR_URL=http://vector-coordinator-service:8020
KNOWLEDGE_BASE_URL=http://knowledge-base:8004
METADATA_SERVICE_URL=http://metadata-service:8005

# LLM配置（用于智能路由和NLQ）
LLM_BASE_URL=http://chat-service:8006
OPENAI_API_KEY=

# 监控配置
METRICS_ENABLED=true
```

## 🚀 快速开始

### 使用Docker Compose

```bash
# 启动服务
docker-compose up -d api-gateway

# 查看日志
docker-compose logs -f api-gateway
```

### 本地开发

```bash
cd api-gateway
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

服务将在 `http://localhost:8000` 启动

## 📝 使用示例

### 统一搜索

```bash
# GET方式
curl "http://localhost:8000/api/unified/search?q=物料管理&limit=10"

# POST方式
curl -X POST "http://localhost:8000/api/unified/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "物料管理",
    "limit": 10,
    "use_vector_search": true,
    "use_cache": true
  }'
```

### 知识图谱搜索

```bash
curl "http://localhost:8000/api/knowledge-graph/search?q=采购订单&limit=10"
```

### 自然语言查询

```bash
curl -X POST "http://localhost:8000/api/nl-query/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查找与物料管理相关的所有实体"
  }'
```

### 智能助手

```bash
curl -X POST "http://localhost:8000/api/assistant/chat/session123" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "什么是物料管理？"
  }'
```

## 📊 性能优化

### 缓存策略

- **L1缓存**: 内存缓存，TTL 60秒
- **L2缓存**: Redis缓存，TTL 300秒
- **缓存键**: 基于查询参数生成唯一键

### 搜索优化

- **并行搜索**: 同时调用多个服务，减少延迟
- **结果融合**: 智能合并和去重，提升相关性
- **向量搜索**: 集成向量相似度搜索，提升语义匹配

## 🔍 监控和调试

### 查看缓存统计

```bash
curl "http://localhost:8000/api/unified/cache/stats"
```

### 查看Prometheus指标

```bash
curl "http://localhost:8000/metrics"
```

### 查看Swagger文档

访问 `http://localhost:8000/docs` 查看完整的API文档

## 📚 相关文档

- [统一搜索实现文档](../STAGE1_UNIFIED_SEARCH_OPTIMIZATION_REPORT.md)
- [知识图谱搜索文档](../STAGE3_IMPLEMENTATION_REPORT.md)
- [SAP MM知识库访问指南](../SAP_MM_KNOWLEDGE_BASE_ACCESS_GUIDE.md)

## 🔗 依赖服务

- **registry-service**: 服务注册与发现
- **knowledge-base**: 知识库服务（文档搜索）
- **metadata-service**: 元数据服务（实体搜索、知识图谱）
- **vector-coordinator-service**: 向量协调服务（向量搜索）
- **chat-service**: 聊天服务（LLM能力）
- **redis**: 缓存和限流

## 📝 注意事项

1. **端口**: 默认使用端口8000，确保该端口未被占用
2. **服务依赖**: 需要registry-service、redis等基础设施服务运行
3. **缓存**: 生产环境建议配置Redis持久化
4. **限流**: 根据实际负载调整限流参数




