# EA-OS完整系统设计方案

**文档版本**: 2.0
**创建时间**: 2025-12-06
**项目名称**: LuminaOS企业AI平台 - EA-OS五层架构完整系统设计
**适用范围**: 整合四数据库架构、五层EA-OS架构、企业架构功能实现

---

## 执行摘要

本方案基于以下三个核心文档整合设计：
1. **Neo4j三引擎融合架构可行性分析与实施计划**
2. **EA-OS五层架构设计分析报告**
3. **企业架构功能缺失分析报告**

结合现有23个服务和四数据库架构（Neo4j、Qdrant、PostgreSQL、MinIO），设计完整的EA-OS系统方案。

**核心设计原则**:
- ✅ **数据库职责清晰划分** - 每个数据库有明确的职责边界
- ✅ **五层架构合理分工** - 门户、网关、EA、AI、工具层各司其职
- ✅ **企业架构功能完整** - 填补所有EA功能缺失
- ✅ **现有服务平滑演进** - 基于现有23个服务渐进式升级

**关键指标**:
| 维度 | 当前状态 | 目标状态 | 实施周期 |
|-----|---------|---------|---------|
| 数据库架构 | 3个(PG+Qdrant+Redis) | 4个(+Neo4j) | 2周 |
| 系统架构 | 扁平化 | 五层EA-OS | 6个月 |
| EA功能 | 完全缺失 | 完整实现 | 2个月 |
| 查询性能 | 1000ms | 10ms | 100倍提升 |
| 准确率 | 70% | 92%+ | +31% |

---

## 目录

1. [四数据库职责架构设计](#1-四数据库职责架构设计)
2. [五层EA-OS架构详细设计](#2-五层ea-os架构详细设计)
3. [企业架构功能完整实现](#3-企业架构功能完整实现)
4. [数据流与交互模式](#4-数据流与交互模式)
5. [服务映射与演进路径](#5-服务映射与演进路径)
6. [分阶段实施计划](#6-分阶段实施计划)
7. [技术规范与标准](#7-技术规范与标准)
8. [监控与运维方案](#8-监控与运维方案)

---

## 1. 四数据库职责架构设计

### 1.1 数据库职责矩阵

| 数据库 | 核心职责 | 存储内容 | 查询特点 | 适用场景 |
|-------|---------|---------|---------|---------|
| **Neo4j** | 图关系存储 | 知识图谱、实体关系、架构图谱 | 图遍历、路径查询 | 多跳查询、关系发现、影响分析 |
| **Qdrant** | 向量存储 | 文档向量、实体向量、多模态向量 | 相似度搜索 | 语义搜索、推荐、多模态检索 |
| **PostgreSQL** | 关系存储 | 业务数据、元数据、配置、事务 | SQL查询、事务 | CRUD、事务处理、聚合统计 |
| **MinIO** | 对象存储 | 文档文件、图片、视频、大文件 | 对象访问 | 文件上传下载、多媒体存储 |

### 1.2 数据库详细职责划分

#### 1.2.1 Neo4j - 图数据库（新增）

**核心能力**: 高性能图遍历、复杂关系查询、路径发现

**存储内容**:

1. **知识图谱**
   ```cypher
   // 节点类型
   (:Entity {uuid, name, type, description, properties})
   (:Document {uuid, title, type, source})
   (:Concept {uuid, name, definition})

   // 关系类型
   -[:RELATED_TO {weight, type}]->
   -[:PART_OF {level}]->
   -[:DEPENDS_ON {strength}]->
   -[:CONTAINS]->
   ```

2. **企业架构图谱**
   ```cypher
   // 业务架构节点
   (:BusinessProcess {id, name, description, owner})
   (:BusinessCapability {id, name, level})
   (:BusinessService {id, name, endpoint})

   // 应用架构节点
   (:ApplicationSystem {id, name, type, status})
   (:ApplicationService {id, name, protocol})
   (:APIInterface {id, path, method})

   // 数据架构节点
   (:DataEntity {id, name, schema})
   (:DataModel {id, name, version})
   (:DataFlow {id, source, target})

   // 技术架构节点
   (:TechnologyComponent {id, name, version})
   (:TechnologyStack {id, name, category})
   (:InfrastructureComponent {id, name, type})

   // 跨层关系
   (:BusinessProcess)-[:IMPLEMENTED_BY]->(:ApplicationSystem)
   (:ApplicationSystem)-[:USES]->(:DataEntity)
   (:DataEntity)-[:STORED_IN]->(:TechnologyComponent)
   ```

3. **组织知识图谱**
   ```cypher
   (:Organization {id, name, type})
   (:Department {id, name, level})
   (:Role {id, name, responsibilities})
   (:Person {id, name, title})

   (:Department)-[:BELONGS_TO]->(:Organization)
   (:Person)-[:HAS_ROLE]->(:Role)
   (:Person)-[:WORKS_IN]->(:Department)
   ```

4. **SAP业务图谱**
   ```cypher
   (:SAPModule {id, name, code})
   (:SAPTransaction {id, tcode, description})
   (:SAPTable {id, name, description})
   (:Supplier {id, name, category})
   (:Material {id, code, name})
   (:PurchaseOrder {id, number, date})

   (:SAPTransaction)-[:ACCESSES]->(:SAPTable)
   (:PurchaseOrder)-[:FROM_SUPPLIER]->(:Supplier)
   (:PurchaseOrder)-[:CONTAINS]->(:Material)
   ```

**查询能力**:
- 1-5跳关系查询 (<50ms)
- 最短路径查询
- 社区发现（Louvain算法）
- PageRank重要性分析
- 影响分析（依赖传播）

**性能指标**:
- 节点容量: 100万+
- 边容量: 500万+
- 简单查询: <10ms
- 复杂查询: <100ms
- 算法查询: <5秒

---

#### 1.2.2 Qdrant - 向量数据库（现有）

**核心能力**: 高维向量相似度搜索、多模态检索

**存储内容**:

1. **文档向量** (Collection: `documents`)
   ```json
   {
     "id": "doc_uuid",
     "vector": [768维向量],
     "payload": {
       "kb_id": "knowledge_base_uuid",
       "doc_id": "document_uuid",
       "chunk_index": 0,
       "content": "文档内容片段",
       "metadata": {
         "title": "文档标题",
         "type": "pdf|docx|md",
         "source": "来源",
         "created_at": "2025-12-06"
       }
     }
   }
   ```

2. **实体向量** (Collection: `entities`)
   ```json
   {
     "id": "entity_uuid",
     "vector": [768维向量],
     "payload": {
       "entity_id": "neo4j_node_id",
       "name": "实体名称",
       "type": "BusinessProcess|Application|DataEntity",
       "description": "实体描述",
       "properties": {}
     }
   }
   ```

3. **企业架构文档向量** (Collection: `ea_documents`)
   ```json
   {
     "id": "ea_doc_uuid",
     "vector": [768维],
     "payload": {
       "kb_id": "ea_knowledge_base_uuid",
       "doc_type": "business_process|application_architecture|data_model",
       "architecture_domain": "business|application|data|technology",
       "content": "架构文档内容",
       "metadata": {
         "title": "文档标题",
         "version": "1.0",
         "owner": "架构师姓名",
         "last_updated": "2025-12-06"
       }
     }
   }
   ```

4. **多模态向量** (Collection: `multimodal`)
   ```json
   {
     "id": "multimodal_uuid",
     "vector": [512维],
     "payload": {
       "type": "image|diagram|video",
       "source": "minio_object_path",
       "description": "架构图、流程图等",
       "related_entities": ["entity_id1", "entity_id2"]
     }
   }
   ```

**查询能力**:
- Top-K相似度搜索
- 过滤条件搜索（payload过滤）
- 混合搜索（向量+关键词）
- 多向量查询（多模态）

**性能指标**:
- 向量容量: 1000万+
- 查询延迟: <50ms (Top-10)
- 召回率: >95%
- QPS: >1000

---

#### 1.2.3 PostgreSQL - 关系数据库（现有）

**核心能力**: 事务处理、关系查询、聚合统计

**存储内容**:

1. **业务数据表**
   ```sql
   -- 用户和权限
   users, user_roles, permissions

   -- 知识库管理
   knowledge_bases, documents, document_chunks

   -- 工作流
   workflows, workflow_executions, workflow_steps

   -- 智能体
   agents, agent_configs, agent_executions
   ```

2. **元数据表**
   ```sql
   -- 元数据分类
   metadata_classifications (id, name, type, parent_id)

   -- 元数据实体
   metadata_entities (id, classification_id, name, type, properties)

   -- 实体关系
   metadata_relationships (id, source_id, target_id, type, properties)

   -- SAP元数据
   sap_metadata (id, object_type, object_name, metadata)
   ```

3. **企业架构表（新增）**
   ```sql
   -- 业务架构
   CREATE TABLE business_processes (
     id UUID PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     description TEXT,
     owner VARCHAR(255),
     status VARCHAR(50),
     level INTEGER,
     parent_id UUID REFERENCES business_processes(id),
     neo4j_node_id VARCHAR(255), -- 关联Neo4j节点
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE business_capabilities (
     id UUID PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     description TEXT,
     level INTEGER,
     parent_id UUID REFERENCES business_capabilities(id),
     neo4j_node_id VARCHAR(255),
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE business_services (
     id UUID PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     description TEXT,
     endpoint VARCHAR(500),
     status VARCHAR(50),
     neo4j_node_id VARCHAR(255),
     created_at TIMESTAMP DEFAULT NOW()
   );

   -- 应用架构
   CREATE TABLE application_systems (
     id UUID PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     description TEXT,
     type VARCHAR(100),
     status VARCHAR(50),
     version VARCHAR(50),
     owner VARCHAR(255),
     neo4j_node_id VARCHAR(255),
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE application_services (
     id UUID PRIMARY KEY,
     application_id UUID REFERENCES application_systems(id),
     name VARCHAR(255) NOT NULL,
     protocol VARCHAR(50),
     endpoint VARCHAR(500),
     neo4j_node_id VARCHAR(255),
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE api_interfaces (
     id UUID PRIMARY KEY,
     service_id UUID REFERENCES application_services(id),
     path VARCHAR(500) NOT NULL,
     method VARCHAR(10) NOT NULL,
     description TEXT,
     neo4j_node_id VARCHAR(255),
     created_at TIMESTAMP DEFAULT NOW()
   );

   -- 数据架构
   CREATE TABLE data_entities (
     id UUID PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     description TEXT,
     schema JSONB,
     type VARCHAR(100),
     neo4j_node_id VARCHAR(255),
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE data_models (
     id UUID PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     version VARCHAR(50),
     definition JSONB,
     neo4j_node_id VARCHAR(255),
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE data_flows (
     id UUID PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     source_entity_id UUID REFERENCES data_entities(id),
     target_entity_id UUID REFERENCES data_entities(id),
     transformation TEXT,
     neo4j_node_id VARCHAR(255),
     created_at TIMESTAMP DEFAULT NOW()
   );

   -- 技术架构
   CREATE TABLE technology_components (
     id UUID PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     type VARCHAR(100),
     version VARCHAR(50),
     description TEXT,
     neo4j_node_id VARCHAR(255),
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE technology_stacks (
     id UUID PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     category VARCHAR(100),
     components JSONB,
     neo4j_node_id VARCHAR(255),
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE infrastructure_components (
     id UUID PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     type VARCHAR(100),
     specifications JSONB,
     neo4j_node_id VARCHAR(255),
     created_at TIMESTAMP DEFAULT NOW()
   );

   -- 架构关系表
   CREATE TABLE architecture_relationships (
     id UUID PRIMARY KEY,
     source_id UUID NOT NULL,
     source_type VARCHAR(100) NOT NULL,
     target_id UUID NOT NULL,
     target_type VARCHAR(100) NOT NULL,
     relationship_type VARCHAR(100) NOT NULL,
     properties JSONB,
     neo4j_relationship_id VARCHAR(255),
     created_at TIMESTAMP DEFAULT NOW()
   );
   ```

4. **配置和系统表**
   ```sql
   -- 系统配置
   system_configs, service_registry, health_checks

   -- 审计日志
   audit_logs, operation_logs, access_logs
   ```

**查询能力**:
- 复杂SQL查询
- 事务ACID保证
- 聚合统计分析
- 全文搜索（pg_trgm）

**性能指标**:
- 数据容量: 1TB+
- 查询延迟: <100ms
- TPS: 10000+
- 事务隔离: READ COMMITTED

---

#### 1.2.4 MinIO - 对象存储（现有）

**核心能力**: 大文件存储、多媒体管理

**存储内容**:

1. **文档文件** (Bucket: `documents`)
   ```
   documents/
   ├── {kb_id}/
   │   ├── {doc_id}.pdf
   │   ├── {doc_id}.docx
   │   ├── {doc_id}.md
   │   └── ...
   ```

2. **企业架构文档** (Bucket: `ea-documents`)
   ```
   ea-documents/
   ├── business-architecture/
   │   ├── process_diagrams/
   │   ├── capability_maps/
   │   └── org_charts/
   ├── application-architecture/
   │   ├── architecture_diagrams/
   │   ├── integration_diagrams/
   │   └── api_docs/
   ├── data-architecture/
   │   ├── data_models/
   │   ├── data_flow_diagrams/
   │   └── data_dictionaries/
   └── technology-architecture/
       ├── infrastructure_diagrams/
       ├── network_diagrams/
       └── tech_stack_docs/
   ```

3. **多媒体文件** (Bucket: `media`)
   ```
   media/
   ├── images/
   ├── videos/
   └── diagrams/
   ```

4. **备份文件** (Bucket: `backups`)
   ```
   backups/
   ├── database/
   ├── graphs/
   └── vectors/
   ```

**访问模式**:
- 上传: POST /api/v1/documents/upload
- 下载: GET /api/v1/documents/{doc_id}/download
- 预览: GET /api/v1/documents/{doc_id}/preview
- 删除: DELETE /api/v1/documents/{doc_id}

**性能指标**:
- 对象容量: 无限
- 上传速度: >100MB/s
- 下载速度: >500MB/s
- 可用性: 99.99%

---

### 1.3 数据库协同工作模式

#### 1.3.1 写入协同

**文档上传流程**:
```
1. 用户上传文档 (PDF/DOCX)
   ↓
2. MinIO存储原始文件
   ↓
3. PostgreSQL记录文档元数据
   ↓
4. 文档解析和分块
   ↓
5. Qdrant存储文档向量
   ↓
6. 提取实体和关系
   ↓
7. Neo4j存储知识图谱
```

**企业架构数据创建流程**:
```
1. 创建架构实体 (Business Process)
   ↓
2. PostgreSQL写入业务数据表 (business_processes)
   ↓
3. Neo4j创建图谱节点 (:BusinessProcess)
   ↓
4. 记录关联关系 (neo4j_node_id)
   ↓
5. 实体描述向量化
   ↓
6. Qdrant存储实体向量 (Collection: entities)
```

#### 1.3.2 查询协同

**简单查询** (单数据库):
```
查询: "获取所有业务流程列表"
PostgreSQL → SELECT * FROM business_processes
```

**语义搜索** (两数据库协同):
```
查询: "采购相关的业务流程"
1. Qdrant向量搜索 → 返回相关实体ID
2. PostgreSQL获取详细数据 → SELECT * WHERE id IN (...)
```

**关系查询** (两数据库协同):
```
查询: "哪些应用系统使用了这个数据实体？"
1. Neo4j图遍历查询:
   MATCH (d:DataEntity {id: $entity_id})<-[:USES]-(a:ApplicationSystem)
   RETURN a
2. PostgreSQL获取应用详细信息:
   SELECT * FROM application_systems WHERE neo4j_node_id IN (...)
```

**复杂查询** (三引擎融合):
```
查询: "采购订单审批流程涉及哪些系统和数据？"

1. LLM Engine: 理解查询意图
   → 识别: "采购订单审批流程"
   → 分析: 需要业务流程、应用系统、数据实体

2. Semantic Engine: 语义增强
   → Qdrant搜索相似实体
   → 返回: [采购流程, 审批流程, 订单管理]

3. Neo4j Engine: 图谱检索
   → 查询:
     MATCH path = (bp:BusinessProcess {name: "采购订单审批"})
       -[:IMPLEMENTED_BY]->(app:ApplicationSystem)
       -[:USES]->(de:DataEntity)
     RETURN path

4. PostgreSQL: 获取详细数据
   → 业务流程详情
   → 应用系统配置
   → 数据实体schema

5. Context Builder: 构建上下文
   → 整合图谱、文档、元数据
   → 格式化为LLM友好格式

6. LLM Generator: 生成答案
   → 基于知识增强生成
   → 包含完整推理路径
   → 可追溯知识来源
```

---

### 1.4 数据一致性保证

#### 1.4.1 双写策略

**PostgreSQL + Neo4j双写**:
```python
class DualWriteRepository:
    async def create_business_process(self, data: BusinessProcessCreate):
        async with transaction():
            # 1. 写入PostgreSQL
            pg_record = await self.pg.execute(
                "INSERT INTO business_processes (name, description, ...) "
                "VALUES ($1, $2, ...) RETURNING id",
                data.name, data.description
            )

            # 2. 写入Neo4j
            neo4j_node = await self.neo4j.execute("""
                CREATE (bp:BusinessProcess {
                    uuid: $uuid,
                    name: $name,
                    description: $description
                })
                RETURN id(bp) AS node_id
            """, uuid=str(pg_record.id), name=data.name, description=data.description)

            # 3. 更新PostgreSQL关联ID
            await self.pg.execute(
                "UPDATE business_processes SET neo4j_node_id = $1 WHERE id = $2",
                str(neo4j_node.node_id), pg_record.id
            )

            # 4. 向量化并写入Qdrant
            vector = await self.vectorizer.vectorize(f"{data.name} {data.description}")
            await self.qdrant.upsert(
                collection_name="entities",
                points=[{
                    "id": str(pg_record.id),
                    "vector": vector,
                    "payload": {
                        "entity_id": str(pg_record.id),
                        "neo4j_node_id": str(neo4j_node.node_id),
                        "name": data.name,
                        "type": "BusinessProcess"
                    }
                }]
            )

            return pg_record
```

#### 1.4.2 一致性检查

**定期一致性检查**:
```python
class ConsistencyChecker:
    async def check_pg_neo4j_consistency(self):
        """检查PostgreSQL和Neo4j数据一致性"""

        # 1. 统计数量一致性
        pg_count = await self.pg.fetchval(
            "SELECT COUNT(*) FROM business_processes WHERE neo4j_node_id IS NOT NULL"
        )

        neo4j_count = await self.neo4j.execute(
            "MATCH (bp:BusinessProcess) RETURN count(bp) AS count"
        )

        if pg_count != neo4j_count.count:
            logger.warning(f"数量不一致: PG={pg_count}, Neo4j={neo4j_count}")
            await self.reconcile()

        # 2. 抽样检查数据一致性
        sample_ids = await self.get_random_ids(100)

        for record_id in sample_ids:
            pg_data = await self.pg.fetchrow(
                "SELECT * FROM business_processes WHERE id = $1", record_id
            )

            neo4j_data = await self.neo4j.execute("""
                MATCH (bp:BusinessProcess {uuid: $uuid})
                RETURN bp
            """, uuid=str(record_id))

            if not self.compare_data(pg_data, neo4j_data):
                logger.warning(f"数据不一致: ID={record_id}")
                await self.reconcile_record(record_id)
```

#### 1.4.3 降级策略

**Neo4j故障降级**:
```python
class FallbackQueryService:
    async def query_with_fallback(self, query: str):
        try:
            # 尝试Neo4j图查询
            return await self.neo4j_service.query(query)
        except Neo4jError as e:
            logger.warning(f"Neo4j查询失败，降级到PostgreSQL: {e}")

            # 降级到PostgreSQL关系查询
            return await self.postgresql_service.query_relationships(query)
```

---

## 2. 五层EA-OS架构详细设计

### 2.1 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                   第一层：企业智能门户层                          │
│                  (Enterprise Intelligence Portal)                │
│  ┌───────────┐  ┌───────────────────────┐  ┌──────────────────┐ │
│  │ 左固定面板 │  │   富内容对话区          │  │  右智能辅助面板   │ │
│  │ - 工作空间 │  │   - 文本消息           │  │  - 上下文信息    │ │
│  │ - 快捷入口 │  │   - 操作卡片           │  │  - 智能推荐      │ │
│  │ - 收藏夹   │  │   - 数据图表           │  │  - 架构视图      │ │
│  │ - 最近使用 │  │   - 工作流进度         │  │  - 关系探索      │ │
│  └───────────┘  │   - 知识引用           │  └──────────────────┘ │
│                 │   - 架构图谱           │                       │
│                 └───────────────────────┘                       │
│                      (web-ui: 3000)                              │
└─────────────────────────────────────────────────────────────────┘
                             ↕ WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                   第二层：对话智能网关层                          │
│               (Conversation Intelligence Gateway)                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │  会话管理器   │ │  意图识别器   │ │  格式转换器   │           │
│  │SessionManager│ │IntentAnalyzer│ │FormatConverter│          │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │  知识注入器   │ │  流式响应器   │ │  路由决策器   │           │
│  │KnowledgeInj..│ │StreamResponder│ │RoutingDecision│          │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│             (api-gateway增强: 8080)                              │
└─────────────────────────────────────────────────────────────────┘
                             ↕ HTTP/gRPC
┌─────────────────────────────────────────────────────────────────┐
│                 第三层：企业架构智能层 (新增)                      │
│               (Enterprise Architecture Intelligence)             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    EA Core Service (8014)                 │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐  │  │
│  │  │业务语义理解   │ │架构映射引擎   │ │执行路径规划    │  │  │
│  │  │BusinessSemantic│ │ArchMapping   │ │PathPlanning    │  │  │
│  │  └──────────────┘ └──────────────┘ └─────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │             智能编排服务 (8016)                           │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐  │  │
│  │  │任务分解      │ │资源调度      │ │执行监控         │  │  │
│  │  │TaskDecompose │ │ResourceSchedule│ │ExecutionMonitor│  │  │
│  │  └──────────────┘ └──────────────┘ └─────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                   (整合dag-orchestrator功能)                     │
└─────────────────────────────────────────────────────────────────┘
                             ↕ HTTP/gRPC
┌─────────────────────────────────────────────────────────────────┐
│                    第四层：AI能力服务层                           │
│                  (AI Capability Services Layer)                  │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐             │
│  │agent-service│ │workflow-eng │ │knowledge-base│             │
│  │   (8010)    │ │   (8002)    │ │    (8004)    │             │
│  └─────────────┘ └─────────────┘ └──────────────┘             │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐             │
│  │mcp-gateway  │ │metadata-svc │ │memory-service│             │
│  │   (8001)    │ │   (8005)    │ │    (8013)    │             │
│  └─────────────┘ └─────────────┘ └──────────────┘             │
│                         (现有15个AI服务)                         │
└─────────────────────────────────────────────────────────────────┘
                             ↕
┌─────────────────────────────────────────────────────────────────┐
│               第五层：专业工具与基础设施层                         │
│            (Professional Tools & Infrastructure)                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────┐ │
│  │  Neo4j     │ │  Qdrant    │ │ PostgreSQL │ │   MinIO     │ │
│  │  (7474)    │ │  (6333)    │ │   (5432)   │ │   (9000)    │ │
│  │图数据库     │ │向量数据库   │ │关系数据库   │ │对象存储      │ │
│  └────────────┘ └────────────┘ └────────────┘ └─────────────┘ │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                 │
│  │  Redis     │ │  Registry  │ │Config-Ctr  │                 │
│  │  (6379)    │ │  (8000)    │ │   (8090)   │                 │
│  │缓存和队列   │ │服务注册     │ │配置中心     │                 │
│  └────────────┘ └────────────┘ └────────────┘                 │
│                                                                 │
│  专业工具 (8050-8059, 可选):                                     │
│  - 工作流设计器 (8050)                                           │
│  - 智能体工作室 (8051)                                           │
│  - 知识库管理器 (8052)                                           │
│  - 架构设计器 (8053)                                             │
│  - 数据分析台 (8054)                                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 第一层：企业智能门户层详细设计

#### 2.2.1 总体布局

**三栏布局设计**:
```tsx
// web-ui/src/layouts/MainLayout.tsx
export default function MainLayout() {
  return (
    <div className="flex h-screen">
      {/* 左侧固定面板 */}
      <LeftSidebar width={280} />

      {/* 中间富内容对话区 */}
      <ConversationArea flex={1} />

      {/* 右侧智能辅助面板 */}
      <RightPanel width={360} collapsible />
    </div>
  )
}
```

#### 2.2.2 左侧固定面板

**个人工作空间**:
```tsx
// web-ui/src/components/LeftSidebar.tsx
export function LeftSidebar() {
  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* 用户信息 */}
      <UserProfile />

      {/* 工作空间导航 */}
      <WorkspaceNavigation>
        <NavItem icon="🏠" label="首页" path="/" />
        <NavItem icon="💬" label="对话" path="/chat" />
        <NavItem icon="📚" label="知识库" path="/knowledge-bases" />
        <NavItem icon="🏗️" label="企业架构" path="/enterprise-architecture" />
        <NavItem icon="📊" label="工作流" path="/workflows" />
        <NavItem icon="🤖" label="智能体" path="/agents" />
        <NavItem icon="🔧" label="工具" path="/tools" />
      </WorkspaceNavigation>

      {/* 快捷入口 */}
      <QuickAccess>
        <QuickItem label="新建对话" action="newChat" />
        <QuickItem label="上传文档" action="uploadDoc" />
        <QuickItem label="创建工作流" action="newWorkflow" />
      </QuickAccess>

      {/* 收藏夹 */}
      <Favorites items={favorites} />

      {/* 最近使用 */}
      <RecentItems items={recentItems} />
    </div>
  )
}
```

#### 2.2.3 中间富内容对话区

**消息类型定义**:
```typescript
// web-ui/src/types/messages.ts
type MessageType =
  | 'text'              // 纯文本消息
  | 'markdown'          // Markdown格式文本
  | 'card'              // 操作卡片
  | 'chart'             // 数据图表
  | 'workflow'          // 工作流进度
  | 'knowledge'         // 知识引用
  | 'graph'             // 知识图谱
  | 'architecture'      // 架构图谱
  | 'code'              // 代码块
  | 'table'             // 表格数据
  | 'form'              // 表单输入

interface Message {
  id: string
  type: MessageType
  role: 'user' | 'assistant' | 'system'
  content: MessageContent
  metadata?: {
    sources?: Source[]
    reasoning_path?: ReasoningPath
    confidence?: number
    timestamp?: string
  }
}
```

**富内容渲染器**:
```tsx
// web-ui/src/components/MessageRenderer.tsx
export function MessageRenderer({ message }: { message: Message }) {
  switch (message.type) {
    case 'text':
      return <TextMessage content={message.content} />

    case 'card':
      return <ActionCard data={message.content} />

    case 'chart':
      return <ChartVisualization data={message.content} />

    case 'workflow':
      return <WorkflowProgress data={message.content} />

    case 'knowledge':
      return <KnowledgeReference data={message.content} />

    case 'graph':
      return <KnowledgeGraphViewer data={message.content} />

    case 'architecture':
      return <ArchitectureGraphViewer data={message.content} />

    default:
      return <TextMessage content={message.content} />
  }
}
```

**操作卡片示例**:
```tsx
// 示例：采购订单卡片
<ActionCard>
  <CardHeader>
    <Icon>📦</Icon>
    <Title>采购订单 PO-2025-001</Title>
    <Status color="green">已审批</Status>
  </CardHeader>

  <CardContent>
    <InfoRow label="供应商">ABC供应商</InfoRow>
    <InfoRow label="金额">¥150,000</InfoRow>
    <InfoRow label="日期">2025-12-06</InfoRow>
    <InfoRow label="物料">电脑配件 x 100</InfoRow>
  </CardContent>

  <CardActions>
    <Button variant="primary">查看详情</Button>
    <Button variant="secondary">查看流程</Button>
    <Button variant="text">相关订单</Button>
  </CardActions>

  <CardFooter>
    <KnowledgeSource>来自SAP MM系统</KnowledgeSource>
  </CardFooter>
</ActionCard>
```

**架构图谱可视化**:
```tsx
// 企业架构图谱展示
<ArchitectureGraphViewer>
  <GraphCanvas>
    {/* 业务流程节点 */}
    <Node id="bp1" type="BusinessProcess" label="采购审批流程" />

    {/* 应用系统节点 */}
    <Node id="app1" type="ApplicationSystem" label="SAP MM" />
    <Node id="app2" type="ApplicationSystem" label="OA审批系统" />

    {/* 数据实体节点 */}
    <Node id="data1" type="DataEntity" label="采购订单" />

    {/* 关系边 */}
    <Edge source="bp1" target="app1" label="IMPLEMENTED_BY" />
    <Edge source="app1" target="data1" label="USES" />
    <Edge source="bp1" target="app2" label="REQUIRES" />
  </GraphCanvas>

  <GraphLegend>
    <LegendItem color="blue">业务流程</LegendItem>
    <LegendItem color="green">应用系统</LegendItem>
    <LegendItem color="orange">数据实体</LegendItem>
  </GraphLegend>

  <GraphToolbar>
    <ToolButton icon="zoom-in">放大</ToolButton>
    <ToolButton icon="zoom-out">缩小</ToolButton>
    <ToolButton icon="fullscreen">全屏</ToolButton>
    <ToolButton icon="export">导出</ToolButton>
  </GraphToolbar>
</ArchitectureGraphViewer>
```

#### 2.2.4 右侧智能辅助面板

**上下文智能面板**:
```tsx
// web-ui/src/components/RightPanel.tsx
export function RightPanel() {
  return (
    <div className="flex flex-col h-full bg-white border-l">
      {/* 面板标签 */}
      <Tabs defaultValue="context">
        <TabsList>
          <Tab value="context">上下文</Tab>
          <Tab value="recommendations">推荐</Tab>
          <Tab value="architecture">架构</Tab>
          <Tab value="knowledge">知识</Tab>
        </TabsList>

        {/* 上下文信息 */}
        <TabPanel value="context">
          <ContextInfo>
            <Section title="当前对话">
              <InfoItem label="主题">采购流程咨询</InfoItem>
              <InfoItem label="轮数">15</InfoItem>
              <InfoItem label="知识库">SAP MM知识库</InfoItem>
            </Section>

            <Section title="相关实体">
              <EntityChip type="BusinessProcess">采购审批流程</EntityChip>
              <EntityChip type="Application">SAP MM</EntityChip>
              <EntityChip type="DataEntity">采购订单</EntityChip>
            </Section>

            <Section title="架构视图">
              <MiniArchitectureMap />
            </Section>
          </ContextInfo>
        </TabPanel>

        {/* 智能推荐 */}
        <TabPanel value="recommendations">
          <RecommendationList>
            <RecommendationCard>
              <Icon>📄</Icon>
              <Title>相关文档</Title>
              <Description>SAP MM采购流程配置指南</Description>
              <Action>查看</Action>
            </RecommendationCard>

            <RecommendationCard>
              <Icon>🔍</Icon>
              <Title>相似问题</Title>
              <Description>如何在SAP中创建采购订单？</Description>
              <Action>查看答案</Action>
            </RecommendationCard>

            <RecommendationCard>
              <Icon>🏗️</Icon>
              <Title>架构关系</Title>
              <Description>采购流程涉及3个系统，5个数据实体</Description>
              <Action>查看架构</Action>
            </RecommendationCard>
          </RecommendationList>
        </TabPanel>

        {/* 架构探索 */}
        <TabPanel value="architecture">
          <ArchitectureExplorer>
            <Section title="业务架构">
              <TreeView>
                <TreeNode label="采购管理" expandable>
                  <TreeNode label="采购申请" />
                  <TreeNode label="采购审批" />
                  <TreeNode label="采购订单" />
                </TreeNode>
              </TreeView>
            </Section>

            <Section title="应用架构">
              <ApplicationList>
                <AppItem name="SAP MM" status="运行中" />
                <AppItem name="OA系统" status="运行中" />
                <AppItem name="供应商门户" status="运行中" />
              </ApplicationList>
            </Section>
          </ArchitectureExplorer>
        </TabPanel>

        {/* 知识图谱 */}
        <TabPanel value="knowledge">
          <KnowledgeGraphMini>
            <MiniGraph nodes={nodes} edges={edges} />
            <GraphStats>
              <Stat label="节点" value="156" />
              <Stat label="关系" value="342" />
              <Stat label="深度" value="3跳" />
            </GraphStats>
          </KnowledgeGraphMini>
        </TabPanel>
      </Tabs>
    </div>
  )
}
```

#### 2.2.5 WebSocket实时通信

**WebSocket连接管理**:
```typescript
// web-ui/src/lib/websocket.ts
export class ConversationWebSocket {
  private ws: WebSocket
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  constructor(private conversationId: string) {
    this.connect()
  }

  private connect() {
    this.ws = new WebSocket(
      `ws://localhost:8080/ws/conversations/${this.conversationId}`
    )

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    }

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      this.handleMessage(message)
    }

    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      this.reconnect()
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  private handleMessage(message: WSMessage) {
    switch (message.type) {
      case 'stream_start':
        // 流式响应开始
        break

      case 'stream_chunk':
        // 接收流式内容片段
        this.appendChunk(message.content)
        break

      case 'stream_end':
        // 流式响应结束
        this.finalizeMessage(message.metadata)
        break

      case 'rich_content':
        // 富内容消息（卡片、图表等）
        this.renderRichContent(message.content)
        break

      case 'knowledge_reference':
        // 知识引用
        this.showKnowledgeSource(message.sources)
        break

      case 'architecture_graph':
        // 架构图谱
        this.renderArchitectureGraph(message.graph)
        break
    }
  }

  sendMessage(content: string) {
    this.ws.send(JSON.stringify({
      type: 'user_message',
      content: content,
      timestamp: new Date().toISOString()
    }))
  }

  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => this.connect(), 2000 * this.reconnectAttempts)
    }
  }
}
```

---

### 2.3 第二层：对话智能网关层详细设计

#### 2.3.1 网关架构

**增强的API Gateway**:
```python
# api-gateway/src/core/conversation_gateway.py

class ConversationIntelligenceGateway:
    """对话智能网关核心"""

    def __init__(
        self,
        session_manager: SessionManager,
        intent_analyzer: IntentAnalyzer,
        format_converter: FormatConverter,
        knowledge_injector: KnowledgeInjector,
        stream_responder: StreamResponder,
        routing_decision: RoutingDecision
    ):
        self.session_manager = session_manager
        self.intent_analyzer = intent_analyzer
        self.format_converter = format_converter
        self.knowledge_injector = knowledge_injector
        self.stream_responder = stream_responder
        self.routing_decision = routing_decision

    async def process_message(
        self,
        conversation_id: str,
        message: UserMessage,
        websocket: WebSocket
    ) -> None:
        """处理用户消息（流式响应）"""

        try:
            # 1. 获取/创建会话
            session = await self.session_manager.get_or_create(conversation_id)

            # 2. 意图识别
            intent = await self.intent_analyzer.analyze(
                message.content,
                session.context
            )

            # 3. 路由决策
            target_service = self.routing_decision.decide(intent)

            # 4. 调用后端服务（流式）
            async for chunk in self._call_service_stream(
                target_service, message, intent, session
            ):
                # 5. 知识注入（实时）
                enriched_chunk = await self.knowledge_injector.enrich_chunk(
                    chunk, intent
                )

                # 6. 格式转换
                formatted_chunk = await self.format_converter.convert_chunk(
                    enriched_chunk
                )

                # 7. 流式发送
                await self.stream_responder.send_chunk(
                    websocket, formatted_chunk
                )

            # 8. 更新会话
            await self.session_manager.update(session, message, response)

        except Exception as e:
            logger.error(f"消息处理失败: {e}")
            await self.stream_responder.send_error(websocket, str(e))
```

#### 2.3.2 会话管理器

**会话状态管理**:
```python
# api-gateway/src/services/session_manager.py

class SessionManager:
    """会话管理器"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = 3600  # 1小时

    async def get_or_create(self, conversation_id: str) -> Session:
        """获取或创建会话"""

        # 从Redis获取会话
        session_data = await self.redis.get(f"session:{conversation_id}")

        if session_data:
            return Session.parse_raw(session_data)

        # 创建新会话
        session = Session(
            id=conversation_id,
            created_at=datetime.now(),
            context=ConversationContext(),
            messages=[],
            metadata={}
        )

        # 保存到Redis
        await self.redis.setex(
            f"session:{conversation_id}",
            self.ttl,
            session.json()
        )

        return session

    async def update(
        self,
        session: Session,
        user_message: UserMessage,
        assistant_response: AssistantMessage
    ):
        """更新会话状态"""

        # 添加消息到历史
        session.messages.append(user_message)
        session.messages.append(assistant_response)

        # 更新上下文
        session.context.update_from_messages([user_message, assistant_response])

        # 更新元数据
        session.metadata["last_updated"] = datetime.now().isoformat()
        session.metadata["message_count"] = len(session.messages)

        # 保存到Redis
        await self.redis.setex(
            f"session:{session.id}",
            self.ttl,
            session.json()
        )
```

#### 2.3.3 意图识别器

**意图分析**:
```python
# api-gateway/src/services/intent_analyzer.py

class IntentAnalyzer:
    """意图识别器"""

    def __init__(
        self,
        llm_client: LLMClient,
        semantic_engine: SemanticEngineClient
    ):
        self.llm = llm_client
        self.semantic = semantic_engine

    async def analyze(
        self,
        message: str,
        context: ConversationContext
    ) -> Intent:
        """分析用户意图"""

        # 1. LLM理解意图
        llm_analysis = await self.llm.analyze(message, context, prompt="""
        分析用户意图，输出JSON：
        {{
            "intent_type": "query|action|exploration|analysis",
            "domain": "business|application|data|technology",
            "entities": ["实体1", "实体2"],
            "action": "search|create|update|delete|analyze",
            "parameters": {{}},
            "requires_ea": true/false,
            "requires_graph": true/false
        }}
        """)

        # 2. 语义增强
        semantic_context = await self.semantic.enhance(message, llm_analysis)

        # 3. 构建意图对象
        intent = Intent(
            type=llm_analysis["intent_type"],
            domain=llm_analysis["domain"],
            entities=llm_analysis["entities"],
            action=llm_analysis["action"],
            parameters=llm_analysis["parameters"],
            requires_ea=llm_analysis["requires_ea"],
            requires_graph=llm_analysis["requires_graph"],
            semantic_context=semantic_context
        )

        return intent
```

#### 2.3.4 路由决策器

**智能路由**:
```python
# api-gateway/src/services/routing_decision.py

class RoutingDecision:
    """路由决策器"""

    def decide(self, intent: Intent) -> TargetService:
        """决策路由目标"""

        # 规则1: EA相关查询路由到EA Core
        if intent.requires_ea:
            return TargetService(
                name="ea-core",
                endpoint="http://ea-core:8014",
                method="POST",
                path="/api/v1/ea/query"
            )

        # 规则2: 图谱查询路由到Knowledge Base（GraphRAG）
        if intent.requires_graph:
            return TargetService(
                name="knowledge-base",
                endpoint="http://knowledge-base:8004",
                method="POST",
                path="/api/v1/graph/query"
            )

        # 规则3: 工作流相关路由到Workflow Engine
        if intent.domain == "workflow":
            return TargetService(
                name="workflow-engine",
                endpoint="http://workflow-engine:8002",
                method="POST",
                path="/api/v1/workflows/execute"
            )

        # 规则4: 智能体相关路由到Agent Service
        if intent.type == "action" and intent.action == "execute":
            return TargetService(
                name="agent-service",
                endpoint="http://agent-service:8010",
                method="POST",
                path="/api/v1/agents/execute"
            )

        # 默认: 路由到统一问答服务
        return TargetService(
            name="agent-service",
            endpoint="http://agent-service:8010",
            method="POST",
            path="/api/v1/chat/completions"
        )
```

#### 2.3.5 知识注入器

**自动知识注入**:
```python
# api-gateway/src/services/knowledge_injector.py

class KnowledgeInjector:
    """知识注入器"""

    def __init__(
        self,
        kb_client: KnowledgeBaseClient,
        neo4j_client: Neo4jClient
    ):
        self.kb = kb_client
        self.neo4j = neo4j_client

    async def enrich_chunk(
        self,
        chunk: ResponseChunk,
        intent: Intent
    ) -> EnrichedChunk:
        """实时知识注入"""

        enriched = EnrichedChunk(
            content=chunk.content,
            metadata=chunk.metadata,
            knowledge_sources=[],
            architecture_context=None
        )

        # 如果是最终块，注入知识引用
        if chunk.is_final:
            # 1. 提取实体
            entities = await self._extract_entities(chunk.content)

            # 2. 查询相关知识
            knowledge_sources = await self.kb.search_related(
                entities=entities,
                top_k=3
            )

            enriched.knowledge_sources = knowledge_sources

            # 3. 如果涉及EA，查询架构上下文
            if intent.requires_ea:
                architecture_context = await self._get_architecture_context(
                    entities, intent.domain
                )
                enriched.architecture_context = architecture_context

        return enriched

    async def _get_architecture_context(
        self,
        entities: List[str],
        domain: str
    ) -> ArchitectureContext:
        """获取架构上下文"""

        # Neo4j查询相关架构
        result = await self.neo4j.query("""
            MATCH path = (start)-[*1..2]-(related)
            WHERE start.name IN $entities
            AND (
                start:BusinessProcess OR start:ApplicationSystem
                OR start:DataEntity OR start:TechnologyComponent
            )
            RETURN path
            LIMIT 20
        """, entities=entities)

        # 构建架构上下文
        context = ArchitectureContext(
            domain=domain,
            entities=[],
            relationships=[],
            mini_graph=result.to_graph()
        )

        return context
```

---

### 2.4 第三层：企业架构智能层详细设计

#### 2.4.1 EA Core Service架构

**新建服务**: `ea-core-service` (端口: 8014)

**目录结构**:
```
ea-core/
├── src/
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── query.py              # EA查询API
│   │   ├── analysis.py           # EA分析API
│   │   └── visualization.py      # EA可视化API
│   ├── core/
│   │   ├── __init__.py
│   │   ├── business_semantic_engine.py   # 业务语义理解
│   │   ├── architecture_mapping_engine.py # 架构映射
│   │   └── path_planning_engine.py       # 路径规划
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ea_query_service.py
│   │   ├── ea_analysis_service.py
│   │   └── ea_knowledge_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── pg_ea_repository.py   # PostgreSQL EA数据
│   │   └── neo4j_ea_repository.py # Neo4j EA图谱
│   └── models/
│       ├── __init__.py
│       ├── ea_models.py
│       └── ea_schemas.py
├── Dockerfile
├── requirements.txt
└── README.md
```

#### 2.4.2 业务语义理解引擎

**Business Semantic Engine**:
```python
# ea-core/src/core/business_semantic_engine.py

class BusinessSemanticEngine:
    """业务语义理解引擎"""

    def __init__(
        self,
        llm_client: LLMClient,
        neo4j_client: Neo4jClient,
        semantic_vectorizer: SemanticVectorizer
    ):
        self.llm = llm_client
        self.neo4j = neo4j_client
        self.vectorizer = semantic_vectorizer

    async def understand(
        self,
        user_query: str,
        context: Dict
    ) -> BusinessIntent:
        """理解业务意图"""

        # 阶段1: LLM初步理解
        llm_analysis = await self.llm.analyze(user_query, prompt="""
        分析业务查询，提取业务意图：

        查询：{query}

        输出JSON：
        {{
            "business_domain": "采购管理|销售管理|财务管理|人力资源|...",
            "business_capability": "订单管理|审批流程|报表分析|...",
            "business_process": "具体流程名称",
            "entities": [
                {{"name": "实体名", "type": "实体类型"}}
            ],
            "actions": ["查询", "创建", "更新", "分析"],
            "scope": "single_process|cross_process|domain_wide"
        }}
        """)

        # 阶段2: 从Neo4j检索业务架构
        business_arch = await self._retrieve_business_architecture(
            llm_analysis
        )

        # 阶段3: 语义向量匹配
        similar_cases = await self._find_similar_cases(user_query)

        # 阶段4: 融合理解结果
        business_intent = self._fuse_understanding(
            llm_analysis,
            business_arch,
            similar_cases,
            context
        )

        return business_intent

    async def _retrieve_business_architecture(
        self,
        llm_analysis: Dict
    ) -> BusinessArchitecture:
        """从Neo4j检索业务架构"""

        # Cypher查询业务架构
        result = await self.neo4j.query("""
            MATCH (domain:BusinessDomain {name: $domain_name})
            -[:HAS_CAPABILITY]->(cap:BusinessCapability {name: $capability_name})
            -[:IMPLEMENTS_PROCESS]->(process:BusinessProcess)
            -[:REQUIRES_DATA]->(data:DataEntity)
            OPTIONAL MATCH (process)-[:IMPLEMENTED_BY]->(app:ApplicationSystem)
            RETURN domain, cap, process, data, collect(app) AS applications
        """, {
            "domain_name": llm_analysis["business_domain"],
            "capability_name": llm_analysis["business_capability"]
        })

        return self._parse_business_arch(result)

    async def _find_similar_cases(self, query: str) -> List[Case]:
        """查找相似历史案例"""

        # 向量化查询
        query_vector = await self.vectorizer.vectorize(query)

        # Qdrant搜索相似历史查询
        similar = await self.qdrant.search(
            collection_name="query_history",
            query_vector=query_vector,
            limit=5,
            score_threshold=0.7
        )

        return [Case.from_qdrant(point) for point in similar]
```

#### 2.4.3 架构映射引擎

**Architecture Mapping Engine**:
```python
# ea-core/src/core/architecture_mapping_engine.py

class ArchitectureMappingEngine:
    """架构映射引擎"""

    def __init__(
        self,
        neo4j_client: Neo4jClient,
        pg_repository: PGEARepository
    ):
        self.neo4j = neo4j_client
        self.pg = pg_repository

    async def map_to_architecture(
        self,
        business_intent: BusinessIntent
    ) -> ArchitectureMapping:
        """将业务意图映射到技术架构"""

        mapping = ArchitectureMapping(
            business_layer=business_intent,
            application_layer=None,
            data_layer=None,
            technology_layer=None
        )

        # 1. 映射到应用架构
        if business_intent.business_process:
            application_systems = await self._map_to_applications(
                business_intent.business_process
            )
            mapping.application_layer = ApplicationLayerMapping(
                systems=application_systems,
                services=[],
                apis=[]
            )

        # 2. 映射到数据架构
        if mapping.application_layer:
            data_entities = await self._map_to_data(
                mapping.application_layer.systems
            )
            mapping.data_layer = DataLayerMapping(
                entities=data_entities,
                models=[],
                flows=[]
            )

        # 3. 映射到技术架构
        if mapping.data_layer:
            tech_components = await self._map_to_technology(
                mapping.data_layer.entities
            )
            mapping.technology_layer = TechnologyLayerMapping(
                components=tech_components,
                infrastructure=[],
                stacks=[]
            )

        return mapping

    async def _map_to_applications(
        self,
        business_process_id: str
    ) -> List[ApplicationSystem]:
        """映射业务流程到应用系统"""

        # Neo4j图查询
        result = await self.neo4j.query("""
            MATCH (bp:BusinessProcess {id: $process_id})
            -[:IMPLEMENTED_BY]->(app:ApplicationSystem)
            RETURN app
        """, process_id=business_process_id)

        # 获取详细信息from PostgreSQL
        app_ids = [r["app"]["uuid"] for r in result]
        applications = await self.pg.get_applications(app_ids)

        return applications

    async def _map_to_data(
        self,
        application_systems: List[ApplicationSystem]
    ) -> List[DataEntity]:
        """映射应用系统到数据实体"""

        app_ids = [app.neo4j_node_id for app in application_systems]

        # Neo4j图查询
        result = await self.neo4j.query("""
            MATCH (app:ApplicationSystem)-[:USES]->(de:DataEntity)
            WHERE id(app) IN $app_ids
            RETURN DISTINCT de
        """, app_ids=app_ids)

        # 获取详细信息
        entity_ids = [r["de"]["uuid"] for r in result]
        entities = await self.pg.get_data_entities(entity_ids)

        return entities

    async def _map_to_technology(
        self,
        data_entities: List[DataEntity]
    ) -> List[TechnologyComponent]:
        """映射数据实体到技术组件"""

        entity_ids = [entity.neo4j_node_id for entity in data_entities]

        # Neo4j图查询
        result = await self.neo4j.query("""
            MATCH (de:DataEntity)-[:STORED_IN]->(tc:TechnologyComponent)
            WHERE id(de) IN $entity_ids
            RETURN DISTINCT tc
        """, entity_ids=entity_ids)

        # 获取详细信息
        component_ids = [r["tc"]["uuid"] for r in result]
        components = await self.pg.get_technology_components(component_ids)

        return components
```

#### 2.4.4 执行路径规划引擎

**Path Planning Engine**:
```python
# ea-core/src/core/path_planning_engine.py

class PathPlanningEngine:
    """执行路径规划引擎"""

    def __init__(
        self,
        neo4j_client: Neo4jClient,
        orchestrator_client: OrchestratorClient
    ):
        self.neo4j = neo4j_client
        self.orchestrator = orchestrator_client

    async def plan_execution_path(
        self,
        business_intent: BusinessIntent,
        architecture_mapping: ArchitectureMapping
    ) -> ExecutionPlan:
        """规划执行路径"""

        plan = ExecutionPlan(
            intent=business_intent,
            mapping=architecture_mapping,
            steps=[],
            dependencies=[],
            estimated_duration=None
        )

        # 1. 根据业务意图分解任务
        tasks = self._decompose_tasks(business_intent)

        # 2. 为每个任务规划执行步骤
        for task in tasks:
            step = await self._plan_task_step(task, architecture_mapping)
            plan.steps.append(step)

        # 3. 分析步骤依赖关系
        plan.dependencies = self._analyze_dependencies(plan.steps)

        # 4. 优化执行顺序
        plan.steps = self._optimize_execution_order(
            plan.steps, plan.dependencies
        )

        # 5. 估算执行时间
        plan.estimated_duration = self._estimate_duration(plan.steps)

        return plan

    def _decompose_tasks(self, intent: BusinessIntent) -> List[Task]:
        """分解业务任务"""

        tasks = []

        if intent.action == "query":
            # 查询类任务
            tasks.append(Task(
                type="data_query",
                target=intent.entities[0] if intent.entities else None,
                action="fetch_data"
            ))

        elif intent.action == "create":
            # 创建类任务
            tasks.extend([
                Task(type="validate", action="validate_input"),
                Task(type="create", action="create_entity"),
                Task(type="notify", action="send_notification")
            ])

        elif intent.action == "analyze":
            # 分析类任务
            tasks.extend([
                Task(type="data_collection", action="collect_data"),
                Task(type="analysis", action="run_analysis"),
                Task(type="visualization", action="generate_charts")
            ])

        return tasks

    async def _plan_task_step(
        self,
        task: Task,
        mapping: ArchitectureMapping
    ) -> ExecutionStep:
        """规划任务执行步骤"""

        step = ExecutionStep(
            task=task,
            service=None,
            endpoint=None,
            parameters={},
            timeout=30
        )

        # 根据任务类型选择服务
        if task.type == "data_query":
            # 使用知识库服务
            step.service = "knowledge-base"
            step.endpoint = "/api/v1/search/semantic"
            step.timeout = 10

        elif task.type == "create":
            # 使用工作流引擎
            step.service = "workflow-engine"
            step.endpoint = "/api/v1/workflows/execute"
            step.timeout = 60

        elif task.type == "analysis":
            # 使用智能体服务
            step.service = "agent-service"
            step.endpoint = "/api/v1/agents/execute"
            step.timeout = 120

        return step

    def _analyze_dependencies(
        self,
        steps: List[ExecutionStep]
    ) -> List[Dependency]:
        """分析步骤依赖"""

        dependencies = []

        for i, step in enumerate(steps):
            for j, other_step in enumerate(steps):
                if i != j and self._has_dependency(step, other_step):
                    dependencies.append(Dependency(
                        from_step=j,
                        to_step=i,
                        type="output_to_input"
                    ))

        return dependencies

    def _optimize_execution_order(
        self,
        steps: List[ExecutionStep],
        dependencies: List[Dependency]
    ) -> List[ExecutionStep]:
        """优化执行顺序（拓扑排序）"""

        # 构建依赖图
        graph = self._build_dependency_graph(steps, dependencies)

        # 拓扑排序
        sorted_steps = self._topological_sort(graph)

        return sorted_steps
```

#### 2.4.5 智能编排服务

**新建服务**: `intelligent-orchestrator` (端口: 8016)

**智能编排器**:
```python
# intelligent-orchestrator/src/core/orchestrator.py

class IntelligentOrchestrator:
    """智能编排服务"""

    def __init__(
        self,
        dag_executor: DAGExecutor,
        agent_executor: AgentExecutor,
        resource_manager: ResourceManager
    ):
        self.dag_executor = dag_executor
        self.agent_executor = agent_executor
        self.resource_manager = resource_manager

    async def execute_plan(
        self,
        execution_plan: ExecutionPlan
    ) -> ExecutionResult:
        """执行规划的任务"""

        execution_id = str(uuid.uuid4())

        # 1. 任务分解
        tasks = self._convert_plan_to_tasks(execution_plan)

        # 2. 资源调度
        resources = await self.resource_manager.allocate(tasks)

        # 3. 构建DAG
        dag = self._build_dag(tasks, execution_plan.dependencies)

        # 4. 执行DAG
        result = await self.dag_executor.execute(
            dag=dag,
            resources=resources,
            execution_id=execution_id
        )

        return result

    def _build_dag(
        self,
        tasks: List[Task],
        dependencies: List[Dependency]
    ) -> DAG:
        """构建执行DAG"""

        dag = DAG(id=str(uuid.uuid4()))

        # 添加节点
        for task in tasks:
            node = DAGNode(
                id=task.id,
                type=task.type,
                executor=self._get_executor(task),
                parameters=task.parameters
            )
            dag.add_node(node)

        # 添加边
        for dep in dependencies:
            dag.add_edge(
                from_node=dep.from_step,
                to_node=dep.to_step
            )

        return dag
```

---

### 2.5 第四层：AI能力服务层详细设计

#### 2.5.1 服务适配改造

**现有AI服务**: 15个（agent-service、workflow-engine、knowledge-base等）

**改造要点**:
1. ✅ 增加EA上下文支持
2. ✅ 集成Neo4j图谱查询
3. ✅ 统一链路追踪
4. ✅ 架构感知能力

**改造示例 - Knowledge Base Service**:
```python
# knowledge-base/src/services/graphrag_service.py

class GraphRAGService:
    """图谱增强检索服务（新增）"""

    def __init__(
        self,
        neo4j_adapter: Neo4jAdapter,
        qdrant_client: QdrantClient,
        llm_client: LLMClient
    ):
        self.neo4j = neo4j_adapter
        self.qdrant = qdrant_client
        self.llm = llm_client

        # 初始化GraphRAG组件
        self.query_analyzer = GraphRAGQueryAnalyzer(llm_client)
        self.graph_retriever = GraphRetriever(neo4j_adapter)
        self.context_builder = GraphContextBuilder()
        self.llm_generator = GraphEnhancedLLMGenerator(llm_client)

    async def answer_with_graph(
        self,
        question: str,
        kb_id: Optional[str] = None,
        ea_context: Optional[EAContext] = None
    ) -> Answer:
        """使用图谱增强的问答"""

        # 阶段1: 查询分析
        query_plan = await self.query_analyzer.analyze(question)

        # 阶段2: 图谱检索
        subgraph = await self.graph_retriever.retrieve(query_plan)

        # 阶段3: 文档检索（传统RAG）
        documents = await self._retrieve_documents(question, kb_id)

        # 阶段4: 上下文构建（融合图谱+文档）
        context = self.context_builder.build_context(
            subgraph=subgraph,
            documents=documents,
            query=question,
            ea_context=ea_context
        )

        # 阶段5: LLM生成
        answer = await self.llm_generator.generate_answer(
            question=question,
            graph_context=context,
            documents=documents
        )

        return answer
```

**改造示例 - Agent Service**:
```python
# agent-service/src/core/ea_aware_agent.py

class EAAwareAgent:
    """架构感知的智能体（改造）"""

    async def execute(
        self,
        task: Task,
        ea_context: Optional[EAContext] = None
    ) -> ExecutionResult:
        """执行任务（带EA上下文）"""

        # 1. 注入EA上下文
        if ea_context:
            task = self._enrich_with_ea_context(task, ea_context)

        # 2. 执行任务
        result = await self._execute_task(task)

        # 3. 记录到EA图谱
        if ea_context:
            await self._record_to_ea_graph(ea_context, task, result)

        return result

    def _enrich_with_ea_context(
        self,
        task: Task,
        ea_context: EAContext
    ) -> Task:
        """用EA上下文增强任务"""

        # 添加架构信息到任务上下文
        task.context["architecture"] = {
            "business_process": ea_context.business_process,
            "application_systems": ea_context.applications,
            "data_entities": ea_context.data_entities
        }

        # 添加约束条件
        task.constraints.extend(ea_context.constraints)

        return task
```

---

### 2.6 第五层：专业工具与基础设施层详细设计

#### 2.6.1 数据库服务

**Neo4j配置**:
```yaml
# docker-compose.yml 新增
neo4j:
  image: neo4j:5-community
  container_name: enterprise-ai-neo4j
  environment:
    NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
    NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
    NEO4J_dbms_memory_heap_max__size: 8G
    NEO4J_dbms_memory_pagecache_size: 16G
    NEO4J_dbms_security_procedures_unrestricted: apoc.*,gds.*
  volumes:
    - neo4j_data:/data
    - neo4j_logs:/logs
    - neo4j_import:/import
  ports:
    - "7474:7474"  # HTTP
    - "7687:7687"  # Bolt
  healthcheck:
    test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_PASSWORD}", "RETURN 1"]
    interval: 10s
    timeout: 5s
    retries: 5
  networks:
    - enterprise-ai-network
  restart: unless-stopped

volumes:
  neo4j_data:
  neo4j_logs:
  neo4j_import:
```

#### 2.6.2 专业工具（可选）

**架构设计器** (8053):
```typescript
// 企业架构设计工具
class ArchitectureDesigner {
  // 可视化设计业务流程
  designBusinessProcess(process: BusinessProcess): void

  // 设计应用架构
  designApplicationArchitecture(apps: Application[]): void

  // 设计数据模型
  designDataModel(model: DataModel): void

  // 导出到Neo4j
  exportToNeo4j(): void
}
```

---

## 3. 企业架构功能完整实现

### 3.1 EA功能缺失填补计划

基于《企业架构功能缺失分析报告》，完整实现所有缺失功能：

#### 3.1.1 知识库文档

**创建EA知识库**:
```sql
-- 1. 创建企业架构知识库
INSERT INTO knowledge_bases (id, name, description, type)
VALUES
  ('ea-kb-001', '企业架构知识库', '企业架构总览和跨域知识', 'enterprise_architecture'),
  ('ea-kb-002', '业务架构知识库', '业务流程、能力、服务', 'business_architecture'),
  ('ea-kb-003', '应用架构知识库', '应用系统、服务、API', 'application_architecture'),
  ('ea-kb-004', '数据架构知识库', '数据模型、实体、流程', 'data_architecture'),
  ('ea-kb-005', '技术架构知识库', '技术栈、基础设施', 'technology_architecture');
```

**导入EA文档**:
```python
# scripts/import_ea_documents.py

async def import_ea_documents():
    """导入企业架构文档"""

    documents = [
        # 业务架构文档
        {
            "kb_id": "ea-kb-002",
            "title": "采购管理业务流程",
            "file_path": "ea-documents/business/procurement_process.pdf",
            "type": "business_process"
        },
        {
            "kb_id": "ea-kb-002",
            "title": "业务能力地图",
            "file_path": "ea-documents/business/capability_map.pdf",
            "type": "capability_map"
        },

        # 应用架构文档
        {
            "kb_id": "ea-kb-003",
            "title": "应用系统清单",
            "file_path": "ea-documents/application/system_inventory.xlsx",
            "type": "system_inventory"
        },
        {
            "kb_id": "ea-kb-003",
            "title": "应用集成架构",
            "file_path": "ea-documents/application/integration_architecture.pdf",
            "type": "integration_diagram"
        },

        # 数据架构文档
        {
            "kb_id": "ea-kb-004",
            "title": "企业数据模型",
            "file_path": "ea-documents/data/enterprise_data_model.pdf",
            "type": "data_model"
        },

        # 技术架构文档
        {
            "kb_id": "ea-kb-005",
            "title": "技术栈标准",
            "file_path": "ea-documents/technology/tech_stack.pdf",
            "type": "tech_standard"
        }
    ]

    for doc in documents:
        await upload_and_process_document(doc)
```

#### 3.1.2 元数据实体

**创建EA元数据**:
```python
# scripts/create_ea_metadata.py

async def create_ea_metadata():
    """创建企业架构元数据"""

    # 1. 创建元数据分类
    classifications = [
        {"name": "企业架构", "type": "enterprise_architecture", "parent": None},
        {"name": "业务架构", "type": "business_architecture", "parent": "企业架构"},
        {"name": "应用架构", "type": "application_architecture", "parent": "企业架构"},
        {"name": "数据架构", "type": "data_architecture", "parent": "企业架构"},
        {"name": "技术架构", "type": "technology_architecture", "parent": "企业架构"}
    ]

    for cls in classifications:
        await create_classification(cls)

    # 2. 创建业务架构实体
    business_entities = [
        {
            "classification": "业务架构",
            "type": "BusinessProcess",
            "name": "采购订单审批流程",
            "properties": {
                "owner": "采购部",
                "status": "active",
                "description": "采购订单创建到审批的完整流程"
            }
        },
        # ... 更多业务流程
    ]

    for entity in business_entities:
        await create_metadata_entity(entity)

    # 3. 创建应用架构实体
    application_entities = [
        {
            "classification": "应用架构",
            "type": "ApplicationSystem",
            "name": "SAP MM",
            "properties": {
                "type": "ERP",
                "version": "S/4HANA",
                "status": "running"
            }
        },
        # ... 更多应用系统
    ]

    for entity in application_entities:
        await create_metadata_entity(entity)

    # 4. 建立关系
    relationships = [
        {
            "source": "采购订单审批流程",
            "target": "SAP MM",
            "type": "IMPLEMENTED_BY"
        },
        # ... 更多关系
    ]

    for rel in relationships:
        await create_metadata_relationship(rel)
```

#### 3.1.3 知识图谱

**构建EA知识图谱**:
```python
# scripts/build_ea_knowledge_graph.py

async def build_ea_knowledge_graph():
    """构建企业架构知识图谱"""

    # 1. 从PostgreSQL读取EA实体
    business_processes = await pg.fetch("SELECT * FROM business_processes")
    applications = await pg.fetch("SELECT * FROM application_systems")
    data_entities = await pg.fetch("SELECT * FROM data_entities")
    tech_components = await pg.fetch("SELECT * FROM technology_components")

    # 2. 创建Neo4j节点
    for bp in business_processes:
        await neo4j.execute("""
            CREATE (bp:BusinessProcess {
                uuid: $uuid,
                name: $name,
                description: $description,
                owner: $owner,
                status: $status
            })
        """, bp)

    for app in applications:
        await neo4j.execute("""
            CREATE (app:ApplicationSystem {
                uuid: $uuid,
                name: $name,
                type: $type,
                version: $version,
                status: $status
            })
        """, app)

    # 3. 创建关系
    relationships = await pg.fetch("""
        SELECT * FROM architecture_relationships
    """)

    for rel in relationships:
        await neo4j.execute("""
            MATCH (source {uuid: $source_id})
            MATCH (target {uuid: $target_id})
            CREATE (source)-[r:$rel_type {
                properties: $properties
            }]->(target)
        """, rel)

    # 4. 创建索引
    await neo4j.execute("""
        CREATE CONSTRAINT entity_uuid_unique IF NOT EXISTS
        FOR (e:Entity) REQUIRE e.uuid IS UNIQUE;

        CREATE INDEX entity_name IF NOT EXISTS
        FOR (e:Entity) ON (e.name);

        CREATE FULLTEXT INDEX entity_search IF NOT EXISTS
        FOR (e:Entity) ON EACH [e.name, e.description];
    """)
```

#### 3.1.4 前端页面

**企业架构总览页**:
```tsx
// web-ui/src/app/enterprise-architecture/page.tsx

export default function EnterpriseArchitecturePage() {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">企业架构总览</h1>

      {/* 四个架构域卡片 */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <ArchitectureDomainCard
          domain="business"
          title="业务架构"
          icon="🏢"
          stats={{
            processes: 45,
            capabilities: 28,
            services: 52
          }}
          link="/enterprise-architecture/business"
        />

        <ArchitectureDomainCard
          domain="application"
          title="应用架构"
          icon="💻"
          stats={{
            systems: 23,
            services: 156,
            apis: 342
          }}
          link="/enterprise-architecture/application"
        />

        <ArchitectureDomainCard
          domain="data"
          title="数据架构"
          icon="🗄️"
          stats={{
            entities: 128,
            models: 34,
            flows: 89
          }}
          link="/enterprise-architecture/data"
        />

        <ArchitectureDomainCard
          domain="technology"
          title="技术架构"
          icon="⚙️"
          stats={{
            components: 67,
            stacks: 12,
            infrastructure: 45
          }}
          link="/enterprise-architecture/technology"
        />
      </div>

      {/* 架构健康度 */}
      <ArchitectureHealthDashboard />

      {/* 架构关系图 */}
      <ArchitectureRelationshipGraph />
    </div>
  )
}
```

**业务架构页面**:
```tsx
// web-ui/src/app/enterprise-architecture/business/page.tsx

export default function BusinessArchitecturePage() {
  const [processes, setProcesses] = useState([])
  const [selectedProcess, setSelectedProcess] = useState(null)

  return (
    <div className="flex h-full">
      {/* 左侧列表 */}
      <div className="w-1/3 border-r p-4">
        <h2 className="text-xl font-bold mb-4">业务流程</h2>
        <BusinessProcessTree
          processes={processes}
          onSelect={setSelectedProcess}
        />
      </div>

      {/* 右侧详情 */}
      <div className="flex-1 p-6">
        {selectedProcess && (
          <>
            <BusinessProcessDetail process={selectedProcess} />
            <BusinessProcessGraph processId={selectedProcess.id} />
            <RelatedApplications processId={selectedProcess.id} />
          </>
        )}
      </div>
    </div>
  )
}
```

#### 3.1.5 后端API

**EA API端点**:
```python
# ea-core/src/api/ea_query.py

from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1/ea", tags=["Enterprise Architecture"])

@router.get("/overview")
async def get_ea_overview() -> EAOverview:
    """获取企业架构总览"""
    return await ea_service.get_overview()

@router.get("/business")
async def get_business_architecture() -> BusinessArchitecture:
    """获取业务架构"""
    return await ea_service.get_business_architecture()

@router.get("/business/processes")
async def get_business_processes(
    parent_id: Optional[str] = None
) -> List[BusinessProcess]:
    """获取业务流程列表"""
    return await ea_service.get_business_processes(parent_id)

@router.get("/business/processes/{process_id}")
async def get_business_process(process_id: str) -> BusinessProcessDetail:
    """获取业务流程详情"""
    return await ea_service.get_business_process(process_id)

@router.get("/business/processes/{process_id}/graph")
async def get_process_graph(process_id: str) -> ProcessGraph:
    """获取业务流程关系图"""
    return await ea_service.get_process_graph(process_id)

@router.get("/application")
async def get_application_architecture() -> ApplicationArchitecture:
    """获取应用架构"""
    return await ea_service.get_application_architecture()

@router.get("/application/systems")
async def get_application_systems(
    type: Optional[str] = None,
    status: Optional[str] = None
) -> List[ApplicationSystem]:
    """获取应用系统列表"""
    return await ea_service.get_application_systems(type, status)

@router.get("/data")
async def get_data_architecture() -> DataArchitecture:
    """获取数据架构"""
    return await ea_service.get_data_architecture()

@router.get("/technology")
async def get_technology_architecture() -> TechnologyArchitecture:
    """获取技术架构"""
    return await ea_service.get_technology_architecture()

@router.get("/graph")
async def get_architecture_graph(
    domains: Optional[List[str]] = None,
    depth: int = 2
) -> ArchitectureGraph:
    """获取架构关系图"""
    return await ea_service.get_architecture_graph(domains, depth)

@router.post("/impact-analysis")
async def analyze_impact(
    entity_id: str,
    change_type: str
) -> ImpactAnalysis:
    """架构影响分析"""
    return await ea_service.analyze_impact(entity_id, change_type)
```

---

## 4. 数据流与交互模式

### 4.1 典型场景数据流

#### 4.1.1 场景1: 用户查询企业架构

**场景**: 用户问"采购订单审批流程涉及哪些系统？"

```
用户输入
  ↓
[第一层] 企业智能门户
  - 富内容对话区接收消息
  - WebSocket发送到网关
  ↓
[第二层] 对话智能网关
  - 会话管理器: 获取会话上下文
  - 意图识别器: 识别为EA查询（requires_ea=true）
  - 路由决策器: 路由到EA Core Service
  ↓
[第三层] EA Core Service (8014)
  - 业务语义引擎: 理解"采购订单审批流程"
    ├─ LLM分析: 识别业务流程实体
    ├─ Neo4j查询: 查找BusinessProcess节点
    └─ 返回: business_process_id

  - 架构映射引擎: 映射到应用架构
    ├─ Neo4j查询:
    │   MATCH (bp:BusinessProcess {id: $process_id})
    │   -[:IMPLEMENTED_BY]->(app:ApplicationSystem)
    │   RETURN app
    ├─ PostgreSQL查询: 获取应用系统详情
    └─ 返回: [SAP MM, OA审批系统]

  - 执行路径规划: 生成响应计划
  ↓
[第四层] Knowledge Base Service (8004)
  - GraphRAG Service: 增强知识检索
    ├─ Graph Retriever: 检索相关子图
    ├─ Context Builder: 构建富上下文
    └─ LLM Generator: 生成答案
  ↓
[第二层] 对话智能网关
  - 知识注入器: 注入架构图谱
  - 格式转换器: 转换为富内容格式
    {
      "type": "architecture",
      "content": {
        "process": "采购订单审批流程",
        "systems": ["SAP MM", "OA审批系统"],
        "graph": { nodes: [...], edges: [...] }
      }
    }
  - 流式响应器: 流式发送
  ↓
[第一层] 企业智能门户
  - 富内容渲染器: 渲染架构图谱
  - 右侧面板: 显示架构上下文
  ↓
用户看到结果
```

**数据库访问顺序**:
1. **Redis**: 获取会话上下文 (<1ms)
2. **Qdrant**: 语义搜索相似查询 (10ms)
3. **Neo4j**: 图谱查询业务流程关系 (15ms)
4. **PostgreSQL**: 获取应用系统详情 (5ms)
5. **Qdrant**: 搜索相关文档 (10ms)
6. **Neo4j**: 构建子图 (20ms)

**总耗时**: ~70ms (vs 当前1000ms+，提升14倍)

---

#### 4.1.2 场景2: 文档上传与知识提取

**场景**: 用户上传企业架构文档

```
用户上传PDF文档
  ↓
[第一层] 门户 → 文件选择器
  ↓
[第二层] 网关 → 路由到Knowledge Base
  ↓
[第四层] Knowledge Base Service
  ↓
1. MinIO存储原始文件
   POST /minio/documents/{kb_id}/{doc_id}.pdf
   ← 返回: minio_object_path

2. PostgreSQL记录文档元数据
   INSERT INTO documents (id, kb_id, title, file_path, ...)
   VALUES (...)
   ← 返回: document_id

3. 文档解析和分块
   - 解析PDF内容
   - 分块 (chunk_size=500, overlap=50)
   - 生成chunks (N个)

4. Qdrant存储文档向量
   FOR EACH chunk:
     - 向量化: vector = embedder.encode(chunk.content)
     - Qdrant.upsert(
         collection="documents",
         points=[{
           "id": chunk_id,
           "vector": vector,
           "payload": {
             "doc_id": document_id,
             "kb_id": kb_id,
             "content": chunk.content
           }
         }]
       )

5. 知识提取 (如果是EA文档)
   - LLM提取实体和关系
     ├─ 识别: BusinessProcess, ApplicationSystem, DataEntity
     ├─ 提取关系: IMPLEMENTED_BY, USES, REQUIRES
     └─ 返回: [
         {"source": "采购流程", "relation": "IMPLEMENTED_BY", "target": "SAP MM"},
         ...
       ]

   - 验证和去重
     ├─ 语义验证: 检查实体是否合理
     ├─ 去重: 检查Neo4j是否已存在
     └─ 置信度评分

   - 存储到Neo4j (如果置信度 > 0.7)
     FOR EACH triple:
       - MERGE (source:Entity {name: triple.source})
       - MERGE (target:Entity {name: triple.target})
       - CREATE (source)-[:triple.relation]->(target)

   - 存储到PostgreSQL (双写)
     FOR EACH entity:
       INSERT INTO metadata_entities (...)
       UPDATE SET neo4j_node_id = ...

6. 向量化实体描述
   FOR EACH extracted_entity:
     - vector = embedder.encode(entity.description)
     - Qdrant.upsert(
         collection="entities",
         points=[{
           "id": entity.id,
           "vector": vector,
           "payload": {
             "entity_id": entity.id,
             "neo4j_node_id": entity.neo4j_node_id,
             "name": entity.name,
             "type": entity.type
           }
         }]
       )

7. 返回处理结果
   {
     "document_id": "...",
     "status": "completed",
     "chunks_created": 45,
     "entities_extracted": 12,
     "relationships_created": 8,
     "vectors_created": 57  // 45 chunks + 12 entities
   }
```

**数据库操作顺序**:
1. **MinIO**: 存储原始文件 (500ms, 10MB文件)
2. **PostgreSQL**: INSERT documents (10ms)
3. **Qdrant**: BATCH upsert vectors (200ms, 45个chunks)
4. **Neo4j**: MERGE nodes + CREATE relationships (150ms, 20个操作)
5. **PostgreSQL**: UPDATE neo4j_node_id (20ms)
6. **Qdrant**: BATCH upsert entity vectors (50ms, 12个entities)

**总耗时**: ~930ms (单次上传)

---

#### 4.1.3 场景3: 复杂推理查询（三引擎融合）

**场景**: "如果SAP MM系统出现故障，会影响哪些业务流程和数据？"

```
用户查询
  ↓
[第二层] 网关
  - 意图识别: 影响分析类查询
  - 路由: EA Core + Knowledge Base
  ↓
[第三层] EA Core
  - 业务语义理解:
    ├─ 识别实体: "SAP MM系统" (ApplicationSystem)
    ├─ 识别意图: 影响分析 (impact_analysis)
    └─ 识别范围: 业务流程 + 数据实体
  ↓
[第四层] Knowledge Base (GraphRAG)

  1. Query Analyzer
     - 查询类型: exploration + analysis
     - 跳数: 1-3跳
     - 关系类型: IMPLEMENTED_BY (反向), USES

  2. Graph Retriever (Neo4j)
     MATCH path = (app:ApplicationSystem {name: "SAP MM"})
       <-[:IMPLEMENTED_BY]-(bp:BusinessProcess)
     MATCH (app)-[:USES]->(de:DataEntity)
     RETURN path, bp, de

     结果:
     - 业务流程: [采购申请流程, 采购订单流程, 库存管理流程, ...]
     - 数据实体: [采购订单, 物料, 供应商, 库存, ...]

  3. Semantic Expansion (Qdrant)
     - 向量搜索"SAP MM"相似实体
     - Top-10相似实体 (threshold=0.7)
     - 扩展图谱: 添加相似节点

  4. Context Builder
     - 整合图谱节点 (50个节点, 80条边)
     - 格式化为结构化上下文:
       """
       ## 影响的业务流程 (8个):
       1. 采购申请流程 - 流程会中断，无法创建采购申请
       2. 采购订单流程 - 无法创建和审批采购订单
       3. ...

       ## 影响的数据实体 (12个):
       1. 采购订单 - 无法读写
       2. 物料数据 - 无法访问
       3. ...

       ## 依赖关系:
       - 采购申请流程 → SAP MM → 采购订单数据
       - 库存管理流程 → SAP MM → 库存数据
       ...
       """

  5. Document Retrieval (Qdrant)
     - 搜索相关文档: "SAP MM 故障 影响"
     - Top-5文档片段

  6. LLM Generator
     - Prompt:
       """
       基于以下知识回答问题：

       ## 知识图谱:
       {graph_context}

       ## 相关文档:
       {documents}

       ## 问题:
       如果SAP MM系统出现故障，会影响哪些业务流程和数据？

       ## 要求:
       1. 列出所有受影响的业务流程
       2. 列出所有受影响的数据实体
       3. 分析影响的严重程度
       4. 提供推理路径
       """

     - LLM生成答案:
       """
       SAP MM系统故障会造成以下影响：

       ### 受影响的业务流程 (8个):
       1. **采购申请流程** (严重)
          - 无法创建采购申请
          - 影响采购计划
          - 推理路径: 采购申请流程 → IMPLEMENTED_BY → SAP MM

       2. **采购订单流程** (严重)
          ...

       ### 受影响的数据 (12个数据实体):
       1. **采购订单数据** (严重)
          - 无法读取和更新
          - 影响订单跟踪
          - 推理路径: SAP MM → USES → 采购订单数据

       2. **物料数据** (中等)
          ...

       ### 影响范围:
       - 业务流程: 8个流程受影响，其中5个严重
       - 数据实体: 12个实体无法访问
       - 预计影响: 采购部门业务完全中断

       ### 建议:
       1. 立即启动应急预案
       2. 通知所有相关业务部门
       3. 考虑使用备份系统（如果有）

       知识来源:
       - 业务流程数据: Neo4j知识图谱
       - SAP MM文档: [文档ID1, 文档ID2]
       - 影响分析: 基于架构关系推理
       """

  7. 返回结果
     {
       "answer": "...",
       "sources": [
         {"type": "graph", "nodes": 50, "edges": 80},
         {"type": "document", "doc_ids": [...]},
       ],
       "reasoning_path": [
         "SAP MM → IMPLEMENTED_BY (反向) → 采购流程",
         "SAP MM → USES → 采购订单数据",
         ...
       ],
       "confidence": 0.94,
       "subgraph": { nodes: [...], edges: [...] }
     }
```

**数据库访问详情**:
1. **Redis**: 会话上下文 (1ms)
2. **Neo4j**: 影响分析图查询 (25ms)
   - 反向关系查询: <-[:IMPLEMENTED_BY]
   - 数据依赖查询: -[:USES]->
   - 返回50个节点, 80条边
3. **Qdrant**: 语义扩展 (15ms)
4. **Qdrant**: 文档检索 (10ms)
5. **LLM**: 生成答案 (2000ms)
6. **Neo4j**: 获取子图详情 (10ms)

**总耗时**: ~2061ms (主要是LLM生成)
**准确率**: 94% (vs 传统RAG 70%)

---

### 4.2 数据一致性保证

#### 4.2.1 实时一致性

**双写机制**:
```python
async def create_business_process_with_dual_write(data):
    """双写创建业务流程"""

    async with distributed_lock(f"bp:{data.name}"):
        try:
            # 1. PostgreSQL写入（主数据）
            pg_record = await pg.execute("""
                INSERT INTO business_processes (...)
                VALUES (...) RETURNING id
            """)

            # 2. Neo4j写入（图谱）
            neo4j_node = await neo4j.execute("""
                CREATE (bp:BusinessProcess {...})
                RETURN id(bp) AS node_id
            """)

            # 3. 更新关联ID
            await pg.execute("""
                UPDATE business_processes
                SET neo4j_node_id = $1
                WHERE id = $2
            """, neo4j_node.node_id, pg_record.id)

            # 4. Qdrant写入（向量）
            vector = await vectorizer.encode(data.description)
            await qdrant.upsert(...)

            # 5. 记录操作日志
            await audit_log.record("dual_write_success", ...)

            return pg_record

        except Exception as e:
            # 回滚所有操作
            await rollback_all(pg_record, neo4j_node)
            raise
```

#### 4.2.2 最终一致性

**后台同步任务**:
```python
# Celery定时任务
@celery.task
async def sync_pg_to_neo4j():
    """PostgreSQL到Neo4j的增量同步"""

    # 1. 获取上次同步时间
    last_sync = await redis.get("last_sync_pg_to_neo4j")

    # 2. 查询增量数据
    new_records = await pg.fetch("""
        SELECT * FROM business_processes
        WHERE updated_at > $1
    """, last_sync)

    # 3. 同步到Neo4j
    for record in new_records:
        await neo4j.execute("""
            MERGE (bp:BusinessProcess {uuid: $uuid})
            SET bp.name = $name,
                bp.description = $description,
                bp.updated_at = $updated_at
        """, record)

    # 4. 更新同步时间
    await redis.set("last_sync_pg_to_neo4j", datetime.now())

@celery.task(schedule=crontab(minute='*/10'))  # 每10分钟
async def consistency_check():
    """一致性检查"""

    # 统计数量
    pg_count = await pg.fetchval("SELECT COUNT(*) FROM business_processes")
    neo4j_count = await neo4j.fetchval("MATCH (bp:BusinessProcess) RETURN count(bp)")

    diff = abs(pg_count - neo4j_count)
    if diff > pg_count * 0.01:  # 差异超过1%
        alert("数据不一致", f"PG={pg_count}, Neo4j={neo4j_count}")
        await reconcile()
```

---

## 5. 服务映射与演进路径

### 5.1 现有服务映射到五层架构

| 现有服务 | 端口 | 映射到层级 | 改造程度 | 说明 |
|---------|------|-----------|---------|------|
| **web-ui** | 3000 | 第一层 (门户) | 大改造 | 重构为三栏富内容布局 |
| **api-gateway** | 8080 | 第二层 (网关) | 中改造 | 增强为对话智能网关 |
| **registry-service** | 8000 | 第五层 (基础设施) | 无需改造 | 保持现状 |
| **config-center** | 8090 | 第五层 (基础设施) | 无需改造 | 保持现状 |
| **auth-service** | 8003 | 第五层 (基础设施) | 无需改造 | 保持现状 |
| **agent-service** | 8010 | 第四层 (AI服务) | 小改造 | 增加EA上下文支持 |
| **workflow-engine** | 8002 | 第四层 (AI服务) | 小改造 | 增加EA上下文支持 |
| **knowledge-base** | 8004 | 第四层 (AI服务) | 中改造 | 集成GraphRAG |
| **metadata-service** | 8005 | 第四层 (AI服务) | 小改造 | 增加EA元数据 |
| **dag-orchestrator** | 8009 | 第三层 (EA层) | 大改造 | 整合到智能编排服务 |
| **agent-orchestrator** | 8011 | 第三层 (EA层) | 大改造 | 整合到智能编排服务 |
| **新增: ea-core** | 8014 | 第三层 (EA层) | 新建服务 | EA核心服务 |
| **新增: intelligent-orchestrator** | 8016 | 第三层 (EA层) | 新建服务 | 智能编排服务 |
| **其他AI服务** | 8006-8020 | 第四层 (AI服务) | 无需改造 | 保持现状，通过网关调用 |

### 5.2 渐进式演进路径

#### 阶段1: 基础设施准备 (Week 1-2)

**目标**: 部署Neo4j，不影响现有系统

```
任务:
1. ✅ 部署Neo4j容器
2. ✅ 创建EA数据库表 (PostgreSQL)
3. ✅ 建立数据库适配器
4. ✅ 实现双写Repository

不影响:
- 现有23个服务继续运行
- 用户使用不受影响
```

#### 阶段2: EA功能实现 (Week 3-6)

**目标**: 实现EA功能，独立测试

```
任务:
1. ✅ 创建EA知识库
2. ✅ 导入EA文档
3. ✅ 构建EA知识图谱
4. ✅ 开发EA Core Service (8014)
5. ✅ 开发EA前端页面

不影响:
- 现有功能继续工作
- EA功能作为新增功能
- 用户可选择使用EA功能
```

#### 阶段3: 网关增强 (Week 7-8)

**目标**: 升级网关，支持富内容

```
任务:
1. ✅ 增强api-gateway
2. ✅ 实现会话管理
3. ✅ 实现意图识别
4. ✅ 实现路由决策
5. ✅ WebSocket支持

平滑切换:
- 保留原有REST API
- 新增WebSocket接口
- 客户端渐进式升级
```

#### 阶段4: 前端重构 (Week 9-12)

**目标**: 重构前端为三栏布局

```
任务:
1. ✅ 重构主布局
2. ✅ 实现富内容消息组件
3. ✅ WebSocket客户端
4. ✅ 状态管理重构

渐进策略:
- 保留旧界面（/chat）
- 新界面（/conversation）
- 用户可选择模式
- Feature flag控制
```

#### 阶段5: GraphRAG集成 (Week 13-16)

**目标**: 集成Neo4j到知识库服务

```
任务:
1. ✅ 实现GraphRAG组件
2. ✅ 数据迁移到Neo4j
3. ✅ 双写机制
4. ✅ 性能测试

灰度发布:
- 10%流量使用GraphRAG
- 监控性能和准确率
- 逐步扩大到100%
```

#### 阶段6: 全面上线 (Week 17-20)

**目标**: 完整五层架构上线

```
任务:
1. ✅ 智能编排服务上线
2. ✅ 所有AI服务适配
3. ✅ 完整测试
4. ✅ 用户培训

验收标准:
- 性能提升100倍
- 准确率提升到92%+
- 用户满意度 > 4.0/5.0
```

---

## 6. 分阶段实施计划

### 6.1 总体时间规划

**总周期**: 24周 (6个月)

```
阶段0: 准备阶段         Week 1        (1周)
阶段1: 基础设施         Week 2-3      (2周)
阶段2: EA功能实现       Week 4-9      (6周)
阶段3: 网关增强         Week 10-11    (2周)
阶段4: 前端重构         Week 12-15    (4周)
阶段5: GraphRAG集成     Week 16-19    (4周)
阶段6: 测试和上线       Week 20-24    (5周)
```

### 6.2 详细实施计划

#### Week 1: 项目启动

**任务**:
- [ ] 项目启动会议
- [ ] 团队组建和培训
- [ ] 开发环境准备
- [ ] 方案评审

**产出**:
- 项目章程
- 团队通讯录
- 开发环境文档

---

#### Week 2-3: Neo4j部署与数据建模

**任务**:
```yaml
Week 2:
  Day 1-2: Neo4j部署
    - Docker Compose配置
    - Neo4j启动和验证
    - 安装APOC和GDS插件

  Day 3-4: 数据库适配器
    - 实现Neo4jAdapter
    - 实现DualWriteRepository
    - 单元测试

  Day 5: 测试验证
    - 连接测试
    - 性能基准测试

Week 3:
  Day 1-3: EA数据库表
    - 创建business_processes表
    - 创建application_systems表
    - 创建data_entities表
    - 创建architecture_relationships表

  Day 4-5: 数据迁移脚本
    - 开发迁移脚本
    - 测试数据迁移
```

**产出**:
- ✅ Neo4j运行
- ✅ 适配器实现
- ✅ EA数据库表创建

**验收标准**:
- Neo4j健康检查通过
- 适配器单元测试覆盖率 > 90%
- 数据库表创建成功

---

#### Week 4-9: EA功能完整实现

**Week 4-5: EA知识库和文档**
```yaml
任务:
  - 创建5个EA知识库
  - 导入EA文档（业务、应用、数据、技术）
  - 文档处理和向量化

产出:
  - 5个知识库
  - 100+文档
  - 1000+向量

验收:
  - 文档上传成功率 100%
  - 向量化完成率 100%
```

**Week 6-7: EA Core Service开发**
```yaml
任务:
  - 开发业务语义理解引擎
  - 开发架构映射引擎
  - 开发路径规划引擎
  - API接口实现

产出:
  - EA Core Service (8014)
  - API文档
  - 单元测试

验收:
  - 服务启动成功
  - API测试通过
  - 单元测试覆盖率 > 85%
```

**Week 8-9: EA知识图谱构建**
```yaml
任务:
  - 从PostgreSQL同步EA数据到Neo4j
  - 建立实体节点
  - 建立关系边
  - 创建索引

产出:
  - Neo4j EA图谱
  - 500+节点
  - 1000+关系

验收:
  - 图谱数据完整
  - 查询性能 < 50ms
```

---

#### Week 10-11: 对话智能网关增强

**Week 10: 网关核心组件**
```yaml
Day 1-2: 会话管理器
  - SessionManager实现
  - Redis集成
  - 会话持久化

Day 3-4: 意图识别器
  - IntentAnalyzer实现
  - LLM集成
  - 规则引擎

Day 5: 路由决策器
  - RoutingDecision实现
  - 路由规则配置
```

**Week 11: 格式转换和流式响应**
```yaml
Day 1-2: 格式转换器
  - FormatConverter实现
  - 富内容格式定义
  - 格式转换逻辑

Day 3-4: 流式响应器
  - StreamResponder实现
  - WebSocket服务器
  - SSE支持

Day 5: 集成测试
  - 端到端测试
  - 性能测试
```

**验收标准**:
- 会话管理正常工作
- 意图识别准确率 > 85%
- WebSocket连接稳定

---

#### Week 12-15: 前端三栏布局重构

**Week 12: 布局和基础组件**
```yaml
任务:
  - 重构MainLayout为三栏布局
  - 实现LeftSidebar
  - 实现RightPanel
  - 响应式设计

产出:
  - 三栏布局
  - 基础UI组件
```

**Week 13: 富内容消息组件**
```yaml
任务:
  - TextMessage组件
  - ActionCard组件
  - ChartVisualization组件
  - ArchitectureGraphViewer组件
  - KnowledgeReference组件

产出:
  - 5+富内容组件
  - 组件Storybook
```

**Week 14: WebSocket客户端**
```yaml
任务:
  - WebSocket连接管理
  - 重连机制
  - 消息处理
  - 状态管理

产出:
  - WebSocket客户端
  - 状态管理Store
```

**Week 15: EA前端页面**
```yaml
任务:
  - 企业架构总览页
  - 业务架构页
  - 应用架构页
  - 数据架构页
  - 技术架构页
  - 架构关系图页

产出:
  - 6个EA页面
  - 页面导航
```

**验收标准**:
- UI布局正确
- 富内容正常渲染
- WebSocket稳定连接
- EA页面功能完整

---

#### Week 16-19: GraphRAG集成

**Week 16: GraphRAG组件开发**
```yaml
任务:
  - QueryAnalyzer实现
  - GraphRetriever实现
  - ContextBuilder实现
  - LLMGenerator实现

产出:
  - 4个GraphRAG组件
  - 单元测试
```

**Week 17: 数据迁移**
```yaml
任务:
  - 历史知识图谱数据迁移
  - 数据验证
  - 索引优化

产出:
  - 10万+节点
  - 50万+关系
  - 迁移报告
```

**Week 18: 双写和一致性**
```yaml
任务:
  - 实现双写机制
  - 一致性检查
  - 降级策略

产出:
  - DualWriteRepository
  - ConsistencyChecker
  - FallbackHandler
```

**Week 19: 性能测试和优化**
```yaml
任务:
  - 查询性能测试
  - 并发压力测试
  - 性能优化

目标:
  - 简单查询 < 20ms
  - 复杂查询 < 100ms
  - QPS > 1000
```

**验收标准**:
- GraphRAG功能完整
- 性能指标达标
- 数据一致性 > 99.9%

---

#### Week 20-24: 全面测试和上线

**Week 20: 功能测试**
```yaml
任务:
  - 功能完整性测试
  - 集成测试
  - 回归测试
  - Bug修复

目标:
  - 功能覆盖率 100%
  - P0 Bug = 0
```

**Week 21: 性能测试**
```yaml
任务:
  - 负载测试
  - 压力测试
  - 稳定性测试
  - 性能调优

目标:
  - 响应时间达标
  - 吞吐量达标
  - 资源使用合理
```

**Week 22-23: 灰度发布**
```yaml
Week 22:
  - 10%流量切换
  - 内部用户测试
  - 监控和调整

Week 23:
  - 50%流量切换
  - 外部用户测试
  - 问题修复
```

**Week 24: 正式上线**
```yaml
任务:
  - 100%流量切换
  - 用户培训
  - 文档完善
  - 项目总结

产出:
  - 上线报告
  - 用户手册
  - 运维手册
  - 项目总结
```

**最终验收标准**:
- ✅ 系统稳定运行 > 1周
- ✅ 查询性能提升 > 50倍
- ✅ 准确率 > 90%
- ✅ 用户满意度 > 4.0/5.0
- ✅ P0/P1 Bug = 0

---

## 7. 技术规范与标准

### 7.1 API规范

**REST API标准**:
```
基础URL: http://localhost:8080/api/v1

命名规范:
- 使用名词复数: /users, /documents, /workflows
- 使用kebab-case: /knowledge-bases, /business-processes
- 版本控制: /api/v1, /api/v2

HTTP方法:
- GET: 查询资源
- POST: 创建资源
- PUT: 完整更新资源
- PATCH: 部分更新资源
- DELETE: 删除资源

响应格式:
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "timestamp": "2025-12-06T10:00:00Z"
}

错误格式:
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "输入参数无效",
    "details": { ... }
  },
  "timestamp": "2025-12-06T10:00:00Z"
}
```

### 7.2 数据库规范

**PostgreSQL命名规范**:
```sql
-- 表名: 小写下划线分隔
business_processes
application_systems
data_entities

-- 字段名: 小写下划线分隔
id, name, description, created_at

-- 主键: id (UUID)
-- 外键: {table_name}_id
-- Neo4j关联: neo4j_node_id
```

**Neo4j命名规范**:
```cypher
-- 节点标签: 大驼峰
:BusinessProcess
:ApplicationSystem
:DataEntity

-- 关系类型: 大写下划线分隔
-[:IMPLEMENTED_BY]->
-[:USES]->
-[:REQUIRES]->

-- 属性名: 小驼峰
uuid, name, createdAt
```

### 7.3 代码规范

**Python代码规范**:
```python
# PEP 8标准
# 类名: 大驼峰 (PascalCase)
class BusinessSemanticEngine:
    pass

# 函数名: 小写下划线 (snake_case)
async def analyze_business_intent():
    pass

# 常量: 大写下划线
MAX_RETRY_ATTEMPTS = 3

# 类型注解
def process_query(query: str) -> Answer:
    pass
```

**TypeScript代码规范**:
```typescript
// 接口名: I开头大驼峰
interface IMessage {
  id: string
  type: MessageType
  content: any
}

// 类名: 大驼峰
class MessageRenderer {
  render(message: IMessage): JSX.Element
}

// 函数名: 小驼峰
function renderMessage(message: IMessage) {}

// 常量: 大写下划线
const MAX_MESSAGE_LENGTH = 1000
```

---

## 8. 监控与运维方案

### 8.1 监控指标

**系统监控**:
```yaml
指标类别: 基础设施
  - CPU使用率: < 80%
  - 内存使用率: < 70%
  - 磁盘使用率: < 80%
  - 网络带宽: 监控

指标类别: 数据库
  Neo4j:
    - 查询响应时间: p50 < 20ms, p95 < 100ms
    - 节点数量: 实时监控
    - 连接池使用率: < 80%

  PostgreSQL:
    - 查询响应时间: p50 < 10ms, p95 < 50ms
    - 连接数: < 80%最大连接
    - 慢查询: 记录 > 100ms的查询

  Qdrant:
    - 向量搜索延迟: p95 < 50ms
    - 索引大小: 监控
    - QPS: 监控

指标类别: 应用
  - 请求响应时间: p95 < 200ms
  - 错误率: < 0.1%
  - QPS: 监控
  - 并发连接数: 监控

指标类别: 业务
  - 对话成功率: > 95%
  - 查询准确率: > 90%
  - 用户满意度: > 4.0/5.0
  - 日活跃用户: 监控
```

### 8.2 告警规则

**告警级别**:
```yaml
P0 (紧急):
  - 服务完全不可用
  - 数据库连接失败
  - 数据一致性错误 > 1%

P1 (重要):
  - 错误率 > 1%
  - 响应时间 > 1s (p95)
  - CPU/内存 > 90%

P2 (警告):
  - 错误率 > 0.1%
  - 响应时间 > 500ms (p95)
  - CPU/内存 > 80%

P3 (提示):
  - 慢查询 > 100ms
  - 并发连接数接近上限
```

### 8.3 日志规范

**日志级别**:
```python
import logging

# ERROR: 错误，需要立即处理
logger.error("Neo4j查询失败", exc_info=True)

# WARNING: 警告，需要关注
logger.warning("数据不一致", extra={"pg_count": 100, "neo4j_count": 99})

# INFO: 重要信息
logger.info("GraphRAG查询完成", extra={"duration": 150, "nodes": 50})

# DEBUG: 调试信息
logger.debug("Cypher查询", extra={"query": "MATCH ..."})
```

**日志格式**:
```json
{
  "timestamp": "2025-12-06T10:00:00.123Z",
  "level": "INFO",
  "service": "ea-core",
  "trace_id": "abc123",
  "message": "GraphRAG查询完成",
  "extra": {
    "duration_ms": 150,
    "nodes_count": 50,
    "edges_count": 80
  }
}
```

---

## 9. 总结

### 9.1 核心成果

本方案完整设计了：

1. ✅ **四数据库架构** - Neo4j、Qdrant、PostgreSQL、MinIO职责清晰
2. ✅ **五层EA-OS架构** - 门户、网关、EA、AI、工具层完整设计
3. ✅ **企业架构功能** - 填补所有EA功能缺失
4. ✅ **数据流设计** - 三个典型场景的完整数据流
5. ✅ **实施计划** - 24周(6个月)分阶段实施路线图
6. ✅ **技术规范** - API、数据库、代码规范
7. ✅ **监控运维** - 完整的监控指标和告警规则

### 9.2 关键指标

| 指标 | 当前 | 目标 | 提升 |
|-----|------|------|------|
| 查询性能 | 1000ms | 10-70ms | 100倍 |
| 准确率 | 70% | 92%+ | +31% |
| 并发能力 | 100 | 1000+ | 10倍 |
| 功能完整性 | EA功能缺失 | EA功能完整 | 100% |
| 用户体验 | 基础 | 富内容+上下文 | 显著提升 |

### 9.3 实施建议

**推荐决策**: ✅ **批准实施**

**理由**:
1. 技术可行性高（所有技术成熟）
2. 业务价值显著（性能+准确率大幅提升）
3. 风险可控（渐进式实施+降级策略）
4. 投资回报合理（2.5年回本）

**前提条件**:
1. ✅ 管理层批准和预算支持
2. ✅ 核心团队稳定（4-5人，6个月）
3. ✅ 用户接受渐进式变化
4. ✅ 充足的硬件资源

### 9.4 下一步行动

**立即执行**:
1. 项目启动会议
2. 团队组建和培训
3. 开发环境准备
4. Week 1开始实施

**批准签字**:

项目发起人: ________________  日期: ______

技术负责人: ________________  日期: ______

项目经理:   ________________  日期: ______

---

**文档结束**

本方案提供了完整的EA-OS五层架构设计、四数据库集成、企业架构功能实现的详细方案。建议按照6个月的分阶段计划渐进式实施，确保风险可控、价值可验证。

