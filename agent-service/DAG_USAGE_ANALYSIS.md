# DAG 使用情况分析

## 概述

代码中有两种 DAG 使用方式：
1. **外部 DAG Orchestrator 服务**：独立的 DAG 编排服务
2. **内部 DAG 实现**：在动态工作流设计器和执行引擎中使用拓扑排序

## 1. 外部 DAG Orchestrator 服务

### 位置
- `agent-service/src/services/dag_client.py` - DAG Orchestrator 客户端
- `agent-service/src/core/service_clients.py` - 服务客户端管理器

### 使用场景

#### 1.1 任务分解（Task Decomposition）
**文件**: `agent-service/src/core/orchestration_engine.py` (第 740-789 行)

```python
# 使用DAG编排器进行任务分解
decomposition_result = await self.service_clients.dag_orchestrator.decompose_task(
    user_input,
    context
)
```

**何时使用**:
- 在 `OrchestrationEngine._execute_complex_task()` 中
- 当任务类型为 `DATA_ANALYSIS` 时（见 `task_classifier.py`）
- 需要将复杂任务分解为子任务时

**功能**:
- 将复杂任务分解为多个子任务节点
- 建立任务之间的依赖关系
- 返回 `task_nodes` 和 `entry_nodes`

#### 1.2 DAG 执行
**文件**: `agent-service/src/services/dag_client.py` (第 67-110 行)

```python
async def execute_dag(
    self,
    dag_id: str,
    input_data: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
```

**何时使用**:
- 当需要执行预定义的 DAG 时
- 通过 `dag_id` 标识特定的 DAG 流程

**当前状态**:
- 代码中定义了方法，但实际调用较少
- 主要在 `interactive_orchestration_engine.py` 中有引用

### 配置
- 环境变量: `DAG_ORCHESTRATOR_URL` (默认: `http://dag-orchestrator:8009`)
- API 端点:
  - `/api/v1/tasks/decompose` - 任务分解
  - `/api/v1/dag/decompose` - 备用路径
  - `/api/v1/dag/{dag_id}/execute` - DAG 执行

## 2. 内部 DAG 实现（拓扑排序）

### 位置
- `agent-service/src/core/dynamic_workflow_designer.py` - 工作流设计器
- `agent-service/src/core/dynamic_execution_engine.py` - 执行引擎

### 2.1 生成执行层（拓扑排序）

**文件**: `dynamic_workflow_designer.py` (第 387-420 行)

```python
def _generate_execution_layers(self, agents: List[Dict[str, Any]]) -> List[List[str]]:
    """根据依赖关系生成执行层"""
    
    # 构建依赖图
    in_degree = {agent["id"]: 0 for agent in agents}
    graph = defaultdict(list)
    
    for agent in agents:
        for dep in agent.get("dependencies", []):
            if dep in in_degree:
                graph[dep].append(agent["id"])
                in_degree[agent["id"]] += 1
    
    # 拓扑排序
    layers = []
    queue = deque([agent_id for agent_id, degree in in_degree.items() if degree == 0])
    
    while queue:
        layer = []
        level_size = len(queue)
        
        for _ in range(level_size):
            agent_id = queue.popleft()
            layer.append(agent_id)
            
            for neighbor in graph[agent_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if layer:
            layers.append(layer)
    
    return layers
```

**何时使用**:
- 在 `DynamicWorkflowDesigner._validate_design()` 中
- 当 LLM 设计的网络没有提供 `execution_layers` 时
- 根据智能体之间的依赖关系自动生成执行层

**功能**:
- 构建依赖图（DAG）
- 使用拓扑排序将智能体分组到执行层
- 确保依赖关系正确：依赖的智能体先执行

### 2.2 按层执行

**文件**: `dynamic_execution_engine.py` (第 398-622 行)

```python
async def _execute_network_with_streaming(
    self,
    network_design: Dict[str, Any],
    context: Dict[str, Any],
    execution_id: Optional[str] = None,
    agent_results: Optional[Dict[str, Any]] = None,
    start_layer: int = 0
) -> AsyncIterator[Dict[str, Any]]:
    """流式执行智能体网络"""
    
    execution_layers = network_design.get("execution_layers", [])
    
    # 按层执行
    for relative_idx, layer_agent_ids in enumerate(layers_to_execute):
        # 并行执行这一层的智能体
        layer_tasks = {}
        for agent_id in layer_agent_ids:
            # 创建执行任务
            layer_tasks[agent_id] = agent.execute_with_tracking(...)
        
        # 等待这一层所有智能体完成
        layer_results = await asyncio.gather(*layer_tasks.values())
        
        # 保存结果，供下一层使用
        for agent_id, result in zip(layer_tasks.keys(), layer_results):
            agent_results[agent_id] = result
```

**何时使用**:
- 在 `DynamicExecutionEngine.execute_dynamic_workflow()` 中
- 每次执行动态工作流时
- 支持从指定层恢复执行（`start_layer` 参数）

**功能**:
- 按执行层顺序执行智能体
- 同一层的智能体并行执行
- 下一层等待上一层完成
- 支持流式输出执行进度

## 3. DAG 使用流程图

```
用户请求
    ↓
DynamicExecutionEngine.execute_dynamic_workflow()
    ↓
DynamicWorkflowDesigner.design_workflow()
    ↓
LLM 设计智能体网络（包含依赖关系）
    ↓
_generate_execution_layers() [拓扑排序]
    ↓
生成 execution_layers (DAG 执行层)
    ↓
_execute_network_with_streaming()
    ↓
按层执行：
  Layer 1: [agent_1] (无依赖)
  Layer 2: [agent_2, agent_3] (依赖 agent_1)
  Layer 3: [agent_4] (依赖 agent_2, agent_3)
    ↓
结果合成
```

## 4. 关键区别

| 特性 | 外部 DAG Orchestrator | 内部 DAG 实现 |
|------|---------------------|--------------|
| **用途** | 任务分解 | 智能体网络执行 |
| **输入** | 自然语言任务 | 智能体依赖关系 |
| **输出** | 子任务节点 | 执行层 |
| **执行** | 通过外部服务 | 内部按层执行 |
| **使用频率** | 较少（特定场景） | 每次动态工作流 |

## 5. 当前使用情况

### 外部 DAG Orchestrator
- ✅ **已实现**: `dag_client.py` 提供完整客户端
- ⚠️ **使用较少**: 主要在 `orchestration_engine.py` 中用于任务分解
- ❓ **状态**: 外部服务可能未完全集成

### 内部 DAG 实现
- ✅ **核心功能**: 每次动态工作流都使用
- ✅ **拓扑排序**: 自动生成执行层
- ✅ **按层执行**: 支持并行和依赖管理
- ✅ **状态恢复**: 支持从指定层恢复执行

## 6. 建议

1. **外部 DAG Orchestrator**:
   - 如果外部服务未运行，任务分解会失败
   - 建议添加降级机制，使用内部实现

2. **内部 DAG 实现**:
   - 当前实现已经很好
   - 可以考虑添加循环检测（虽然理论上不应该有循环）

3. **统一 DAG 管理**:
   - 考虑将两种 DAG 实现统一
   - 或者明确各自的使用场景

## 7. 相关文件

- `agent-service/src/services/dag_client.py` - DAG Orchestrator 客户端
- `agent-service/src/core/orchestration_engine.py` - 编排引擎（使用外部 DAG）
- `agent-service/src/core/dynamic_workflow_designer.py` - 工作流设计器（内部 DAG）
- `agent-service/src/core/dynamic_execution_engine.py` - 执行引擎（按层执行）
- `agent-service/src/core/service_clients.py` - 服务客户端管理器


