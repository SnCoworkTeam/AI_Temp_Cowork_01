# 文档处理流程说明

## 📋 处理流程概览

文档上传后会经过以下9个处理阶段：

```
上传 → 解析 → 预处理 → 质量评估 → 元数据增强 → 分块 → 向量化 → 存储块 → 存储向量 → 完成
```

## 🔄 详细处理阶段

### 1. 上传阶段 (UPLOADING) - 5% 权重
- **状态**: `uploading`
- **操作**: 文件上传到服务器
- **时间**: 通常 < 1秒

### 2. 解析阶段 (PARSING) - 15% 权重
- **状态**: `processing` (stage: `parsing`)
- **操作**: 
  - 解析文档内容（PDF/Word/Excel等）
  - 提取文本和元数据
- **时间**: 通常 2-10秒（取决于文档大小）

### 3. 预处理阶段 (PREPROCESSING) - 包含在分块阶段
- **状态**: `processing` (stage: `chunking`, step: `preprocessing`)
- **操作**:
  - 清洗文本（移除噪音字符）
  - 标准化格式
  - 检测编码和语言
- **时间**: 通常 1-3秒

### 4. 质量评估阶段 (QUALITY_ASSESSMENT) - 包含在分块阶段
- **状态**: `processing` (step: `quality_assessment`)
- **操作**:
  - 评估文档完整性
  - 评估可读性
  - 检测重复内容
  - 计算质量评分
- **时间**: 通常 1-2秒

### 5. 元数据增强阶段 (METADATA_ENHANCEMENT) - 包含在分块阶段
- **状态**: `processing` (step: `metadata_enhancement`)
- **操作**:
  - 生成文档摘要
  - 提取关键词
  - 识别实体
  - 情感分析
- **时间**: 通常 2-5秒

### 6. 分块阶段 (CHUNKING) - 10% 权重
- **状态**: `processing` (stage: `chunking`)
- **操作**:
  - 将文档分割成多个块
  - 根据策略（固定大小/语义/层次等）分块
- **时间**: 通常 1-5秒（取决于文档大小和分块策略）

### 7. **向量化阶段 (EMBEDDING) - 60% 权重** ⭐
- **状态**: `processing` (stage: `embedding`)
- **操作**:
  - 为每个文档块生成嵌入向量
  - 使用嵌入模型（如 text-embedding-ada-002）将文本转换为向量
  - 这是**最耗时的阶段**
- **时间**: 通常 5-30秒（取决于块数量和模型速度）
- **进度**: 显示 `completed_steps / total_steps`（已完成块数/总块数）

### 8. 存储块阶段 (STORING_CHUNKS) - 包含在存储阶段
- **状态**: `processing` (stage: `storing`, step: `saving_chunks`)
- **操作**:
  - 将文档块和嵌入向量保存到数据库
- **时间**: 通常 1-3秒

### 9. 存储向量阶段 (STORING_VECTORS) - 包含在存储阶段
- **状态**: `processing` (stage: `storing`, step: `storing_vectors`)
- **操作**:
  - 将向量存储到向量数据库（Chroma/Weaviate）
- **时间**: 通常 2-5秒

### 10. 完成阶段 (COMPLETED)
- **状态**: `processed`
- **操作**: 更新文档状态和元数据
- **时间**: < 1秒

## 📊 进度权重分配

各阶段在总进度中的权重：

| 阶段 | 权重 | 说明 |
|------|------|------|
| 上传 | 5% | 快速完成 |
| 解析 | 15% | 文档解析 |
| 分块 | 10% | 文档分块 |
| **向量化** | **60%** | **最耗时，最重要** |
| 存储 | 10% | 保存到数据库 |

## 🔍 如何查看处理进度

### 方法 1: 通过 API 查询

```bash
# 查询文档处理进度
curl http://localhost:8004/api/documents/{document_id}/progress

# 或通过 API Gateway
curl http://localhost:8080/api/knowledge/documents/{document_id}/progress
```

**响应示例**：
```json
{
  "document_id": "xxx",
  "stage": "embedding",  // 当前阶段
  "progress_percentage": 45.5,  // 总进度百分比
  "current_step": "embedding",  // 当前步骤
  "total_steps": 100,  // 总块数
  "completed_steps": 45,  // 已完成块数
  "estimated_time_remaining": 12.5,  // 预估剩余时间（秒）
  "started_at": "2024-02-15T10:00:00",
  "updated_at": "2024-02-15T10:01:30"
}
```

### 方法 2: 查看文档状态

```bash
# 获取文档详情
curl http://localhost:8004/api/documents/{document_id}
```

文档状态字段：
- `uploading` - 上传中
- `processing` - 处理中（包括所有处理阶段）
- `processed` - 处理完成
- `failed` - 处理失败

### 方法 3: 查看后端日志

查看知识库服务的日志输出：

```bash
# Docker
docker logs -f knowledge-base

# 直接运行
# 查看控制台输出
```

日志会显示：
```
Document {document_id} started stage: embedding
Document {document_id} completed stage: embedding
```

## ⚡ 向量化阶段详解

### 什么时候开始向量化？

向量化在**第6步**开始，在以下步骤完成后：
1. ✅ 文档解析完成
2. ✅ 预处理完成（如果启用）
3. ✅ 质量评估完成（如果启用）
4. ✅ 元数据增强完成（如果启用）
5. ✅ 文档分块完成

### 向量化过程

1. **准备文本块**：
   - 从分块阶段获取所有文档块
   - 提取每个块的内容

2. **生成嵌入向量**：
   - 使用嵌入模型（如 `text-embedding-ada-002`）
   - 为每个块生成一个向量（通常是 1536 维）
   - 批量处理以提高效率

3. **进度更新**：
   - 每完成一个块的向量化，更新 `completed_steps`
   - 进度百分比 = (已完成块数 / 总块数) × 60% + 之前阶段的进度

### 如何判断是否已开始向量化？

查看处理进度，如果：
- `stage` = `"embedding"` → **正在向量化**
- `stage` = `"chunking"` → 还在分块，未开始向量化
- `stage` = `"storing"` → 向量化已完成，正在存储

## 📈 进度百分比计算

总进度 = 各阶段进度 × 权重

例如：
- 上传完成：5%
- 解析完成：5% + 15% = 20%
- 分块完成：20% + 10% = 30%
- 向量化 50% 完成：30% + (60% × 50%) = 60%
- 向量化 100% 完成：30% + 60% = 90%
- 存储完成：90% + 10% = 100%

## 🐛 常见问题

### Q: 文档一直显示 "processing"，如何知道是否在向量化？

A: 查询处理进度 API，查看 `stage` 字段：
- `"embedding"` = 正在向量化
- `"chunking"` = 还在分块
- `"storing"` = 向量化完成，正在存储

### Q: 向量化需要多长时间？

A: 取决于：
- 文档块数量（块越多，时间越长）
- 嵌入模型速度（不同模型速度不同）
- 服务器性能

通常：
- 小文档（< 10块）：5-10秒
- 中等文档（10-50块）：10-30秒
- 大文档（> 50块）：30秒-几分钟

### Q: 如何加速向量化？

A: 
1. 使用更快的嵌入模型
2. 增加批量处理大小
3. 使用 GPU 加速（如果支持）
4. 优化分块策略（减少块数量）

### Q: 向量化失败怎么办？

A: 
1. 检查后端日志查看错误信息
2. 检查嵌入模型服务是否正常
3. 检查网络连接
4. 系统会自动重试（最多3次）

## 🔧 检查工具

使用以下工具快速检查文档处理状态：

```bash
# 检查文档处理进度
python check_document_progress.py {document_id}
```

## 📝 总结

- **向量化是第6步**，在分块之后开始
- **向量化是最耗时的阶段**（占60%权重）
- **通过查询进度 API 可以实时查看**是否已开始向量化
- **`stage = "embedding"`** 表示正在向量化
- **`completed_steps / total_steps`** 显示向量化进度


