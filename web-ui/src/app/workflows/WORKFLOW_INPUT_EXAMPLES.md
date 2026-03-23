# 工作流输入参数说明

## 概述

工作流的输入参数通过 `input_data` 字段传递，它是一个 JSON 对象（字典）。输入数据会被放入工作流状态中的 `input` 字段，供各个节点使用。

## 基本格式

```json
{
  "input_data": {
    "key1": "value1",
    "key2": "value2",
    ...
  }
}
```

## 常见节点类型的输入参数示例

### 1. LLM 节点（大语言模型）

LLM 节点默认从 `input` 字段获取数据，可以通过模板 `{input}` 访问。

**示例 1：简单文本输入**

```json
{
  "input": "请帮我写一首关于春天的诗"
}
```

**示例 2：结构化输入**

```json
{
  "input": "用户问题：什么是人工智能？",
  "context": "这是一个技术咨询场景",
  "language": "zh-CN"
}
```

**示例 3：多字段输入**

```json
{
  "question": "如何学习Python？",
  "level": "beginner",
  "topic": "programming"
}
```

### 2. 知识搜索节点

知识搜索节点从 `input` 或配置的查询字段获取搜索关键词。

**示例 1：简单查询**

```json
{
  "input": "人工智能的发展历史"
}
```

**示例 2：带参数的查询**

```json
{
  "query": "机器学习算法",
  "search_type": "semantic",
  "limit": 10
}
```

### 3. 工具节点

工具节点根据工具类型需要不同的参数。

**示例 1：SAP 查询工具**

```json
{
  "table": "MARA",
  "query": "MATNR = '123456'",
  "fields": ["MATNR", "MAKTX", "MEINS"]
}
```

**示例 2：HTTP 请求工具**

```json
{
  "url": "https://api.example.com/data",
  "method": "GET",
  "headers": {
    "Authorization": "Bearer token"
  }
}
```

### 4. 数据转换节点

数据转换节点从指定的 `input_key` 字段获取数据。

**示例：**

```json
{
  "data": {
    "name": "张三",
    "age": 30,
    "city": "北京"
  },
  "format": "json"
}
```

### 5. 条件节点

条件节点根据状态中的数据进行条件判断。

**示例：**

```json
{
  "score": 85,
  "status": "active",
  "category": "premium"
}
```

### 6. 智能体节点

智能体节点通常需要 `content` 字段作为输入。

**示例：**

```json
{
  "content": "请帮我分析这个数据",
  "agent_id": "agent-12345678-1234-1234-1234-123456789abc",
  "context": {
    "user_id": "user-001",
    "session_id": "session-001"
  }
}
```

## 完整工作流示例

### 示例 1：简单问答工作流

**输入参数：**

```json
{
  "question": "什么是机器学习？"
}
```

**工作流结构：**

- Start → LLM → End

**LLM 节点配置：**

- Prompt Template: `"请回答以下问题：{input.question}"`

### 示例 2：知识增强问答工作流

**输入参数：**

```json
{
  "query": "Python 编程最佳实践",
  "max_results": 5
}
```

**工作流结构：**

- Start → 知识搜索 → LLM → End

**节点配置：**

- 知识搜索节点：从 `input.query` 获取查询
- LLM 节点：使用搜索结果增强回答

### 示例 3：数据处理工作流

**输入参数：**

```json
{
  "data": {
    "users": [
      { "name": "张三", "age": 25 },
      { "name": "李四", "age": 30 }
    ]
  },
  "operation": "filter",
  "condition": "age > 28"
}
```

**工作流结构：**

- Start → 数据转换 → 条件判断 → End

## 空输入

如果工作流不需要输入参数，可以传递空对象：

```json
{}
```

## 注意事项

1. **字段名称**：不同节点可能从不同的字段读取数据，请根据节点配置确定字段名
2. **数据类型**：确保数据类型与节点期望的类型匹配（字符串、数字、对象、数组等）
3. **模板变量**：在 LLM 节点的 prompt_template 中，可以使用 `{input.field_name}` 访问输入字段
4. **状态访问**：节点可以通过 `state["input"]` 访问完整的输入数据
5. **嵌套结构**：支持嵌套的 JSON 对象和数组

## 在 UI 中使用

1. **执行对话框**：在工作流列表中点击"执行"按钮，在对话框中输入 JSON 格式的参数
2. **公开执行页面**：通过工作流的公开链接访问，在输入框中输入 JSON 参数

## 调试技巧

1. 如果工作流执行失败，检查输入数据格式是否正确
2. 查看节点配置，确认节点期望的输入字段名称
3. 使用简单的输入数据先测试，逐步增加复杂度
4. 查看执行日志，了解节点实际接收到的数据
