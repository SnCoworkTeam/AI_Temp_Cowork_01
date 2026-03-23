# 动态工作流快速启动指南

## 一、已实现功能

### ✅ 核心组件

1. **基础智能体接口** (`base_agent.py`)
   - 统一的智能体基类
   - 执行跟踪和统计

2. **三个核心智能体**
   - **MCP工具智能体** (`mcp_tool_agent.py`)：工具选择、执行、错误处理
   - **工作流智能体** (`workflow_agent.py`)：工作流编排、执行、监控
   - **元数据智能体** (`metadata_agent.py`)：业务语义、实体映射、上下文增强

3. **动态工作流设计器** (`dynamic_workflow_designer.py`)
   - LLM动态分析请求
   - 动态设计智能体网络
   - 流式输出思考过程

4. **动态执行引擎** (`dynamic_execution_engine.py`)
   - 执行动态设计的网络
   - 支持并行执行
   - 流式输出执行过程

5. **API路由** (`dynamic_workflow.py`)
   - `/api/v1/dynamic-workflow/execute` - 执行（流式）
   - `/api/v1/dynamic-workflow/design` - 仅设计

6. **前端组件**
   - `DynamicWorkflowDisplay.tsx` - 显示思考和执行过程
   - `dynamic-workflow.ts` - API客户端
   - `ChatInterface.tsx` - 集成动态工作流

## 二、使用方式

### 2.1 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 或单独启动agent-service
cd agent-service
python -m uvicorn src.main:app --host 0.0.0.0 --port 8010 --reload
```

### 2.2 前端使用

1. **打开聊天界面**
   - 访问 `http://localhost:3000`
   - 进入AI助手页面

2. **启用动态工作流**
   - 在输入框上方勾选"使用动态工作流（显示思考和执行过程）"

3. **发送消息**
   - 输入消息，例如："分析一下销售订单，形成分析报告，然后发送给刘玉斌"
   - 系统会自动使用动态工作流处理

4. **查看过程**
   - **思考过程**（蓝色区域）：显示LLM的分析和设计过程
   - **执行过程**（绿色区域）：显示每个智能体的执行状态
   - **最终结果**：显示执行结果

## 三、流式输出示例

### 3.1 思考过程输出

```
💭 思考过程
  🔍 正在分析用户请求... (10%)
  ✓ 请求分析完成：complex复杂度 (30%)
    复杂度: complex | 类型: analysis | 预计时间: 10-30秒
  🎨 正在设计智能体执行网络... (40%)
  ✓ 智能体网络设计完成：5个智能体，3个执行层 (60%)
    5个智能体 | 3个执行层 | 预计时间: 10-30秒
  ✅ 正在验证和优化网络设计... (70%)
  ✓ 网络设计验证完成 (90%)
```

### 3.2 执行过程输出

```
⚙️ 执行过程
  ✓ 开始执行智能体网络：5个智能体，3个执行层
  
  第 1/3 层
    执行第 1/3 层：1个智能体
    🤖 提供业务上下文 (5%)
    ✓ 智能体 metadata_agent_1 执行完成 (0.5s)
    ✓ 第 1/3 层执行完成
  
  第 2/3 层
    执行第 2/3 层：2个智能体
    🤖 执行数据查询 (35%)
    ✓ 智能体 mcp_tool_agent_1 执行完成 (2.3s)
    🤖 分析数据 (40%)
    ✓ 智能体 analysis_agent_1 执行完成 (1.8s)
    ✓ 第 2/3 层执行完成
  
  第 3/3 层
    执行第 3/3 层：2个智能体
    🤖 生成报告内容 (70%)
    ✓ 智能体 content_agent_1 执行完成 (3.2s)
    🤖 发送邮件 (85%)
    ✓ 智能体 mcp_tool_agent_2 执行完成 (1.5s)
    ✓ 第 3/3 层执行完成
  
  🔄 正在合成最终结果... (95%)
  ✓ 智能体网络执行完成 (100%)
```

## 四、测试场景

### 场景1：简单查询
**输入**："查询销售订单"

**预期**：
- 思考过程：快速分析，设计简单网络
- 执行过程：元数据智能体 → MCP工具智能体 → 格式优化智能体
- 结果：返回查询结果

### 场景2：复杂分析
**输入**："分析本季度销售趋势，生成分析报告并发送给管理层"

**预期**：
- 思考过程：深度分析，设计复杂网络
- 执行过程：多智能体协作（元数据 → 数据查询 → 分析 → 报告生成 → 邮件发送）
- 结果：完整的分析报告和发送确认

### 场景3：即时问答
**输入**："SAP的MRP是什么？"

**预期**：
- 思考过程：识别为简单问答
- 执行过程：直接使用内容智能体回答
- 结果：直接回答，无需复杂流程

## 五、下一步扩展

### 5.1 需要实现的智能体

- [ ] 数据查询智能体（DataQueryAgent）
- [ ] 数据清洗智能体（DataCleanAgent）
- [ ] 数据增强智能体（DataEnrichAgent）
- [ ] 分析智能体（AnalysisAgent）
- [ ] 洞察生成智能体（InsightAgent）
- [ ] 内容生成智能体（ContentAgent）
- [ ] 格式优化智能体（FormatAgent）
- [ ] 交付准备智能体（DeliveryAgent）

### 5.2 需要优化的功能

- [ ] 智能体网络设计缓存
- [ ] 执行结果缓存
- [ ] 错误恢复和降级策略
- [ ] 性能监控和优化
- [ ] 智能体执行历史分析

## 六、API文档

### 6.1 执行动态工作流

```bash
POST /api/v1/dynamic-workflow/execute
Content-Type: application/json

{
  "user_input": "分析一下销售订单",
  "context": {
    "user_id": "user_123",
    "username": "刘玉斌"
  },
  "stream": true
}

# 响应：Server-Sent Events (SSE)
data: {"type": "thinking", "stage": "analyzing_request", ...}
data: {"type": "thinking", "stage": "analysis_complete", ...}
data: {"type": "execution", "stage": "execution_start", ...}
...
```

### 6.2 仅设计工作流

```bash
POST /api/v1/dynamic-workflow/design
Content-Type: application/json

{
  "user_input": "分析一下销售订单",
  "context": {
    "user_id": "user_123"
  },
  "stream": false
}

# 响应：
{
  "success": true,
  "design": {
    "agents": [...],
    "execution_layers": [...],
    "estimated_duration": "10-30秒"
  }
}
```

## 七、总结

### ✅ 已实现

- ✅ 动态工作流核心架构
- ✅ 三个核心智能体
- ✅ LLM工作流设计器
- ✅ 动态执行引擎
- ✅ 流式输出（思考和执行过程）
- ✅ 前端显示组件

### 🎯 核心优势

- ✅ **真正的动态**：每个请求都定制化处理
- ✅ **完全透明**：用户可以看到思考和执行过程
- ✅ **高度灵活**：适应各种业务场景
- ✅ **易于扩展**：可以轻松添加新智能体

### 📝 使用说明

1. 启动服务
2. 打开前端
3. 启用动态工作流（复选框）
4. 发送消息
5. 查看思考和执行过程


