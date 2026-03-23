# 文档删除失败排查指南

## 问题描述

删除知识库中的文档时失败。

## 可能的原因

### 1. 后端服务未运行（502/504 错误）

**症状**：
- 前端显示 "文档删除失败"
- 浏览器控制台显示 502 或 504 错误
- 网络请求超时

**解决方案**：
```bash
# 检查知识库服务是否运行
curl http://localhost:8004/api/health

# 如果未运行，启动服务
cd knowledge-base
python -m uvicorn src.main:app --host 0.0.0.0 --port 8004 --reload
```

### 2. 文档不存在（404 错误）

**症状**：
- 返回 404 错误
- 日志显示 "Document not found"

**解决方案**：
- 检查文档ID是否正确
- 确认文档确实存在（可能已被删除）
- 刷新页面重新加载文档列表

### 3. 向量存储删除失败

**症状**：
- 文档状态更新但向量未删除
- 日志显示向量删除警告

**解决方案**：
- 检查向量存储服务（Chroma/Weaviate）是否正常运行
- 查看后端日志了解具体错误
- 向量删除失败不会阻止文档删除，但需要手动清理

### 4. 数据库连接问题

**症状**：
- 返回 500 错误
- 日志显示数据库连接错误

**解决方案**：
```bash
# 检查数据库连接
psql -U postgres -d enterprise_ai -c "SELECT 1"

# 检查数据库服务
docker ps | grep postgres
# 或
sudo systemctl status postgresql
```

### 5. 权限问题

**症状**：
- 返回 403 错误
- 日志显示权限不足

**解决方案**：
- 检查用户权限
- 确认文档属于当前用户或知识库

## 排查步骤

### 步骤 1: 检查浏览器控制台

打开浏览器开发者工具（F12），查看：
1. **Network 标签**：查看删除请求的详细信息
   - 请求URL
   - 响应状态码
   - 响应内容

2. **Console 标签**：查看错误日志
   - 查找 `[Delete Document]` 开头的日志
   - 查看错误堆栈

### 步骤 2: 检查后端日志

查看知识库服务的日志：

```bash
# Docker
docker logs -f knowledge-base

# 直接运行
# 查看控制台输出
```

查找以下日志：
- `Starting deletion of document {document_id}`
- `Deleted {count} vectors from vector store`
- `Deleted {count} chunks from database`
- `Document {document_id} deleted successfully`
- 或错误信息

### 步骤 3: 直接测试后端API

```bash
# 测试删除API
curl -X DELETE http://localhost:8004/api/documents/{document_id}

# 或通过 API Gateway
curl -X DELETE http://localhost:8080/api/knowledge/documents/{document_id}
```

### 步骤 4: 检查文档状态

```bash
# 查询文档详情
curl http://localhost:8004/api/documents/{document_id}

# 检查文档是否已被软删除（status = "deleted"）
```

## 改进的错误处理

我已经改进了错误处理，现在会：

1. **详细的日志记录**：
   - 前端：记录请求URL、文档ID、错误详情
   - 后端：记录删除过程的每个步骤

2. **更好的错误消息**：
   - 区分不同类型的错误（网络错误、服务器错误、文档不存在等）
   - 提供调试信息

3. **超时控制**：
   - 30秒超时，避免长时间等待

4. **向量删除容错**：
   - 向量删除失败不会阻止文档删除
   - 记录警告但继续执行

## 常见错误和解决方案

### 错误 1: "Failed to connect to backend service"

**原因**：后端服务未运行或无法连接

**解决方案**：
1. 检查后端服务是否运行
2. 检查端口是否正确（默认 8004）
3. 检查防火墙设置

### 错误 2: "Document not found"

**原因**：文档不存在或已被删除

**解决方案**：
1. 刷新文档列表
2. 检查文档ID是否正确
3. 确认文档确实存在

### 错误 3: "Request timeout"

**原因**：删除操作耗时过长（超过30秒）

**解决方案**：
1. 检查后端服务性能
2. 检查向量存储服务是否正常
3. 查看后端日志了解具体原因

### 错误 4: "Failed to delete vectors from vector store"

**原因**：向量存储服务问题

**解决方案**：
1. 检查向量存储服务（Chroma/Weaviate）
2. 文档仍会被删除，但向量可能需要手动清理
3. 查看后端日志了解具体错误

## 手动清理

如果删除失败但需要清理数据：

### 1. 手动删除向量

```python
from knowledge_base.src.core.vector_store import get_vector_store

vector_store = get_vector_store()
# 删除特定文档的向量
vector_store.delete(ids=[chunk_id1, chunk_id2, ...])
```

### 2. 手动删除数据库记录

```sql
-- 软删除文档
UPDATE documents SET status = 'deleted' WHERE id = 'document_id';

-- 删除文档块（硬删除）
DELETE FROM document_chunks WHERE document_id = 'document_id';
```

## 预防措施

1. **定期备份**：定期备份数据库和向量存储
2. **监控日志**：监控删除操作的日志
3. **错误告警**：设置删除失败告警
4. **测试删除**：定期测试删除功能

## 调试工具

使用以下工具帮助调试：

```bash
# 检查文档详情
python check_document_progress.py {document_id}

# 检查知识库数据
python check_knowledge_bases.py
```

## 联系支持

如果问题仍然存在，请提供：
1. 浏览器控制台的完整错误信息
2. 后端服务的日志
3. 文档ID和知识库ID
4. 错误发生的时间


