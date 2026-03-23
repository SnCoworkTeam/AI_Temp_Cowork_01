# 向量协调服务

## 📋 概述

向量协调服务（Vector Coordinator Service）是阶段1的核心服务，提供统一的向量空间管理、多模态向量融合和向量相似度搜索功能。

## ✨ 功能特性

- 🔗 **统一向量模型管理**: 确保所有服务使用相同的模型和版本
- 🔀 **多模态向量融合**: 支持加权平均、拼接、注意力机制等融合策略
- 🔍 **向量相似度服务**: 提供向量相似度计算和搜索功能
- 📊 **向量注册管理**: 统一管理来自不同服务的向量
- 💾 **Qdrant集成**: 持久化向量存储，支持HNSW索引
- ⚡ **多级缓存**: L1内存缓存 + L2 Redis缓存，显著提升性能
- 📦 **批量写入**: 异步批量写入优化，提升吞吐量

## 🚀 快速开始

### 安装依赖

```bash
cd vector-coordinator-service
pip install -r requirements.txt
```

### 运行服务

```bash
python -m src.main
```

或使用uvicorn：

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8020
```

## 📡 API端点

### 向量管理

- `POST /api/vectors/register` - 注册向量（支持priority参数：realtime、normal、batch）
- `GET /api/vectors/info/{entity_uri}` - 获取向量信息
- `GET /api/vectors/stats` - 获取统计信息（包含缓存和批量写入统计）

### 向量融合

- `POST /api/vectors/fuse` - 融合多个模态的向量

### 相似度搜索

- `POST /api/vectors/similar` - 查找相似向量

### 缓存管理

- `GET /api/vectors/cache/stats` - 获取缓存统计
- `DELETE /api/vectors/cache` - 清除缓存

### 健康检查

- `GET /health` - 健康检查
- `GET /health/ready` - 就绪检查

## 🔧 配置

通过环境变量或`.env`文件配置：

```env
HOST=0.0.0.0
PORT=8020
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
FUSION_STRATEGY=weighted_average
SIMILARITY_METRIC=cosine

# Qdrant配置
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=vectors
QDRANT_INDEX_TYPE=hnsw

# 缓存配置
CACHE_ENABLED=true
CACHE_L1_MAX_SIZE=1000
CACHE_L1_TTL=60
CACHE_L2_TTL=300
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# 批量写入配置
BATCH_WRITER_ENABLED=true
BATCH_WRITER_INTERVAL_SEC=5
BATCH_WRITER_BATCH_SIZE=100
```

## 📝 使用示例

### 注册向量

```bash
curl -X POST http://localhost:8020/api/vectors/register \
  -H "Content-Type: application/json" \
  -d '{
    "entity_uri": "entity://metadata/data_asset/123",
    "modality": "metadata",
    "vector": [0.1, 0.2, ...],
    "metadata": {"name": "客户数据"}
  }'
```

### 融合向量

```bash
curl -X POST http://localhost:8020/api/vectors/fuse \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "metadata": [0.1, 0.2, ...],
      "knowledge": [0.3, 0.4, ...]
    },
    "weights": {
      "metadata": 0.5,
      "knowledge": 0.5
    }
  }'
```

### 查找相似向量

```bash
curl -X POST http://localhost:8020/api/vectors/similar \
  -H "Content-Type: application/json" \
  -d '{
    "query": "客户",
    "modalities": ["metadata", "knowledge"],
    "limit": 10
  }'
```

## 📊 性能优化

### 已实现的优化

1. **Qdrant集成**: 持久化向量存储，支持HNSW索引
2. **多级缓存**: L1内存缓存 + L2 Redis缓存，性能提升44x
3. **批量写入**: 异步批量写入，提升吞吐量
4. **索引优化**: HNSW索引配置，提升搜索性能

### 性能测试结果

- **向量搜索**: 44x性能提升（相比无缓存）
- **统一搜索**: 18.7x性能提升（集成向量搜索后）

## 🎯 阶段1完成情况

1. ✅ 验证统一向量模型管理的可行性
2. ✅ 验证多模态向量融合策略
3. ✅ 验证向量相似度计算性能
4. ✅ 完成Qdrant向量数据库集成
5. ✅ 实现多级缓存优化
6. ✅ 实现批量写入优化

## 📊 当前状态

**阶段**: 阶段1完成  
**状态**: ✅ 生产就绪  
**集成**: 已集成到api-gateway统一搜索

## 📚 相关文档

- [阶段1实施报告](../STAGE1_COMPLETE_SUMMARY_FINAL.md)
- [Qdrant集成报告](../STAGE1_QDRANT_INTEGRATION_REPORT.md)
- [性能优化报告](../STAGE1_PERFORMANCE_OPTIMIZATION_REPORT.md)




