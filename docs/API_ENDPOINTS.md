# API端点文档

## 统一意图服务API端点

### 端点信息

**服务**: Agent Service  
**基础URL**: `http://localhost:8010`  
**路径前缀**: `/api/v1/unified`

### 端点列表

#### 1. POST /api/v1/unified/process

**描述**: 统一意图处理（POST方式，支持流式响应）

**请求体**:
```json
{
  "user_input": "创建采购订单",
  "user_id": "user123",
  "session_id": "session456",
  "context": {
    "use_streaming_llm": true
  }
}
```

**响应**: Server-Sent Events (SSE) 流式响应

**示例**:
```bash
curl -X POST http://localhost:8010/api/v1/unified/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "创建采购订单",
    "user_id": "test_user",
    "session_id": "test_session"
  }'
```

#### 2. GET /api/v1/unified/process

**描述**: 统一意图处理（GET方式，支持SSE流式响应）

**查询参数**:
- `input` (required): 用户输入
- `session_id` (optional): 会话ID
- `user_id` (optional): 用户ID
- `use_streaming_llm` (optional): 是否使用流式LLM（"true"/"false"）

**响应**: Server-Sent Events (SSE) 流式响应

**示例**:
```bash
curl "http://localhost:8010/api/v1/unified/process?input=创建采购订单&user_id=test_user&session_id=test_session"
```

### 通过API Gateway访问

**基础URL**: `http://localhost:8080`  
**路径**: `/api/agents/api/v1/unified/process`

**示例**:
```bash
curl -X POST http://localhost:8080/api/agents/api/v1/unified/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "创建采购订单",
    "user_id": "test_user",
    "session_id": "test_session"
  }'
```

---

## 其他重要API端点

### Agent Service

- `GET /api/v1/health` - 健康检查
- `GET /docs` - API文档（Swagger UI）
- `POST /api/v1/agents/{agent_id}/execute` - 执行智能体
- `GET /api/v1/agents` - 获取智能体列表

### API Gateway

- `GET /health` - 健康检查
- `GET /metrics` - Prometheus指标
- `GET /api/docs` - API文档

---

## 注意事项

1. **统一意图服务端点**: 位于Agent Service (`http://localhost:8010/api/v1/unified/process`)
2. **流式响应**: 统一意图服务使用SSE返回流式结果
3. **认证**: 生产环境需要配置JWT认证
4. **限流**: API Gateway已配置限流（60请求/分钟）

