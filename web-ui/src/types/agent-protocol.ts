/**
 * 前端与智能体工作流交互协议 - TypeScript类型定义
 *
 * 与后端智能体通信协议 (任务1.2) 完全兼容
 * 支持实时通信、状态同步、工作流可视化等功能
 *
 * 版本: 1.0.0
 * 创建日期: 2024-11-15
 */

// ============================================================================
// 1. 基础类型定义
// ============================================================================

/**
 * WebSocket消息类型枚举
 */
export enum MessageType {
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
  NOTIFICATION = 'notification',
}

/**
 * 连接状态枚举
 */
export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error',
}

/**
 * 工作流状态枚举
 */
export enum WorkflowStatus {
  PENDING = 'pending',
  INITIALIZING = 'initializing',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  TIMEOUT = 'timeout',
}

/**
 * 错误代码枚举
 */
export enum ErrorCode {
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
  MAINTENANCE_MODE = 'MAINTENANCE_MODE',
}

// ============================================================================
// 2. WebSocket消息结构
// ============================================================================

/**
 * WebSocket基础消息结构
 */
export interface WebSocketMessage<T = any> {
  /** 消息唯一ID */
  id: string;
  /** 消息类型 */
  type: MessageType;
  /** 时间戳 */
  timestamp: number;
  /** 消息内容 */
  payload: T;
  /** 会话ID */
  sessionId: string;
  /** 用户ID */
  userId: string;
  /** 请求ID（用于响应匹配） */
  requestId?: string;
  /** 元数据 */
  metadata?: Record<string, any>;
}

/**
 * WebSocket连接配置
 */
export interface WebSocketConfig {
  /** WebSocket URL */
  url: string;
  /** 协议列表 */
  protocols?: string[];
  /** 重连间隔（毫秒） */
  reconnectInterval: number;
  /** 最大重连尝试次数 */
  maxReconnectAttempts: number;
  /** 心跳间隔（毫秒） */
  heartbeatInterval: number;
  /** 消息队列大小 */
  messageQueueSize: number;
}

// ============================================================================
// 3. 聊天相关类型
// ============================================================================

/**
 * 聊天消息载荷
 */
export interface ChatMessagePayload {
  /** 消息内容 */
  content: string;
  /** 消息类型 */
  messageType: 'text' | 'image' | 'file' | 'voice';
  /** 对话ID */
  conversationId: string;
  /** 父消息ID */
  parentMessageId?: string;
  /** 附件列表 */
  attachments?: Attachment[];
}

/**
 * 聊天响应载荷
 */
export interface ChatResponsePayload {
  /** 响应内容 */
  content: string;
  /** 消息ID */
  messageId: string;
  /** 对话ID */
  conversationId: string;
  /** 智能体ID */
  agentId?: string;
  /** 智能体名称 */
  agentName?: string;
  /** 是否流式传输 */
  streaming: boolean;
  /** 是否完成 */
  isComplete: boolean;
  /** 工具调用 */
  toolCalls?: ToolCall[];
  /** 知识库引用 */
  citations?: KnowledgeCitation[];
  /** 推理步骤 */
  reasoning?: string[];
  /** 置信度 */
  confidence?: number;
  /** Token使用统计 */
  tokens?: {
    input: number;
    output: number;
    total: number;
  };
}

/**
 * 附件信息
 */
export interface Attachment {
  /** 附件ID */
  id: string;
  /** 附件类型 */
  type: 'file' | 'image' | 'document';
  /** 文件名 */
  name: string;
  /** 文件大小（字节） */
  size: number;
  /** 文件URL */
  url: string;
  /** 预览图URL */
  preview?: string;
}

/**
 * 工具调用
 */
export interface ToolCall {
  /** 工具调用ID */
  id: string;
  /** 工具名称 */
  name: string;
  /** 调用参数 */
  arguments: Record<string, any>;
  /** 调用结果 */
  result?: any;
  /** 错误信息 */
  error?: string;
  /** 执行状态 */
  status: 'pending' | 'running' | 'completed' | 'failed';
  /** 开始时间 */
  startTime: number;
  /** 结束时间 */
  endTime?: number;
}

/**
 * 知识库引用
 */
export interface KnowledgeCitation {
  /** 文档块ID */
  chunkId: string;
  /** 文档ID */
  documentId: string;
  /** 文档名称 */
  documentName: string;
  /** 引用内容 */
  content: string;
  /** 相关性分数 */
  score: number;
  /** 页码 */
  page?: number;
  /** 章节 */
  section?: string;
}

/**
 * 对话消息
 */
export interface ConversationMessage {
  /** 角色 */
  role: 'user' | 'assistant' | 'system' | 'tool';
  /** 消息内容 */
  content: string;
  /** 工具调用 */
  toolCalls?: ToolCall[];
  /** 元数据 */
  metadata?: Record<string, any>;
  /** 时间戳 */
  timestamp: number;
}

// ============================================================================
// 4. 工作流相关类型
// ============================================================================

/**
 * 工作流启动载荷
 */
export interface WorkflowStartPayload {
  /** 工作流ID */
  workflowId: string;
  /** 工作流名称 */
  workflowName: string;
  /** 版本 */
  version: string;
  /** 输入数据 */
  input: Record<string, any>;
  /** 配置参数 */
  config?: Record<string, any>;
  /** 优先级 */
  priority?: 'low' | 'normal' | 'high' | 'urgent';
}

/**
 * 工作流进度载荷
 */
export interface WorkflowProgressPayload {
  /** 执行ID */
  executionId: string;
  /** 工作流ID */
  workflowId: string;
  /** 工作流名称 */
  workflowName: string;
  /** 执行状态 */
  status: WorkflowStatus;
  /** 执行进度（0-100） */
  progress: number;
  /** 当前节点ID */
  currentNode: string;
  /** 当前节点名称 */
  currentNodeName: string;
  /** 预估剩余时间（毫秒） */
  estimatedTimeRemaining?: number;
  /** 执行指标 */
  metrics?: {
    /** 已完成节点数 */
    nodesCompleted: number;
    /** 总节点数 */
    totalNodes: number;
    /** 执行时间（毫秒） */
    executionTime: number;
    /** 错误计数 */
    errorCount: number;
  };
}

/**
 * 节点完成载荷
 */
export interface WorkflowNodeCompletePayload {
  /** 执行ID */
  executionId: string;
  /** 节点ID */
  nodeId: string;
  /** 节点名称 */
  nodeName: string;
  /** 节点类型 */
  nodeType: string;
  /** 执行状态 */
  status: 'success' | 'failed' | 'skipped';
  /** 输出数据 */
  output: Record<string, any>;
  /** 执行时间（毫秒） */
  executionTime: number;
  /** 错误信息 */
  error?: string;
  /** 下一个节点列表 */
  nextNodes?: string[];
}

/**
 * 节点位置
 */
export interface NodePosition {
  /** X坐标 */
  x: number;
  /** Y坐标 */
  y: number;
}

/**
 * 节点大小
 */
export interface NodeSize {
  /** 宽度 */
  width: number;
  /** 高度 */
  height: number;
}

/**
 * 工作流节点
 */
export interface WorkflowNode {
  /** 节点ID */
  id: string;
  /** 节点名称 */
  name: string;
  /** 节点类型 */
  type: string;
  /** 后端节点类型（兼容性） */
  node_type?: string;
  /** 节点配置 */
  config: Record<string, any>;
  /** 节点位置 */
  position: NodePosition;
  /** 节点大小 */
  size?: NodeSize;
  /** 节点样式 */
  style?: Record<string, any>;
  /** 节点标签 */
  label?: string;
  /** 输入端口 */
  inputs?: string[];
  /** 输出端口 */
  outputs?: string[];
  /** 下一个节点 */
  next_nodes?: string[];
  /** 条件表达式 */
  condition?: string;
}

/**
 * 连接点
 */
export interface ConnectionPoint {
  /** 节点ID */
  node_id: string;
  /** 端口名称 */
  port: string;
  /** 位置 */
  position?: NodePosition;
}

/**
 * 工作流连接
 */
export interface WorkflowConnection {
  /** 连接ID */
  id: string;
  /** 源连接点 */
  source: ConnectionPoint;
  /** 目标连接点 */
  target: ConnectionPoint;
  /** 条件表达式 */
  condition?: string;
  /** 连接标签 */
  label?: string;
  /** 连接样式 */
  style?: Record<string, any>;
  /** 元数据 */
  metadata?: Record<string, any>;
}

/**
 * 工作流配置
 */
export interface WorkflowConfig {
  /** 工作流名称 */
  name: string;
  /** 工作流描述 */
  description: string;
  /** 版本 */
  version: string;
  /** 节点列表 */
  nodes: WorkflowNode[];
  /** 连接列表 */
  connections: WorkflowConnection[];
  /** 开始节点ID */
  start_node_id: string;
  /** 结束节点ID列表 */
  end_node_ids: string[];
  /** 变量定义 */
  variables?: Record<string, any>;
  /** 元数据 */
  metadata?: Record<string, any>;
}

/**
 * 节点类型定义
 */
export interface NodeTypeDefinition {
  /** 类型名称 */
  type: string;
  /** 显示标签 */
  label: string;
  /** 图标 */
  icon?: string;
  /** 颜色 */
  color: string;
  /** 分类 */
  category: string;
  /** 默认配置 */
  defaultConfig: Record<string, any>;
}

/**
 * 节点执行状态
 */
export interface NodeExecutionStatus {
  /** 节点ID */
  nodeId: string;
  /** 执行状态 */
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  /** 执行进度 */
  progress?: number;
  /** 开始时间 */
  startTime?: number;
  /** 结束时间 */
  endTime?: number;
  /** 执行时间 */
  executionTime?: number;
  /** 输入数据 */
  input?: Record<string, any>;
  /** 输出数据 */
  output?: Record<string, any>;
  /** 错误信息 */
  error?: string;
  /** 日志条目 */
  logs?: LogEntry[];
}

/**
 * 日志条目
 */
export interface LogEntry {
  /** 日志ID */
  id: string;
  /** 日志级别 */
  level: 'debug' | 'info' | 'warn' | 'error';
  /** 日志消息 */
  message: string;
  /** 时间戳 */
  timestamp: number;
  /** 来源 */
  source: string;
  /** 元数据 */
  metadata?: Record<string, any>;
}

// ============================================================================
// 5. 智能体相关类型
// ============================================================================

/**
 * 智能体执行载荷
 */
export interface AgentExecutePayload {
  /** 智能体ID */
  agentId: string;
  /** 智能体名称 */
  agentName: string;
  /** 输入数据 */
  input: {
    /** 输入内容 */
    content: string;
    /** 上下文 */
    context: Record<string, any>;
    /** 变量 */
    variables: Record<string, any>;
    /** 对话ID */
    conversationId: string;
    /** 元数据 */
    metadata: Record<string, any>;
  };
  /** 配置参数 */
  config?: {
    /** 是否流式传输 */
    streaming: boolean;
    /** 超时时间（毫秒） */
    timeout: number;
    /** 重试次数 */
    retryCount: number;
    /** 启用缓存 */
    enableCache: boolean;
    /** 缓存TTL（秒） */
    cacheTtl: number;
  };
}

/**
 * 智能体响应载荷
 */
export interface AgentResponsePayload {
  /** 执行ID */
  executionId: string;
  /** 智能体ID */
  agentId: string;
  /** 智能体名称 */
  agentName: string;
  /** 执行成功 */
  success: boolean;
  /** 输出数据 */
  output: {
    /** 响应内容 */
    content: string;
    /** 元数据 */
    metadata: Record<string, any>;
    /** 工具调用 */
    toolCalls: ToolCall[];
    /** 推理步骤 */
    reasoningSteps: string[];
    /** 置信度分数 */
    confidenceScore: number;
    /** 执行时间 */
    executionTime: number;
    /** 使用的Token数 */
    tokensUsed: number;
  };
  /** 上下文 */
  context: {
    /** 对话ID */
    conversationId: string;
    /** 消息列表 */
    messages: ConversationMessage[];
    /** 变量 */
    variables: Record<string, any>;
    /** 共享内存 */
    sharedMemory: Record<string, any>;
  };
  /** 错误信息 */
  error?: string;
}

/**
 * 智能体思考载荷
 */
export interface AgentThinkingPayload {
  /** 智能体ID */
  agentId: string;
  /** 智能体名称 */
  agentName: string;
  /** 思考状态 */
  status: 'thinking' | 'analyzing' | 'planning' | 'executing';
  /** 思考内容 */
  thought?: string;
  /** 当前步骤 */
  step?: number;
  /** 总步骤数 */
  totalSteps?: number;
}

// ============================================================================
// 6. 决策点交互类型
// ============================================================================

/**
 * 决策请求载荷
 */
export interface DecisionRequestPayload {
  /** 决策ID */
  decisionId: string;
  /** 工作流ID */
  workflowId: string;
  /** 执行ID */
  executionId: string;
  /** 节点ID */
  nodeId: string;
  /** 节点名称 */
  nodeName: string;
  /** 决策问题 */
  question: string;
  /** 问题描述 */
  description?: string;
  /** 选项列表 */
  options: Array<{
    /** 选项ID */
    id: string;
    /** 选项标签 */
    label: string;
    /** 选项描述 */
    description?: string;
    /** 选项值 */
    value: any;
    /** 元数据 */
    metadata?: Record<string, any>;
  }>;
  /** 允许自定义输入 */
  allowCustomInput: boolean;
  /** 超时时间（毫秒） */
  timeout?: number;
  /** 默认选项 */
  defaultOption?: string;
}

/**
 * 决策响应载荷
 */
export interface DecisionResponsePayload {
  /** 决策ID */
  decisionId: string;
  /** 选择的选项 */
  selectedOption?: string;
  /** 自定义输入 */
  customInput?: any;
  /** 时间戳 */
  timestamp: number;
  /** 元数据 */
  metadata?: Record<string, any>;
}

/**
 * 用户输入请求载荷
 */
export interface UserInputRequestPayload {
  /** 请求ID */
  requestId: string;
  /** 工作流ID */
  workflowId: string;
  /** 执行ID */
  executionId: string;
  /** 节点ID */
  nodeId: string;
  /** 输入提示 */
  prompt: string;
  /** 输入类型 */
  inputType: 'text' | 'number' | 'date' | 'select' | 'multi-select' | 'file';
  /** 验证规则 */
  validation?: {
    /** 是否必需 */
    required: boolean;
    /** 最小长度 */
    minLength?: number;
    /** 最大长度 */
    maxLength?: number;
    /** 正则模式 */
    pattern?: string;
    /** 选项列表 */
    options?: string[];
  };
  /** 超时时间（毫秒） */
  timeout?: number;
  /** 占位符文本 */
  placeholder?: string;
  /** 默认值 */
  defaultValue?: any;
}

/**
 * 用户输入响应载荷
 */
export interface UserInputResponsePayload {
  /** 请求ID */
  requestId: string;
  /** 输入值 */
  value: any;
  /** 时间戳 */
  timestamp: number;
  /** 验证通过 */
  isValid: boolean;
  /** 错误信息 */
  error?: string;
}

// ============================================================================
// 7. 状态同步类型
// ============================================================================

/**
 * 状态同步载荷
 */
export interface StateSyncPayload {
  /** 状态类型 */
  stateType: 'conversation' | 'workflow' | 'agent' | 'global';
  /** 状态ID */
  stateId: string;
  /** 状态数据 */
  state: Record<string, any>;
  /** 版本号 */
  version: number;
  /** 时间戳 */
  timestamp: number;
  /** 是否部分更新 */
  partial: boolean;
}

/**
 * 上下文更新载荷
 */
export interface ContextUpdatePayload {
  /** 上下文ID */
  contextId: string;
  /** 上下文类型 */
  contextType: 'conversation' | 'workflow' | 'session';
  /** 更新内容 */
  updates: Record<string, any>;
  /** 操作类型 */
  operation: 'set' | 'update' | 'delete' | 'merge';
  /** 时间戳 */
  timestamp: number;
}

// ============================================================================
// 8. 错误处理类型
// ============================================================================

/**
 * 错误载荷
 */
export interface ErrorPayload {
  /** 错误代码 */
  code: string;
  /** 错误消息 */
  message: string;
  /** 错误详情 */
  details?: Record<string, any>;
  /** 是否可重试 */
  retryable: boolean;
  /** 重试延迟时间（毫秒） */
  retryAfter?: number;
  /** 关联的请求ID */
  requestId?: string;
  /** 错误堆栈（仅开发环境） */
  stack?: string;
}

/**
 * 错误处理策略
 */
export interface ErrorHandlingStrategy {
  /** 重试次数 */
  retryAttempts: number;
  /** 重试延迟（毫秒） */
  retryDelay: number;
  /** 指数退避 */
  exponentialBackoff: boolean;
  /** 显示用户通知 */
  showUserNotification: boolean;
  /** 记录到控制台 */
  logToConsole: boolean;
  /** 报告到分析系统 */
  reportToAnalytics: boolean;
}

// ============================================================================
// 9. 前端组件类型
// ============================================================================

/**
 * 聊天界面组件属性
 */
export interface ChatInterfaceProps {
  /** 对话ID */
  conversationId: string;
  /** 智能体ID */
  agentId?: string;
  /** 配置参数 */
  config?: {
    /** 显示打字指示器 */
    showTypingIndicator: boolean;
    /** 显示消息状态 */
    showMessageStatus: boolean;
    /** 启用文件上传 */
    enableFileUpload: boolean;
    /** 启用语音输入 */
    enableVoiceInput: boolean;
    /** 最大消息长度 */
    maxMessageLength: number;
    /** 主题 */
    theme?: 'light' | 'dark' | 'auto';
  };
  /** 消息发送回调 */
  onMessageSend?: (message: ChatMessagePayload) => void;
  /** 消息接收回调 */
  onMessageReceive?: (message: ChatResponsePayload) => void;
  /** 错误处理回调 */
  onError?: (error: Error) => void;
}

/**
 * 工作流设计器属性
 */
export interface WorkflowDesignerProps {
  /** 工作流ID */
  workflowId?: string;
  /** 工作流配置 */
  config?: WorkflowConfig;
  /** 只读模式 */
  readonly?: boolean;
  /** 显示网格 */
  showGrid?: boolean;
  /** 显示小地图 */
  showMiniMap?: boolean;
  /** 启用缩放 */
  enableZoom?: boolean;
  /** 启用平移 */
  enablePan?: boolean;
  /** 节点类型列表 */
  nodeTypes: NodeTypeDefinition[];
  /** 配置变更回调 */
  onConfigChange?: (config: WorkflowConfig) => void;
  /** 节点添加回调 */
  onNodeAdd?: (nodeType: string, position: NodePosition) => void;
  /** 节点删除回调 */
  onNodeDelete?: (nodeId: string) => void;
  /** 连接添加回调 */
  onConnectionAdd?: (connection: WorkflowConnection) => void;
  /** 连接删除回调 */
  onConnectionDelete?: (connectionId: string) => void;
}

/**
 * 决策对话框属性
 */
export interface DecisionDialogProps {
  /** 决策数据 */
  decision: DecisionRequestPayload;
  /** 是否打开 */
  isOpen: boolean;
  /** 选择回调 */
  onSelect: (option: string | any) => void;
  /** 取消回调 */
  onCancel?: () => void;
  /** 超时时间 */
  timeout?: number;
}

// ============================================================================
// 10. 状态管理类型
// ============================================================================

/**
 * 全局应用状态
 */
export interface AppState {
  /** 连接状态 */
  connection: ConnectionState;
  /** 用户状态 */
  user: {
    id: string;
    name: string;
    avatar?: string;
    preferences: UserPreferences;
    permissions: string[];
  };
  /** 对话状态 */
  conversations: {
    active: string | null;
    list: Record<string, ConversationState>;
  };
  /** 工作流状态 */
  workflows: {
    active: string | null;
    list: Record<string, WorkflowState>;
    executions: Record<string, WorkflowExecutionState>;
  };
  /** 智能体状态 */
  agents: {
    list: Record<string, AgentInfo>;
    activeExecutions: Record<string, AgentExecutionState>;
  };
  /** UI状态 */
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
}

/**
 * 用户偏好设置
 */
export interface UserPreferences {
  /** 语言 */
  language: string;
  /** 时区 */
  timezone: string;
  /** 主题 */
  theme: 'light' | 'dark' | 'auto';
  /** 通知设置 */
  notifications: {
    desktop: boolean;
    sound: boolean;
    email: boolean;
  };
  /** 聊天设置 */
  chat: {
    showTypingIndicator: boolean;
    showTimestamps: boolean;
    messageGrouping: boolean;
    autoScroll: boolean;
  };
  /** 工作流设置 */
  workflow: {
    showGrid: boolean;
    showMiniMap: boolean;
    autoSave: boolean;
    snapToGrid: boolean;
  };
}

/**
 * 对话状态
 */
export interface ConversationState {
  /** 对话ID */
  id: string;
  /** 对话标题 */
  title: string;
  /** 智能体ID */
  agentId?: string;
  /** 智能体名称 */
  agentName?: string;
  /** 消息列表 */
  messages: Message[];
  /** 打字状态 */
  typing: {
    isTyping: boolean;
    userId?: string;
    userName?: string;
  };
  /** 上下文 */
  context: Record<string, any>;
  /** 元数据 */
  metadata: {
    createdAt: number;
    updatedAt: number;
    messageCount: number;
    participantCount: number;
  };
}

/**
 * 消息
 */
export interface Message {
  /** 消息ID */
  id: string;
  /** 消息类型 */
  type: 'text' | 'system' | 'workflow' | 'tool' | 'error';
  /** 消息内容 */
  content: string;
  /** 发送者 */
  sender: string;
  /** 发送者ID */
  senderId: string;
  /** 时间戳 */
  timestamp: number;
  /** 消息状态 */
  status: 'sending' | 'sent' | 'failed' | 'delivered';
  /** 元数据 */
  metadata?: {
    workflowId?: string;
    workflowName?: string;
    toolName?: string;
    executionId?: string;
    progress?: number;
    error?: string;
    knowledgeCitations?: KnowledgeCitation[];
    sourceDocuments?: string[];
  };
}

/**
 * 工作流状态
 */
export interface WorkflowState {
  /** 工作流配置 */
  config: WorkflowConfig;
  /** 是否在编辑 */
  isEditing: boolean;
  /** 是否有未保存更改 */
  isDirty: boolean;
  /** 验证错误 */
  validationErrors: ValidationError[];
  /** 执行历史 */
  executionHistory: string[];
}

/**
 * 工作流执行状态
 */
export interface WorkflowExecutionState {
  /** 执行ID */
  executionId: string;
  /** 工作流ID */
  workflowId: string;
  /** 工作流名称 */
  workflowName: string;
  /** 执行状态 */
  status: WorkflowStatus;
  /** 执行进度 */
  progress: number;
  /** 当前节点 */
  currentNode: string;
  /** 节点状态 */
  nodeStatuses: Record<string, NodeExecutionStatus>;
  /** 执行日志 */
  executionLog: LogEntry[];
  /** 开始时间 */
  startTime: number;
  /** 结束时间 */
  endTime?: number;
  /** 输入数据 */
  input: Record<string, any>;
  /** 输出数据 */
  output?: Record<string, any>;
  /** 错误信息 */
  error?: string;
}

/**
 * 智能体信息
 */
export interface AgentInfo {
  /** 智能体ID */
  id: string;
  /** 名称 */
  name: string;
  /** 描述 */
  description: string;
  /** 头像 */
  avatar?: string;
  /** 类型 */
  type: 'conversational' | 'task' | 'workflow' | 'hybrid';
  /** 能力列表 */
  capabilities: string[];
  /** 模型 */
  model: string;
  /** 提供商 */
  provider: string;
  /** 状态 */
  status: 'active' | 'inactive' | 'error' | 'updating';
  /** 配置 */
  config: AgentConfig;
}

/**
 * 智能体配置
 */
export interface AgentConfig {
  /** 模型配置 */
  model: {
    provider: string;
    name: string;
    version: string;
    parameters: Record<string, any>;
  };
  /** 指令配置 */
  instructions: {
    system: string;
    context?: string;
    examples?: Array<{
      input: string;
      output: string;
    }>;
  };
  /** 工具配置 */
  tools: Array<{
    name: string;
    enabled: boolean;
    config: Record<string, any>;
  }>;
  /** 内存配置 */
  memory: {
    type: 'none' | 'short' | 'long' | 'episodic';
    size: number;
    persistAcrossSessions: boolean;
  };
}

/**
 * 智能体执行状态
 */
export interface AgentExecutionState {
  /** 执行ID */
  executionId: string;
  /** 智能体ID */
  agentId: string;
  /** 执行状态 */
  status: 'pending' | 'thinking' | 'executing' | 'completed' | 'failed';
  /** 执行进度 */
  progress?: number;
  /** 当前步骤 */
  currentStep?: string;
  /** 输入数据 */
  input: Record<string, any>;
  /** 输出数据 */
  output?: Record<string, any>;
  /** 思考内容 */
  thinking?: string;
  /** 工具调用 */
  toolCalls: ToolCall[];
  /** 开始时间 */
  startTime: number;
  /** 结束时间 */
  endTime?: number;
  /** 错误信息 */
  error?: string;
}

/**
 * 验证错误
 */
export interface ValidationError {
  /** 错误类型 */
  type: 'error' | 'warning';
  /** 错误代码 */
  code: string;
  /** 错误消息 */
  message: string;
  /** 关联节点ID */
  nodeId?: string;
  /** 关联连接ID */
  connectionId?: string;
  /** 修复建议 */
  suggestions?: string[];
}

/**
 * 决策模态状态
 */
export interface DecisionModalState {
  /** 决策数据 */
  decision: DecisionRequestPayload;
  /** 是否显示 */
  isVisible: boolean;
  /** 剩余时间 */
  timeRemaining?: number;
}

/**
 * 用户输入模态状态
 */
export interface UserInputModalState {
  /** 输入请求 */
  inputRequest: UserInputRequestPayload;
  /** 是否显示 */
  isVisible: boolean;
  /** 当前值 */
  currentValue?: any;
  /** 验证错误 */
  validationError?: string;
}

/**
 * 通知状态
 */
export interface NotificationState {
  /** 通知ID */
  id: string;
  /** 通知类型 */
  type: 'info' | 'success' | 'warning' | 'error';
  /** 标题 */
  title: string;
  /** 消息 */
  message: string;
  /** 时间戳 */
  timestamp: number;
  /** 超时时间 */
  timeout?: number;
  /** 操作按钮 */
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
}

// ============================================================================
// 11. 性能和监控类型
// ============================================================================

/**
 * 性能指标
 */
export interface PerformanceMetrics {
  /** 连接延迟 */
  connectionLatency: number;
  /** 连接运行时间 */
  connectionUptime: number;
  /** 重连次数 */
  reconnectionCount: number;
  /** 发送消息数 */
  messagesSent: number;
  /** 接收消息数 */
  messagesReceived: number;
  /** 消息延迟 */
  messageLatency: number;
  /** 消息错误率 */
  messageErrorRate: number;
  /** 渲染时间 */
  renderTime: number;
  /** 内存使用 */
  memoryUsage: number;
  /** 组件更新次数 */
  componentUpdateCount: number;
}

/**
 * 监控配置
 */
export interface MonitoringConfig {
  /** 启用性能追踪 */
  enablePerformanceTracking: boolean;
  /** 启用错误追踪 */
  enableErrorTracking: boolean;
  /** 启用用户追踪 */
  enableUserTracking: boolean;
  /** 启用网络追踪 */
  enableNetworkTracking: boolean;
  /** 采样率 */
  sampleRate: number;
  /** 缓冲区大小 */
  bufferSize: number;
  /** 报告间隔 */
  reportInterval: number;
  /** 数据匿名化 */
  anonymizeData: boolean;
}

// ============================================================================
// 12. 工具函数类型
// ============================================================================

/**
 * WebSocket消息发送器
 */
export type MessageSender<T> = (message: WebSocketMessage<T>) => Promise<void>;

/**
 * WebSocket消息监听器
 */
export type MessageListener<T> = (message: WebSocketMessage<T>) => void;

/**
 * WebSocket事件处理器
 */
export type EventHandler<T = any> = (event: T) => void;

/**
 * 状态更新器
 */
export type StateUpdater<T> = (state: T) => T;

/**
 * 异步状态更新器
 */
export type AsyncStateUpdater<T> = (state: T) => Promise<T>;

// ============================================================================
// 导出所有类型
// ============================================================================

export default {
  // 枚举
  MessageType,
  ConnectionState,
  WorkflowStatus,
  ErrorCode,

  // 基础类型导出声明...（为了简洁，这里只列出主要类型）
  // 实际使用时，所有上述定义的接口都会被导出
};
