# 工具选择逻辑修复

## 问题描述

用户报告：发送邮件请求时，系统错误地调用了SAP查询工具，而不是邮件工具。

错误信息显示：
```
抱歉，执行SAP查询时遇到问题：HTTP 400: {"detail":"Tool execution failed: Missing required parameter: to_emails"}
```

## 根本原因

虽然系统已经实现了基于元数据的意图识别（`MetadataFirstIntentRecognizer`），并且使用LLM进行意图分析，但是在工具执行阶段（`_handle_tool_execution`）仍然存在大量硬编码的fallback逻辑：

1. **硬编码的工具选择**：如果`decision.required_tools`为空，代码会使用关键词匹配（如"SAP"、"销售订单"）来选择工具，而不是依赖元数据识别结果
2. **硬编码的错误信息**：错误信息固定为"SAP查询"，即使实际使用的是其他工具
3. **参数提取逻辑混乱**：参数提取依赖于硬编码的工具类型判断，而不是从LLM的意图分析结果中获取

## 修复方案

### 1. 优化工具选择优先级

修改`_handle_tool_execution`方法，建立清晰的工具选择优先级：

```python
# 1. 优先使用RoutingDecision中的required_tools（来自元数据识别）
if decision.required_tools:
    tool_id = decision.required_tools[0]

# 2. 如果没有，尝试从IntentAnalysis中获取
elif intent_analysis and intent_analysis.required_tools:
    tool_id = intent_analysis.required_tools[0]

# 3. 如果还没有，尝试从execution_params中获取
elif decision.execution_params.get("context", {}).get("required_tools"):
    tool_id = decision.execution_params["context"]["required_tools"][0]

# 4. 如果还是没有，尝试通过MCP Gateway搜索工具（基于语义搜索）
if not tool_id:
    tools = await self.service_clients.mcp_gateway.search_tools(user_input)
    # ... 处理搜索结果

# 5. 如果仍然没有找到工具，返回错误（不再使用硬编码的fallback）
if not tool_id:
    return {"success": False, "error": "未找到合适的工具..."}
```

### 2. 移除硬编码的fallback逻辑

**删除以下硬编码逻辑**：
- 删除基于"SAP"、"销售订单"关键词的默认工具选择
- 删除基于"发送邮件"关键词的硬编码工具选择
- 删除所有硬编码的工具类型判断

### 3. 优化参数提取逻辑

修改参数提取，优先使用LLM提取的参数：

```python
# 优先从intent_analysis中获取参数（LLM提取的参数）
if intent_analysis and intent_analysis.extracted_context:
    parameters = intent_analysis.extracted_context.get("parameters", {})

# 如果没有，尝试从execution_params中获取
if not parameters:
    parameters = decision.execution_params.get("context", {}).get("parameters", {})

# 如果仍然没有参数，根据工具类型尝试从用户输入中提取
if not parameters:
    if tool_id == "send_email":
        parameters = self._extract_email_parameters(user_input, intent_analysis)
    elif tool_id == "sap_query":
        parameters = {...}
```

### 4. 改进错误信息

根据实际使用的工具类型提供不同的错误信息：

```python
if not success:
    error_msg = result.get("error", "工具执行失败")
    if tool_id == "send_email" or "email" in tool_id.lower():
        output = f"抱歉，发送邮件时遇到问题：{error_msg}..."
    elif tool_id == "sap_query" or "sap" in tool_id.lower():
        output = f"抱歉，执行SAP查询时遇到问题：{error_msg}..."
    else:
        output = f"抱歉，执行工具 '{tool_id}' 时遇到问题：{error_msg}"
```

### 5. 修复方法签名

修复`_extract_email_parameters`方法签名，移除不再需要的`decision`参数：

```python
# 修改前
def _extract_email_parameters(self, user_input: str, decision: RoutingDecision, intent_analysis: Optional[IntentAnalysis] = None)

# 修改后
def _extract_email_parameters(self, user_input: str, intent_analysis: Optional[IntentAnalysis] = None)
```

## 修改的文件

- `agent-service/src/core/orchestration_engine.py`
  - `_handle_tool_execution`方法：优化工具选择逻辑，移除硬编码fallback
  - `_extract_email_parameters`方法：修复方法签名，优化参数提取

## 验证步骤

1. **测试邮件发送**：
   ```
   给yubin.liu@pcitc.com发邮件，收件人刘玉斌，主题会议通知，主题关于ai场景的讨论，时间是明天下午3点
   ```
   - 应该识别为`tool_execution`，`required_tools = ["send_email"]`
   - 应该调用`send_email`工具，而不是SAP工具

2. **测试SAP查询**：
   ```
   分析一下销售订单
   ```
   - 应该识别为`tool_execution`，`required_tools = ["sap_query"]`
   - 应该调用`sap_query`工具
   - **注意**：SAP查询功能仍然可以正常工作，因为：
     - 元数据识别器会检测SAP关键词（"sap", "销售订单"等）
     - LLM基于元数据上下文会正确识别为`required_tools = ["sap_query"]`
     - 工具选择逻辑会优先使用`decision.required_tools[0]`，即`"sap_query"`
   - 详细流程请参考 `SAP_QUERY_WORKFLOW.md`

3. **检查日志**：
   - 查看工具选择过程的日志，确认使用了元数据识别结果
   - 确认没有触发硬编码的fallback逻辑
   - 对于SAP查询，应该看到：`Using tool from routing decision: sap_query`

## 预期效果

1. **工具选择基于元数据**：系统优先使用元数据识别结果，而不是硬编码的关键词匹配
2. **更准确的工具识别**：LLM基于元数据上下文识别工具，准确率更高
3. **更好的错误处理**：错误信息根据实际使用的工具类型提供，更加友好和准确
4. **更清晰的代码逻辑**：移除硬编码逻辑，代码更易维护

## 注意事项

1. **元数据识别必须正常工作**：如果元数据识别失败，系统会fallback到MCP Gateway搜索，如果搜索也失败，会返回错误
2. **LLM意图分析必须准确**：LLM需要正确识别用户意图并提取`required_tools`
3. **工具元数据必须完整**：工具必须在元数据服务中注册，并且元数据信息完整

## 后续优化建议

1. **增强日志记录**：记录工具选择的完整过程，包括每个优先级步骤的结果
2. **工具匹配评分**：如果多个工具匹配，使用评分机制选择最佳工具
3. **用户反馈机制**：如果工具选择错误，允许用户纠正，并学习用户的偏好
4. **工具推荐**：如果用户请求不明确，推荐可能的工具供用户选择

