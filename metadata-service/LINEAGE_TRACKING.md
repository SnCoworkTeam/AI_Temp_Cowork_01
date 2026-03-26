# 数据血缘追踪实现说明

本文档说明数据血缘追踪功能在各服务中的实现情况。

## 概述

数据血缘追踪功能用于自动记录和追踪数据在系统中的流动和转换过程，包括：
- MCP工具执行时的数据流
- 工作流执行时的节点间数据流
- 知识库文档处理流程
- AI模型推理过程

## 实现架构

### 核心组件

1. **LineageCollector** (`src/collectors/lineage_collector.py`)
   - 血缘采集器核心类
   - 提供统一的血缘追踪接口
   - 自动提取数据源和目标
   - 创建和管理血缘关系

2. **血缘追踪API** (`src/api/lineage_tracking.py`)
   - 接收来自各服务的血缘追踪请求
   - 提供RESTful API接口

## 集成点

### 1. MCP Gateway - 工具执行血缘

**位置**: `mcp-gateway/src/services/tool_service.py`

**触发时机**: 工具执行完成后

**追踪内容**:
- 工具输入数据源
- 工具输出数据目标
- 执行元数据（执行ID、执行时间等）

**实现代码**:
```python
# 追踪MCP工具执行血缘
try:
    import httpx
    from ..config import settings
    async with httpx.AsyncClient() as client:
        lineage_data = {
            "tool_name": tool_name,
            "input_data": parameters,
            "output_data": execution_response.result,
            "execution_id": execution_id,
            "execution_time": execution_time
        }
        await client.post(
            f"{settings.METADATA_SERVICE_URL}/api/collection/lineage/tool-execution",
            json=lineage_data
        )
except Exception as e:
    logger.warning(f"Failed to track tool execution lineage: {str(e)}")
```

### 2. Workflow Engine - 工作流执行血缘

**位置**: `workflow-engine/src/workflows/workflow_manager_db.py`

**触发时机**: 工作流执行完成后

**追踪内容**:
- 工作流节点执行信息
- 节点间的数据流
- 节点间的依赖关系
- 节点输入输出数据

**实现代码**:
```python
# 追踪工作流执行血缘
try:
    import httpx
    from ..config import settings
    
    # 构建节点执行信息
    node_executions = []
    node_results = execution_result.get("node_results", {})
    for node_id, node_result in node_results.items():
        node_exec = {
            "node_id": node_id,
            "node_type": node_result.get("node_type", "unknown"),
            "input_data": node_result.get("input", {}),
            "output_data": node_result.get("output", {}),
            "execution_time": node_result.get("execution_time"),
            "success": node_result.get("success", True)
        }
        node_executions.append(node_exec)
    
    # 发送到元数据服务
    async with httpx.AsyncClient() as client:
        lineage_data = {
            "workflow_id": str(workflow_id),
            "execution_id": execution_id,
            "node_executions": node_executions
        }
        await client.post(
            f"{settings.METADATA_SERVICE_URL}/api/collection/lineage/workflow-execution",
            json=lineage_data
        )
except Exception as e:
    logger.warning(f"Failed to track workflow execution lineage: {str(e)}")
```

### 3. Knowledge Base - 知识处理血缘

**位置**: `knowledge-base/src/services/document_service.py`

**触发时机**: 文档处理过程中

**追踪内容**:
- 文档解析步骤
- 文档分块步骤
- 向量嵌入步骤
- 处理步骤间的依赖关系

**实现代码**:
```python
# 追踪知识处理血缘
processing_steps = []
processing_steps.append({
    "step_name": "document_parsing",
    "step_type": "parsing",
    "input_data": {"file_path": file_path},
    "output_data": {"text": text[:100] if text else "", "chunk_count": len(chunks)},
    "processing_time": None
})

# ... 其他处理步骤 ...

# 发送到元数据服务
try:
    import httpx
    from ..config import settings
    async with httpx.AsyncClient() as client:
        lineage_data = {
            "document_id": document_id,
            "processing_id": f"processing_{document_id}",
            "processing_steps": processing_steps
        }
        await client.post(
            f"{settings.METADATA_SERVICE_URL}/api/collection/lineage/knowledge-processing",
            json=lineage_data
        )
except Exception as e:
    logger.warning(f"Failed to track knowledge processing lineage: {str(e)}")
```

### 4. AI模型推理血缘（待实现）

**位置**: 模型推理服务

**触发时机**: 模型推理完成后

**追踪内容**:
- 模型输入数据源
- 模型输出数据目标
- 推理元数据

## API端点

### 血缘追踪API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/collection/lineage/tool-execution` | POST | 追踪MCP工具执行血缘 |
| `/api/collection/lineage/workflow-execution` | POST | 追踪工作流执行血缘 |
| `/api/collection/lineage/knowledge-processing` | POST | 追踪知识处理血缘 |
| `/api/collection/lineage/model-inference` | POST | 追踪模型推理血缘 |

## 血缘关系类型

### 数据流 (data_flow)
- `reads`: 读取数据源
- `writes`: 写入数据目标
- `transforms`: 转换数据

### 依赖关系 (dependency)
- `depends_on`: 依赖关系
- `contains`: 包含关系

## 数据源和目标提取

`LineageCollector` 自动从输入输出数据中提取数据源和目标：

### 支持的数据标识格式

1. **明确标识**:
   - `source_id` / `target_id`: 明确的源/目标ID
   - `data_source` / `data_target`: 格式为 `type:id` 的字符串

2. **字段推断**:
   - 以 `_id` 结尾的字段会被识别为实体ID
   - 自动推断实体类型

### 示例

```python
# 输入数据
input_data = {
    "source_id": "customer_table",
    "source_type": "data_asset",
    "query": "SELECT * FROM customers"
}

# 输出数据
output_data = {
    "target_id": "customer_summary",
    "target_type": "data_asset",
    "result": {...}
}

# LineageCollector会自动提取：
# - 源: data_asset:customer_table
# - 目标: data_asset:customer_summary
```

## 血缘关系存储

血缘关系存储在 `data_lineage` 表中，包含以下信息：

- 源资产和目标资产
- 关系类型和血缘类型
- 转换过程和逻辑
- 业务规则
- 数据质量影响
- 执行元数据

## 使用示例

### 手动追踪工具执行血缘

```python
from metadata_service.src.collectors.lineage_collector import get_lineage_collector

collector = get_lineage_collector()

await collector.track_mcp_tool_execution(
    tool_name="data_processor",
    input_data={"source_id": "raw_data", "source_type": "data_asset"},
    output_data={"target_id": "processed_data", "target_type": "data_asset"},
    execution_id="exec_123",
    execution_time=1.5
)
```

### 手动追踪工作流执行血缘

```python
from metadata_service.src.collectors.lineage_collector import NodeExecution

node_executions = [
    NodeExecution(
        node_id="node_1",
        node_type="data_input",
        input_data={"source": "data_asset:input_table"},
        output_data={"result": "processed"},
        execution_time=0.5,
        success=True
    ),
    NodeExecution(
        node_id="node_2",
        node_type="transformation",
        input_data={"source": "node_1"},
        output_data={"target": "data_asset:output_table"},
        execution_time=1.0,
        success=True
    )
]

await collector.track_workflow_execution(
    workflow_id="workflow_123",
    node_executions=node_executions,
    execution_id="exec_456"
)
```

## 注意事项

1. **异步执行**: 血缘追踪是异步执行的，不会阻塞主业务流程
2. **错误处理**: 追踪失败不会影响主业务，只会记录警告日志
3. **性能影响**: 追踪操作设计为轻量级，对主业务性能影响最小
4. **数据一致性**: 血缘数据可能与实际数据有短暂延迟

## 未来改进

1. **批量追踪**: 支持批量追踪多个血缘关系
2. **实时追踪**: 支持实时血缘关系更新
3. **血缘可视化**: 提供血缘图谱可视化界面
4. **血缘分析**: 提供血缘影响分析功能

