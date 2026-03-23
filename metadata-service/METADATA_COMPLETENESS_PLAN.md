# 元数据完整性实施计划

## 当前状态总结

### ✅ 已实现的元数据收集

1. **MCP工具元数据** - 工具定义、参数、返回值
2. **工作流元数据** - 工作流定义、输入输出schema
3. **知识库元数据** - 文档和知识库结构
4. **AI模型元数据** - 模型信息、训练配置（包括智能体）
5. **数据血缘** - 数据流向和依赖关系

### ⚠️ 需要补充的元数据收集

#### 高优先级（意图识别必需）

1. **用户意图元数据**
   - 数据来源：agent-service的意图分析结果
   - 需要API：`GET /api/v1/intents` 或从执行记录中提取
   - 收集内容：
     - 意图类型（task_type）
     - 意图置信度
     - 意图到服务的映射
     - 意图使用频率
   - 存储方式：业务实体（entity_type: "intent_pattern"）

2. **工具执行统计元数据**
   - 数据来源：mcp-gateway的执行记录
   - 需要API：`GET /api/tools/{tool_id}/stats` 或 `GET /api/tools/stats`
   - 收集内容：
     - 执行频率
     - 成功率
     - 平均执行时间
     - 常用参数模式
     - 错误模式
   - 存储方式：更新工具的工作流元数据

3. **任务执行元数据**
   - 数据来源：agent-service的执行记录
   - 需要API：`GET /api/v1/executions` 和 `GET /api/v1/executions/{id}`
   - 收集内容：
     - 任务类型和执行策略
     - 路由决策
     - 执行路径
     - 使用的服务和工具
     - 执行时间和成功率
   - 存储方式：工作流元数据（execution_pattern类型）

#### 中优先级（任务编排必需）

4. **智能体执行元数据**
   - 数据来源：agent_execution_records表
   - 需要API：从数据库直接查询或通过agent-service API
   - 收集内容：
     - 智能体执行统计
     - 输入输出模式
     - 性能指标
   - 存储方式：更新AI模型元数据

5. **服务调用元数据**
   - 数据来源：各服务间的API调用日志
   - 需要API：各服务的监控API
   - 收集内容：
     - 服务间调用关系
     - API调用频率
     - 调用链
   - 存储方式：数据血缘或业务实体

#### 低优先级（优化用）

6. **用户行为模式元数据**
   - 数据来源：各服务的访问日志
   - 收集内容：
     - 用户访问模式
     - 常用工具和服务
     - 查询模式
   - 存储方式：业务实体或数据资产

## 实施步骤

### 第一步：添加必要的API端点

#### 1.1 mcp-gateway: 工具执行统计API
```python
# mcp-gateway/src/routes/tools.py
@router.get("/{tool_id}/stats")
async def get_tool_stats(tool_id: str):
    """获取工具执行统计"""
    stats = execution_repo.get_statistics(tool_id=tool_id)
    return stats

@router.get("/stats")
async def get_all_tools_stats():
    """获取所有工具的执行统计"""
    # 返回所有工具的统计信息
```

#### 1.2 agent-service: 执行记录和意图历史API
```python
# agent-service/src/routes/executions.py
@router.get("/intents")
async def list_intents():
    """获取意图历史（从执行记录中提取）"""
    # 从执行记录中聚合意图信息
    
@router.get("/patterns")
async def list_execution_patterns():
    """获取执行模式（聚合的执行路径）"""
    # 从执行记录中聚合执行模式
```

### 第二步：更新收集器实现

#### 2.1 IntentCollector
- 调用 `GET /api/v1/executions/intents` 获取意图历史
- 聚合意图到服务的映射关系
- 存储为业务实体

#### 2.2 ExecutionCollector
- 调用 `GET /api/v1/executions` 获取执行记录
- 聚合执行模式（相同任务类型的执行路径）
- 存储为工作流元数据（execution_pattern类型）

#### 2.3 ToolExecutionCollector
- 调用 `GET /api/tools/stats` 获取工具执行统计
- 更新工具的工作流元数据中的使用统计

### 第三步：实时元数据更新

在关键操作点添加元数据更新：

1. **意图分析后** - 记录意图元数据
2. **工具执行后** - 更新工具执行统计
3. **任务完成后** - 记录执行模式和路径
4. **智能体执行后** - 更新智能体执行统计

### 第四步：元数据查询API增强

为意图识别和任务编排提供专门的查询API：

```python
# metadata-service/src/api/intent_routing.py
@router.get("/intent-to-service")
async def get_intent_to_service_mapping(intent_type: str):
    """获取意图到服务的映射"""
    
@router.get("/execution-patterns")
async def get_execution_patterns(task_type: str):
    """获取执行模式"""
    
@router.get("/tool-recommendations")
async def get_tool_recommendations(intent: str, context: dict):
    """基于元数据推荐工具"""
```

## 元数据完整性检查清单

### 意图识别所需元数据
- [x] 可用工具列表
- [x] 可用工作流列表
- [x] 可用智能体列表
- [ ] 用户意图历史
- [ ] 意图到服务的映射
- [ ] 工具使用模式
- [ ] 用户行为模式

### 任务编排所需元数据
- [x] 工作流定义
- [x] 工具定义
- [ ] 任务执行历史
- [ ] 执行路径模式
- [ ] 服务依赖关系
- [ ] 性能指标
- [ ] 错误模式

### 智能路由所需元数据
- [x] 服务元数据
- [ ] 服务调用关系
- [ ] 服务性能统计
- [ ] 服务可用性
- [ ] 负载情况

## 下一步行动

1. ✅ 创建元数据收集器框架（已完成）
2. ⏳ 添加必要的API端点（mcp-gateway和agent-service）
3. ⏳ 实现收集器的实际数据收集逻辑
4. ⏳ 添加实时元数据更新机制
5. ⏳ 创建元数据查询API（用于意图识别和任务编排）


