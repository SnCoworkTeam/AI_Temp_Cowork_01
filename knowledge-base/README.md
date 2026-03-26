# 企业知识库管理服务

企业AI平台的知识库管理服务，提供文档管理、向量检索、知识图谱等功能。

## 功能特性

### 核心功能
- 📄 **多格式文档支持**: PDF、Word、Excel、TXT、Markdown
- 🔍 **智能搜索**: 语义搜索、关键词搜索、混合搜索
- 📊 **向量存储**: 基于Qdrant的向量数据库（已从Chroma迁移）
- 🤖 **自动处理**: 文档解析、分块、向量化、质量评估
- 🔄 **异步处理**: 支持批量文档上传和异步处理
- 💾 **数据库存储**: 文档元数据和chunks存储在PostgreSQL

### 文档处理流程
- ✅ **文档上传**: 支持multipart/form-data格式
- ✅ **文本提取**: 自动提取PDF、Word、Excel等格式的文本
- ✅ **智能分块**: 基于语义和长度的智能分块
- ✅ **向量化**: 使用Sentence Transformers生成向量
- ✅ **质量评估**: 自动评估文档的完整性、可读性、相关性
- ✅ **状态管理**: 文档处理状态跟踪（uploaded、processing、processed、failed）

### 集成功能
- ✅ **向量协调服务集成**: 与vector-coordinator-service集成，统一向量管理
- ✅ **文档实体关联**: 与metadata-service集成，支持文档-实体关联

## 技术栈

- **框架**: FastAPI
- **向量存储**: Qdrant（已从Chroma迁移）
- **数据库**: PostgreSQL（文档元数据和chunks）
- **嵌入模型**: Sentence Transformers
- **文档处理**: PyPDF2, python-docx, openpyxl
- **缓存**: Redis（可选）

## API端点

### 文档管理

- `POST /api/documents/upload` - 上传文档（multipart/form-data格式）
- `GET /api/documents` - 获取文档列表（支持分页和过滤）
- `GET /api/documents/{id}` - 获取文档详情
- `GET /api/documents/{id}/chunks` - 获取文档chunks
- `DELETE /api/documents/{id}` - 删除文档

### 搜索功能

- `GET /api/documents/search` - 文档搜索（支持关键词和向量搜索）
- `POST /api/search/semantic` - 语义搜索
- `POST /api/search/keyword` - 关键词搜索
- `GET /api/search/hybrid` - 混合搜索

### 健康检查

- `GET /api/health` - 健康检查
- `GET /api/health/ready` - 就绪检查
- `GET /api/health/live` - 存活检查

## 配置

环境变量配置（参考 `.env.example`）：

```bash
# 服务配置
PORT=8004
DEBUG=false

# 向量存储配置
VECTOR_STORE_TYPE=qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=knowledge_base

# 嵌入模型配置
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
EMBEDDING_DIMENSION=384

# 文档处理配置
MAX_FILE_SIZE=104857600  # 100MB
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# 文档存储
DOCUMENT_STORAGE_DIR=./documents

# 数据库配置
DB_HOST=postgres
DB_PORT=5432
DB_USER=ai_user
DB_PASSWORD=ai_password
DB_NAME=ai_platform

# 向量协调服务配置
VECTOR_COORDINATOR_URL=http://vector-coordinator-service:8020
```

## 开发

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行服务
uvicorn src.main:app --reload --port 8004
```

### Docker开发

```bash
# 构建开发镜像
docker build -f Dockerfile.dev -t knowledge-base:dev .

# 运行容器
docker run -p 8004:8004 -v $(pwd):/app knowledge-base:dev
```

## 使用示例

### 上传文档

```bash
curl -X POST "http://localhost:8004/api/documents/upload" \
  -F "file=@document.pdf" \
  -F "tags=技术,文档" \
  -F "process_async=true"
```

### 语义搜索

```bash
curl -X POST "http://localhost:8004/api/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是人工智能？",
    "top_k": 10,
    "min_score": 0.5
  }'
```

### 关键词搜索

```bash
curl -X POST "http://localhost:8004/api/search/keyword" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["人工智能", "机器学习"],
    "match_all": false,
    "page": 1,
    "page_size": 20
  }'
```

## 注意事项

1. **向量存储**: 使用Qdrant向量数据库，需要Qdrant服务运行
2. **文档存储**: 上传的文档存储在 `DOCUMENT_STORAGE_DIR` 目录
3. **数据库**: 文档元数据和chunks存储在PostgreSQL数据库中
4. **嵌入模型**: 首次运行时会下载模型，可能需要一些时间
5. **文档处理**: 文档处理是异步的，上传后需要等待处理完成
6. **质量评估**: 文档处理完成后会自动进行质量评估

## 数据统计

当前SAP MM知识库数据：
- **文档数**: 21个（全部processed）
- **文档Chunks**: 447个
- **向量存储**: Qdrant

## 相关文档

- [SAP MM知识库访问指南](../SAP_MM_KNOWLEDGE_BASE_ACCESS_GUIDE.md)
- [阶段1-4实施总结](../STAGES_1-4_FINAL_SUMMARY.md)









