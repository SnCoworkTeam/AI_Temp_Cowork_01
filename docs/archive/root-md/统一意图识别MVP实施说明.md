# 统一意图识别MVP实施说明（阶段1）

## 📋 实施状态

✅ **已完成**：
1. 创建 `UnifiedIntentMVP` 类（`services/unified_intent_mvp.py`）
2. 创建API路由端点（`agent-service/src/routes/unified_intent_mvp.py`）
3. 注册路由到主应用（`agent-service/src/main.py`）
4. 实现SSE流式响应

## 🚀 使用方法

### API端点

**POST** `/api/v1/unified/process`
**GET** `/api/v1/unified/process?input={user_input}&session_id={session_id}&user_id={user_id}`

### 请求示例

```bash
# POST方式
curl -X POST "http://localhost:8000/api/v1/unified/process" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "查询采购订单",
    "context": {
      "user_id": "user123",
      "session_id": "session456"
    }
  }'

# GET方式（用于SSE）
curl -N "http://localhost:8000/api/v1/unified/process?input=查询采购订单&user_id=user123&session_id=session456"
```

### 响应格式（SSE）

```
data: {"stage":"received","status":"success","progress":5,"message":"请求已接收，正在处理...","timestamp":"2024-01-01T12:00:00"}

data: {"stage":"processing","status":"analyzing","progress":20,"message":"正在分析用户意图...","timestamp":"2024-01-01T12:00:01"}

data: {"stage":"intent_complete","status":"complete","progress":50,"result":{"task_type":"tool_execution","confidence":0.85},"timestamp":"2024-01-01T12:00:02"}

data: {"stage":"execution","status":"executing","progress":60,"message":"正在执行任务...","timestamp":"2024-01-01T12:00:03"}

data: {"stage":"complete","status":"success","progress":100,"result":{...},"timestamp":"2024-01-01T12:00:05"}
```

## 🔧 前端集成示例

```typescript
// 使用EventSource接收SSE流
const eventSource = new EventSource(
  `/api/v1/unified/process?input=${encodeURIComponent(userInput)}&user_id=${userId}&session_id=${sessionId}`
);

eventSource.onmessage = (event) => {
  const chunk = JSON.parse(event.data);
  
  // 更新进度条
  updateProgress(chunk.progress);
  
  // 显示阶段信息
  showStageMessage(chunk.stage, chunk.message);
  
  // 如果有结果，更新UI
  if (chunk.result) {
    updateResult(chunk.result);
  }
  
  // 完成或错误
  if (chunk.stage === 'complete' || chunk.stage === 'error') {
    eventSource.close();
  }
};

eventSource.onerror = (error) => {
  console.error('SSE连接错误:', error);
  eventSource.close();
};
```

## 📊 处理阶段说明

1. **received** (5%)：请求已接收
2. **processing** (20%)：开始处理
3. **intent_complete** (50%)：意图分析完成
4. **execution** (60%)：开始执行
5. **complete** (100%)：执行完成

## ⚠️ 注意事项

1. **延迟加载**：组件采用延迟加载，避免循环依赖
2. **错误处理**：所有错误都会被捕获并返回错误信息
3. **超时控制**：语义引擎查询有3秒超时限制
4. **向后兼容**：不影响现有系统，可以并行运行

## 🧪 测试建议

1. **功能测试**：
   - 测试简单查询
   - 测试工具执行
   - 测试复杂任务

2. **性能测试**：
   - 响应时间
   - 并发处理能力
   - 错误恢复能力

3. **集成测试**：
   - 与现有系统集成
   - 前端SSE连接
   - 错误场景处理

## 📝 下一步计划

- [ ] 添加单元测试
- [ ] 添加集成测试
- [ ] 性能优化
- [ ] 错误处理增强
- [ ] 日志记录完善




