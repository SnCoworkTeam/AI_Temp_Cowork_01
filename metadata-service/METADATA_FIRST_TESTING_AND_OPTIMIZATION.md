# 元数据前置意图识别测试与优化

## ✅ 已完成的工作

### 1. 测试脚本

**文件**：`agent-service/test_metadata_first_intent.py`

**测试场景**：
- ✅ 邮件发送意图识别（4个测试用例）
- ✅ SAP查询意图识别（5个测试用例）
- ✅ 缓存性能测试
- ✅ 混合场景测试（简单查询、知识搜索、工作流、复杂分析）

**功能**：
- 自动测试多个场景
- 性能统计（耗时、准确率）
- 生成详细测试报告（JSON格式）

### 2. 性能监控

**文件**：
- `agent-service/src/core/intent_performance_monitor.py` - 性能监控器
- `agent-service/src/routes/performance_monitoring.py` - 性能监控API

**监控指标**：
- ✅ 总请求数
- ✅ 缓存命中率
- ✅ 平均耗时
- ✅ 元数据检索耗时
- ✅ LLM理解耗时
- ✅ 分类耗时
- ✅ 错误率
- ✅ 按任务类型统计

**API端点**：
- `GET /api/v1/performance/metrics` - 获取性能指标
- `GET /api/v1/performance/metrics/summary` - 获取性能摘要
- `GET /api/v1/performance/metrics/recent` - 获取最近请求
- `POST /api/v1/performance/metrics/reset` - 重置指标

### 3. 工具元数据向量化

**文件**：`mcp-gateway/src/services/tool_vectorization_service.py`

**功能**：
- ✅ 将工具元数据转换为文档
- ✅ 存储到知识库（自动向量化）
- ✅ 支持语义搜索工具
- ✅ 自动创建工具元数据知识库

**集成**：
- ✅ 工具注册时自动向量化
- ✅ 在 `ToolService.register_tool` 中调用

### 4. 检索算法优化

**优化内容**：
- ✅ 语义搜索优先（如果工具已向量化）
- ✅ 降级到关键词搜索
- ✅ 并行检索多种元数据
- ✅ 智能缓存机制

## 🧪 测试方法

### 运行测试脚本

```bash
# 在agent-service容器中
cd /app
python test_metadata_first_intent.py
```

或在本地（需要配置环境）：
```bash
cd agent-service
python test_metadata_first_intent.py
```

### 测试报告

测试完成后会生成 `metadata_first_intent_test_report.json`，包含：
- 各场景的准确率和平均耗时
- 缓存性能数据
- 详细测试结果

### 查看性能指标

```bash
# 获取性能指标
curl http://localhost:8010/api/v1/performance/metrics

# 获取性能摘要
curl http://localhost:8010/api/v1/performance/metrics/summary

# 获取最近10条请求
curl http://localhost:8010/api/v1/performance/metrics/recent?limit=10
```

## 📊 性能监控

### 监控指标说明

```json
{
  "total_requests": 100,
  "cache_hits": 85,
  "cache_misses": 15,
  "cache_hit_rate": 85.0,
  "avg_time_ms": 250.5,
  "metadata_retrieval_time_ms": 120.3,
  "llm_time_ms": 800.2,
  "classification_time_ms": 5.1,
  "errors": 2,
  "error_rate": 2.0,
  "task_type_stats": {
    "tool_execution": {
      "count": 60,
      "total_time_ms": 15000.0,
      "cache_hits": 50,
      "cache_misses": 10
    }
  }
}
```

### 性能目标

- **缓存命中率**：>80%
- **平均延迟**：<500ms（缓存命中），<1500ms（缓存未命中）
- **错误率**：<5%

## 🔧 工具元数据向量化

### 工作流程

```
工具注册
  ↓
保存到数据库（mcp_tools表）
  ↓
同步到元数据服务（workflow_metadata表）
  ↓
向量化工具元数据
  ├─ 构建工具文档
  ├─ 存储到知识库（工具元数据知识库）
  └─ 自动生成向量嵌入
  ↓
支持语义搜索
```

### 工具文档格式

```markdown
# send_email

## 描述
发送电子邮件。支持文本和HTML格式，可以添加附件、抄送和密送。

## 功能
这是一个MCP工具，用于执行特定任务。

## 参数
- to_emails (string): 收件人邮箱地址
- subject (string): 邮件主题
- body (string): 邮件正文内容

## 使用场景
- 发送通知邮件
- 发送会议邀请
- 发送报告

## 标签
邮件, 发送, 通知, 通信

## 业务领域
通信
```

### 语义搜索

```python
# 通过语义搜索工具
tools = await vectorization_service.search_tools_by_semantics(
    query="发送邮件通知",
    limit=5
)
```

## 🚀 优化建议

### 1. 提高缓存命中率

**当前**：基于精确匹配

**优化**：
- 实现相似查询匹配（向量相似度）
- 使用更智能的缓存键生成
- 增加缓存大小

### 2. 优化元数据检索

**当前**：并行检索，但可能检索到不相关的结果

**优化**：
- 使用向量相似度排序
- 实现更精确的关键词匹配
- 添加相关性评分

### 3. 工具元数据质量

**建议**：
- 为每个工具添加详细的使用场景
- 添加示例和最佳实践
- 定期更新工具描述

### 4. 性能优化

**建议**：
- 实现批量向量化
- 优化向量搜索参数
- 添加结果缓存

## 📝 使用示例

### 测试邮件发送

```python
from agent_service.src.core.metadata_first_intent_recognizer import MetadataFirstIntentRecognizer

recognizer = MetadataFirstIntentRecognizer()
intent = await recognizer.recognize_intent("发送邮件给yubin.liu@pcitc.com")

print(f"任务类型: {intent.task_type}")
print(f"需要的工具: {intent.required_tools}")
```

### 查看性能指标

```python
from agent_service.src.core.intent_performance_monitor import get_performance_monitor

monitor = get_performance_monitor()
metrics = monitor.get_metrics()
print(f"缓存命中率: {metrics['cache_hit_rate']:.1f}%")
print(f"平均耗时: {metrics['avg_time_ms']:.2f}ms")
```

### 向量化工具

```python
from mcp_gateway.src.services.tool_vectorization_service import get_tool_vectorization_service

service = get_tool_vectorization_service()
await service.vectorize_tool_metadata(
    tool_name="send_email",
    tool_description="发送电子邮件",
    tool_parameters={"to_emails": {"type": "string"}},
    tool_metadata={"category": "communication", "tags": ["邮件", "发送"]}
)
```

## 🎯 下一步

### 阶段1：测试验证（当前）

- [x] 创建测试脚本
- [x] 实现性能监控
- [ ] 运行测试并分析结果
- [ ] 根据结果优化

### 阶段2：向量化优化

- [x] 实现工具元数据向量化
- [ ] 批量向量化现有工具
- [ ] 优化向量搜索参数
- [ ] 实现相似查询缓存

### 阶段3：算法优化

- [ ] 实现向量相似度匹配
- [ ] 优化元数据检索算法
- [ ] 添加相关性评分
- [ ] 实现自适应学习

## 📊 预期效果

### 准确性

- **邮件发送识别准确率**：>90%
- **SAP查询识别准确率**：>85%
- **总体准确率**：>85%

### 性能

- **缓存命中率**：>80%
- **平均延迟**：<500ms（缓存命中），<1500ms（未命中）
- **错误率**：<5%

### 用户体验

- **首次识别成功率**：>85%
- **用户澄清次数**：减少40%+


