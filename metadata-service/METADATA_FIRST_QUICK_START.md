# 元数据前置意图识别快速开始

## 🚀 快速启用

### 1. 安装依赖

```bash
# 在agent-service容器中
pip install cachetools>=5.3.0
```

或通过requirements.txt（已更新）：
```bash
docker-compose exec agent-service pip install -r requirements.txt
```

### 2. 重启服务

```bash
docker-compose restart agent-service
```

### 3. 验证

检查日志确认元数据前置识别器已初始化：
```bash
docker logs enterprise-ai-agent-service | grep "Metadata-first"
```

应该看到：
```
Metadata-first intent recognizer initialized
```

## 📝 使用示例

### 测试邮件发送意图

```bash
curl -X POST http://localhost:8010/api/intelligent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "发送邮件给yubin.liu@pcitc.com，主题是会议通知",
    "user_id": "test_user"
  }'
```

**预期结果**：
- `task_type`: `tool_execution`
- `required_tools`: `["send_email"]`
- `confidence`: > 0.8

### 测试SAP查询意图

```bash
curl -X POST http://localhost:8010/api/intelligent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "查询销售订单",
    "user_id": "test_user"
  }'
```

**预期结果**：
- `task_type`: `tool_execution`
- `required_services`: 包含SAP相关服务
- `confidence`: > 0.7

## 🔧 配置

### 启用/禁用元数据前置

**默认启用**，如需禁用：

```python
# 在agent-service/src/core/conversation_agent.py
conversation_agent = ConversationAgent(use_metadata_first=False)
```

### 环境变量

确保以下服务URL配置正确：

```bash
METADATA_SERVICE_URL=http://metadata-service:8005
MCP_GATEWAY_URL=http://mcp-gateway:8001
KNOWLEDGE_BASE_URL=http://knowledge-base:8004
```

## 📊 监控

### 查看缓存效果

检查日志中的缓存命中：
```bash
docker logs enterprise-ai-agent-service | grep "Using cached"
```

### 查看元数据检索

检查元数据检索日志：
```bash
docker logs enterprise-ai-agent-service | grep "metadata"
```

## ⚠️ 故障排除

### 问题1：元数据前置识别器初始化失败

**症状**：日志显示 "Failed to initialize metadata-first recognizer"

**解决**：
1. 检查依赖是否安装：`pip list | grep cachetools`
2. 检查服务URL配置是否正确
3. 检查网络连接（服务间通信）

### 问题2：元数据检索超时

**症状**：识别延迟较高

**解决**：
1. 检查元数据服务是否正常运行
2. 检查网络延迟
3. 查看缓存命中率（应该>80%）

### 问题3：降级到基础识别

**症状**：日志显示 "Metadata-first recognition failed"

**解决**：
1. 检查具体错误信息
2. 确保元数据服务可访问
3. 系统会自动降级，不影响基本功能

## 🎯 性能指标

### 预期性能

- **首次识别**：~600-1300ms（包含元数据检索）
- **缓存命中**：~100-300ms（仅LLM理解）
- **缓存命中率**：>80%（稳定后）

### 优化建议

1. **提高缓存命中率**：相似查询会被缓存
2. **优化元数据检索**：确保元数据服务响应快速
3. **监控性能**：定期检查识别延迟

## 📚 相关文档

- `METADATA_FIRST_IMPLEMENTATION_COMPLETE.md` - 完整实施文档
- `METADATA_FIRST_INTENT_RECOGNITION_ANALYSIS.md` - 方案分析文档
- `METADATA_DRIVEN_INTENT_RECOGNITION_ARCHITECTURE.md` - 架构设计文档


