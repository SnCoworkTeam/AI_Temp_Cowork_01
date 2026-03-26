# 智能体系统升级指南

## 一、升级内容概览

### ✅ 已实现的升级

1. **标准化协议** - 符合Agent Protocol标准
2. **智能体注册发现** - 动态注册和发现机制
3. **状态持久化** - 支持检查点和恢复
4. **性能分析** - 执行历史分析和优化
5. **学习优化** - 基于历史数据自动优化
6. **智能体协作** - 直接通信和协作机制

## 二、核心组件

### 2.1 标准化协议 (`protocols.py`)

定义了标准化的数据结构和接口：

```python
from agent_service.src.core.agents.protocols import (
    StandardTask, StandardResult, AgentCapabilities,
    CollaborationRequest, CollaborationResponse
)

# 创建标准化任务
task = StandardTask(
    task_id="task_123",
    task_type="data_analysis",
    description="分析销售订单",
    input_data={"table": "sales_orders"},
    context={"user_id": "user_123"}
)

# 返回标准化结果
result = StandardResult(
    success=True,
    output={"analysis": "..."},
    confidence=0.9,
    quality_score=85.0
)
```

### 2.2 标准化智能体 (`standardized_agent.py`)

新智能体应该继承`StandardizedAgent`：

```python
from agent_service.src.core.agents.standardized_agent import StandardizedAgent
from agent_service.src.core.agents.protocols import StandardTask, StandardResult

class MyAgent(StandardizedAgent):
    def __init__(self):
        super().__init__(
            agent_id="my_agent",
            name="我的智能体",
            description="智能体描述",
            capabilities={"capability1": "能力1描述"},
            supported_task_types=["task_type1"],
            supported_input_formats=["dict"],
            supported_output_formats=["dict"]
        )
    
    async def analyze_task(self, task: StandardTask) -> Dict[str, Any]:
        return {"can_handle": True}
    
    async def execute(self, task: StandardTask) -> StandardResult:
        return StandardResult(
            success=True,
            output={"result": "..."}
        )
```

### 2.3 智能体注册表

```python
from agent_service.src.core.agents.agent_registry import AgentRegistry

registry = AgentRegistry()

# 注册智能体
await registry.register_agent(my_agent)

# 发现智能体
agents = await registry.discover_agents_by_capability("data_analysis")
agents = await registry.discover_agents_by_task_type("data_query")

# 为任务找最佳智能体
best_agent = await registry.find_best_agent_for_task(task)
```

### 2.4 状态管理

```python
from agent_service.src.core.agents.state_manager import StateManager, InMemoryStateStore

state_manager = StateManager(InMemoryStateStore())

# 创建检查点
await state_manager.create_checkpoint(
    execution_id="exec_123",
    user_input="分析销售订单",
    context={},
    network_design={},
    current_layer=2,
    agent_results={}
)

# 恢复执行
saved_state = await state_manager.resume_execution("exec_123")
```

### 2.5 性能分析

```python
from agent_service.src.core.agents.performance_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()

# 添加执行记录
analyzer.add_execution_record(execution_record)

# 分析智能体性能
perf = analyzer.analyze_agent_performance("data_query_agent")

# 查找最佳模式
best_patterns = analyzer.find_best_pattern_for_request("分析销售订单")
```

## 三、API使用

### 3.1 执行动态工作流（支持恢复）

```bash
POST /api/v1/dynamic-workflow/execute
{
  "user_input": "分析销售订单",
  "context": {"user_id": "user_123"},
  "stream": true,
  "execution_id": "exec_123",  # 可选，用于恢复
  "resume": false  # 是否恢复执行
}
```

### 3.2 智能体注册表API

```bash
# 列出所有智能体
GET /api/v1/agents

# 获取智能体详情
GET /api/v1/agents/{agent_id}

# 发现智能体
POST /api/v1/agents/discover
{
  "task_type": "data_analysis",
  "capabilities": ["data_analysis", "statistical_analysis"]
}

# 获取智能体能力
GET /api/v1/agents/{agent_id}/capabilities

# 获取智能体统计
GET /api/v1/agents/{agent_id}/stats

# 获取性能摘要
GET /api/v1/performance/summary
```

## 四、迁移指南

### 4.1 旧智能体迁移

**无需修改**：所有现有智能体通过`AgentAdapter`自动适配，无需修改代码。

**可选迁移**：如果想使用新特性，可以逐步迁移到`StandardizedAgent`：

```python
# 旧版智能体（继续工作）
class OldAgent(IntelligentAgent):
    async def execute(self, input_data, context):
        return {"result": "..."}

# 新版智能体（推荐）
class NewAgent(StandardizedAgent):
    async def execute(self, task: StandardTask) -> StandardResult:
        return StandardResult(
            success=True,
            output={"result": "..."}
        )
```

### 4.2 使用新特性

```python
# 1. 使用标准化接口
task = StandardTask(...)
result = await agent.execute(task)

# 2. 智能体协作
response = await agent_a.request_collaboration(
    target_agent=agent_b,
    request_type="data_request",
    description="需要数据"
)

# 3. 状态持久化
await state_manager.create_checkpoint(...)
saved_state = await state_manager.resume_execution(execution_id)
```

## 五、配置选项

### 5.1 执行引擎配置

```python
engine = DynamicExecutionEngine(
    enable_learning=True,  # 启用学习功能
    enable_state_persistence=True,  # 启用状态持久化
    state_store=InMemoryStateStore()  # 或DatabaseStateStore
)
```

### 5.2 生产环境配置

```python
from agent_service.src.core.agents.state_manager import DatabaseStateStore

# 使用数据库存储（需要实现DatabaseStateStore）
state_store = DatabaseStateStore(db_session)
engine = DynamicExecutionEngine(
    enable_learning=True,
    enable_state_persistence=True,
    state_store=state_store
)
```

## 六、最佳实践

### 6.1 新智能体开发

1. **继承StandardizedAgent**
2. **实现标准化接口**
3. **注册到注册表**
4. **提供能力描述**

### 6.2 性能优化

1. **启用学习功能**：系统会自动优化
2. **记录执行历史**：用于分析和优化
3. **使用检查点**：长时间任务支持恢复

### 6.3 智能体协作

1. **使用协作请求**：智能体间直接通信
2. **处理协作请求**：实现`handle_collaboration_request`
3. **广播能力**：让其他智能体发现

## 七、总结

### ✅ 升级完成

- ✅ 标准化协议和接口
- ✅ 智能体注册发现
- ✅ 状态持久化
- ✅ 性能分析
- ✅ 学习优化
- ✅ 智能体协作

### 🎯 核心优势

- ✅ **符合主流标准**：与Agent Protocol对齐
- ✅ **企业级特性**：完整的状态管理和性能分析
- ✅ **向后兼容**：现有代码无需修改
- ✅ **持续优化**：基于历史数据自动优化

系统现在已达到主流智能体架构的水平！


