# SAP查询工作流程说明

## ✅ 修复后的SAP查询流程

修复移除硬编码fallback后，SAP查询功能**仍然可以正常工作**，因为系统现在完全依赖**元数据驱动的意图识别**。

## 📋 完整工作流程

### 1. 用户请求
```
分析一下销售订单
```
或
```
查询SAP系统中的销售订单
```

### 2. 元数据前置检索（`MetadataFirstIntentRecognizer`）

#### 2.1 快速关键词匹配
- 检测到关键词：`["sap", "销售订单", "采购订单", "物料", "客户", "供应商"]`
- 在metadata中设置：
  ```python
  metadata["sap_services"] = [{"name": "SAP查询", "type": "sap_query"}]
  ```

#### 2.2 完整元数据检索
- 通过 `MetadataRetriever._search_tools()` 搜索工具元数据
- 从MCP Gateway获取所有工具列表
- 如果工具已向量化，可以通过语义搜索找到 `sap_query` 工具

#### 2.3 元数据上下文构建
```python
metadata_context = """
可用工具: sap_query, send_email, knowledge_search
SAP服务: SAP查询
业务实体: 销售订单, 采购订单
"""
```

### 3. LLM意图理解（基于元数据）

LLM收到包含元数据上下文的提示词：
```
你是一个企业业务助手，基于以下业务元数据理解用户需求：

# 业务上下文
可用工具: sap_query, send_email, knowledge_search
SAP服务: SAP查询
业务实体: 销售订单, 采购订单

用户输入: "分析一下销售订单"

请基于以上业务元数据，分析用户的真实业务意图...
```

LLM返回：
```json
{
    "entities": ["销售订单"],
    "operation": "sap_query",
    "required_services": ["sap"],
    "required_tools": ["sap_query"],
    "business_scenario": "查询SAP系统中的销售订单数据",
    "parameters": {
        "table": "I_SalesOrder",
        "query": "分析一下销售订单"
    },
    "confidence": 0.95
}
```

### 4. 动态分类（`_dynamic_classification`）

基于LLM理解结果：
- `operation = "sap_query"`
- `required_tools = ["sap_query"]`
- `required_services = ["sap"]`

分类为：
- `task_type = TaskType.TOOL_EXECUTION`
- `required_tools = ["sap_query"]`

### 5. 路由决策（`TaskClassifier`）

生成 `RoutingDecision`：
```python
RoutingDecision(
    strategy=ExecutionStrategy.TOOL_CALL,
    target_service="mcp-gateway",
    required_tools=["sap_query"],  # ✅ 来自元数据识别
    execution_params={
        "task_type": "tool_execution",
        "context": {
            "parameters": {
                "table": "I_SalesOrder",
                "query": "分析一下销售订单"
            },
            "required_tools": ["sap_query"]
        }
    }
)
```

### 6. 工具执行（`_handle_tool_execution`）

#### 6.1 工具选择（优先级顺序）

1. **优先使用 `decision.required_tools[0]`**
   ```python
   if decision.required_tools:
       tool_id = decision.required_tools[0]  # ✅ "sap_query"
   ```

2. **如果没有，从 `intent_analysis.required_tools` 获取**
   ```python
   elif intent_analysis.required_tools:
       tool_id = intent_analysis.required_tools[0]  # ✅ "sap_query"
   ```

3. **如果还没有，通过MCP Gateway搜索**
   ```python
   if not tool_id:
       tools = await mcp_gateway.search_tools(user_input)
       # 会找到 sap_query 工具
   ```

#### 6.2 参数提取

优先使用LLM提取的参数：
```python
if intent_analysis.extracted_context:
    parameters = intent_analysis.extracted_context.get("parameters", {})
    # ✅ {"table": "I_SalesOrder", "query": "分析一下销售订单"}
```

如果没有，根据工具类型提取：
```python
if tool_id == "sap_query":
    parameters = {
        "table": "I_SalesOrder",  # 默认表名
        "query": user_input
    }
```

#### 6.3 执行工具

```python
result = await mcp_gateway.execute_tool(
    "sap_query",
    {
        "table": "I_SalesOrder",
        "query": "分析一下销售订单"
    },
    context
)
```

### 7. 结果处理

- 如果成功：返回SAP查询结果
- 如果失败：根据工具类型提供错误信息
  ```python
  if tool_id == "sap_query":
      output = f"抱歉，执行SAP查询时遇到问题：{error_msg}..."
  ```

## 🔍 关键点说明

### ✅ 为什么SAP查询仍然能工作？

1. **元数据识别器支持SAP关键词检测**
   - `_quick_keyword_match()` 会检测SAP相关关键词
   - 在metadata中设置 `sap_services`

2. **LLM基于元数据上下文理解**
   - LLM看到元数据上下文中的 `sap_query` 工具
   - 正确识别为 `required_tools = ["sap_query"]`

3. **工具选择逻辑支持**
   - 优先使用 `decision.required_tools[0]`
   - 如果元数据识别正确，会得到 `tool_id = "sap_query"`

4. **参数提取逻辑保留**
   - 如果工具是 `sap_query`，会提取SAP查询参数
   - 默认表名为 `I_SalesOrder`

### ⚠️ 与硬编码fallback的区别

**修复前（硬编码fallback）**：
```python
if not tool_id:
    if "sap" in user_input.lower():
        tool_id = "sap_query"  # ❌ 硬编码
```

**修复后（元数据驱动）**：
```python
if decision.required_tools:
    tool_id = decision.required_tools[0]  # ✅ 来自元数据识别
```

### 🎯 优势

1. **更准确**：基于元数据和LLM理解，而不是简单的关键词匹配
2. **更灵活**：如果工具名称改变，只需更新元数据，不需要修改代码
3. **更智能**：LLM可以理解复杂的查询请求，提取更准确的参数
4. **更易维护**：移除硬编码逻辑，代码更清晰

## 📝 测试验证

### 测试用例1：简单SAP查询
```
输入：分析一下销售订单
预期：
- 识别为 tool_execution
- required_tools = ["sap_query"]
- 调用 sap_query 工具
- 参数：{"table": "I_SalesOrder", "query": "分析一下销售订单"}
```

### 测试用例2：复杂SAP查询
```
输入：查询最近一个月的销售订单，按客户分组统计
预期：
- 识别为 tool_execution
- required_tools = ["sap_query"]
- LLM提取更详细的参数（时间范围、分组条件等）
```

### 测试用例3：SAP查询 + 分析
```
输入：分析一下销售订单，找出销售额最高的客户
预期：
- 识别为 tool_execution
- 先执行 sap_query 获取数据
- 然后使用LLM分析数据
```

## 🔧 故障排查

如果SAP查询不工作，检查：

1. **元数据识别是否正常**
   - 查看日志：`Using tool from routing decision: sap_query`
   - 检查 `decision.required_tools` 是否包含 `"sap_query"`

2. **工具是否注册**
   - 检查MCP Gateway：`GET /api/tools`
   - 确认 `sap_query` 工具在列表中

3. **工具元数据是否同步**
   - 检查元数据服务：`GET /api/tools`
   - 确认 `sap_query` 工具的元数据完整

4. **LLM理解是否准确**
   - 查看日志：`Intent analysis: required_tools=['sap_query']`
   - 检查LLM返回的JSON是否包含 `required_tools`

## 📊 日志示例

### 成功的SAP查询日志
```
[INFO] Intent analysis: type=tool_execution, confidence=0.95
[INFO] Routing decision: strategy=tool_call, required_tools=['sap_query']
[INFO] Using tool from routing decision: sap_query
[INFO] Extracted parameters for SAP query: {'table': 'I_SalesOrder', 'query': '分析一下销售订单'}
[INFO] Executing tool: sap_query
```

### 失败的SAP查询日志
```
[ERROR] No tool identified for request. 
Decision required_tools: [], 
Intent required_tools: None, 
User input: 分析一下销售订单
```

如果看到这个错误，说明：
- 元数据识别失败
- LLM理解失败
- 需要检查元数据服务和LLM服务是否正常


