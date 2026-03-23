# SAP元数据语义索引构建指南

## 📋 概述

本指南说明如何构建SAP元数据的语义索引，将SAP元数据转换为可搜索的语义文档并存储到知识库中。

## ✅ 前置条件

### 1. 服务运行状态

在执行语义索引构建之前，确保以下服务正在运行：

- **知识库服务** (http://localhost:8004)
- **SAP元数据代理服务** (http://localhost:8015)

### 2. 检查服务状态

运行健康检查脚本：

```bash
cd sap-metadata-agent
python check_semantic_index_health.py
```

如果所有检查通过，可以继续执行构建。

## 🚀 执行语义索引构建

### 方式1: 使用执行脚本（推荐）

```bash
cd sap-metadata-agent
python execute_semantic_index_build.py
```

### 方式2: 指定知识库ID

如果您想将文档关联到特定的知识库：

```bash
python execute_semantic_index_build.py <knowledge_base_id>
```

例如：

```bash
python execute_semantic_index_build.py 46b77fb0-9d26-45af-aa7e-63c1ad5abf42
```

### 方式3: 使用原始构建脚本

```bash
cd sap-metadata-agent
python build_semantic_index.py
```

## 📊 构建过程

语义索引构建过程包括以下步骤：

1. **调用SAP元数据代理API**
   - 端点: `POST http://localhost:8015/api/sap-metadata/discover`
   - 参数: `build_semantic_index: true`

2. **发现SAP元数据**
   - 数据资产 (Data Assets)
   - 业务实体 (Business Entities)
   - 业务流程 (Business Processes)

3. **创建语义文档**
   - 为每个资产/实体/流程创建文档
   - 包含名称、描述、分类、标签等信息

4. **存储到知识库**
   - 调用知识库服务的 `/api/documents/create` API
   - 文档自动分块和向量化
   - 存储到向量数据库

## 🔍 验证构建结果

### 1. 检查构建日志

构建完成后，查看输出：

```
语义索引构建完成
   索引成功: 150
   索引失败: 0
   总计: 150
```

### 2. 在知识库中查看文档

访问知识库管理页面，查看是否有新文档：

```
http://localhost:3000/knowledge/<knowledge_base_id>
```

### 3. 测试语义搜索

在知识库中搜索SAP相关的关键词，验证索引是否正常工作。

## ⚠️ 常见问题

### 问题1: 服务未运行

**错误信息**:
```
❌ 知识库服务未运行或无法访问
```

**解决方案**:
1. 启动知识库服务
2. 启动SAP元数据代理服务
3. 重新运行构建脚本

### 问题2: 没有文档被索引

**可能原因**:
- 没有可用的SAP元数据
- 知识库服务连接问题
- 文档处理失败

**解决方案**:
1. 检查SAP元数据代理服务是否有数据
2. 查看知识库服务日志
3. 检查文档创建API是否正常

### 问题3: 构建超时

**错误信息**:
```
❌ 请求超时（超过30分钟）
```

**解决方案**:
1. 检查数据量是否过大
2. 考虑分批处理
3. 增加超时时间

## 📝 技术细节

### 语义索引构建器

位置: `sap-metadata-agent/src/core/sap_semantic_index_builder.py`

主要方法:
- `build_semantic_index()`: 构建语义索引
- `_create_semantic_document()`: 创建语义文档
- `_store_document()`: 存储文档到知识库

### 知识库API

文档创建端点: `POST http://localhost:8004/api/documents/create`

请求格式:
```json
{
  "title": "SAP表: MARA",
  "content": "名称: MARA\n描述: 物料主数据...",
  "category": "sap_metadata",
  "knowledge_base_id": "kb-uuid",
  "tags": ["SAP", "物料"],
  "metadata": {
    "sap_table_name": "MARA",
    "classification": "sap_table"
  },
  "process_async": false
}
```

## 🎯 最佳实践

1. **定期构建**: 建议定期（如每天）构建语义索引，以保持数据最新

2. **指定知识库**: 为SAP元数据创建专门的知识库，便于管理

3. **监控构建**: 关注构建日志，及时发现和解决问题

4. **分批处理**: 如果数据量很大，考虑分批处理

5. **验证结果**: 构建完成后，验证文档是否正确索引

## 📚 相关文档

- [知识库语义索引支持情况总结](./KNOWLEDGE_BASE_SEMANTIC_INDEX_SUMMARY.md)
- [知识库实现指南](./KNOWLEDGE_BASE_IMPLEMENTATION_GUIDE.md)
- [文档处理流程](./DOCUMENT_PROCESSING_FLOW.md)


