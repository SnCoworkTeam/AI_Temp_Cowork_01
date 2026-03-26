# 平台元数据覆盖分析报告

## 当前元数据收集情况

### ✅ 已实现的元数据收集

1. **MCP工具元数据** (`MCPToolCollector`)
   - 来源：mcp-gateway
   - 收集内容：工具名称、描述、参数、返回值、状态
   - 存储位置：workflow_metadata表（作为workflow类型）

2. **工作流元数据** (`WorkflowCollector`)
   - 来源：workflow-engine
   - 收集内容：工作流定义、输入输出schema、执行统计
   - 存储位置：workflow_metadata表

3. **知识库元数据** (`KnowledgeCollector`)
   - 来源：knowledge-base
   - 收集内容：文档、知识库结构
   - 存储位置：data_assets表

4. **AI模型元数据** (`ModelCollector`)
   - 来源：metadata-service（直接创建）
   - 收集内容：模型信息、训练配置、性能指标
   - 存储位置：ai_models表
   - **新增**：智能体自动注册为AI模型

5. **数据血缘** (`DataLineageCollector`)
   - 来源：各服务的数据流
   - 收集内容：数据流向、依赖关系
   - 存储位置：lineage_graph表

### ⚠️ 缺失的元数据收集

1. **用户意图和对话元数据**
   - 数据来源：agent-service的对话记录、意图分析结果
   - 当前状态：有Conversation和Message模型，但未注册到metadata-service
   - 需要收集：
     - 用户意图类型（task_type）
     - 意图置信度
     - 对话上下文
     - 意图到服务的映射关系

2. **任务执行元数据**
   - 数据来源：agent-service的ExecutionState、orchestration_engine
   - 当前状态：有执行记录，但未注册到metadata-service
   - 需要收集：
     - 任务类型和执行策略
     - 路由决策
     - 执行路径
     - 使用的服务和工具
     - 执行时间和成功率

3. **工具执行元数据**
   - 数据来源：mcp-gateway的tool_executions表、audit日志
   - 当前状态：有执行记录和审计日志，但未注册到metadata-service
   - 需要收集：
     - 工具执行频率
     - 执行成功率
     - 平均执行时间
     - 参数模式
     - 错误模式

4. **智能体执行元数据**
   - 数据来源：agent_execution_records表
   - 当前状态：有执行记录，但未注册到metadata-service
   - 需要收集：
     - 智能体执行统计
     - 输入输出模式
     - 性能指标
     - 质量评分

5. **用户行为模式元数据**
   - 数据来源：knowledge-base的UserBehaviorRepository、各服务的访问日志
   - 当前状态：有部分行为记录，但未统一注册到metadata-service
   - 需要收集：
     - 用户访问模式
     - 常用工具和服务
     - 查询模式
     - 时间分布

6. **服务调用元数据**
   - 数据来源：各服务间的API调用
   - 当前状态：可能有日志，但未统一收集
   - 需要收集：
     - 服务间调用关系
     - API调用频率
     - 调用链
     - 依赖关系

7. **数据查询元数据**
   - 数据来源：SAP查询、知识库查询等
   - 当前状态：有查询记录，但未注册到metadata-service
   - 需要收集：
     - 查询模式
     - 常用查询条件
     - 查询结果统计
     - 数据访问模式

## 元数据完整性要求（用于意图识别和任务编排）

### 1. 意图识别所需元数据

- ✅ 工具元数据（可用工具列表）
- ✅ 工作流元数据（可用工作流）
- ✅ AI模型元数据（可用智能体）
- ⚠️ **用户意图历史**（需要补充）
- ⚠️ **意图到服务的映射**（需要补充）
- ⚠️ **用户行为模式**（需要补充）

### 2. 任务编排所需元数据

- ✅ 工作流定义（工作流结构）
- ✅ 工具定义（工具参数和返回值）
- ⚠️ **任务执行历史**（需要补充）
- ⚠️ **执行路径模式**（需要补充）
- ⚠️ **服务依赖关系**（需要补充）
- ⚠️ **性能指标**（需要补充）

### 3. 智能路由所需元数据

- ✅ 服务元数据（可用服务）
- ⚠️ **服务调用关系**（需要补充）
- ⚠️ **服务性能统计**（需要补充）
- ⚠️ **服务可用性**（需要补充）

## 建议补充的元数据收集器

1. **IntentCollector** - 收集用户意图和对话元数据
2. **ExecutionCollector** - 收集任务执行元数据
3. **ToolExecutionCollector** - 收集工具执行详细元数据
4. **AgentExecutionCollector** - 收集智能体执行元数据
5. **UserBehaviorCollector** - 收集用户行为模式元数据
6. **ServiceCallCollector** - 收集服务调用元数据
7. **QueryPatternCollector** - 收集数据查询模式元数据

## 优先级

### 高优先级（意图识别必需）
1. IntentCollector - 用户意图历史
2. ToolExecutionCollector - 工具使用模式
3. UserBehaviorCollector - 用户行为模式

### 中优先级（任务编排必需）
4. ExecutionCollector - 任务执行历史
5. ServiceCallCollector - 服务调用关系
6. AgentExecutionCollector - 智能体执行统计

### 低优先级（优化用）
7. QueryPatternCollector - 查询模式分析


