# SAP MM数据导入报告

## 问题描述

服务器上知识库的SAP MM数据缺失，需要导入SAP MM文档到知识库。

## 解决方案

### 1. 检查本地数据

- ✅ `sap_mm_documents.json` 存在，包含SAP MM文档定义
- ✅ 文件已同步到服务器

### 2. 修复导入脚本

**问题**:
- 原脚本使用错误的API端点 (`http://localhost:8003/api/knowledge/documents`)
- 请求格式不正确

**修复**:
- ✅ 更新API端点为 `http://localhost:8004/api/documents/create`
- ✅ 修复请求数据格式，匹配 `DocumentCreateRequest` 模型：
  ```python
  {
      "title": doc['title'],
      "content": doc['content'],
      "category": doc.get('metadata', {}).get('category', ''),
      "tags": doc.get('metadata', {}).get('tags', []),
      "metadata": doc.get('metadata', {}),
      "process_async": True
  }
  ```

### 3. 导入步骤

1. 上传修复后的导入脚本到服务器
2. 在knowledge-base容器中运行导入脚本
3. 验证导入结果

## 导入脚本说明

### 脚本位置
- 本地: `import_sap_mm_documents.py`
- 服务器: `/opt/enterprise-ai-platform/import_sap_mm_documents.py`

### 运行方式

在服务器上运行：
```bash
cd /opt/enterprise-ai-platform
docker compose exec knowledge-base python3 /opt/enterprise-ai-platform/import_sap_mm_documents.py
```

或者在容器内运行：
```bash
docker compose exec -T knowledge-base python3 /opt/enterprise-ai-platform/import_sap_mm_documents.py
```

### 文档数据

SAP MM文档包含：
- 采购流程文档
- 数据字典文档（MARA、EKKO/EKPO等表）
- 库存管理流程
- 供应商管理
- 其他SAP MM相关文档

## 验证

导入完成后，检查：
1. 文档数量是否正确
2. 文档状态是否为 `processed`
3. 文档是否有chunks（向量化完成）

## 注意事项

1. 文档处理是异步的，需要等待向量化完成
2. 如果文档已存在，会跳过（409状态码）
3. 导入过程可能需要几分钟时间




