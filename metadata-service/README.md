# 元数据服务 (Metadata Service)

企业AI平台的元数据管理服务，提供数据资产、AI模型、业务实体和工作流的元数据管理功能，以及知识图谱、本体构建、关系发现和智能推荐等高级功能。

## 功能特性

### 核心元数据管理
- ✅ **数据资产元数据**: 管理数据集的元数据信息（schema、质量指标、业务信息等）
- ✅ **AI模型元数据**: 管理AI模型的元数据信息（训练配置、性能指标、部署信息等）
- ✅ **业务实体元数据**: 管理业务实体和术语（数据字典、业务规则等）
- ✅ **工作流元数据**: 管理工作流的元数据信息（定义、执行统计、依赖关系等）
- ✅ **数据血缘**: 追踪数据之间的依赖和转换关系
- ✅ **元数据搜索**: 全文搜索和标签搜索
- ✅ **数据质量**: 数据质量指标管理和监控
- ✅ **自动采集**: 从各个服务自动采集元数据
- ✅ **血缘追踪**: 实时追踪数据流和转换过程

### 知识图谱与本体（阶段2-3）
- ✅ **业务本体构建**: 自动构建业务概念的本体结构
- ✅ **SAP业务本体**: 支持SAP ERP模块的业务本体构建
- ✅ **知识图谱管理**: 节点和关系的CRUD操作
- ✅ **关系发现**: 混合方案（规则引擎 + LLM增强）
- ✅ **文档实体关联**: 自动关联知识库文档与业务实体
- ✅ **知识图谱查询**: 节点、边、子图、路径查询

### 统一实体标识（阶段3）
- ✅ **EntityURI系统**: 统一实体标识格式（`entity://domain/type/id`）
- ✅ **实体注册服务**: 管理跨服务的实体映射
- ✅ **实体解析**: EntityURI到内部ID的解析

### 智能功能（阶段4）
- ✅ **智能推荐**: 基于知识图谱和相似度的实体推荐
- ✅ **决策支持**: 影响分析、路径查找、实体洞察
- ✅ **知识图谱可视化**: 支持大规模图谱的可视化数据API
- ✅ **智能质量检测**: AI驱动的数据质量检测和修复建议

## 架构

### 核心组件

1. **元数据目录服务** (`src/services/metadata_catalog.py`)
   - 提供所有元数据的CRUD操作
   - 支持数据资产、AI模型、业务实体、工作流元数据管理

2. **数据血缘服务** (`src/services/data_lineage.py`)
   - 管理数据之间的依赖关系
   - 支持上游/下游血缘查询
   - 构建血缘图谱

3. **搜索服务** (`src/services/search_service.py`)
   - 全局元数据搜索
   - 标签搜索
   - 热门标签统计

4. **数据质量服务** (`src/services/quality_service.py`)
   - 质量指标管理
   - 质量摘要统计
   - 质量问题识别

5. **元数据采集管理器** (`src/collectors/collection_manager.py`)
   - 管理各种采集时机的元数据收集
   - 服务启动时注册基础元数据
   - 数据变更时更新元数据版本
   - 工具执行时收集使用统计
   - 工作流运行时收集执行指标
   - 用户交互时收集访问模式

6. **血缘采集器** (`src/collectors/lineage_collector.py`)
   - 追踪MCP工具执行血缘
   - 追踪工作流执行血缘
   - 追踪知识处理血缘
   - 追踪模型推理血缘

## API端点

### 数据资产

- `POST /api/data-assets` - 创建数据资产
- `GET /api/data-assets` - 列出数据资产（支持分页、过滤、搜索）
- `GET /api/data-assets/{id}` - 获取数据资产详情
- `PUT /api/data-assets/{id}` - 更新数据资产
- `DELETE /api/data-assets/{id}` - 删除数据资产

### AI模型

- `POST /api/ai-models` - 创建AI模型
- `GET /api/ai-models` - 列出AI模型
- `GET /api/ai-models/{id}` - 获取AI模型详情
- `PUT /api/ai-models/{id}` - 更新AI模型
- `DELETE /api/ai-models/{id}` - 删除AI模型

### 业务实体

- `POST /api/metadata/business-entities` - 创建业务实体
- `GET /api/metadata/business-entities` - 列出业务实体（支持分页、过滤、搜索）
- `GET /api/metadata/business-entities/{id}` - 获取业务实体详情
- `PUT /api/metadata/business-entities/{id}` - 更新业务实体
- `DELETE /api/metadata/business-entities/{id}` - 删除业务实体

### 工作流元数据

- `POST /api/workflows` - 创建工作流元数据
- `GET /api/workflows` - 列出工作流元数据
- `GET /api/workflows/{workflow_id}` - 获取工作流元数据详情
- `PUT /api/workflows/{workflow_id}` - 更新工作流元数据
- `DELETE /api/workflows/{workflow_id}` - 删除工作流元数据

### 搜索

- `GET /api/search?q={query}` - 全局搜索
- `GET /api/search/tags?tags={tag1,tag2}` - 按标签搜索
- `GET /api/search/popular-tags` - 获取热门标签

### 数据血缘

- `POST /api/lineage` - 创建血缘关系
- `GET /api/lineage` - 列出血缘关系
- `GET /api/lineage/upstream/{type}/{id}` - 获取上游血缘（数据来源）
- `GET /api/lineage/downstream/{type}/{id}` - 获取下游血缘（数据去向）
- `GET /api/lineage/full/{type}/{id}` - 获取完整血缘（上游+下游）
- `GET /api/lineage/impact/{asset_id}` - 影响分析（下游影响）
- `GET /api/lineage/lineage/{asset_id}` - 获取数据血缘详情（包含完整图谱和分析）
- `GET /api/lineage/root-cause/{asset_id}` - 根因分析（上游溯源）
- `DELETE /api/lineage/{id}` - 删除血缘关系

### 元数据API（统一接口）

- `GET /api/metadata/assets` - 列出数据资产（支持分类、业务域、质量分数过滤）
- `GET /api/metadata/assets/{asset_id}` - 获取资产详情（包含血缘关系等扩展信息）
- `GET /api/metadata/search` - 搜索元数据（返回结构化搜索结果，包含分面信息）

### 数据质量

- `PUT /api/quality/assets/{id}/metrics` - 更新质量指标
- `GET /api/quality/assets/{id}/metrics` - 获取质量指标
- `GET /api/quality/metrics/{asset_id}` - 获取数据质量指标（标准化DataQualityMetrics格式）
- `POST /api/quality/checks/{asset_id}` - 执行质量检查（运行完整的质量评估）
- `GET /api/quality/dashboard` - 质量监控仪表板（包含质量分布、主要问题、趋势数据）
- `GET /api/quality/summary` - 获取质量摘要
- `GET /api/quality/issues?threshold=0.7` - 获取质量问题
- `POST /api/quality/validate` - 验证质量指标格式

### 元数据采集

- `POST /api/collection/startup` - 服务启动时注册基础元数据
- `POST /api/collection/data-change` - 数据变更时更新元数据
- `POST /api/collection/tool-usage` - 工具执行时收集使用统计
- `POST /api/collection/workflow-execution` - 工作流运行时收集执行指标
- `POST /api/collection/user-access` - 用户交互时收集访问模式
- `POST /api/collection/sync-all` - 手动触发同步所有元数据

### 血缘追踪

- `POST /api/collection/lineage/tool-execution` - 追踪MCP工具执行血缘
- `POST /api/collection/lineage/workflow-execution` - 追踪工作流执行血缘
- `POST /api/collection/lineage/knowledge-processing` - 追踪知识处理血缘
- `POST /api/collection/lineage/model-inference` - 追踪模型推理血缘

### 本体构建

- `POST /api/ontology/build` - 构建业务本体
- `GET /api/ontology/concepts` - 获取概念列表
- `POST /api/ontology/sap/build` - 构建SAP业务本体

### 知识图谱

- `GET /api/knowledge-graph/nodes` - 获取知识图谱节点
- `GET /api/knowledge-graph/edges` - 获取知识图谱关系
- `GET /api/knowledge-graph/nodes/{node_id}` - 获取节点详情
- `GET /api/knowledge-graph/nodes/{node_id}/neighbors` - 获取节点的邻居
- `GET /api/knowledge-graph/paths` - 查找节点间路径
- `GET /api/knowledge-graph/subgraph` - 获取子图
- `GET /api/knowledge-graph/visualization` - 获取可视化数据

### 实体注册（EntityURI）

- `POST /api/entity-registry/register` - 注册实体
- `GET /api/entity-registry/entities` - 获取实体注册列表
- `POST /api/entity-registry/validate-uri` - 验证EntityURI格式
- `POST /api/entity-registry/parse-uri` - 解析EntityURI
- `GET /api/entity-registry/entities/count` - 获取实体注册总数

### 文档实体关联

- `POST /api/document-entity-linker/link` - 关联文档与实体
- `GET /api/document-entity-linker/stats` - 获取关联统计

### 智能推荐

- `GET /api/recommendation/entities/{entity_id}/related` - 推荐相关实体
- `GET /api/recommendation/entities/{entity_id}/similar` - 推荐相似实体
- `GET /api/recommendation/cache/stats` - 获取推荐缓存统计
- `POST /api/recommendation/cache/clear` - 清除推荐缓存

### 决策支持

- `POST /api/recommendation/decision/analyze-impact` - 分析实体影响范围
- `POST /api/recommendation/decision/find-path` - 查找实体间最优路径
- `GET /api/recommendation/decision/insights/{entity_id}` - 获取实体洞察

### 健康检查

- `GET /api/health` - 健康检查
- `GET /api/health/ready` - 就绪检查（检查数据库连接）
- `GET /api/health/live` - 存活检查

## 配置

### 环境变量

```bash
# 服务配置
PORT=8005
DEBUG=false

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=enterprise_ai_platform

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 搜索配置
SEARCH_MAX_RESULTS=100
SEARCH_DEFAULT_LIMIT=20

# 血缘配置
LINEAGE_MAX_DEPTH=10
LINEAGE_CACHE_TTL=3600

# 质量配置
QUALITY_CHECK_INTERVAL=3600
QUALITY_CACHE_TTL=1800

# LLM配置（用于关系发现和智能推荐）
LLM_BASE_URL=http://chat-service:8006
OPENAI_API_KEY=
LLM_RELATIONSHIP_DISCOVERY_ENABLED=true

# 知识库配置（用于文档实体关联）
KNOWLEDGE_BASE_URL=http://knowledge-base:8004
```

## 使用示例

### 1. 创建数据资产

```bash
curl -X POST "http://localhost:8005/api/data-assets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "customer_data",
    "display_name": "客户数据",
    "description": "客户基本信息表",
    "asset_type": "table",
    "source_system": "CRM",
    "source_path": "public.customer",
    "tags": ["customer", "pii"],
    "classification": "sensitive"
  }'
```

### 2. 搜索元数据

```bash
curl -X GET "http://localhost:8005/api/search?q=customer&entity_types=data_asset"
```

### 3. 创建血缘关系

```bash
curl -X POST "http://localhost:8005/api/lineage" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "data_asset",
    "source_id": "1",
    "target_type": "workflow",
    "target_id": "workflow_123",
    "relation_type": "reads",
    "lineage_type": "data_flow"
  }'
```

### 4. 获取上游血缘

```bash
curl -X GET "http://localhost:8005/api/lineage/upstream/data_asset/1?max_depth=5"
```

### 5. 更新质量指标

```bash
curl -X PUT "http://localhost:8005/api/quality/assets/1/metrics" \
  -H "Content-Type: application/json" \
  -d '{
    "quality_score": 0.95,
    "completeness": 0.98,
    "accuracy": 0.92,
    "timeliness": 0.90
  }'
```

### 6. 构建SAP业务本体

```bash
curl -X POST "http://localhost:8005/api/ontology/sap/build"
```

### 7. 查询知识图谱

```bash
# 获取节点
curl "http://localhost:8005/api/knowledge-graph/nodes?node_type=concept&limit=10"

# 获取关系
curl "http://localhost:8005/api/knowledge-graph/edges?relationship_type=related_to&limit=10"

# 获取节点的邻居
curl "http://localhost:8005/api/knowledge-graph/nodes/{node_id}/neighbors"
```

### 8. 注册实体（EntityURI）

```bash
curl -X POST "http://localhost:8005/api/entity-registry/register" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "metadata",
    "entity_type": "business_entity",
    "internal_id": "123",
    "service_name": "metadata-service",
    "extra_metadata": {"name": "物料主数据"}
  }'
```

### 9. 关联文档与实体

```bash
curl -X POST "http://localhost:8005/api/document-entity-linker/link" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": ["doc-123"],
    "entity_ids": [456]
  }'
```

### 10. 智能推荐

```bash
# 推荐相关实体
curl "http://localhost:8005/api/recommendation/entities/123/related?max_depth=2&limit=10"

# 推荐相似实体
curl "http://localhost:8005/api/recommendation/entities/123/similar?limit=10"
```

### 11. 决策支持

```bash
# 分析实体影响范围
curl -X POST "http://localhost:8005/api/recommendation/decision/analyze-impact" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": 123, "analysis_type": "full"}'

# 查找实体间路径
curl -X POST "http://localhost:8005/api/recommendation/decision/find-path" \
  -H "Content-Type: application/json" \
  -d '{"source_entity_id": 123, "target_entity_id": 456, "max_depth": 5}'
```

## 开发

### 本地运行

```bash
cd metadata-service
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8005
```

### Docker运行

```bash
# 开发环境
docker-compose up metadata-service

# 生产环境
docker build -f Dockerfile -t metadata-service .
docker run -p 8005:8005 metadata-service
```

## 数据库模型

服务使用以下数据库表：

### 核心元数据表
- `data_assets` - 数据资产元数据
- `ai_models` - AI模型元数据
- `business_entities` - 业务实体元数据
- `workflow_metadata` - 工作流元数据
- `data_lineage` - 数据血缘关系

### 知识图谱表（阶段2-3）
- `knowledge_graph_nodes` - 知识图谱节点
- `knowledge_graph_edges` - 知识图谱关系

### 实体注册表（阶段3）
- `entity_registry` - 实体注册表（EntityURI映射）

### 实体映射表
- `entity_mappings` - 实体映射关系

## 依赖

- FastAPI
- SQLAlchemy
- PostgreSQL (通过database模块)
- Redis (可选，用于缓存)

## 端口说明

⚠️ **注意**: 默认使用端口8005。确保该端口未被其他服务占用。

## 文档

- [采集时机说明](./COLLECTION_TIMING.md) - 元数据采集时机的详细说明
- [血缘追踪说明](./LINEAGE_TRACKING.md) - 数据血缘追踪功能的详细说明
- [阶段2-4实施报告](../STAGES_1-4_FINAL_SUMMARY.md) - 阶段2-4的完整实施总结
- [SAP MM知识库访问指南](../SAP_MM_KNOWLEDGE_BASE_ACCESS_GUIDE.md) - SAP MM知识库和元数据访问指南

