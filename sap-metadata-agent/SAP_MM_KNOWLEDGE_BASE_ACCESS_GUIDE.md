# SAP MM知识库和元数据访问指南

## 📋 概述

本文档介绍如何访问和查看SAP MM知识库和元数据。系统提供了多种访问方式，包括API端点和Swagger文档界面。

## 🌐 Web界面访问

### 1. API Gateway Swagger文档
**URL**: http://localhost:8000/docs

**功能**:
- 查看所有统一API端点
- 测试统一搜索功能
- 查看知识图谱搜索API
- 测试自然语言查询

**主要端点**:
- `GET /api/unified/search` - 统一搜索
- `POST /api/unified/search` - 统一搜索（POST方式）
- `GET /api/knowledge-graph/search` - 知识图谱搜索
- `POST /api/nl-query/search` - 自然语言搜索

### 2. Metadata Service Swagger文档
**URL**: http://localhost:8005/docs

**功能**:
- 查看业务实体API
- 查看知识图谱API
- 查看本体构建API
- 查看文档-实体关联API

**主要端点**:
- `GET /api/metadata/business-entities` - 获取业务实体列表
- `GET /api/knowledge-graph/nodes` - 获取知识图谱节点
- `GET /api/knowledge-graph/edges` - 获取知识图谱关系
- `GET /api/ontology/concepts` - 获取本体概念
- `POST /api/document-entity-linker/link` - 文档-实体关联

### 3. Knowledge Base Swagger文档
**URL**: http://localhost:8004/docs

**功能**:
- 查看文档管理API
- 查看文档搜索API
- 查看文档chunks API

**主要端点**:
- `GET /api/documents` - 获取文档列表
- `GET /api/documents/{id}` - 获取文档详情
- `GET /api/documents/search` - 搜索文档
- `GET /api/documents/{id}/chunks` - 获取文档chunks

## 🔍 查询SAP MM数据

### 1. 查询SAP MM业务实体

```bash
# 获取所有SAP MM实体
curl "http://localhost:8005/api/metadata/business-entities?entity_type=concept&limit=100"

# 搜索特定实体
curl "http://localhost:8005/api/metadata/business-entities?search=物料&limit=10"
```

### 2. 查询知识图谱

```bash
# 获取知识图谱节点
curl "http://localhost:8005/api/knowledge-graph/nodes?node_type=concept&limit=100"

# 获取知识图谱关系
curl "http://localhost:8005/api/knowledge-graph/edges?relationship_type=related_to&limit=50"

# 获取特定节点的邻居
curl "http://localhost:8005/api/knowledge-graph/nodes/{node_id}/neighbors"
```

### 3. 查询SAP MM文档

```bash
# 获取所有SAP MM文档
curl "http://localhost:8004/api/documents?limit=100"

# 搜索文档
curl "http://localhost:8004/api/documents/search?q=物料管理"

# 获取文档详情
curl "http://localhost:8004/api/documents/{document_id}"

# 获取文档chunks
curl "http://localhost:8004/api/documents/{document_id}/chunks"
```

### 4. 统一搜索

```bash
# 统一搜索（GET方式）
curl "http://localhost:8000/api/unified/search?q=物料管理&limit=10"

# 统一搜索（POST方式，支持更多参数）
curl -X POST "http://localhost:8000/api/unified/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "物料管理",
    "limit": 10,
    "use_vector_search": true,
    "use_cache": true
  }'
```

### 5. 知识图谱可视化查询

```bash
# 获取知识图谱可视化数据
curl "http://localhost:8005/api/knowledge-graph/visualization?node_type=concept&limit=100"
```

## 📊 数据库直接查询

如果需要直接查询数据库，可以使用以下SQL：

### 1. 查询SAP MM实体

```sql
-- 连接到PostgreSQL
docker exec -it enterprise-ai-postgres psql -U ai_user -d ai_platform

-- 查询SAP MM业务实体
SELECT id, name, display_name, entity_type, description 
FROM business_entities 
WHERE metadata->>'sap_module' = 'MM' 
LIMIT 10;
```

### 2. 查询知识图谱

```sql
-- 查询知识图谱节点
SELECT node_type, COUNT(*) as count 
FROM knowledge_graph_nodes 
GROUP BY node_type;

-- 查询知识图谱关系
SELECT relationship_type, COUNT(*) as count 
FROM knowledge_graph_edges 
GROUP BY relationship_type;

-- 查询特定节点的关系
SELECT e.relationship_type, n2.label as target_node
FROM knowledge_graph_edges e
JOIN knowledge_graph_nodes n1 ON e.source_node_id = n1.id
JOIN knowledge_graph_nodes n2 ON e.target_node_id = n2.id
WHERE n1.label = '物料主数据'
LIMIT 10;
```

### 3. 查询文档

```sql
-- 查询SAP MM文档
SELECT id, filename, status, 
       (SELECT COUNT(*) FROM document_chunks WHERE document_id = d.id) as chunk_count
FROM documents d
WHERE filename LIKE '%MM%'
ORDER BY created_at DESC;

-- 查询文档chunks
SELECT dc.chunk_index, dc.content, dc.embedding_model
FROM document_chunks dc
JOIN documents d ON dc.document_id = d.id
WHERE d.filename LIKE '%MM%'
LIMIT 10;
```

### 4. 查询文档-实体关联

```sql
-- 查询文档-实体关联
SELECT 
    n1.label as document_label,
    n2.label as entity_label,
    e.relationship_type
FROM knowledge_graph_edges e
JOIN knowledge_graph_nodes n1 ON e.source_node_id = n1.id
JOIN knowledge_graph_nodes n2 ON e.target_node_id = n2.id
WHERE e.relationship_type = 'mentions'
LIMIT 10;
```

## 🎯 快速访问示例

### 在浏览器中访问Swagger文档

1. **API Gateway**: 打开浏览器访问 http://localhost:8000/docs
2. **Metadata Service**: 打开浏览器访问 http://localhost:8005/docs
3. **Knowledge Base**: 打开浏览器访问 http://localhost:8004/docs

### 使用curl命令查询

```bash
# 查询SAP MM实体
curl "http://localhost:8005/api/metadata/business-entities?search=物料&limit=5"

# 查询知识图谱节点
curl "http://localhost:8005/api/knowledge-graph/nodes?node_type=concept&limit=5"

# 查询SAP MM文档
curl "http://localhost:8004/api/documents?limit=5"

# 统一搜索
curl "http://localhost:8000/api/unified/search?q=采购订单"
```

## 📝 注意事项

1. **服务端口**:
   - API Gateway: 8000
   - Metadata Service: 8005
   - Knowledge Base: 8004

2. **数据访问**:
   - 所有API都支持Swagger文档界面，可以直接在浏览器中测试
   - 数据库查询需要直接连接PostgreSQL容器

3. **权限**:
   - 当前所有API都是开放的，生产环境需要添加认证

4. **数据量**:
   - SAP MM实体: 2734个概念
   - 知识图谱节点: 712个
   - 知识图谱关系: 84个
   - SAP MM文档: 21个
   - 文档Chunks: 447个

## 🔗 相关文档

- API Gateway文档: http://localhost:8000/docs
- Metadata Service文档: http://localhost:8005/docs
- Knowledge Base文档: http://localhost:8004/docs




