# AgentWorkflowInterface 组件

任务4.2：前端组件实现

## 概述

`AgentWorkflowInterface` 是一个整合了智能体聊天和工作流可视化的统一界面组件。它实现了前端与智能体工作流的交互，支持实时通信、状态同步和工作流进度可视化。

## 组件结构

```
AgentWorkflowInterface/
├── AgentWorkflowInterface.tsx  # 主组件
├── WorkflowVisualizer.tsx      # 工作流可视化组件
├── AgentChat.tsx               # 智能体聊天组件
├── index.ts                    # 导出文件
└── README.md                   # 说明文档
```

## 主要组件

### AgentWorkflowInterface

主组件，整合了工作流可视化和智能体聊天功能。

**Props:**

- `workflowId?: string` - 工作流ID
- `agentId?: string` - 智能体ID
- `initialInput?: string` - 初始输入
- `autoStart?: boolean` - 是否自动开始（默认：false）
- `onError?: (error: Error) => void` - 错误处理回调
- `onWorkflowComplete?: (result: any) => void` - 工作流完成回调

**使用示例:**

```tsx
import { AgentWorkflowInterface } from '@/components/AgentWorkflowInterface';

function MyPage() {
  return (
    <AgentWorkflowInterface
      workflowId="workflow-123"
      agentId="agent-456"
      initialInput="请帮我分析这个文档"
      autoStart={true}
      onError={(error) => console.error('Error:', error)}
      onWorkflowComplete={(result) => console.log('Complete:', result)}
    />
  );
}
```

### WorkflowVisualizer

工作流可视化组件，显示工作流的执行进度和节点状态。

**Props:**

- `progress: WorkflowProgress` - 工作流进度对象
- `isLoading?: boolean` - 是否加载中
- `onNodeClick?: (nodeId: string) => void` - 节点点击回调

**功能:**

- 显示工作流执行状态
- 显示进度条和百分比
- 显示当前执行的节点
- 显示各节点的执行状态
- 显示错误信息

### AgentChat

智能体聊天组件，提供与智能体交互的聊天界面。

**Props:**

- `agent: AgentState | null` - 智能体状态
- `onSendMessage: (message: string) => Promise<void>` - 发送消息回调
- `isLoading?: boolean` - 是否加载中
- `suggestions?: string[]` - 建议的问题列表

**功能:**

- 显示聊天消息历史
- 支持用户输入和发送消息
- 显示智能体响应（支持流式显示）
- 显示建议问题
- 显示状态指示器（思考中、等待输入等）

## 类型定义

### AgentState

智能体状态接口：

```typescript
interface AgentState {
  agentId?: string;
  agentName?: string;
  nodeId?: string;
  nodeName?: string;
  status: 'idle' | 'thinking' | 'executing' | 'awaiting_input' | 'completed' | 'error';
  currentMessage?: string;
  suggestions?: string[];
  error?: string;
  executionId?: string;
}
```

### WorkflowProgress

工作流进度接口：

```typescript
interface WorkflowProgress {
  id?: string;
  executionId?: string;
  name?: string;
  status?: 'pending' | 'running' | 'completed' | 'failed' | 'paused' | 'cancelled';
  progress?: number; // 0-100
  currentNodeId?: string;
  currentNodeName?: string;
  nodeStatuses?: Record<
    string,
    {
      status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
      progress?: number;
      error?: string;
    }
  >;
  startTime?: number;
  endTime?: number;
  error?: string;
}
```

### AgentResponse

智能体响应接口（扩展自 `AgentResponsePayload`）：

```typescript
interface AgentResponse extends AgentResponsePayload {
  requires_further_input?: boolean;
  suggested_questions?: string[];
  next_node?: string;
  workflow_id?: string;
}
```

## API 端点

组件使用以下API端点：

1. **继续工作流**: `POST /api/agent/continue`

   ```json
   {
     "input": "用户输入",
     "workflow_id": "工作流ID",
     "execution_id": "执行ID",
     "current_node": "当前节点ID",
     "agent_id": "智能体ID"
   }
   ```

2. **推进工作流**: `POST /api/workflows/advance`

   ```json
   {
     "workflow_id": "工作流ID",
     "execution_id": "执行ID",
     "next_node_id": "下一个节点ID"
   }
   ```

3. **启动工作流**: `POST /api/workflows/{workflowId}/start`
   ```json
   {
     "input": { "content": "初始输入" },
     "agent_id": "智能体ID"
   }
   ```

## 工作流程

1. **初始化**: 组件挂载后，如果设置了 `autoStart=true` 和 `workflowId`，会自动启动工作流
2. **用户输入**: 用户在聊天界面输入消息，调用 `handleUserInput`
3. **API调用**: 发送请求到 `/api/agent/continue`
4. **处理响应**: 收到响应后，调用 `handleAgentResponse` 处理
5. **状态更新**: 根据响应更新智能体状态和工作流进度
6. **工作流推进**: 如果需要，调用 `advanceWorkflow` 推进到下一个节点
7. **UI更新**: 组件自动更新UI显示最新状态

## 错误处理

组件实现了完整的错误处理机制：

- 网络错误：显示错误提示，3秒后自动清除
- API错误：显示错误消息，更新智能体状态为 `error`
- 工作流错误：在工作流可视化器中显示错误信息

## 状态管理

组件使用 React Hooks 进行状态管理：

- `useState`: 管理组件状态（智能体状态、工作流进度、加载状态、错误信息）
- `useCallback`: 优化回调函数性能
- `useEffect`: 处理副作用（自动启动、初始化）

## 样式

组件使用 Tailwind CSS 进行样式设计，支持响应式布局。

## 依赖

- React 18+
- TypeScript
- `@/types/agent-protocol` - 协议类型定义

## 注意事项

1. 确保后端API端点已实现并可用
2. API响应格式需要符合 `AgentResponse` 接口定义
3. 工作流进度更新需要实时同步
4. 错误处理需要用户友好的提示

## 后续优化建议

1. 添加WebSocket支持，实现实时通信
2. 添加消息历史持久化
3. 添加工作流可视化图形
4. 添加更多交互功能（暂停、取消、重试等）
5. 优化性能和用户体验
