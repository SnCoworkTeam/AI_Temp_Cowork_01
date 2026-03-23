# 前端与智能体工作流交互协议设计 - 任务4.1

## 项目概述

本文档设计了前端与智能体工作流引擎之间的完整交互协议，包括实时通信API、前端组件结构和状态管理规范。该协议与后端智能体通信协议（任务1.2）完全兼容，为LuminaOS平台提供流畅的用户体验。

## 设计目标

### 核心目标
1. **实时响应**: WebSocket双向通信，毫秒级消息传递
2. **状态一致**: 前后端状态实时同步，避免数据不一致
3. **用户体验**: 流畅的对话界面和可视化工作流操作
4. **容错能力**: 网络断开重连、消息重发、错误恢复
5. **可扩展性**: 支持多种智能体类型和工作流模式

## 1. 实时通信API设计 (WebSocket)

### 1.1 WebSocket连接管理

```typescript
// WebSocket连接配置
interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnectInterval: number;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
  messageQueueSize: number;
}

// 连接状态
enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}
```

### 1.2 WebSocket消息格式

```typescript
// 基础消息结构
interface WebSocketMessage<T = any> {
  id: string;                    // 消息唯一ID
  type: MessageType;             // 消息类型
  timestamp: number;             // 时间戳
  payload: T;                    // 消息内容
  sessionId: string;             // 会话ID
  userId: string;                // 用户ID
  requestId?: string;            // 请求ID（用于响应匹配）
  metadata?: Record<string, any>; // 元数据
}

// 消息类型枚举
enum MessageType {
  // 连接管理
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  HEARTBEAT = 'heartbeat',

  // 对话消息
  CHAT_MESSAGE = 'chat_message',
  CHAT_RESPONSE = 'chat_response',
  CHAT_TYPING = 'chat_typing',

  // 工作流相关
  WORKFLOW_START = 'workflow_start',
  WORKFLOW_PROGRESS = 'workflow_progress',
  WORKFLOW_NODE_COMPLETE = 'workflow_node_complete',
  WORKFLOW_COMPLETE = 'workflow_complete',
  WORKFLOW_ERROR = 'workflow_error',
  WORKFLOW_PAUSE = 'workflow_pause',
  WORKFLOW_RESUME = 'workflow_resume',
  WORKFLOW_CANCEL = 'workflow_cancel',

  // 智能体相关
  AGENT_EXECUTE = 'agent_execute',
  AGENT_RESPONSE = 'agent_response',
  AGENT_THINKING = 'agent_thinking',
  AGENT_TOOL_CALL = 'agent_tool_call',
  AGENT_ERROR = 'agent_error',

  // 决策点交互
  DECISION_REQUEST = 'decision_request',
  DECISION_RESPONSE = 'decision_response',
  USER_INPUT_REQUEST = 'user_input_request',
  USER_INPUT_RESPONSE = 'user_input_response',

  // 状态同步
  STATE_SYNC = 'state_sync',
  CONTEXT_UPDATE = 'context_update',

  // 系统消息
  ERROR = 'error',
  SUCCESS = 'success',
  NOTIFICATION = 'notification'
}
```

### 1.3 具体消息载荷定义

#### 1.3.1 对话消息

```typescript
// 聊天消息
interface ChatMessagePayload {
  content: string;
  messageType: 'text' | 'image' | 'file' | 'voice';
  conversationId: string;
  parentMessageId?: string;
  attachments?: Array<{
    type: 'file' | 'image' | 'document';
    url: string;
    name: string;
    size: number;
  }>;
}

// 聊天响应
interface ChatResponsePayload {
  content: string;
  messageId: string;
  conversationId: string;
  agentId?: string;
  agentName?: string;
  streaming: boolean;
  isComplete: boolean;
  toolCalls?: ToolCall[];
  citations?: KnowledgeCitation[];
  reasoning?: string[];
  confidence?: number;
  tokens?: {
    input: number;
    output: number;
    total: number;
  };
}

// 工具调用
interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, any>;
  result?: any;
  error?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime: number;
  endTime?: number;
}

// 知识库引用
interface KnowledgeCitation {
  chunkId: string;
  documentId: string;
  documentName: string;
  content: string;
  score: number;
  page?: number;
  section?: string;
}
```

#### 1.3.2 工作流消息

```typescript
// 工作流启动
interface WorkflowStartPayload {
  workflowId: string;
  workflowName: string;
  version: string;
  input: Record<string, any>;
  config?: Record<string, any>;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
}

// 工作流进度
interface WorkflowProgressPayload {
  executionId: string;
  workflowId: string;
  workflowName: string;
  status: WorkflowStatus;
  progress: number;
  currentNode: string;
  currentNodeName: string;
  estimatedTimeRemaining?: number;
  metrics?: {
    nodesCompleted: number;
    totalNodes: number;
    executionTime: number;
    errorCount: number;
  };
}

// 节点完成
interface WorkflowNodeCompletePayload {
  executionId: string;
  nodeId: string;
  nodeName: string;
  nodeType: string;
  status: 'success' | 'failed' | 'skipped';
  output: Record<string, any>;
  executionTime: number;
  error?: string;
  nextNodes?: string[];
}

// 工作流状态
enum WorkflowStatus {
  PENDING = 'pending',
  INITIALIZING = 'initializing',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  TIMEOUT = 'timeout'
}
```

#### 1.3.3 智能体消息

```typescript
// 智能体执行请求
interface AgentExecutePayload {
  agentId: string;
  agentName: string;
  input: {
    content: string;
    context: Record<string, any>;
    variables: Record<string, any>;
    conversationId: string;
    metadata: Record<string, any>;
  };
  config?: {
    streaming: boolean;
    timeout: number;
    retryCount: number;
    enableCache: boolean;
    cacheTtl: number;
  };
}

// 智能体响应
interface AgentResponsePayload {
  executionId: string;
  agentId: string;
  agentName: string;
  success: boolean;
  output: {
    content: string;
    metadata: Record<string, any>;
    toolCalls: ToolCall[];
    reasoningSteps: string[];
    confidenceScore: number;
    executionTime: number;
    tokensUsed: number;
  };
  context: {
    conversationId: string;
    messages: ConversationMessage[];
    variables: Record<string, any>;
    sharedMemory: Record<string, any>;
  };
  error?: string;
}

// 智能体思考状态
interface AgentThinkingPayload {
  agentId: string;
  agentName: string;
  status: 'thinking' | 'analyzing' | 'planning' | 'executing';
  thought?: string;
  step?: number;
  totalSteps?: number;
}

// 对话消息
interface ConversationMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  toolCalls?: ToolCall[];
  metadata?: Record<string, any>;
  timestamp: number;
}
```

#### 1.3.4 决策点交互

```typescript
// 决策请求
interface DecisionRequestPayload {
  decisionId: string;
  workflowId: string;
  executionId: string;
  nodeId: string;
  nodeName: string;
  question: string;
  description?: string;
  options: Array<{
    id: string;
    label: string;
    description?: string;
    value: any;
    metadata?: Record<string, any>;
  }>;
  allowCustomInput: boolean;
  timeout?: number;
  defaultOption?: string;
}

// 决策响应
interface DecisionResponsePayload {
  decisionId: string;
  selectedOption?: string;
  customInput?: any;
  timestamp: number;
  metadata?: Record<string, any>;
}

// 用户输入请求
interface UserInputRequestPayload {
  requestId: string;
  workflowId: string;
  executionId: string;
  nodeId: string;
  prompt: string;
  inputType: 'text' | 'number' | 'date' | 'select' | 'multi-select' | 'file';
  validation?: {
    required: boolean;
    minLength?: number;
    maxLength?: number;
    pattern?: string;
    options?: string[];
  };
  timeout?: number;
  placeholder?: string;
  defaultValue?: any;
}

// 用户输入响应
interface UserInputResponsePayload {
  requestId: string;
  value: any;
  timestamp: number;
  isValid: boolean;
  error?: string;
}
```

#### 1.3.5 状态同步

```typescript
// 状态同步
interface StateSyncPayload {
  stateType: 'conversation' | 'workflow' | 'agent' | 'global';
  stateId: string;
  state: Record<string, any>;
  version: number;
  timestamp: number;
  partial: boolean;
}

// 上下文更新
interface ContextUpdatePayload {
  contextId: string;
  contextType: 'conversation' | 'workflow' | 'session';
  updates: Record<string, any>;
  operation: 'set' | 'update' | 'delete' | 'merge';
  timestamp: number;
}
```

## 2. 前端组件结构设计

### 2.1 智能体聊天界面

```typescript
// 聊天界面组件属性
interface ChatInterfaceProps {
  conversationId: string;
  agentId?: string;
  config?: {
    showTypingIndicator: boolean;
    showMessageStatus: boolean;
    enableFileUpload: boolean;
    enableVoiceInput: boolean;
    maxMessageLength: number;
    theme?: 'light' | 'dark' | 'auto';
  };
  onMessageSend?: (message: ChatMessagePayload) => void;
  onMessageReceive?: (message: ChatResponsePayload) => void;
  onError?: (error: Error) => void;
}

// 消息组件
interface MessageComponentProps {
  message: Message;
  showAvatar: boolean;
  showTimestamp: boolean;
  showStatus: boolean;
  onRetry?: (messageId: string) => void;
  onEdit?: (messageId: string, newContent: string) => void;
  onDelete?: (messageId: string) => void;
}

// 输入组件
interface MessageInputProps {
  placeholder?: string;
  maxLength?: number;
  multiline?: boolean;
  showSendButton?: boolean;
  showAttachButton?: boolean;
  showVoiceButton?: boolean;
  onSend: (content: string, attachments?: Attachment[]) => void;
  onTyping?: (isTyping: boolean) => void;
  disabled?: boolean;
}

// 附件类型
interface Attachment {
  id: string;
  type: 'file' | 'image' | 'document';
  name: string;
  size: number;
  url: string;
  preview?: string;
}
```

### 2.2 工作流可视化组件

```typescript
// 工作流设计器属性
interface WorkflowDesignerProps {
  workflowId?: string;
  config?: WorkflowConfig;
  readonly?: boolean;
  showGrid?: boolean;
  showMiniMap?: boolean;
  enableZoom?: boolean;
  enablePan?: boolean;
  nodeTypes: NodeTypeDefinition[];
  onConfigChange?: (config: WorkflowConfig) => void;
  onNodeAdd?: (nodeType: string, position: NodePosition) => void;
  onNodeDelete?: (nodeId: string) => void;
  onConnectionAdd?: (connection: WorkflowConnection) => void;
  onConnectionDelete?: (connectionId: string) => void;
}

// 工作流执行可视化
interface WorkflowExecutionVisualizerProps {
  executionId: string;
  workflowConfig: WorkflowConfig;
  executionStatus: WorkflowExecutionStatus;
  nodeStatuses: Record<string, NodeExecutionStatus>;
  showProgress?: boolean;
  showMetrics?: boolean;
  showLogs?: boolean;
  onNodeClick?: (nodeId: string) => void;
}

// 节点执行状态
interface NodeExecutionStatus {
  nodeId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  progress?: number;
  startTime?: number;
  endTime?: number;
  executionTime?: number;
  input?: Record<string, any>;
  output?: Record<string, any>;
  error?: string;
  logs?: LogEntry[];
}

// 日志条目
interface LogEntry {
  id: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  timestamp: number;
  source: string;
  metadata?: Record<string, any>;
}
```

### 2.3 决策点交互组件

```typescript
// 决策对话框属性
interface DecisionDialogProps {
  decision: DecisionRequestPayload;
  isOpen: boolean;
  onSelect: (option: string | any) => void;
  onCancel?: () => void;
  timeout?: number;
}

// 用户输入对话框
interface UserInputDialogProps {
  inputRequest: UserInputRequestPayload;
  isOpen: boolean;
  onSubmit: (value: any) => void;
  onCancel?: () => void;
  onValidate?: (value: any) => { isValid: boolean; error?: string };
}

// 审批流组件
interface ApprovalFlowProps {
  approvalRequest: {
    id: string;
    title: string;
    description: string;
    requestedBy: string;
    requestTime: number;
    deadline?: number;
    details: Record<string, any>;
    attachments?: Attachment[];
  };
  onApprove: (comments?: string) => void;
  onReject: (reason: string) => void;
  onDelegate?: (toUserId: string) => void;
}
```

### 2.4 状态管理组件

```typescript
// WebSocket状态提供者
interface WebSocketProviderProps {
  config: WebSocketConfig;
  children: React.ReactNode;
}

// 通知系统
interface NotificationProps {
  notifications: Array<{
    id: string;
    type: 'info' | 'success' | 'warning' | 'error';
    title: string;
    message: string;
    timestamp: number;
    timeout?: number;
    actions?: Array<{
      label: string;
      action: () => void;
    }>;
  }>;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  maxVisible?: number;
}
```

## 3. 状态管理规范

### 3.1 Redux/Zustand状态结构

```typescript
// 全局状态接口
interface AppState {
  // 连接状态
  connection: ConnectionState;

  // 用户状态
  user: {
    id: string;
    name: string;
    avatar?: string;
    preferences: UserPreferences;
    permissions: string[];
  };

  // 对话状态
  conversations: {
    active: string | null;
    list: Record<string, ConversationState>;
  };

  // 工作流状态
  workflows: {
    active: string | null;
    list: Record<string, WorkflowState>;
    executions: Record<string, WorkflowExecutionState>;
  };

  // 智能体状态
  agents: {
    list: Record<string, AgentInfo>;
    activeExecutions: Record<string, AgentExecutionState>;
  };

  // UI状态
  ui: {
    theme: 'light' | 'dark' | 'auto';
    sidebar: {
      collapsed: boolean;
      activeTab: string;
    };
    modals: {
      decision: DecisionModalState | null;
      userInput: UserInputModalState | null;
    };
    notifications: NotificationState[];
  };

  // 缓存状态
  cache: {
    messages: Record<string, Message>;
    workflowConfigs: Record<string, WorkflowConfig>;
    agentConfigs: Record<string, AgentConfig>;
  };
}

// 用户偏好
interface UserPreferences {
  language: string;
  timezone: string;
  theme: 'light' | 'dark' | 'auto';
  notifications: {
    desktop: boolean;
    sound: boolean;
    email: boolean;
  };
  chat: {
    showTypingIndicator: boolean;
    showTimestamps: boolean;
    messageGrouping: boolean;
    autoScroll: boolean;
  };
  workflow: {
    showGrid: boolean;
    showMiniMap: boolean;
    autoSave: boolean;
    snapToGrid: boolean;
  };
}
```

### 3.2 对话状态管理

```typescript
// 对话状态
interface ConversationState {
  id: string;
  title: string;
  agentId?: string;
  agentName?: string;
  messages: Message[];
  typing: {
    isTyping: boolean;
    userId?: string;
    userName?: string;
  };
  context: Record<string, any>;
  metadata: {
    createdAt: number;
    updatedAt: number;
    messageCount: number;
    participantCount: number;
  };
  settings: {
    notifications: boolean;
    autoScroll: boolean;
    showReadStatus: boolean;
  };
}

// 消息状态管理操作
interface ConversationActions {
  // 消息操作
  sendMessage: (conversationId: string, content: string, attachments?: Attachment[]) => void;
  receiveMessage: (conversationId: string, message: Message) => void;
  updateMessage: (conversationId: string, messageId: string, updates: Partial<Message>) => void;
  deleteMessage: (conversationId: string, messageId: string) => void;
  markAsRead: (conversationId: string, messageId?: string) => void;

  // 对话操作
  createConversation: (agentId?: string) => string;
  deleteConversation: (conversationId: string) => void;
  setActiveConversation: (conversationId: string | null) => void;
  updateConversationTitle: (conversationId: string, title: string) => void;
  updateConversationContext: (conversationId: string, context: Record<string, any>) => void;

  // 打字状态
  setTyping: (conversationId: string, isTyping: boolean, userId?: string) => void;

  // 历史管理
  loadConversationHistory: (conversationId: string, offset?: number, limit?: number) => void;
  searchConversations: (query: string) => ConversationState[];
  exportConversation: (conversationId: string, format: 'json' | 'txt' | 'pdf') => void;
}
```

### 3.3 工作流状态管理

```typescript
// 工作流状态
interface WorkflowState {
  config: WorkflowConfig;
  isEditing: boolean;
  isDirty: boolean;
  validationErrors: ValidationError[];
  executionHistory: string[];
  metadata: {
    createdAt: number;
    updatedAt: number;
    version: string;
    createdBy: string;
    tags: string[];
  };
}

// 工作流执行状态
interface WorkflowExecutionState {
  executionId: string;
  workflowId: string;
  status: WorkflowStatus;
  progress: number;
  currentNode: string;
  nodeStatuses: Record<string, NodeExecutionStatus>;
  executionLog: LogEntry[];
  startTime: number;
  endTime?: number;
  input: Record<string, any>;
  output?: Record<string, any>;
  error?: string;
  metrics: {
    totalNodes: number;
    completedNodes: number;
    failedNodes: number;
    executionTime: number;
    memoryUsage: number;
    cpuUsage: number;
  };
}

// 工作流操作
interface WorkflowActions {
  // 配置管理
  createWorkflow: (name: string, description?: string) => string;
  loadWorkflow: (workflowId: string) => void;
  saveWorkflow: (workflowId: string) => void;
  deleteWorkflow: (workflowId: string) => void;
  duplicateWorkflow: (workflowId: string, newName: string) => string;

  // 编辑操作
  updateWorkflowConfig: (workflowId: string, config: Partial<WorkflowConfig>) => void;
  addNode: (workflowId: string, node: WorkflowNode) => void;
  updateNode: (workflowId: string, nodeId: string, updates: Partial<WorkflowNode>) => void;
  deleteNode: (workflowId: string, nodeId: string) => void;
  addConnection: (workflowId: string, connection: WorkflowConnection) => void;
  deleteConnection: (workflowId: string, connectionId: string) => void;

  // 执行管理
  startExecution: (workflowId: string, input?: Record<string, any>) => string;
  pauseExecution: (executionId: string) => void;
  resumeExecution: (executionId: string) => void;
  cancelExecution: (executionId: string) => void;
  retryExecution: (executionId: string, fromNode?: string) => void;

  // 状态更新
  updateExecutionStatus: (executionId: string, status: Partial<WorkflowExecutionState>) => void;
  updateNodeStatus: (executionId: string, nodeId: string, status: Partial<NodeExecutionStatus>) => void;

  // 验证
  validateWorkflow: (workflowId: string) => ValidationError[];

  // 导出导入
  exportWorkflow: (workflowId: string, format: 'json' | 'yaml' | 'xml') => string;
  importWorkflow: (data: string, format: 'json' | 'yaml' | 'xml') => string;
}

// 验证错误
interface ValidationError {
  type: 'error' | 'warning';
  code: string;
  message: string;
  nodeId?: string;
  connectionId?: string;
  suggestions?: string[];
}
```

### 3.4 智能体状态管理

```typescript
// 智能体信息
interface AgentInfo {
  id: string;
  name: string;
  description: string;
  avatar?: string;
  type: 'conversational' | 'task' | 'workflow' | 'hybrid';
  capabilities: string[];
  model: string;
  provider: string;
  status: 'active' | 'inactive' | 'error' | 'updating';
  config: AgentConfig;
  metrics: {
    totalExecutions: number;
    successRate: number;
    averageResponseTime: number;
    lastUsed: number;
  };
}

// 智能体配置
interface AgentConfig {
  model: {
    provider: string;
    name: string;
    version: string;
    parameters: Record<string, any>;
  };
  instructions: {
    system: string;
    context?: string;
    examples?: Array<{
      input: string;
      output: string;
    }>;
  };
  tools: Array<{
    name: string;
    enabled: boolean;
    config: Record<string, any>;
  }>;
  memory: {
    type: 'none' | 'short' | 'long' | 'episodic';
    size: number;
    persistAcrossSessions: boolean;
  };
  constraints: {
    maxResponseTime: number;
    maxTokens: number;
    temperature: number;
    topP: number;
    frequencyPenalty: number;
    presencePenalty: number;
  };
}

// 智能体执行状态
interface AgentExecutionState {
  executionId: string;
  agentId: string;
  status: 'pending' | 'thinking' | 'executing' | 'completed' | 'failed';
  progress?: number;
  currentStep?: string;
  input: Record<string, any>;
  output?: Record<string, any>;
  thinking?: string;
  toolCalls: ToolCall[];
  startTime: number;
  endTime?: number;
  error?: string;
  metrics: {
    tokensUsed: number;
    executionTime: number;
    toolCallsCount: number;
    retryCount: number;
  };
}

// 智能体操作
interface AgentActions {
  // 智能体管理
  loadAgents: () => void;
  createAgent: (config: AgentConfig) => string;
  updateAgent: (agentId: string, updates: Partial<AgentInfo>) => void;
  deleteAgent: (agentId: string) => void;
  duplicateAgent: (agentId: string, newName: string) => string;

  // 执行管理
  executeAgent: (agentId: string, input: Record<string, any>) => string;
  cancelExecution: (executionId: string) => void;
  retryExecution: (executionId: string) => void;

  // 状态更新
  updateExecutionStatus: (executionId: string, status: Partial<AgentExecutionState>) => void;
  updateAgentThinking: (executionId: string, thinking: string) => void;
  addToolCall: (executionId: string, toolCall: ToolCall) => void;
  updateToolCall: (executionId: string, toolCallId: string, updates: Partial<ToolCall>) => void;

  // 配置管理
  updateAgentConfig: (agentId: string, config: Partial<AgentConfig>) => void;
  testAgent: (agentId: string, testInput: Record<string, any>) => void;

  // 监控
  getAgentMetrics: (agentId: string, timeRange?: { start: number; end: number }) => AgentMetrics;
  getExecutionHistory: (agentId: string, limit?: number) => AgentExecutionState[];
}

// 智能体指标
interface AgentMetrics {
  executions: {
    total: number;
    successful: number;
    failed: number;
    cancelled: number;
  };
  performance: {
    averageResponseTime: number;
    p95ResponseTime: number;
    throughput: number;
    errorRate: number;
  };
  usage: {
    totalTokens: number;
    totalCost: number;
    apiCalls: number;
    toolCalls: number;
  };
  timeline: Array<{
    timestamp: number;
    metric: string;
    value: number;
  }>;
}
```

### 3.5 实时同步机制

```typescript
// 同步管理器
interface SyncManager {
  // 连接管理
  connect: () => Promise<void>;
  disconnect: () => void;
  isConnected: () => boolean;
  getConnectionState: () => ConnectionState;

  // 消息发送
  sendMessage: (message: WebSocketMessage) => Promise<void>;
  sendRequest: <T>(message: WebSocketMessage) => Promise<T>;

  // 事件监听
  addEventListener: (eventType: string, handler: (payload: any) => void) => void;
  removeEventListener: (eventType: string, handler: (payload: any) => void) => void;

  // 状态同步
  syncState: (stateType: string, stateId: string, state: Record<string, any>) => void;
  requestStateSync: (stateType: string, stateId: string) => void;

  // 重连机制
  enableAutoReconnect: (enabled: boolean) => void;
  setReconnectConfig: (config: { interval: number; maxAttempts: number }) => void;

  // 消息队列
  enableOfflineQueue: (enabled: boolean) => void;
  clearMessageQueue: () => void;
  getQueueSize: () => number;
}

// 状态同步策略
interface SyncStrategy {
  immediate: boolean;     // 立即同步
  batched: boolean;       // 批量同步
  interval: number;       // 同步间隔（毫秒）
  maxBatchSize: number;   // 最大批次大小
  conflictResolution: 'client' | 'server' | 'merge' | 'ask_user';
}

// 离线支持
interface OfflineManager {
  isOffline: () => boolean;
  getOfflineActions: () => Array<{ action: string; payload: any; timestamp: number }>;
  queueAction: (action: string, payload: any) => void;
  syncOfflineActions: () => Promise<void>;
  clearOfflineActions: () => void;
}
```

## 4. API文档

### 4.1 WebSocket端点

```typescript
// 连接端点
const WS_ENDPOINT = "wss://api.luminaos.com/v1/ws";

// 连接参数
interface ConnectionParams {
  token: string;           // 认证令牌
  userId: string;          // 用户ID
  sessionId?: string;      // 会话ID
  clientType: 'web' | 'mobile' | 'desktop';
  clientVersion: string;   // 客户端版本
  locale?: string;         // 语言环境
  timezone?: string;       // 时区
}
```

### 4.2 消息流示例

#### 4.2.1 发送聊天消息

```typescript
// 客户端发送
const chatMessage: WebSocketMessage<ChatMessagePayload> = {
  id: uuid(),
  type: MessageType.CHAT_MESSAGE,
  timestamp: Date.now(),
  payload: {
    content: "Hello, can you help me with a task?",
    messageType: 'text',
    conversationId: 'conv_123',
  },
  sessionId: 'session_456',
  userId: 'user_789'
};

// 服务器响应（流式）
const chatResponse: WebSocketMessage<ChatResponsePayload> = {
  id: uuid(),
  type: MessageType.CHAT_RESPONSE,
  timestamp: Date.now(),
  payload: {
    content: "Of course! I'd be happy to help you.",
    messageId: 'msg_456',
    conversationId: 'conv_123',
    agentId: 'agent_001',
    agentName: 'Assistant',
    streaming: false,
    isComplete: true,
    confidence: 0.95,
    tokens: { input: 12, output: 15, total: 27 }
  },
  sessionId: 'session_456',
  userId: 'user_789',
  requestId: chatMessage.id
};
```

#### 4.2.2 启动工作流

```typescript
// 启动工作流
const startWorkflow: WebSocketMessage<WorkflowStartPayload> = {
  id: uuid(),
  type: MessageType.WORKFLOW_START,
  timestamp: Date.now(),
  payload: {
    workflowId: 'workflow_001',
    workflowName: 'Document Analysis',
    version: '1.0.0',
    input: {
      document_url: 'https://example.com/doc.pdf',
      analysis_type: 'summary'
    },
    priority: 'normal'
  },
  sessionId: 'session_456',
  userId: 'user_789'
};

// 进度更新
const progressUpdate: WebSocketMessage<WorkflowProgressPayload> = {
  id: uuid(),
  type: MessageType.WORKFLOW_PROGRESS,
  timestamp: Date.now(),
  payload: {
    executionId: 'exec_123',
    workflowId: 'workflow_001',
    workflowName: 'Document Analysis',
    status: WorkflowStatus.RUNNING,
    progress: 45,
    currentNode: 'node_003',
    currentNodeName: 'Text Extraction',
    estimatedTimeRemaining: 30000,
    metrics: {
      nodesCompleted: 3,
      totalNodes: 7,
      executionTime: 15000,
      errorCount: 0
    }
  },
  sessionId: 'session_456',
  userId: 'user_789',
  requestId: startWorkflow.id
};
```

#### 4.2.3 决策点交互

```typescript
// 决策请求
const decisionRequest: WebSocketMessage<DecisionRequestPayload> = {
  id: uuid(),
  type: MessageType.DECISION_REQUEST,
  timestamp: Date.now(),
  payload: {
    decisionId: 'decision_001',
    workflowId: 'workflow_001',
    executionId: 'exec_123',
    nodeId: 'node_005',
    nodeName: 'Quality Check',
    question: 'The extracted text quality is lower than expected. How would you like to proceed?',
    options: [
      {
        id: 'retry',
        label: 'Retry with higher quality settings',
        description: 'This will take longer but may produce better results',
        value: { action: 'retry', quality: 'high' }
      },
      {
        id: 'continue',
        label: 'Continue with current results',
        description: 'Proceed with the extracted text as-is',
        value: { action: 'continue' }
      },
      {
        id: 'manual',
        label: 'Manual review required',
        description: 'Pause workflow for manual intervention',
        value: { action: 'pause', reason: 'manual_review' }
      }
    ],
    allowCustomInput: false,
    timeout: 300000, // 5 minutes
    defaultOption: 'continue'
  },
  sessionId: 'session_456',
  userId: 'user_789'
};

// 决策响应
const decisionResponse: WebSocketMessage<DecisionResponsePayload> = {
  id: uuid(),
  type: MessageType.DECISION_RESPONSE,
  timestamp: Date.now(),
  payload: {
    decisionId: 'decision_001',
    selectedOption: 'retry',
    timestamp: Date.now()
  },
  sessionId: 'session_456',
  userId: 'user_789',
  requestId: decisionRequest.id
};
```

### 4.3 错误处理

```typescript
// 错误消息格式
interface ErrorPayload {
  code: string;
  message: string;
  details?: Record<string, any>;
  retryable: boolean;
  retryAfter?: number;
  requestId?: string;
  stack?: string; // 仅开发环境
}

// 错误代码
enum ErrorCode {
  // 连接错误
  CONNECTION_FAILED = 'CONNECTION_FAILED',
  CONNECTION_TIMEOUT = 'CONNECTION_TIMEOUT',
  AUTHENTICATION_FAILED = 'AUTHENTICATION_FAILED',
  AUTHORIZATION_FAILED = 'AUTHORIZATION_FAILED',

  // 消息错误
  INVALID_MESSAGE_FORMAT = 'INVALID_MESSAGE_FORMAT',
  MESSAGE_TOO_LARGE = 'MESSAGE_TOO_LARGE',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',

  // 工作流错误
  WORKFLOW_NOT_FOUND = 'WORKFLOW_NOT_FOUND',
  WORKFLOW_EXECUTION_FAILED = 'WORKFLOW_EXECUTION_FAILED',
  WORKFLOW_VALIDATION_ERROR = 'WORKFLOW_VALIDATION_ERROR',
  WORKFLOW_TIMEOUT = 'WORKFLOW_TIMEOUT',

  // 智能体错误
  AGENT_NOT_FOUND = 'AGENT_NOT_FOUND',
  AGENT_EXECUTION_FAILED = 'AGENT_EXECUTION_FAILED',
  AGENT_TIMEOUT = 'AGENT_TIMEOUT',
  AGENT_QUOTA_EXCEEDED = 'AGENT_QUOTA_EXCEEDED',

  // 系统错误
  INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  MAINTENANCE_MODE = 'MAINTENANCE_MODE'
}

// 错误处理策略
interface ErrorHandlingStrategy {
  retryAttempts: number;
  retryDelay: number;
  exponentialBackoff: boolean;
  showUserNotification: boolean;
  logToConsole: boolean;
  reportToAnalytics: boolean;
}
```

### 4.4 性能和监控

```typescript
// 性能指标
interface PerformanceMetrics {
  // 连接指标
  connectionLatency: number;
  connectionUptime: number;
  reconnectionCount: number;

  // 消息指标
  messagesSent: number;
  messagesReceived: number;
  messageLatency: number;
  messageErrorRate: number;

  // UI指标
  renderTime: number;
  memoryUsage: number;
  componentUpdateCount: number;

  // 用户体验指标
  timeToFirstResponse: number;
  conversationResponseTime: number;
  workflowCompletionTime: number;
  userInteractionDelay: number;
}

// 监控配置
interface MonitoringConfig {
  enablePerformanceTracking: boolean;
  enableErrorTracking: boolean;
  enableUserTracking: boolean;
  enableNetworkTracking: boolean;
  sampleRate: number; // 0-1
  bufferSize: number;
  reportInterval: number;
  anonymizeData: boolean;
}
```

## 5. 安全和认证

### 5.1 认证机制

```typescript
// JWT Token结构
interface JWTPayload {
  sub: string;        // 用户ID
  iss: string;        // 发行者
  exp: number;        // 过期时间
  iat: number;        // 发行时间
  jti: string;        // Token ID
  scope: string[];    // 权限范围
  session_id: string; // 会话ID
}

// WebSocket认证
interface WebSocketAuth {
  type: 'bearer' | 'session' | 'api_key';
  token: string;
  refreshToken?: string;
  expiresIn?: number;
}

// 权限验证
interface PermissionCheck {
  resource: string;
  action: string;
  context?: Record<string, any>;
}
```

### 5.2 数据验证

```typescript
// 消息验证规则
interface MessageValidationRules {
  maxMessageSize: number;     // 最大消息大小
  maxAttachmentSize: number;  // 最大附件大小
  allowedFileTypes: string[]; // 允许的文件类型
  rateLimits: {
    messagesPerMinute: number;
    messagesPerHour: number;
    attachmentsPerDay: number;
  };
  contentFilters: {
    profanityFilter: boolean;
    spamDetection: boolean;
    malwareScanning: boolean;
  };
}

// 输入清理
interface InputSanitization {
  stripHTML: boolean;
  allowedTags: string[];
  escapeSpecialChars: boolean;
  maxLength: number;
  validateEncoding: boolean;
}
```

## 总结

本前端与智能体工作流交互协议设计为LuminaOS平台提供了：

### 技术特性
1. **完整的WebSocket通信协议**：26种消息类型，覆盖所有交互场景
2. **模块化组件架构**：智能体聊天、工作流可视化、决策交互组件
3. **统一状态管理**：Redux/Zustand兼容的状态结构和操作
4. **实时同步机制**：前后端状态一致性保证
5. **企业级错误处理**：完整的错误码体系和恢复策略

### 集成优势
- **与后端协议无缝对接**：与任务1.2智能体通信协议完全兼容
- **TypeScript类型安全**：完整的类型定义，编译期错误检测
- **现代前端架构**：支持React、Vue等主流框架
- **可扩展设计**：支持自定义消息类型和组件扩展

### 用户体验
- **流畅的实时交互**：毫秒级响应，流式消息传输
- **直观的可视化界面**：工作流设计器和执行可视化
- **智能决策辅助**：决策点交互和用户输入引导
- **完整的状态追踪**：对话历史、执行进度、错误恢复

这个协议设计确保了前端能够充分利用后端智能体系统的强大功能，为用户提供卓越的智能体工作流体验。