# 统一意图识别LLM增强 - 部署指南

**版本**: v2.0  
**部署日期**: 2025-12-02

---

## 📋 部署前准备

### 1. 环境要求

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose（可选）

### 2. 依赖安装

```bash
# 安装Python依赖
pip install httpx langchain-openai fastapi uvicorn sqlalchemy pydantic

# 或使用requirements.txt
pip install -r requirements.txt
```

### 3. 环境变量配置

创建或更新 `.env` 文件：

```bash
# LLM配置（DeepSeek）
DEEPSEEK_API_KEY=your-deepseek-api-key
# 或使用
OPENAI_API_KEY=your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.3
LLM_TIMEOUT=10.0

# 统一意图识别配置
UNIFIED_INTENT_USE_LLM=true
LLM_CACHE_TTL=3600
LLM_FALLBACK_TO_RULES=true

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/enterprise_ai
REDIS_URL=redis://localhost:6379/0
```

---

## 🚀 部署步骤

### 方式1: Docker Compose部署（推荐）

```bash
# 1. 确保docker-compose.yml包含新服务
docker-compose up -d

# 2. 检查服务状态
docker-compose ps

# 3. 查看日志
docker-compose logs -f unified-intent-service
```

### 方式2: 直接部署

```bash
# 1. 克隆代码
git clone <repository-url>
cd enterprise-ai-platform

# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置环境变量
export DEEPSEEK_API_KEY=your-key
export LLM_BASE_URL=https://api.deepseek.com

# 4. 运行服务
python -m uvicorn api.unified_intent_api:app --host 0.0.0.0 --port 8002
```

---

## 🔧 配置说明

### LLM配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | - |
| `LLM_BASE_URL` | LLM API地址 | `https://api.deepseek.com` |
| `LLM_MODEL` | 模型名称 | `deepseek-chat` |
| `LLM_TEMPERATURE` | 温度参数 | `0.3` |
| `LLM_TIMEOUT` | 超时时间（秒） | `10.0` |

### 统一意图识别配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `UNIFIED_INTENT_USE_LLM` | 是否使用LLM | `true` |
| `LLM_CACHE_TTL` | 缓存TTL（秒） | `3600` |
| `LLM_FALLBACK_TO_RULES` | LLM失败时降级到规则 | `true` |

---

## ✅ 验证部署

### 1. 健康检查

```bash
curl http://localhost:8002/health
```

预期响应：
```json
{
  "status": "healthy",
  "service": "unified_intent_service",
  "timestamp": "2025-12-02T..."
}
```

### 2. 测试意图理解

```bash
curl -X POST http://localhost:8002/api/v1/intent/understand \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "我需要创建采购订单，供应商ABC，物料MAT001，数量100"
  }'
```

预期响应：
```json
{
  "user_input": "我需要创建采购订单...",
  "base_intent": "tool_execution",
  "confidence": 0.90,
  "suggested_activities": [...],
  "execution_suggestions": [...]
}
```

### 3. 检查日志

```bash
# Docker方式
docker-compose logs unified-intent-service

# 直接部署
tail -f logs/unified_intent_service.log
```

---

## 🔍 故障排查

### 问题1: LLM初始化失败

**症状**: 日志显示 "LLM客户端初始化失败"

**解决方案**:
1. 检查API密钥是否正确
2. 检查网络连接（能否访问DeepSeek API）
3. 检查环境变量是否设置

```bash
# 测试API连接
curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
     -H "Content-Type: application/json" \
     https://api.deepseek.com/v1/models
```

### 问题2: 降级到规则匹配

**症状**: 所有请求都使用规则匹配，没有LLM分析

**解决方案**:
1. 检查 `UNIFIED_INTENT_USE_LLM` 是否为 `true`
2. 检查LLM客户端是否初始化成功
3. 查看日志中的错误信息

### 问题3: 语义引擎查询失败

**症状**: 日志显示 "语义引擎查询失败"

**解决方案**:
1. 检查数据库连接
2. 检查业务活动数据是否存在
3. 检查语义引擎服务是否正常运行

---

## 📊 监控指标

### 关键指标

- **LLM调用成功率**: 应 > 95%
- **平均响应时间**: 应 < 2秒
- **缓存命中率**: 应 > 50%
- **降级率**: 应 < 5%

### 监控命令

```bash
# 查看缓存统计
curl http://localhost:8002/api/v1/intent/cache/stats

# 查看服务健康
curl http://localhost:8002/health
```

---

## 🔄 回滚方案

如果部署后出现问题，可以快速回滚：

```bash
# 方式1: 禁用LLM（使用环境变量）
export UNIFIED_INTENT_USE_LLM=false

# 方式2: 回滚代码
git checkout <previous-commit>
docker-compose restart unified-intent-service

# 方式3: 使用旧版本镜像
docker-compose pull unified-intent-service:previous-version
docker-compose up -d unified-intent-service
```

---

## 📝 更新日志

### v2.0 (2025-12-02)
- ✅ 集成DeepSeek LLM作为统一入口
- ✅ 实现动态融合策略
- ✅ 添加语义引擎适配器
- ✅ 支持自动参数填充
- ✅ 实现多层级降级机制

---

**部署状态**: ✅ 准备就绪  
**文档版本**: v2.0  
**最后更新**: 2025-12-02
