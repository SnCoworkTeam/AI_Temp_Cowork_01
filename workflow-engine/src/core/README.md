# 动态工作流引擎

基于JSON配置的动态工作流引擎，支持从JSON配置构建和执行LangGraph工作流。

## 核心组件

### 1. DynamicWorkflowEngine
动态工作流引擎主类，负责从JSON配置构建LangGraph图并执行工作流。

**主要方法：**
- `build_from_config(workflow_config)` - 从JSON配置构建工作流
- `execute_workflow(workflow_id, input_data)` - 执行工作流

### 2. NodeRegistry
节点注册表，支持动态添加节点类型。

**内置节点类型：**
- `llm` - LLM节点（调用大语言模型）
- `tool` - 工具调用节点（调用MCP工具）
- `condition` - 条件判断节点
- `transform` - 数据转换节点
- `http` - HTTP请求节点
- `start` - 开始节点
- `end` - 结束节点
- `delay` - 延迟节点
- `log` - 日志节点

### 3. WorkflowConfigParser
工作流配置解析器，验证JSON配置的合法性并构建WorkflowDefinition对象。

## 使用示例

### 构建工作流

```python
from workflow_engine.src.core import DynamicWorkflowEngine
import json

engine = DynamicWorkflowEngine()

# 读取JSON配置
with open('workflow_config.json') as f:
    config = json.load(f)

# 构建工作流
workflow_id = engine.build_from_config(config)
```

### 执行工作流

```python
# 执行工作流
result = await engine.execute_workflow(
    workflow_id=workflow_id,
    input_data={"product_id": "123456"},
    timeout=300
)

print(f"Execution result: {result['result']}")
```

### 注册自定义节点

```python
from workflow_engine.src.core import node_registry
from workflow_engine.src.nodes.base_node import BaseNode

class CustomNode(BaseNode):
    async def execute(self, state):
        # 自定义节点逻辑
        state["custom_output"] = "custom result"
        return state

# 注册节点类型
node_registry.register_node_type(
    "custom",
    lambda config: CustomNode(
        name=config.get("name"),
        description=config.get("description", ""),
        config=config.get("config", {})
    )
)
```

## JSON配置格式

工作流配置JSON格式如下：

```json
{
  "name": "workflow_name",
  "description": "工作流描述",
  "version": "1.0.0",
  "nodes": [
    {
      "id": "node1",
      "name": "节点名称",
      "type": "llm",
      "config": {
        "model": "gpt-4",
        "prompt_template": "处理：{input}"
      },
      "position": {"x": 100, "y": 100}
    }
  ],
  "connections": [
    {
      "id": "conn1",
      "source": {"node_id": "node1", "port": "output"},
      "target": {"node_id": "node2", "port": "input"}
    }
  ],
  "start_node_id": "node1",
  "end_node_ids": ["node2"]
}
```

## 节点类型说明

### LLM节点
```json
{
  "id": "llm1",
  "type": "llm",
  "config": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000,
    "prompt_template": "分析数据：{data}"
  }
}
```

### 工具调用节点
```json
{
  "id": "tool1",
  "type": "tool",
  "config": {
    "tool_name": "sap_query",
    "parameters": {
      "table": "MARA",
      "query": "${search_query}"
    },
    "mcp_gateway_url": "http://mcp-gateway:8001"
  }
}
```

### 条件判断节点
```json
{
  "id": "cond1",
  "type": "condition",
  "config": {
    "condition": "len(state.get('data', [])) > 0",
    "true_output": "has_data",
    "false_output": "no_data"
  }
}
```

### HTTP请求节点
```json
{
  "id": "http1",
  "type": "http",
  "config": {
    "url": "https://api.example.com/data",
    "method": "POST",
    "headers": {"Authorization": "Bearer ${token}"},
    "body": {"key": "value"}
  }
}
```

## 状态变量引用

节点配置中可以使用状态变量引用，格式为 `${variable_name}`：

```json
{
  "config": {
    "tool_name": "query",
    "parameters": {
      "table": "${table_name}",
      "filter": "${search_filter}"
    }
  }
}
```

## 错误处理

工作流执行过程中的错误会被捕获并添加到状态中：

```python
result = await engine.execute_workflow(workflow_id, input_data)

if not result["success"]:
    print(f"Error: {result.get('error')}")
```

## LangGraph集成

如果LangGraph可用，引擎会自动使用LangGraph构建和执行工作流。如果不可用，会使用模拟执行模式。

## 注意事项

1. 条件表达式求值使用了`eval()`，生产环境应使用更安全的表达式解析器
2. 状态变量引用支持简单的字符串替换
3. 节点执行是异步的，支持并发执行
4. 工作流支持超时控制









