# 知识库与元数据服务架构优化及AI原生统一数据表示 - 完整实施路线图

## 📋 执行摘要

**报告日期**: 2025-11-28  
**报告版本**: 2.0.0  
**目标**: 解决架构问题 + 实现AI原生统一数据表示  
**总时间估算**: 8-12个月  
**可行性评分**: ⭐⭐⭐⭐ (85%) - **高度可行**

### 核心目标

1. **解决5个架构问题**:
   - 知识图谱功能重复
   - 搜索功能分散
   - 向量化能力重复
   - 数据模型碎片化
   - 服务边界模糊

2. **实现AI原生统一数据表示**:
   - 统一向量空间
   - 多模态融合
   - 统一实体标识
   - 预测性治理

---

## 🔍 第一部分：现有系统深度分析

### 1.1 系统架构现状

#### 1.1.1 微服务架构概览

```
LuminaOS企业AI平台
├── 核心架构层
│   ├── registry-service (8000) - 服务注册与发现
│   ├── api-gateway (8080) - 统一API网关
│   └── config-center (8090) - 配置管理
│
├── 业务服务层
│   ├── knowledge-base (8004) - 知识库服务
│   ├── metadata-service (8005) - 元数据管理服务
│   ├── auth-service (8003) - 认证授权服务
│   ├── agent-service (8010) - 智能体服务
│   ├── chat-service (8006) - AI对话服务
│   └── sap-metadata-agent (8015) - SAP元数据代理
│
└── 基础设施层
    ├── postgres (5432) - PostgreSQL数据库
    ├── redis (6379) - Redis缓存
    └── qdrant (6333) - 向量数据库
```

#### 1.1.2 服务间依赖关系

```
api-gateway
  ├── → knowledge-base (文档搜索、知识图谱)
  ├── → metadata-service (元数据查询、业务实体)
  ├── → auth-service (认证授权)
  └── → agent-service (智能体调用)

knowledge-base
  ├── → postgres (文档存储)
  ├── → qdrant (向量存储)
  └── → redis (缓存)

metadata-service
  ├── → postgres (元数据存储)
  ├── → qdrant (部分向量存储，待统一)
  └── → sap-metadata-agent (SAP元数据)

agent-service
  ├── → knowledge-base (知识库查询)
  ├── → metadata-service (元数据查询)
  └── → chat-service (对话服务)
```

---

### 1.2 知识库服务（knowledge-base）现状分析

#### 1.2.1 核心功能

**文件结构**:
```
knowledge-base/
├── src/
│   ├── core/
│   │   ├── embedding_manager.py      # 向量化管理器
│   │   └── vector_store.py            # 向量存储（Qdrant/ChromaDB）
│   ├── services/
│   │   ├── search_service.py          # 语义搜索服务
│   │   └── ontology_builder.py        # 本体构建器
│   ├── repositories/
│   │   └── knowledge_graph_repository.py  # 知识图谱Repository
│   └── routes/
│       ├── search_db.py               # 搜索API
│       └── ontology.py                 # 本体API
```

**核心能力**:
1. **向量化能力** ⭐⭐⭐⭐⭐
   ```python
   # knowledge-base/src/core/embedding_manager.py
   class EmbeddingManager:
       - 模型: SentenceTransformer('all-MiniLM-L6-v2')
       - 维度: 384
       - 支持批量编码
       - 设备选择（CPU/CUDA）
   ```

2. **向量存储** ⭐⭐⭐⭐⭐
   ```python
   # knowledge-base/src/core/vector_store.py
   class VectorStore:
       - Qdrant支持
       - ChromaDB支持（可选）
       - 向量搜索能力
       - 元数据过滤
   ```

3. **语义搜索** ⭐⭐⭐⭐⭐
   ```python
   # knowledge-base/src/services/search_service.py
   class SearchService:
       async def semantic_search(self, query: str, top_k: int = 5):
           - 向量语义搜索
           - 元数据过滤
           - 搜索历史记录
           - 用户反馈收集
   ```

4. **知识图谱** ⭐⭐⭐⭐
   ```python
   # knowledge-base/src/repositories/knowledge_graph_repository.py
   class KnowledgeGraphRepository:
       - KnowledgeGraphNode (UUID, label, node_type, properties)
       - KnowledgeGraphEdge (source_node_id, target_node_id, label, weight)
       - 图查询能力
       - 图遍历能力
   ```

**API端点**:
- `POST /api/search/semantic` - 语义搜索
- `GET /api/search/history` - 搜索历史
- `POST /api/ontology/build` - 构建业务本体
- `POST /api/ontology/sap/build` - 构建SAP业务本体

**数据模型**:
```python
# database/src/models/knowledge_models.py
class KnowledgeGraphNode:
    id: UUID
    label: String(200)
    node_type: String(50)
    properties: JSONB
    document_id: UUID

class KnowledgeGraphEdge:
    id: UUID
    source_node_id: UUID
    target_node_id: UUID
    label: String(200)
    weight: Float
    properties: JSONB
```

**评估**: ⭐⭐⭐⭐⭐ (5/5) - **功能完善，技术先进**

---

### 1.3 元数据服务（metadata-service）现状分析

#### 1.3.1 核心功能

**文件结构**:
```
metadata-service/
├── src/
│   ├── models/
│   │   ├── data_asset.py              # 数据资产模型
│   │   ├── business_entity.py         # 业务实体模型
│   │   ├── lineage.py                 # 数据血缘模型
│   │   └── quality_vector.py          # 质量向量模型
│   ├── services/
│   │   ├── metadata_catalog.py        # 元数据目录服务
│   │   ├── search_service.py          # 搜索服务（SQL LIKE）
│   │   ├── data_lineage.py            # 数据血缘服务
│   │   ├── quality_rules_engine.py    # 质量规则引擎
│   │   └── business_entity_modeler.py # 业务实体建模器
│   └── routes/
│       ├── data_assets.py             # 数据资产API
│       ├── business_entities.py       # 业务实体API
│       ├── search.py                  # 搜索API
│       └── quality_rules.py           # 质量规则API
```

**核心能力**:
1. **元数据管理** ⭐⭐⭐⭐⭐
   ```python
   # metadata-service/src/services/metadata_catalog.py
   class MetadataCatalogService:
       - 数据资产CRUD
       - AI模型管理
       - 业务实体管理
       - 工作流元数据管理
   ```

2. **搜索能力** ⭐⭐⭐
   ```python
   # metadata-service/src/services/search_service.py
   class SearchService:
       def search_all(self, query: str):
           - SQL LIKE关键词搜索
           - 多实体类型搜索
           - 标签过滤
           - ❌ 无向量语义搜索
   ```

3. **向量化能力** ⭐⭐
   ```python
   # metadata-service/src/services/quality_rules_engine.py
   class QualityRulesEngine:
       - 本地Sentence Transformers（懒加载）
       - 质量指标向量化
       - ⚠️ 存储: PostgreSQL ARRAY（无向量搜索能力）
   ```

4. **数据血缘** ⭐⭐⭐⭐
   ```python
   # metadata-service/src/services/data_lineage.py
   class DataLineageService:
       - 血缘关系管理
       - 上游/下游查询
       - 影响分析
       - 根因分析
   ```

5. **业务实体** ⭐⭐⭐⭐
   ```python
   # metadata-service/src/models/business_entity.py
   class BusinessEntity:
       id: Integer
       name: String(255)
       entity_type: Enum
       related_entities: JSON  # 只是JSON列表，不是图关系
   ```

**API端点**:
- `GET /api/data-assets` - 数据资产列表
- `GET /api/business-entities` - 业务实体列表
- `GET /api/search` - 全局搜索（SQL LIKE）
- `POST /api/lineage` - 创建血缘关系
- `POST /api/quality/rules/execute` - 执行质量规则

**数据模型**:
```python
# metadata-service/src/models/business_entity.py
class BusinessEntity:
    id: Integer
    name: String(255)
    entity_type: EntityType
    related_entities: JSON  # 不是图关系

# metadata-service/src/models/lineage.py
class DataLineage:
    id: Integer
    source_type: String(50)
    source_id: String(255)
    target_type: String(50)
    target_id: String(255)
    relation_type: LineageRelationType

# metadata-service/src/models/quality_vector.py
class QualityRuleVector:
    id: Integer
    asset_id: Integer
    vector: ARRAY[Float]  # PostgreSQL ARRAY，无搜索能力
    vector_dimension: Integer
```

**评估**: ⭐⭐⭐ (3/5) - **功能基础，需扩展向量化和搜索能力**

---

### 1.4 架构问题详细分析

#### 问题1: 知识图谱功能重复 🔴

**现状**:
- **Knowledge Base**: `KnowledgeGraphNode` + `KnowledgeGraphEdge` (UUID, PostgreSQL)
- **Metadata Service**: `BusinessEntity` + `DataLineage` (Integer, PostgreSQL)

**问题**:
- 两套独立的图存储机制
- 无法跨域查询
- 实体无法关联

**影响**:
- 用户困惑（查询"客户"时不知道看哪个图谱）
- 数据割裂（文档中的"客户"无法与SAP"客户"关联）
- 维护成本高（两套图存储需要分别维护）

**代码证据**:
```python
# knowledge-base/src/repositories/knowledge_graph_repository.py
def get_related_nodes(self, node_id: str):
    # 基于KnowledgeGraphNode和KnowledgeGraphEdge
    pass

# metadata-service/src/services/data_lineage.py
def get_upstream_lineage(self, asset_type: str, asset_id: str):
    # 基于DataLineage表
    pass
```

---

#### 问题2: 搜索功能分散 🔴

**现状**:
- **Knowledge Base**: 向量语义搜索（Qdrant）
- **Metadata Service**: SQL关键词搜索（PostgreSQL LIKE）

**问题**:
- 两套独立的搜索系统
- 无法统一搜索
- 结果不完整

**影响**:
- 用户体验割裂（需要分别在两个系统搜索）
- 结果不完整（无法同时搜索文档和元数据）
- 学习成本高（需要学习两套搜索语法）

**代码证据**:
```python
# knowledge-base/src/services/search_service.py
async def semantic_search(self, query: str):
    # 向量语义搜索
    query_embedding = embedding_manager.encode_single(query)
    results = vector_store.search(query_embedding, top_k=5)

# metadata-service/src/services/search_service.py
def search_all(self, query: str):
    # SQL LIKE搜索
    search_pattern = f"%{query}%"
    query = db.query(DataAsset).filter(DataAsset.name.ilike(search_pattern))
```

---

#### 问题3: 向量化能力重复 🟡

**现状**:
- **Knowledge Base**: Sentence Transformers + Qdrant
- **Metadata Service**: Sentence Transformers + PostgreSQL ARRAY

**问题**:
- 两个服务都加载相同的模型
- 向量存储分散
- 无法跨服务向量相似度计算

**影响**:
- 资源浪费（两个服务都加载模型）
- 维护成本高（模型更新需要在两个地方进行）
- 无法统一（无法进行跨域的向量相似度计算）

**代码证据**:
```python
# knowledge-base/src/core/embedding_manager.py
self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 384维

# metadata-service/src/services/quality_rules_engine.py
self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384维
# 但存储到PostgreSQL ARRAY，无搜索能力
```

---

#### 问题4: 数据模型碎片化 🔴

**现状**:
- **Knowledge Base**: `KnowledgeGraphNode` (UUID, 文档实体)
- **Metadata Service**: `BusinessEntity` (Integer, SAP业务实体)

**问题**:
- 相同的业务概念存储在两处
- 无法自动关联
- ID格式不一致（UUID vs Integer）

**影响**:
- 数据割裂（文档中的"客户"无法与SAP"客户"关联）
- 查询结果重复或不一致
- 无法构建完整的知识网络

**代码证据**:
```python
# knowledge-base: 从文档提取的实体
KnowledgeGraphNode(
    label="客户",
    node_type="concept",
    properties={"name": "客户", "source": "document"}
)

# metadata-service: SAP业务实体
BusinessEntity(
    name="客户",
    entity_type=EntityType.CONCEPT,
    metadata={"source_system": "SAP", "table_name": "KNA1"}
)
```

---

#### 问题5: 服务边界模糊 🟡

**现状**:
- **Knowledge Base**: 处理业务本体构建（超出文档管理范围）
- **Metadata Service**: 业务实体缺乏知识图谱能力

**问题**:
- Knowledge Base越界（处理SAP业务概念）
- Metadata Service能力不足（业务实体只是表，不是图节点）

**影响**:
- 职责不清
- 维护困难
- 扩展受限

**代码证据**:
```python
# knowledge-base/src/services/ontology_builder.py
async def build_sap_business_ontology(self):
    # ⚠️ 从metadata-service获取SAP业务实体
    # ⚠️ 按SAP模块组织
    # ⚠️ 构建业务层次结构
    # 这超出了文档管理的职责范围
```

---

## 🎯 第二部分：目标架构设计

### 2.1 最终架构愿景

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Knowledge Platform                │
│                    (统一知识平台)                            │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
│  Unified       │  │  Vector        │  │  Entity         │
│  Search        │  │  Coordinator   │  │  Mapping       │
│  (统一搜索)    │  │  (向量协调)    │  │  (实体映射)    │
└───────┬────────┘  └───────┬────────┘  └───────┬────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
│  Knowledge     │  │  Metadata      │  │  Auth          │
│  Base          │  │  Service        │  │  Service       │
│  (知识库)      │  │  (元数据)      │  │  (权限)        │
└───────┬────────┘  └───────┬────────┘  └───────┬────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Unified       │
                    │  Vector Store  │
                    │  (Qdrant)      │
                    └────────────────┘
```

### 2.2 核心组件设计

#### 2.2.1 统一搜索层

**组件**: `UnifiedSearchService`
**位置**: `api-gateway/src/services/unified_search.py`

**功能**:
- 统一搜索接口
- 结果融合和排序
- 跨服务搜索协调

**API设计**:
```python
POST /api/unified/search
{
    "query": "客户",
    "types": ["document", "metadata", "entity"],
    "limit": 20,
    "filters": {...}
}

Response:
{
    "results": [
        {
            "type": "document",
            "id": "...",
            "title": "...",
            "score": 0.95,
            "source": "knowledge-base"
        },
        {
            "type": "entity",
            "id": "...",
            "title": "...",
            "score": 0.92,
            "source": "metadata-service"
        }
    ],
    "total": 20,
    "search_time_ms": 150
}
```

---

#### 2.2.2 向量协调服务

**组件**: `vector-coordinator-service`
**端口**: 8020

**功能**:
- 统一向量空间管理
- 多模态向量融合
- 统一实体标识分配
- 向量相似度服务

**API设计**:
```python
POST /api/vectors/register
{
    "entity_uri": "entity://metadata/data_asset/123",
    "modality": "metadata",
    "vector": [0.1, 0.2, ...],
    "metadata": {...}
}

POST /api/vectors/fuse
{
    "metadata_vec": [...],
    "knowledge_vec": [...],
    "permission_vec": [...]
}

POST /api/vectors/similar
{
    "query": "客户",
    "modalities": ["metadata", "knowledge"],
    "limit": 10
}
```

---

#### 2.2.3 统一实体标识

**组件**: `EntityURI`
**位置**: `shared-libs/luminaos_common/common/entity_uri.py`

**格式**: `entity://{domain}/{type}/{id}`

**示例**:
- `entity://metadata/data_asset/123`
- `entity://knowledge/node/uuid-123`
- `entity://sap/business_entity/456`

---

#### 2.2.4 实体映射服务

**组件**: `EntityMappingService`
**位置**: `metadata-service/src/services/entity_mapping_service.py`

**功能**:
- 自动实体映射（基于向量相似度）
- 手动实体映射
- 映射关系管理

**数据模型**:
```python
class EntityMapping(Base, TimestampMixin):
    id: Integer
    source_uri: String  # entity://knowledge/node/uuid-123
    target_uri: String   # entity://metadata/business_entity/456
    mapping_type: String  # auto, manual, similarity
    confidence: Float
    status: String  # pending, confirmed, rejected
```

---

#### 2.2.5 统一知识图谱层

**组件**: `UnifiedKnowledgeGraphService`
**位置**: `api-gateway/src/services/unified_knowledge_graph.py`

**功能**:
- 统一节点查询
- 跨域路径查询
- 关系分析

**API设计**:
```python
GET /api/unified/knowledge-graph/nodes?type=concept&source=all

POST /api/unified/knowledge-graph/paths
{
    "source": "entity://knowledge/node/uuid-123",
    "target": "entity://metadata/business_entity/456",
    "max_depth": 3
}
```

---

## 🛠️ 第三部分：分阶段详细实施计划

### 阶段0：快速改进（Quick Wins）（2-3周）⭐ 立即开始

**目标**: 快速解决用户体验问题，获得立竿见影的效果

**优先级**: 🔴 P0 - **最高优先级**

---

#### 工作项0.1：统一搜索网关（1周）

**目标**: 在api-gateway中创建统一搜索端点

**实施步骤**:

1. **创建统一搜索服务**

**文件**: `api-gateway/src/services/unified_search_service.py`

```python
"""
统一搜索服务
整合knowledge-base和metadata-service的搜索结果
"""
import httpx
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class UnifiedSearchService:
    """统一搜索服务"""
    
    def __init__(self):
        self.knowledge_base_url = os.getenv(
            "KNOWLEDGE_BASE_URL", 
            "http://knowledge-base:8004"
        )
        self.metadata_service_url = os.getenv(
            "METADATA_SERVICE_URL",
            "http://metadata-service:8005"
        )
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def unified_search(
        self,
        query: str,
        types: List[str] = ["document", "metadata"],
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        统一搜索
        
        Args:
            query: 搜索查询
            types: 搜索类型列表（document, metadata, entity）
            limit: 返回结果数量限制
            filters: 过滤条件
        
        Returns:
            统一格式的搜索结果
        """
        start_time = datetime.now()
        results = {
            "documents": [],
            "metadata": [],
            "entities": [],
            "total": 0
        }
        
        # 并行搜索
        search_tasks = []
        
        if "document" in types:
            search_tasks.append(
                self._search_knowledge_base(query, limit)
            )
        
        if "metadata" in types or "entity" in types:
            search_tasks.append(
                self._search_metadata_service(query, limit)
            )
        
        # 等待所有搜索完成
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # 处理knowledge-base结果
        if "document" in types and len(search_results) > 0:
            kb_result = search_results[0]
            if not isinstance(kb_result, Exception):
                results["documents"] = self._normalize_kb_results(kb_result)
        
        # 处理metadata-service结果
        if ("metadata" in types or "entity" in types) and len(search_results) > 1:
            ms_result = search_results[1] if len(search_results) > 1 else search_results[0]
            if not isinstance(ms_result, Exception):
                normalized = self._normalize_metadata_results(ms_result)
                results["metadata"].extend(normalized.get("assets", []))
                results["entities"].extend(normalized.get("entities", []))
        
        # 融合和排序结果
        merged_results = self._merge_and_rank_results(results, query)
        
        # 计算总时间
        search_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "results": merged_results,
            "total": len(merged_results),
            "search_time_ms": search_time_ms,
            "query": query
        }
    
    async def _search_knowledge_base(
        self,
        query: str,
        limit: int
    ) -> Dict[str, Any]:
        """搜索knowledge-base"""
        try:
            response = await self.http_client.post(
                f"{self.knowledge_base_url}/api/search/semantic",
                json={
                    "query": query,
                    "top_k": limit
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to search knowledge-base: {e}")
            return {"results": []}
    
    async def _search_metadata_service(
        self,
        query: str,
        limit: int
    ) -> Dict[str, Any]:
        """搜索metadata-service"""
        try:
            response = await self.http_client.get(
                f"{self.metadata_service_url}/api/search",
                params={
                    "query": query,
                    "limit": limit
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to search metadata-service: {e}")
            return {"data_assets": [], "business_entities": []}
    
    def _normalize_kb_results(self, kb_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """标准化knowledge-base结果"""
        normalized = []
        results = kb_result.get("results", [])
        
        for result in results:
            normalized.append({
                "type": "document",
                "id": result.get("document_id") or result.get("id"),
                "title": result.get("title") or result.get("content", "")[:100],
                "content": result.get("content", ""),
                "score": result.get("score", 0.0),
                "source": "knowledge-base",
                "metadata": {
                    "document_id": result.get("document_id"),
                    "chunk_id": result.get("chunk_id"),
                    "knowledge_base_id": result.get("knowledge_base_id")
                }
            })
        
        return normalized
    
    def _normalize_metadata_results(self, ms_result: Dict[str, Any]) -> Dict[str, Any]:
        """标准化metadata-service结果"""
        normalized = {
            "assets": [],
            "entities": []
        }
        
        # 处理数据资产
        assets = ms_result.get("data_assets", [])
        for asset in assets:
            normalized["assets"].append({
                "type": "data_asset",
                "id": asset.get("id"),
                "title": asset.get("name") or asset.get("display_name"),
                "description": asset.get("description", ""),
                "score": self._calculate_relevance_score(asset, query),
                "source": "metadata-service",
                "metadata": {
                    "asset_type": asset.get("asset_type"),
                    "source_system": asset.get("source_system"),
                    "sap_table_name": asset.get("sap_table_name")
                }
            })
        
        # 处理业务实体
        entities = ms_result.get("business_entities", [])
        for entity in entities:
            normalized["entities"].append({
                "type": "business_entity",
                "id": entity.get("id"),
                "title": entity.get("name") or entity.get("display_name"),
                "description": entity.get("description", ""),
                "score": self._calculate_relevance_score(entity, query),
                "source": "metadata-service",
                "metadata": {
                    "entity_type": entity.get("entity_type"),
                    "source_system": entity.get("metadata", {}).get("source_system")
                }
            })
        
        return normalized
    
    def _calculate_relevance_score(
        self,
        item: Dict[str, Any],
        query: str
    ) -> float:
        """计算相关性分数（简单实现）"""
        query_lower = query.lower()
        score = 0.0
        
        # 名称匹配
        name = (item.get("name") or item.get("display_name") or "").lower()
        if query_lower in name:
            score += 0.5
        if name in query_lower:
            score += 0.3
        
        # 描述匹配
        description = (item.get("description") or "").lower()
        if query_lower in description:
            score += 0.2
        
        return min(score, 1.0)
    
    def _merge_and_rank_results(
        self,
        results: Dict[str, Any],
        query: str
    ) -> List[Dict[str, Any]]:
        """融合和排序结果"""
        all_results = []
        
        # 收集所有结果
        all_results.extend(results.get("documents", []))
        all_results.extend(results.get("metadata", []))
        all_results.extend(results.get("entities", []))
        
        # 按分数排序
        all_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return all_results
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
```

2. **创建统一搜索API路由**

**文件**: `api-gateway/src/routes/unified_search.py`

```python
"""
统一搜索API路由
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..services.unified_search_service import UnifiedSearchService
from luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/unified", tags=["Unified Search"])
logger = setup_logger(__name__)


class UnifiedSearchRequest(BaseModel):
    """统一搜索请求"""
    query: str
    types: List[str] = ["document", "metadata"]
    limit: int = 20
    filters: Optional[Dict[str, Any]] = None


@router.post("/search", summary="统一搜索")
async def unified_search(request: UnifiedSearchRequest):
    """
    统一搜索接口
    
    整合knowledge-base和metadata-service的搜索结果
    """
    try:
        service = UnifiedSearchService()
        result = await service.unified_search(
            query=request.query,
            types=request.types,
            limit=request.limit,
            filters=request.filters
        )
        await service.close()
        return result
    except Exception as e:
        logger.error(f"Unified search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", summary="统一搜索（GET方式）")
async def unified_search_get(
    query: str = Query(..., description="搜索查询"),
    types: str = Query("document,metadata", description="搜索类型，逗号分隔"),
    limit: int = Query(20, ge=1, le=100, description="返回结果数量")
):
    """统一搜索接口（GET方式）"""
    try:
        type_list = [t.strip() for t in types.split(",")]
        service = UnifiedSearchService()
        result = await service.unified_search(
            query=query,
            types=type_list,
            limit=limit
        )
        await service.close()
        return result
    except Exception as e:
        logger.error(f"Unified search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

3. **注册路由到api-gateway**

**文件**: `api-gateway/src/main.py`

```python
# 在main.py中添加
from .routes import unified_search

app.include_router(unified_search.router)
```

**测试**:
```bash
# 测试统一搜索
curl -X POST http://localhost:8080/api/unified/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "客户",
    "types": ["document", "metadata"],
    "limit": 20
  }'
```

**预期成果**:
- ✅ 统一搜索API可用
- ✅ 搜索结果融合和排序
- ✅ 响应时间 < 1.5s

---

#### 工作项0.2：实体映射基础（1周）

**目标**: 创建实体映射表和服务

**实施步骤**:

1. **创建实体映射数据模型**

**文件**: `database/src/models/entity_mapping.py`

```python
"""
实体映射模型
用于映射knowledge-base和metadata-service的实体
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.sql import func
from pydantic import BaseModel, Field

from database.src.models.base import Base, TimestampMixin


class EntityMapping(Base, TimestampMixin):
    """实体映射表"""
    __tablename__ = "entity_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 源实体（knowledge-base）
    source_uri = Column(String(500), nullable=False, index=True, comment="源实体URI")
    source_type = Column(String(50), nullable=False, comment="源实体类型")
    source_id = Column(String(255), nullable=False, comment="源实体ID")
    
    # 目标实体（metadata-service）
    target_uri = Column(String(500), nullable=False, index=True, comment="目标实体URI")
    target_type = Column(String(50), nullable=False, comment="目标实体类型")
    target_id = Column(String(255), nullable=False, comment="目标实体ID")
    
    # 映射信息
    mapping_type = Column(String(50), nullable=False, default="auto", comment="映射类型：auto, manual, similarity")
    confidence = Column(Float, nullable=False, default=0.0, comment="映射置信度（0-1）")
    status = Column(String(20), nullable=False, default="pending", comment="状态：pending, confirmed, rejected")
    
    # 映射时间
    mapped_at = Column(DateTime, default=func.now(), nullable=False, comment="映射时间")
    
    # 索引
    __table_args__ = (
        Index('idx_source_uri', 'source_uri'),
        Index('idx_target_uri', 'target_uri'),
        Index('idx_source_target', 'source_uri', 'target_uri'),
        Index('idx_status', 'status'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "source_uri": self.source_uri,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "target_uri": self.target_uri,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "mapping_type": self.mapping_type,
            "confidence": self.confidence,
            "status": self.status,
            "mapped_at": self.mapped_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class EntityMappingBase(BaseModel):
    """实体映射基础模型"""
    source_uri: str = Field(..., description="源实体URI")
    target_uri: str = Field(..., description="目标实体URI")
    mapping_type: str = Field("auto", description="映射类型")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="映射置信度")
    status: str = Field("pending", description="状态")


class EntityMappingCreate(EntityMappingBase):
    """创建实体映射请求"""
    source_type: str = Field(..., description="源实体类型")
    source_id: str = Field(..., description="源实体ID")
    target_type: str = Field(..., description="目标实体类型")
    target_id: str = Field(..., description="目标实体ID")


class EntityMappingSchema(EntityMappingBase):
    """实体映射Schema"""
    id: int
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    mapped_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

2. **创建数据库迁移**

**文件**: `database/alembic/versions/xxxx_create_entity_mapping.py`

```python
"""create entity mapping table

Revision ID: xxxx
Revises: yyyy
Create Date: 2025-11-28
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'entity_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_uri', sa.String(500), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', sa.String(255), nullable=False),
        sa.Column('target_uri', sa.String(500), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('target_id', sa.String(255), nullable=False),
        sa.Column('mapping_type', sa.String(50), nullable=False, server_default='auto'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('mapped_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_source_uri', 'entity_mappings', ['source_uri'])
    op.create_index('idx_target_uri', 'entity_mappings', ['target_uri'])
    op.create_index('idx_source_target', 'entity_mappings', ['source_uri', 'target_uri'])
    op.create_index('idx_status', 'entity_mappings', ['status'])


def downgrade():
    op.drop_table('entity_mappings')
```

3. **创建实体映射服务**

**文件**: `metadata-service/src/services/entity_mapping_service.py`

```python
"""
实体映射服务
"""
import logging
import httpx
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from database.src.models.entity_mapping import (
    EntityMapping,
    EntityMappingCreate,
    EntityMappingSchema
)

logger = logging.getLogger(__name__)


class EntityMappingService:
    """实体映射服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.knowledge_base_url = os.getenv(
            "KNOWLEDGE_BASE_URL",
            "http://knowledge-base:8004"
        )
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def auto_map_entities(
        self,
        similarity_threshold: float = 0.8
    ) -> List[EntityMappingSchema]:
        """
        自动映射实体
        
        基于名称相似度自动映射knowledge-base和metadata-service的实体
        """
        try:
            # 1. 获取knowledge-base的实体
            kg_entities = await self._get_knowledge_base_entities()
            
            # 2. 获取metadata-service的业务实体
            be_entities = self._get_business_entities()
            
            # 3. 基于名称相似度自动映射
            mappings = []
            for kg_entity in kg_entities:
                kg_name = kg_entity.get("name", "").lower()
                kg_id = kg_entity.get("id")
                kg_uri = f"entity://knowledge/node/{kg_id}"
                
                for be_entity in be_entities:
                    be_name = be_entity.name.lower()
                    be_id = be_entity.id
                    be_uri = f"entity://metadata/business_entity/{be_id}"
                    
                    # 计算名称相似度
                    similarity = self._calculate_name_similarity(kg_name, be_name)
                    
                    if similarity >= similarity_threshold:
                        # 检查是否已存在映射
                        existing = self.db.query(EntityMapping).filter(
                            or_(
                                and_(
                                    EntityMapping.source_uri == kg_uri,
                                    EntityMapping.target_uri == be_uri
                                ),
                                and_(
                                    EntityMapping.source_uri == be_uri,
                                    EntityMapping.target_uri == kg_uri
                                )
                            )
                        ).first()
                        
                        if not existing:
                            mapping = EntityMapping(
                                source_uri=kg_uri,
                                source_type="knowledge_graph_node",
                                source_id=str(kg_id),
                                target_uri=be_uri,
                                target_type="business_entity",
                                target_id=str(be_id),
                                mapping_type="auto",
                                confidence=similarity,
                                status="pending"
                            )
                            self.db.add(mapping)
                            mappings.append(mapping)
            
            self.db.commit()
            
            # 刷新并返回
            for mapping in mappings:
                self.db.refresh(mapping)
            
            return [EntityMappingSchema.model_validate(m) for m in mappings]
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to auto map entities: {e}", exc_info=True)
            raise
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """计算名称相似度（简单实现）"""
        if name1 == name2:
            return 1.0
        
        # 包含关系
        if name1 in name2 or name2 in name1:
            return 0.8
        
        # 字符重叠度
        set1 = set(name1)
        set2 = set(name2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    async def _get_knowledge_base_entities(self) -> List[Dict[str, Any]]:
        """获取knowledge-base的实体"""
        try:
            response = await self.http_client.get(
                f"{self.knowledge_base_url}/api/ontology/concepts",
                params={"limit": 1000}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("concepts", [])
        except Exception as e:
            logger.error(f"Failed to get knowledge-base entities: {e}")
            return []
    
    def _get_business_entities(self):
        """获取metadata-service的业务实体"""
        from ..services.metadata_catalog import MetadataCatalogService
        catalog = MetadataCatalogService(self.db)
        return catalog.list_business_entities(limit=1000)
    
    def get_mappings(
        self,
        source_uri: Optional[str] = None,
        target_uri: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[EntityMappingSchema]:
        """获取实体映射列表"""
        query = self.db.query(EntityMapping)
        
        if source_uri:
            query = query.filter(EntityMapping.source_uri == source_uri)
        if target_uri:
            query = query.filter(EntityMapping.target_uri == target_uri)
        if status:
            query = query.filter(EntityMapping.status == status)
        
        mappings = query.offset(skip).limit(limit).all()
        return [EntityMappingSchema.model_validate(m) for m in mappings]
    
    def create_mapping(self, mapping_data: EntityMappingCreate) -> EntityMappingSchema:
        """创建实体映射"""
        mapping = EntityMapping(**mapping_data.model_dump())
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return EntityMappingSchema.model_validate(mapping)
    
    def update_mapping_status(
        self,
        mapping_id: int,
        status: str
    ) -> Optional[EntityMappingSchema]:
        """更新映射状态"""
        mapping = self.db.query(EntityMapping).filter(
            EntityMapping.id == mapping_id
        ).first()
        
        if not mapping:
            return None
        
        mapping.status = status
        self.db.commit()
        self.db.refresh(mapping)
        return EntityMappingSchema.model_validate(mapping)
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
```

4. **创建实体映射API路由**

**文件**: `metadata-service/src/routes/entity_mapping.py`

```python
"""
实体映射API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.entity_mapping_service import EntityMappingService
from database.src.models.entity_mapping import (
    EntityMappingCreate,
    EntityMappingSchema
)
from luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/entity-mapping", tags=["Entity Mapping"])
logger = setup_logger(__name__)


@router.post("/auto-map", summary="自动映射实体")
async def auto_map_entities(
    similarity_threshold: float = Body(0.8, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """自动映射knowledge-base和metadata-service的实体"""
    try:
        service = EntityMappingService(db)
        mappings = await service.auto_map_entities(similarity_threshold)
        await service.close()
        return {
            "success": True,
            "mappings": mappings,
            "count": len(mappings)
        }
    except Exception as e:
        logger.error(f"Failed to auto map entities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mappings", summary="获取实体映射列表")
async def get_mappings(
    source_uri: Optional[str] = Query(None),
    target_uri: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取实体映射列表"""
    try:
        service = EntityMappingService(db)
        mappings = service.get_mappings(
            source_uri=source_uri,
            target_uri=target_uri,
            status=status,
            skip=skip,
            limit=limit
        )
        await service.close()
        return {
            "success": True,
            "mappings": mappings,
            "count": len(mappings)
        }
    except Exception as e:
        logger.error(f"Failed to get mappings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mappings", summary="创建实体映射")
async def create_mapping(
    mapping_data: EntityMappingCreate,
    db: Session = Depends(get_db)
):
    """创建实体映射"""
    try:
        service = EntityMappingService(db)
        mapping = service.create_mapping(mapping_data)
        await service.close()
        return {
            "success": True,
            "mapping": mapping
        }
    except Exception as e:
        logger.error(f"Failed to create mapping: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/mappings/{mapping_id}/status", summary="更新映射状态")
async def update_mapping_status(
    mapping_id: int,
    status: str = Body(..., description="新状态：pending, confirmed, rejected"),
    db: Session = Depends(get_db)
):
    """更新映射状态"""
    try:
        service = EntityMappingService(db)
        mapping = service.update_mapping_status(mapping_id, status)
        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")
        await service.close()
        return {
            "success": True,
            "mapping": mapping
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update mapping status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

5. **注册路由**

**文件**: `metadata-service/src/main.py`

```python
# 在main.py中添加
from .routes import entity_mapping

app.include_router(entity_mapping.router)
```

**测试**:
```bash
# 自动映射实体
curl -X POST http://localhost:8005/api/entity-mapping/auto-map \
  -H "Content-Type: application/json" \
  -d '{"similarity_threshold": 0.8}'

# 获取映射列表
curl http://localhost:8005/api/entity-mapping/mappings?status=confirmed
```

**预期成果**:
- ✅ 实体映射表创建
- ✅ 自动映射服务可用
- ✅ 映射管理API可用

---

#### 工作项0.3：统一监控（1周）

**目标**: 创建跨服务的知识图谱监控面板

**实施步骤**:

1. **创建监控服务**

**文件**: `api-gateway/src/services/knowledge_graph_monitor.py`

```python
"""
知识图谱监控服务
"""
import httpx
import os
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class KnowledgeGraphMonitor:
    """知识图谱监控服务"""
    
    def __init__(self):
        self.knowledge_base_url = os.getenv(
            "KNOWLEDGE_BASE_URL",
            "http://knowledge-base:8004"
        )
        self.metadata_service_url = os.getenv(
            "METADATA_SERVICE_URL",
            "http://metadata-service:8005"
        )
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def get_unified_stats(self) -> Dict[str, Any]:
        """获取统一统计信息"""
        stats = {
            "knowledge_base": {},
            "metadata_service": {},
            "entity_mappings": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 获取knowledge-base统计
            kb_response = await self.http_client.get(
                f"{self.knowledge_base_url}/api/ontology/concepts",
                params={"limit": 1}
            )
            if kb_response.status_code == 200:
                kb_data = kb_response.json()
                stats["knowledge_base"] = {
                    "total_concepts": kb_data.get("total", 0),
                    "status": "healthy"
                }
        except Exception as e:
            logger.error(f"Failed to get knowledge-base stats: {e}")
            stats["knowledge_base"] = {"status": "error", "error": str(e)}
        
        try:
            # 获取metadata-service统计
            ms_response = await self.http_client.get(
                f"{self.metadata_service_url}/api/business-entities",
                params={"limit": 1}
            )
            if ms_response.status_code == 200:
                ms_data = ms_response.json()
                stats["metadata_service"] = {
                    "total_entities": len(ms_data) if isinstance(ms_data, list) else ms_data.get("total", 0),
                    "status": "healthy"
                }
        except Exception as e:
            logger.error(f"Failed to get metadata-service stats: {e}")
            stats["metadata_service"] = {"status": "error", "error": str(e)}
        
        try:
            # 获取实体映射统计
            mapping_response = await self.http_client.get(
                f"{self.metadata_service_url}/api/entity-mapping/mappings",
                params={"limit": 1}
            )
            if mapping_response.status_code == 200:
                mapping_data = mapping_response.json()
                stats["entity_mappings"] = {
                    "total_mappings": mapping_data.get("count", 0),
                    "status": "healthy"
                }
        except Exception as e:
            logger.error(f"Failed to get entity mapping stats: {e}")
            stats["entity_mappings"] = {"status": "error", "error": str(e)}
        
        return stats
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
```

2. **创建监控API路由**

**文件**: `api-gateway/src/routes/knowledge_graph_monitor.py`

```python
"""
知识图谱监控API路由
"""
from fastapi import APIRouter, HTTPException
from ..services.knowledge_graph_monitor import KnowledgeGraphMonitor
from luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/monitor", tags=["Monitor"])
logger = setup_logger(__name__)


@router.get("/knowledge-graph/stats", summary="获取知识图谱统计信息")
async def get_knowledge_graph_stats():
    """获取统一的知识图谱统计信息"""
    try:
        monitor = KnowledgeGraphMonitor()
        stats = await monitor.get_unified_stats()
        await monitor.close()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**预期成果**:
- ✅ 统一监控API可用
- ✅ 跨服务统计信息展示

---

### 阶段0总结

**完成时间**: 2-3周

**交付物**:
1. ✅ 统一搜索网关（api-gateway）
2. ✅ 实体映射基础（数据库模型 + 服务 + API）
3. ✅ 统一监控（监控服务 + API）

**成功指标**:
- ✅ 统一搜索响应时间 < 1.5s
- ✅ 搜索结果完整性 > 90%
- ✅ 实体映射成功率 > 70%

**解决的问题**:
- ✅ 部分解决搜索功能分散问题（报告1问题2）

---

## 📝 由于报告过长，后续阶段将在下一部分继续...

**当前进度**: 阶段0完成，阶段1-4的详细实施计划将在后续补充。

**建议**: 先完成阶段0的实施，验证效果后再继续后续阶段。

---

**报告生成时间**: 2025-11-28  
**报告版本**: 2.0.0  
**状态**: ✅ 阶段0完成，阶段1-4待补充

