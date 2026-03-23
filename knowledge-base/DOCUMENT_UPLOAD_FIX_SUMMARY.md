# 文档上传和处理问题修复总结

## 修复的问题

### 1. **异步事件循环问题** ✅
**问题**: 在后台任务中使用 `asyncio.get_event_loop()` 可能导致错误
**修复**: 改用 `asyncio.get_running_loop()`，确保在已有事件循环中运行

**修复位置**:
- `knowledge-base/src/services/document_service.py`
  - `parse_document()` 函数
  - `generate_embeddings()` 函数
  - `store_vectors()` 函数

### 2. **同步操作阻塞事件循环** ✅
**问题**: 在异步函数中直接调用同步方法会阻塞事件循环
**修复**: 使用 `loop.run_in_executor()` 在线程池中执行同步操作

**修复位置**:
- `knowledge-base/src/services/document_service.py`
  - 文档解析 (`processor.process_document`)
  - 向量生成 (`embedding_manager.encode`)
  - 向量存储 (`vector_store.add_documents`)

### 3. **错误日志增强** ✅
**问题**: 错误日志不够详细，难以诊断问题
**修复**: 添加详细的日志记录，包括文件信息、处理步骤等

**修复位置**:
- `knowledge-base/src/routes/documents_db.py`
  - `_process_document_async()` 函数
  - `_ensure_storage_dir()` 函数

### 4. **未使用的导入清理** ✅
**问题**: 代码中有未使用的导入
**修复**: 移除了未使用的 `get_db` 导入

**修复位置**:
- `knowledge-base/src/routes/documents_db.py`

## 测试建议

### 1. 检查服务状态
```bash
docker-compose ps knowledge-base
```

### 2. 查看日志
```bash
docker-compose logs knowledge-base --tail 100 -f
```

### 3. 测试上传
- 通过前端界面上传一个小文档（如 .txt 文件）
- 观察日志输出，确认处理流程正常

### 4. 检查文档状态
- 查看文档列表，确认状态从 `processing` 变为 `processed`
- 如果状态变为 `failed`，查看日志中的错误信息

## 可能的问题和解决方案

### 问题1: 文档状态一直显示 "processing"
**可能原因**:
- 后台任务没有执行
- 处理过程中出现错误但未正确更新状态

**解决方案**:
1. 查看日志中的 `[Background Task]` 相关日志
2. 检查是否有错误信息
3. 确认数据库连接正常

### 问题2: 文档处理失败
**可能原因**:
- 文件格式不支持
- 文件损坏
- 依赖库缺失（PyPDF2, python-docx, openpyxl）
- 向量数据库连接失败

**解决方案**:
1. 检查文件格式是否在支持列表中
2. 查看日志中的具体错误信息
3. 确认所有依赖库已安装
4. 检查向量数据库（Chroma/Qdrant）连接

### 问题3: 上传成功但处理不开始
**可能原因**:
- 后台任务未正确添加
- 文件路径问题

**解决方案**:
1. 检查日志中是否有 "starting background task" 消息
2. 确认文件已正确保存到存储目录
3. 检查文件路径是否正确

## 调试步骤

1. **查看上传日志**:
   ```bash
   docker-compose logs knowledge-base | grep -i "upload\|document"
   ```

2. **查看后台任务日志**:
   ```bash
   docker-compose logs knowledge-base | grep -i "background task"
   ```

3. **检查文件存储**:
   ```bash
   docker-compose exec knowledge-base ls -la /app/documents
   ```

4. **检查数据库状态**:
   ```bash
   docker-compose exec postgres psql -U postgres -d luminaos -c "SELECT id, filename, status FROM documents ORDER BY created_at DESC LIMIT 5;"
   ```

## 下一步

如果问题仍然存在，请：
1. 收集完整的错误日志
2. 确认文档格式和大小
3. 检查所有依赖服务是否正常运行
4. 查看数据库中的文档记录状态

