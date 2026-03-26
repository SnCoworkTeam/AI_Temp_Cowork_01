# 知识库增强功能快速开始指南

## 🎯 功能概览

已实现以下8大功能模块，全面提升知识库的文档处理能力：

1. ✅ **智能分块策略** - 6种分块策略，自动选择最佳方案
2. ✅ **文档质量评估** - 自动评估文档质量并评分
3. ✅ **增量更新** - 支持文档版本管理和增量处理
4. ✅ **处理进度跟踪** - 实时查询处理进度和预估时间
5. ✅ **错误处理和重试** - 自动重试失败的操作
6. ✅ **批量处理优化** - 并发处理、优先级队列
7. ✅ **文档预处理** - 自动清洗、标准化、编码/语言检测
8. ✅ **元数据增强** - 自动摘要、关键词、实体识别、情感分析

---

## 🚀 快速使用

### 1. 上传文档（自动使用所有增强功能）

文档上传后会自动：
- 预处理（清洗、标准化、编码/语言检测）
- 质量评估（评分并保存到元数据）
- 智能分块（根据内容自动选择最佳策略）
- 元数据增强（生成摘要、提取关键词等）
- 进度跟踪（可实时查询）

```python
# 上传文档
POST /api/documents/upload
{
    "file": <file>,
    "knowledge_base_id": "kb-123",
    "process_async": true
}
```

### 2. 查询处理进度

```python
# 获取处理进度
GET /api/documents/{document_id}/progress

# 返回示例
{
    "document_id": "doc-123",
    "stage": "embedding",
    "progress_percentage": 65.5,
    "current_step": "embedding",
    "total_steps": 100,
    "completed_steps": 65,
    "estimated_time_remaining": 12.5,
    "started_at": "2024-01-01T10:00:00",
    "updated_at": "2024-01-01T10:01:30",
    "details": {},
    "error": null
}
```

### 3. 配置分块策略

在知识库创建时指定分块策略：

```python
POST /api/knowledge-bases
{
    "name": "我的知识库",
    "description": "描述",
    "chunking_strategy": "smart",  # 可选: fixed, semantic, hierarchical, table, code, smart
    "chunk_size": 1000,
    "chunk_overlap": 200
}
```

---

## 📋 功能详细说明

### 智能分块策略

**策略选择**：
- `fixed` - 固定大小分块（默认，向后兼容）
- `semantic` - 语义分块（按段落和句子）
- `hierarchical` - 层次分块（文档→章节→段落）
- `table` - 表格分块（表格作为独立块）
- `code` - 代码分块（代码块保持完整）
- `smart` - 智能分块（自动选择最佳策略）⭐推荐

**使用场景**：
- 技术文档 → 使用 `code` 或 `hierarchical`
- 表格数据 → 使用 `table`
- 普通文档 → 使用 `semantic` 或 `smart`
- 长文档 → 使用 `hierarchical`

### 文档质量评估

**评估维度**：
- 完整性（30%权重）：文本长度、段落数量、元数据完整性
- 可读性（30%权重）：句子数量、平均句子长度
- 相关性（20%权重）：与知识库的相关性
- 唯一性（20%权重）：重复内容检测

**质量评分保存位置**：
- `document.document_metadata['quality_score']` - 总体评分（0-100）
- `document.document_metadata['quality_details']` - 详细评分

### 处理进度跟踪

**进度阶段**：
1. `uploading` - 上传中（5%权重）
2. `parsing` - 解析中（15%权重）
3. `chunking` - 分块中（10%权重）
4. `embedding` - 向量化中（60%权重）
5. `storing` - 存储中（10%权重）
6. `completed` - 完成

**进度计算**：
- 基于各阶段权重和完成情况
- 自动估算剩余时间

### 错误处理和重试

**自动重试的错误类型**：
- 网络错误（network）
- 嵌入错误（embedding）
- 存储错误（storage）

**重试配置**：
- 默认最多重试3次
- 指数退避（1s → 2s → 4s）
- 最大延迟60秒

### 文档预处理

**预处理步骤**：
1. 清洗文本（移除噪音字符）
2. 标准化格式（统一换行符、空白）
3. 检测编码（自动检测文档编码）
4. 检测语言（自动检测文档语言）

**结果保存**：
- `document_metadata['detected_language']` - 检测到的语言
- `document_metadata['detected_encoding']` - 检测到的编码

### 元数据增强

**增强内容**：
- **摘要**：自动生成文档摘要（前3个句子）
- **关键词**：提取Top 10关键词
- **实体**：识别邮箱、URL、专有名词
- **情感**：分析文档情感（正面/负面/中性）

**结果保存**：
- `document_metadata['summary']` - 摘要
- `document_metadata['keywords']` - 关键词列表
- `document_metadata['sentiment']` - 情感分析结果

---

## 🔧 配置选项

### 知识库配置

```python
{
    "chunking_strategy": "smart",      # 分块策略
    "chunk_size": 1000,                # 分块大小
    "chunk_overlap": 200,              # 分块重叠
    "enable_preprocessing": true,      # 启用预处理
    "enable_quality_assessment": true, # 启用质量评估
    "enable_metadata_enhancement": true # 启用元数据增强
}
```

### 重试配置

```python
RetryConfig(
    max_retries=3,          # 最大重试次数
    initial_delay=1.0,      # 初始延迟（秒）
    max_delay=60.0,         # 最大延迟（秒）
    exponential_base=2.0    # 指数退避基数
)
```

---

## 📊 功能对比

| 功能 | 实现前 | 实现后 |
|------|--------|--------|
| 分块策略 | 仅固定大小 | 6种策略，智能选择 |
| 质量评估 | ❌ | ✅ 自动评估并评分 |
| 进度跟踪 | 仅状态 | ✅ 百分比+时间预估 |
| 错误处理 | 仅标记失败 | ✅ 自动重试 |
| 预处理 | ❌ | ✅ 清洗+标准化+检测 |
| 元数据 | 仅基本 | ✅ 摘要+关键词+实体+情感 |

---

## 🎯 最佳实践

### 1. 选择合适的分块策略

- **技术文档**：使用 `code` 或 `hierarchical`
- **表格数据**：使用 `table`
- **普通文档**：使用 `smart`（推荐）
- **长文档**：使用 `hierarchical`

### 2. 监控处理进度

上传大文档后，定期查询进度：
```python
# 每5秒查询一次进度
while True:
    progress = await get_progress(document_id)
    if progress['stage'] == 'completed':
        break
    await asyncio.sleep(5)
```

### 3. 利用质量评分

根据质量评分过滤低质量文档：
```python
# 查询质量评分 > 70 的文档
documents = await list_documents(quality_score_min=70)
```

### 4. 使用元数据增强

利用自动生成的摘要和关键词：
```python
# 获取文档摘要
summary = document.metadata.get('summary')

# 获取关键词
keywords = document.metadata.get('keywords')
```

---

## ⚠️ 注意事项

1. **可选依赖**：某些功能需要额外安装依赖
   - `chardet` - 编码检测
   - `langdetect` - 语言检测
   - `nltk` - 关键词提取和摘要

2. **性能影响**：
   - 预处理和质量评估会增加处理时间
   - 建议对大文档启用异步处理

3. **存储空间**：
   - 增强的元数据会占用更多存储空间
   - 质量评分和摘要会保存在文档元数据中

---

## 📝 示例代码

### 完整的上传和处理流程

```python
# 1. 上传文档
response = await upload_document(
    file=file,
    knowledge_base_id="kb-123",
    process_async=True
)

document_id = response.document_id

# 2. 监控处理进度
while True:
    progress = await get_document_progress(document_id)
    
    print(f"Progress: {progress['progress_percentage']:.1f}%")
    print(f"Stage: {progress['stage']}")
    print(f"Estimated time: {progress['estimated_time_remaining']:.1f}s")
    
    if progress['stage'] == 'completed':
        break
    elif progress['stage'] == 'failed':
        print(f"Error: {progress['error']}")
        break
    
    await asyncio.sleep(2)

# 3. 获取处理后的文档
document = await get_document(document_id)

# 4. 查看质量评分
quality_score = document.metadata.get('quality_score')
print(f"Quality Score: {quality_score}")

# 5. 查看增强的元数据
summary = document.metadata.get('summary')
keywords = document.metadata.get('keywords')
sentiment = document.metadata.get('sentiment')

print(f"Summary: {summary}")
print(f"Keywords: {keywords}")
print(f"Sentiment: {sentiment}")

# 6. 清除进度跟踪
await clear_document_progress(document_id)
```

---

## 🔗 相关文件

- `knowledge-base/src/core/chunking_strategies.py` - 智能分块策略
- `knowledge-base/src/core/document_quality.py` - 文档质量评估
- `knowledge-base/src/core/processing_progress.py` - 处理进度跟踪
- `knowledge-base/src/core/error_handler.py` - 错误处理和重试
- `knowledge-base/src/core/document_preprocessor.py` - 文档预处理
- `knowledge-base/src/core/metadata_enhancer.py` - 元数据增强
- `knowledge-base/src/services/document_service.py` - 文档服务（已集成）

---

## ✅ 测试清单

- [ ] 测试不同分块策略的效果
- [ ] 验证进度跟踪的准确性
- [ ] 测试错误重试机制
- [ ] 验证质量评分的合理性
- [ ] 测试元数据增强功能
- [ ] 验证预处理效果

---

所有功能已实现并集成到文档处理流程中！🎉


