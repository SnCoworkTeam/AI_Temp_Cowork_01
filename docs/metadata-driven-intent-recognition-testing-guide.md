# 基于元数据的意图识别 - 测试验证指南

## 一、功能验证清单

### ✅ 已实现的功能

1. **实时元数据查询引擎** (`RealtimeMetadataEngine`)
   - 文件：`metadata-service/src/core/realtime_metadata_engine.py`
   - API：`POST /api/v1/metadata/realtime-query`
   - 功能：并行查询数据资产、AI模型、业务实体、工作流

2. **元数据增强的提示词构建器** (`MetadataEnhancedPromptBuilder`)
   - 文件：`agent-service/src/core/metadata_enhanced_prompt.py`
   - 集成：已集成到`ConversationAgent`
   - 功能：自动查询元数据并构建增强提示词

3. **语义服务发现** (`SemanticServiceDiscovery`)
   - 文件：`metadata-service/src/core/semantic_service_discovery.py`
   - 功能：基于knowledge-base的向量搜索

4. **元数据驱动执行编排** (`MetadataDrivenExecutor`)
   - 文件：`agent-service/src/core/metadata_driven_executor.py`
   - 集成：已集成到`OrchestrationEngine`
   - 功能：使用元数据增强路由决策

5. **元数据知识图谱** (`MetadataGraph`)
   - 文件：`metadata-service/src/core/metadata_graph.py`
   - 功能：PostgreSQL递归CTE查询

6. **用户行为模式分析** (`UserPatternAnalyzer`)
   - 文件：`metadata-service/src/core/user_pattern_analyzer.py`
   - 功能：分析用户行为模式

---

## 二、验证步骤

### 步骤1: 检查服务状态

```bash
# 检查服务是否运行
docker ps --filter "name=metadata-service" --filter "name=agent-service"

# 检查服务健康状态
curl http://localhost:8005/api/health  # metadata-service
curl http://localhost:8010/api/v1/health  # agent-service
```

### 步骤2: 测试实时元数据查询

```bash
curl -X POST http://localhost:8005/api/v1/metadata/realtime-query \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "查询SAP销售订单",
    "context": {
      "user_id": "test_user",
      "session_id": "test_session"
    },
    "use_cache": true,
    "limit_per_type": 5
  }'
```

**预期结果**：
- 返回状态码：200
- 包含`metadata`字段，其中有：
  - `data_assets`: 数据资产列表
  - `ai_models`: AI模型列表
  - `business_entities`: 业务实体列表
  - `workflows`: 工作流列表
  - `query_time`: 查询时间（秒）

### 步骤3: 测试意图识别（带元数据增强）

```bash
curl -X POST http://localhost:8010/api/v1/chat/intelligent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "查询SAP销售订单",
    "conversation_history": [],
    "user_context": {
      "user_id": "test_user",
      "username": "test"
    },
    "session_id": "test_session"
  }'
```

**预期结果**：
- 返回状态码：200
- 包含`intent_analysis`字段：
  - `task_type`: 任务类型（应为`tool_execution`）
  - `confidence`: 置信度（0-1之间）
  - `reasoning`: 推理过程
- 包含`strategy`字段：执行策略
- 包含`output`字段：AI回复

### 步骤4: 检查日志确认元数据增强

```bash
# 查看agent-service日志
docker logs enterprise-ai-agent-service | grep -i "metadata\|enhanced\|routing"

# 查看metadata-service日志
docker logs enterprise-ai-metadata-service | grep -i "realtime\|query"
```

**预期日志**：
- `Built metadata-enhanced system prompt` - 提示词构建成功
- `Enhanced routing decision with metadata` - 路由决策增强成功
- `Metadata query completed` - 元数据查询完成

---

## 三、功能验证测试用例

### 测试用例1: SAP数据查询

**输入**：`"查询SAP销售订单"`

**预期行为**：
1. 查询元数据（SAP相关服务、数据资产）
2. 构建增强提示词（包含SAP服务信息）
3. 意图识别为`tool_execution`
4. 路由到`mcp-gateway`执行`sap_query`工具
5. 返回查询结果

### 测试用例2: 简单查询

**输入**：`"什么是SAP ERP"`

**预期行为**：
1. 查询元数据（业务实体、知识库）
2. 构建增强提示词
3. 意图识别为`simple_query`
4. 直接使用LLM回答
5. 返回知识性回答

### 测试用例3: 数据分析

**输入**：`"分析9月份的销售数据"`

**预期行为**：
1. 查询元数据（数据资产、分析工具）
2. 构建增强提示词
3. 意图识别为`data_analysis`或`complex_analysis`
4. 路由到数据分析服务
5. 执行分析并返回结果

---

## 四、性能验证

### 关键指标

1. **元数据查询延迟**
   - 目标：< 200ms (P95)
   - 验证：检查`query_time`字段

2. **意图识别延迟**
   - 目标：< 1s (P95)
   - 验证：检查API响应时间

3. **系统响应时间**
   - 目标：< 2s (P95)
   - 验证：端到端测试

### 性能测试

```bash
# 测试元数据查询性能
time curl -X POST http://localhost:8005/api/v1/metadata/realtime-query \
  -H "Content-Type: application/json" \
  -d '{"user_input":"测试","context":{},"limit_per_type":5}'

# 测试意图识别性能
time curl -X POST http://localhost:8010/api/v1/chat/intelligent \
  -H "Content-Type: application/json" \
  -d '{"message":"测试","conversation_history":[],"user_context":{},"session_id":"test"}'
```

---

## 五、故障排查

### 问题1: 元数据查询失败

**症状**：API返回错误或超时

**排查步骤**：
1. 检查metadata-service是否运行：`docker ps | grep metadata`
2. 检查服务日志：`docker logs enterprise-ai-metadata-service`
3. 检查数据库连接：`docker logs enterprise-ai-metadata-service | grep -i database`
4. 检查Redis连接：`docker logs enterprise-ai-metadata-service | grep -i redis`

**解决方案**：
- 确保metadata-service正常运行
- 确保PostgreSQL和Redis正常运行
- 检查环境变量配置

### 问题2: 意图识别失败

**症状**：API返回错误或超时

**排查步骤**：
1. 检查agent-service是否运行：`docker ps | grep agent`
2. 检查服务日志：`docker logs enterprise-ai-agent-service`
3. 检查LLM配置：`docker logs enterprise-ai-agent-service | grep -i llm`
4. 检查metadata-service连接：`docker logs enterprise-ai-agent-service | grep -i metadata`

**解决方案**：
- 确保agent-service正常运行
- 确保LLM配置正确
- 确保metadata-service可访问

### 问题3: 元数据增强未生效

**症状**：日志中没有metadata相关记录

**排查步骤**：
1. 检查metadata_client连接：查看agent-service日志
2. 检查元数据查询是否成功：测试元数据查询API
3. 检查提示词构建：查看日志中的"Built metadata-enhanced"记录

**解决方案**：
- 确保metadata-service可访问
- 检查网络连接
- 查看详细错误日志

---

## 六、验证成功标准

### ✅ 功能验证通过标准

1. **元数据查询**
   - ✅ API返回200状态码
   - ✅ 返回了相关元数据（至少一种类型有数据）
   - ✅ 查询时间< 1秒

2. **意图识别**
   - ✅ API返回200状态码
   - ✅ 正确识别了任务类型
   - ✅ 置信度> 0.3
   - ✅ 返回了执行策略

3. **元数据增强**
   - ✅ 日志中显示了"metadata"相关记录
   - ✅ 提示词包含了元数据信息
   - ✅ 路由决策考虑了元数据推荐

4. **智能任务编排**
   - ✅ 根据意图选择了正确的执行策略
   - ✅ 路由到了合适的服务
   - ✅ 任务执行成功（或返回了合理的错误）

---

## 七、持续监控

### 监控指标

1. **元数据查询成功率**
   - 目标：> 95%
   - 监控：API响应状态码

2. **意图识别准确率**
   - 目标：> 80%
   - 监控：任务类型识别正确性

3. **系统响应时间**
   - 目标：< 2s (P95)
   - 监控：端到端响应时间

4. **缓存命中率**
   - 目标：> 50%
   - 监控：Redis缓存统计

---

## 八、测试脚本

可以使用以下PowerShell脚本进行快速测试：

```powershell
# 测试元数据查询
$body = @{
    user_input = "查询SAP销售订单"
    context = @{ user_id = "test" }
    limit_per_type = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8005/api/v1/metadata/realtime-query" `
    -Method POST -Body $body -ContentType "application/json"

# 测试意图识别
$body = @{
    message = "查询SAP销售订单"
    conversation_history = @()
    user_context = @{ user_id = "test" }
    session_id = "test123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8010/api/v1/chat/intelligent" `
    -Method POST -Body $body -ContentType "application/json"
```

---

**文档版本**：v1.0  
**最后更新**：2024-12-19


