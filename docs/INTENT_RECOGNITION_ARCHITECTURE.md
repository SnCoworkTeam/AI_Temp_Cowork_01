# 意图识别架构说明

## 📋 当前实现方式

### 主要方式：基于LLM（大语言模型）

系统的意图识别**主要基于LLM**，具体流程如下：

#### 1. 优先级顺序

```
1. 优化提示词 + LLM（如果提供 prompt_engine 和 prompt_context）
   ↓ (如果失败)
2. 基础LLM分析（_analyze_with_llm）
   ↓ (如果LLM不可用)
3. 硬编码规则匹配（_analyze_with_rules）
```

#### 2. LLM分析流程

**代码位置**：`agent-service/src/core/conversation_agent.py`

```python
async def understand_conversation(...):
    # 1. 尝试使用优化提示词（如果提供）
    if prompt_engine and prompt_context and self.use_llm:
        # 使用 PromptEngine 获取优化提示词
        optimized_prompt = await prompt_engine.get_optimized_prompt(...)
        response = await deepseek_llm.chat(messages=optimized_prompt.messages)
        return self._parse_intent_response(response)
    
    # 2. 降级到基础LLM方法
    if self.use_llm and deepseek_llm.llm:
        return await self._analyze_with_llm(...)
    
    # 3. 最后降级到硬编码规则
    return await self._analyze_with_rules(...)
```

#### 3. LLM系统提示词

LLM使用的系统提示词定义在：
- `agent-service/config/prompt_templates.yaml` - 配置文件
- `agent-service/src/core/prompt_templates/base_templates.py` - 代码定义
- `agent-service/src/core/conversation_agent.py` - 默认提示词

**关键提示词内容**：
```
任务类型：
1. simple_query - 简单查询，只需要LLM回答
2. tool_execution - 需要执行工具或调用API
3. workflow_task - 工作流相关任务
...

重要规则：
- 如果用户查询SAP ERP数据，必须使用 tool_execution 类型
- 如果用户提到"SAP"、"ERP"、"查询"等关键词，应识别为 tool_execution
```

### 降级方案：硬编码规则

**代码位置**：`agent-service/src/core/conversation_agent.py`

```python
# 关键词模式（用于规则匹配，仅在LLM不可用时使用）
self.keyword_patterns = {
    TaskType.TOOL_EXECUTION: [
        r"执行|调用|运行|使用.*工具",
        r"SAP|sap|ERP|erp|销售订单",
        r"发送.*邮件|发邮件|邮件.*发送",  # 我刚添加的
        ...
    ],
    ...
}
```

**使用场景**：
- LLM服务不可用时
- LLM分析失败时
- 作为最后的降级方案

## 🔍 为什么邮件发送被识别为 simple_query？

### 问题分析

虽然系统主要使用LLM进行意图识别，但LLM的系统提示词中**没有明确说明邮件发送应该使用工具**。

**当前提示词的问题**：
1. ✅ 明确说明了SAP查询应该使用 `tool_execution`
2. ❌ **没有说明邮件发送应该使用 `tool_execution`**
3. ❌ 没有列出可用的工具列表（如 `send_email`）

### LLM的决策过程

当用户说"发送邮件给XXX"时，LLM可能这样思考：
1. "发送邮件" - 这是一个操作请求
2. 但提示词中没有明确说明邮件发送需要工具
3. LLM可能认为这是一个简单的请求，可以直接用文本回复
4. 结果：识别为 `simple_query`，生成"邮件已发送"的文本回复

## ✅ 解决方案

### 方案1: 改进LLM系统提示词（推荐）

在LLM的系统提示词中明确说明邮件发送应该使用工具：

**修改文件**：`agent-service/config/prompt_templates.yaml` 或 `agent-service/src/core/conversation_agent.py`

```yaml
重要规则：
- 如果用户查询SAP ERP数据，必须使用 tool_execution 类型
- 如果用户提到"SAP"、"ERP"、"查询"等关键词，应识别为 tool_execution
- **如果用户要发送邮件、发邮件、邮件发送等，必须使用 tool_execution 类型，required_tools 应包含 "send_email"**
- **如果用户要执行任何实际操作（发送邮件、调用API、查询数据等），必须使用 tool_execution，而不是 simple_query**

可用工具：
- send_email: 发送电子邮件
- sap_query: 查询SAP数据
- knowledge_search: 搜索知识库
...
```

### 方案2: 在提示词中列出可用工具

让LLM知道系统有哪些工具可用，这样它更容易识别应该使用哪个工具：

```python
system_prompt = f"""...
可用工具列表：
{available_tools_list}

规则：
- 如果用户请求执行上述任何工具的功能，必须使用 tool_execution 类型
- required_tools 应包含具体的工具名称（如 "send_email"、"sap_query"）
"""
```

### 方案3: 增强提示词示例

在提示词模板中添加邮件发送的示例：

```yaml
examples:
  - user: "发送邮件给yubin.liu@pcitc.com，主题是会议通知"
    assistant: '{"task_type": "tool_execution", "confidence": 0.95, "required_tools": ["send_email"], ...}'
```

## 📊 当前架构总结

| 方式 | 优先级 | 使用场景 | 优点 | 缺点 |
|------|--------|----------|------|------|
| **LLM分析** | 1（主要） | LLM可用时 | 理解自然语言，灵活 | 依赖提示词质量，可能误判 |
| **硬编码规则** | 3（降级） | LLM不可用时 | 快速、可靠 | 不够灵活，需要维护规则 |

## 🎯 建议

1. **改进LLM提示词**：在系统提示词中明确说明邮件发送、工具调用等场景
2. **添加工具列表**：让LLM知道系统有哪些工具可用
3. **添加示例**：在提示词模板中添加邮件发送的示例
4. **保留硬编码规则**：作为降级方案和快速匹配

## 📝 代码位置

- **LLM分析**：`agent-service/src/core/conversation_agent.py` - `_analyze_with_llm()`
- **规则匹配**：`agent-service/src/core/conversation_agent.py` - `_analyze_with_rules()`
- **提示词模板**：`agent-service/config/prompt_templates.yaml`
- **提示词定义**：`agent-service/src/core/prompt_templates/base_templates.py`


