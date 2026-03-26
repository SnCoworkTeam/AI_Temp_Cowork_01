# SAP MM模块构建快速操作指南

## 🚀 快速开始（5步完成）

### 步骤1: 导入SAP MM业务实体

```bash
# 运行实体导入脚本
python import_sap_mm_entities.py
```

**预期结果**:
- ✅ 创建15个SAP MM核心实体
- ✅ 包括：物料、供应商、采购订单、库存地点等

**验证**:
```bash
curl "http://localhost:8005/api/metadata/business-entities?metadata.sap_module=MM"
```

---

### 步骤2: 构建SAP MM知识图谱

```bash
# 执行SAP MM专用本体构建
curl -X POST http://localhost:8005/api/ontology/sap/build \
  -H "Content-Type: application/json" \
  -d '{"use_llm": true}'
```

**预期时间**: 5-15分钟

**预期结果**:
- ✅ 知识图谱节点: 15+ 个
- ✅ 知识图谱边: 30+ 条
- ✅ 关系类型: 多样化

**验证**:
```bash
# 检查知识图谱统计
curl http://localhost:8005/api/knowledge-graph/stats

# 检查SAP MM相关节点
curl "http://localhost:8005/api/knowledge-graph/nodes?properties.sap_module=MM"
```

---

### 步骤3: 导入SAP MM知识库文档

```bash
# 运行文档导入脚本
python import_sap_mm_documents.py
```

**预期结果**:
- ✅ 导入6个SAP MM文档
- ✅ 文档自动向量化
- ✅ 支持语义搜索

**验证**:
```bash
curl "http://localhost:8003/api/knowledge/documents?metadata.module=MM"
```

---

### 步骤4: 建立文档与实体关联

```bash
# 运行文档实体关联脚本
python link_sap_mm_documents.py
```

**预期结果**:
- ✅ 文档关联到对应实体
- ✅ 支持从文档查找实体
- ✅ 支持从实体查找文档

**验证**:
```bash
# 测试文档实体关联
curl http://localhost:8005/api/document-entity-linker/link?document_id=xxx
```

---

### 步骤5: 验证和测试

```bash
# 1. 测试推荐功能
curl "http://localhost:8005/api/recommendation/entities/{material_entity_id}/related?limit=5"

# 2. 测试搜索功能
curl -X POST http://localhost:8080/api/unified/search \
  -H "Content-Type: application/json" \
  -d '{"query": "SAP MM采购流程", "types": ["entity", "document"]}'

# 3. 测试知识图谱查询
curl "http://localhost:8005/api/knowledge-graph/viz/graph-data?max_nodes=50"
```

---

## 📋 完整操作流程

### 一键执行脚本

创建 `build_sap_mm.sh`:

```bash
#!/bin/bash

echo "=== SAP MM模块构建开始 ==="

# 步骤1: 导入实体
echo "步骤1: 导入SAP MM实体..."
python import_sap_mm_entities.py

# 等待
sleep 5

# 步骤2: 构建知识图谱
echo "步骤2: 构建SAP MM知识图谱..."
curl -X POST http://localhost:8005/api/ontology/sap/build \
  -H "Content-Type: application/json" \
  -d '{"use_llm": true}'

echo "等待知识图谱构建完成（约10分钟）..."
sleep 600

# 步骤3: 导入文档
echo "步骤3: 导入SAP MM文档..."
python import_sap_mm_documents.py

# 等待文档向量化
sleep 60

# 步骤4: 建立关联
echo "步骤4: 建立文档实体关联..."
python link_sap_mm_documents.py

echo "=== SAP MM模块构建完成 ==="
```

---

## 🎯 预期结果

### 元数据结果

- ✅ SAP MM业务实体: 15个
- ✅ 知识图谱节点: 15+ 个
- ✅ 知识图谱边: 30+ 条
- ✅ 实体关系: 完整的SAP MM关系网络

### 知识库结果

- ✅ SAP MM文档: 6篇
- ✅ 文档向量化: 100%
- ✅ 文档实体关联: 80%+

### 功能验证

- ✅ 推荐功能: 能推荐SAP MM相关实体
- ✅ 搜索功能: 能搜索SAP MM文档和实体
- ✅ 分析功能: 能分析SAP MM实体关系

---

## 💡 使用示例

### 示例1: 搜索SAP MM采购流程

```bash
curl -X POST http://localhost:8080/api/unified/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SAP MM采购流程",
    "types": ["document", "entity"]
  }'
```

### 示例2: 推荐与物料相关的实体

```bash
# 先查找物料实体ID
curl "http://localhost:8005/api/metadata/business-entities?name=material"

# 然后推荐相关实体
curl "http://localhost:8005/api/recommendation/entities/{material_id}/related?limit=5"
```

### 示例3: 查看SAP MM知识图谱

```bash
# 获取可视化数据
curl "http://localhost:8005/api/knowledge-graph/viz/graph-data?max_nodes=50"

# 获取子图
curl "http://localhost:8005/api/knowledge-graph/viz/subgraph-data/{node_id}?max_depth=2"
```

---

**操作指南生成时间**: 2025-11-28  
**状态**: ✅ **准备使用**




