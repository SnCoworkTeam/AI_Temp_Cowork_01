# SAP查询问题修复说明

## 问题描述

用户查询"SAP ERP 销售订单"时，系统没有调用SAP OData MCP工具去查询具体数据，而是直接使用LLM给出了通用的说明文档。

## 问题分析

### 根本原因

从日志分析可以看到：

```
2025-11-21 10:04:20,687 - Intent analysis: type=simple_query, confidence=0.50
2025-11-21 10:04:20,698 - Orchestration Decision - Strategy: direct_llm, Target: chat-service
```

**问题点**：
1. **对话理解错误**：系统将"SAP ERP 销售订单"识别为 `simple_query`（简单查询），而不是 `tool_execution`（工具执行）
2. **路由决策错误**：因为识别为 `simple_query`，系统选择了 `direct_llm` 策略，直接使用LLM回答
3. **关键词模式缺失**：对话理解的关键词模式中没有包含SAP相关的模式
4. **LLM提示词不明确**：系统提示词没有明确说明SAP查询应该使用工具

### 执行流程

```
用户输入: "查一下 SAP ERP 销售订单"
    ↓
对话理解 (conversation_agent)
    ↓
识别结果: simple_query (错误！应该是 tool_execution)
    ↓
任务分类 (task_classifier)
    ↓
路由决策: direct_llm → chat-service (错误！应该调用 mcp-gateway)
    ↓
执行: 直接使用LLM回答，给出通用说明文档
```

### 正确的执行流程应该是

```
用户输入: "查一下 SAP ERP 销售订单"
    ↓
对话理解 (conversation_agent)
    ↓
识别结果: tool_execution (正确)
    ↓
任务分类 (task_classifier)
    ↓
路由决策: tool_call → mcp-gateway (正确)
    ↓
执行: 调用SAP MCP工具查询数据
    ↓
返回: 具体的SAP销售订单数据
```

## 修复方案

### 1. 增强关键词模式

在 `agent-service/src/core/conversation_agent.py` 中添加SAP相关的关键词模式：

```python
TaskType.TOOL_EXECUTION: [
    r"执行|调用|运行|使用.*工具|调用.*API|执行.*命令",
    r"tool|execute|run|call.*api|invoke",
    r"帮我.*做|请.*执行|需要.*工具",
    # SAP相关查询模式 ⭐NEW
    r"SAP|sap|ERP|erp|销售订单|采购订单|物料|客户|供应商|发票|交货单",
    r"查询.*SAP|查.*SAP|SAP.*查询|SAP.*数据|SAP.*订单|SAP.*客户",
    r"sales.*order|purchase.*order|material|customer|vendor|invoice|delivery",
    r"OData|odata|MCP.*工具|sap.*工具"
],
```

### 2. 改进LLM系统提示词

在 `_analyze_with_llm` 方法中更新系统提示词，明确说明SAP查询规则：

```python
system_prompt = """...
重要规则：
- 如果用户查询SAP ERP数据（如销售订单、采购订单、物料、客户、供应商等），必须使用 tool_execution 类型
- 如果用户提到"SAP"、"ERP"、"查询"、"查一下"等关键词，且涉及具体业务数据，应识别为 tool_execution
- 如果只是询问SAP概念、使用方法等知识性问题，可以使用 simple_query
- 对于SAP查询，required_tools 应包含 "sap_query" 或相关的SAP工具
..."""
```

## 修复效果

修复后，当用户查询"SAP ERP 销售订单"时：

1. **对话理解**：正确识别为 `tool_execution`
2. **任务分类**：选择 `tool_call` 策略
3. **路由决策**：路由到 `mcp-gateway`
4. **工具执行**：调用SAP MCP工具（如 `search-sap-services`、`execute-entity-operation`）
5. **返回结果**：返回具体的SAP销售订单数据

## 验证方法

1. 重启 agent-service 使修复生效
2. 测试查询："查一下 SAP ERP 销售订单"
3. 检查日志，确认：
   - Intent analysis: type=tool_execution
   - Routing decision: strategy=tool_call, target_service=mcp-gateway
   - 实际调用了SAP工具

## 相关文件

- `agent-service/src/core/conversation_agent.py` - 对话理解逻辑
- `agent-service/src/core/task_classifier.py` - 任务分类逻辑
- `mcp-gateway/src/tools/tool_registry.py` - 工具注册
- `sap-odata-to-mcp-server/` - SAP MCP Server

## 后续优化建议

1. **工具发现增强**：在对话理解时，可以查询可用工具列表，更准确地识别需要使用的工具
2. **上下文感知**：根据对话历史，更好地理解用户意图
3. **工具推荐**：当识别为SAP查询时，自动推荐相关的SAP工具
4. **错误处理**：当SAP工具调用失败时，提供友好的错误提示和替代方案
































