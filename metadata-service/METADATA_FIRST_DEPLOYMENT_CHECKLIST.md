# 元数据前置意图识别部署检查清单

## ✅ 部署前检查

### 1. 依赖安装

```bash
# 检查cachetools是否已安装
docker exec enterprise-ai-agent-service pip list | grep cachetools

# 如果未安装，执行：
docker exec enterprise-ai-agent-service pip install cachetools>=5.3.0
```

### 2. 代码文件检查

```bash
# 检查核心文件是否存在
ls -la agent-service/src/core/metadata_first_intent_recognizer.py
ls -la agent-service/src/core/conversation_agent.py

# 检查requirements.txt是否包含cachetools
grep cachetools agent-service/requirements.txt
```

### 3. 服务配置检查

```bash
# 检查环境变量
docker exec enterprise-ai-agent-service env | grep -E "METADATA_SERVICE_URL|MCP_GATEWAY_URL|KNOWLEDGE_BASE_URL"
```

应该看到：
- `METADATA_SERVICE_URL=http://metadata-service:8005`
- `MCP_GATEWAY_URL=http://mcp-gateway:8001`
- `KNOWLEDGE_BASE_URL=http://knowledge-base:8004`

## 🔄 部署步骤

### 1. 安装依赖

```bash
docker exec enterprise-ai-agent-service pip install cachetools>=5.3.0
```

### 2. 重启服务

```bash
docker-compose restart agent-service
```

### 3. 等待服务启动

```bash
# 等待15-20秒
Start-Sleep -Seconds 20
```

### 4. 验证初始化

```bash
# 检查日志
docker logs enterprise-ai-agent-service --tail 50 | grep -i "metadata-first"

# 应该看到：
# "Metadata-first intent recognizer initialized"
```

如果看到 "Failed to initialize metadata-first recognizer"，检查：
1. cachetools是否已安装
2. 是否有循环导入错误
3. 服务URL配置是否正确

## 🧪 功能测试

### 测试1：邮件发送意图

```bash
curl -X POST http://localhost:8010/api/intelligent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "发送邮件给yubin.liu@pcitc.com，主题是会议通知",
    "user_id": "test_user"
  }'
```

**预期**：
- `task_type`: `tool_execution`
- `required_tools`: 包含 `send_email`
- `confidence`: > 0.7

### 测试2：SAP查询意图

```bash
curl -X POST http://localhost:8010/api/intelligent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "查询销售订单",
    "user_id": "test_user"
  }'
```

**预期**：
- `task_type`: `tool_execution`
- `required_services`: 包含SAP相关服务
- `confidence`: > 0.6

### 测试3：缓存效果

```bash
# 第一次调用（应该检索元数据）
time curl -X POST http://localhost:8010/api/intelligent \
  -H "Content-Type: application/json" \
  -d '{"message": "发送邮件", "user_id": "test"}'

# 第二次调用（应该使用缓存，更快）
time curl -X POST http://localhost:8010/api/intelligent \
  -H "Content-Type: application/json" \
  -d '{"message": "发送邮件", "user_id": "test"}'
```

## 🔍 故障排除

### 问题1：循环导入错误

**症状**：
```
cannot import name 'MetadataFirstIntentRecognizer' from partially initialized module
```

**解决**：
- ✅ 已修复：使用延迟导入（在函数内部导入）

### 问题2：cachetools未安装

**症状**：
```
No module named 'cachetools'
```

**解决**：
```bash
docker exec enterprise-ai-agent-service pip install cachetools>=5.3.0
docker-compose restart agent-service
```

### 问题3：元数据服务不可用

**症状**：
- 日志显示 "Failed to search tools" 或类似错误
- 识别延迟较高

**解决**：
1. 检查元数据服务是否运行：`docker ps | grep metadata-service`
2. 检查服务URL配置
3. 系统会自动降级，不影响基本功能

### 问题4：识别器未初始化

**症状**：
- 日志中没有 "Metadata-first intent recognizer initialized"
- 但也没有错误信息

**检查**：
```bash
docker exec enterprise-ai-agent-service python -c "
import sys
sys.path.insert(0, '/app')
from src.core.conversation_agent import conversation_agent
print(f'Metadata first enabled: {conversation_agent.use_metadata_first}')
print(f'Has recognizer: {conversation_agent.metadata_first_recognizer is not None}')
"
```

**预期输出**：
```
Metadata first enabled: True
Has recognizer: True
```

## 📊 性能监控

### 查看缓存命中率

```bash
# 查看缓存相关的日志
docker logs enterprise-ai-agent-service | grep -i "cached"
```

### 查看元数据检索

```bash
# 查看元数据检索日志
docker logs enterprise-ai-agent-service | grep -i "metadata"
```

### 查看识别延迟

```bash
# 查看意图识别相关的日志
docker logs enterprise-ai-agent-service | grep -i "intent"
```

## ✅ 验证清单

- [ ] cachetools已安装
- [ ] 服务已重启
- [ ] 日志显示 "Metadata-first intent recognizer initialized"
- [ ] 测试邮件发送意图识别成功
- [ ] 测试SAP查询意图识别成功
- [ ] 缓存功能正常（第二次调用更快）
- [ ] 降级策略正常（元数据服务不可用时仍能工作）

## 🎯 完成标志

当看到以下日志时，表示部署成功：

```
Metadata-first intent recognizer initialized
Agent Service started successfully
```

并且测试请求能够正确识别意图并返回结果。


