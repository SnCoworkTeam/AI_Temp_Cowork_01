# 前端智能体交互协议 - API使用文档

## 概述

本文档为前端开发团队提供智能体工作流交互协议的详细API使用指南。该协议基于WebSocket实现实时双向通信，支持聊天对话、工作流执行、决策点交互和状态同步等核心功能。

## 目录

1. [快速开始](#1-快速开始)
2. [WebSocket连接](#2-websocket连接)
3. [消息格式规范](#3-消息格式规范)
4. [聊天对话API](#4-聊天对话api)
5. [工作流执行API](#5-工作流执行api)
6. [智能体调用API](#6-智能体调用api)
7. [决策点交互API](#7-决策点交互api)
8. [状态同步API](#8-状态同步api)
9. [错误处理](#9-错误处理)
10. [实际示例](#10-实际示例)
11. [最佳实践](#11-最佳实践)

## 1. 快速开始

### 1.1 安装依赖

```bash
# 如果使用 npm
npm install @types/uuid uuid

# 如果使用 yarn
yarn add @types/uuid uuid
```

### 1.2 导入类型定义

```typescript
// 导入协议类型
import {
  WebSocketMessage,
  MessageType,
  ChatMessagePayload,
  ChatResponsePayload,
  WorkflowStartPayload,
  WorkflowProgressPayload,
  AgentExecutePayload,
  AgentResponsePayload,
  ConnectionState,
  WorkflowStatus
} from './types/agent-protocol';
```

### 1.3 基础连接示例

```typescript
import { v4 as uuidv4 } from 'uuid';

class AgentWebSocketClient {
  private ws: WebSocket | null = null;
  private connectionState: ConnectionState = ConnectionState.DISCONNECTED;
  private messageHandlers: Map<MessageType, Function[]> = new Map();
  private requestHandlers: Map<string, Function> = new Map();

  // 连接到服务器
  async connect(token: string, userId: string): Promise<void> {
    const wsUrl = `wss://api.luminaos.com/v1/ws?token=${token}&userId=${userId}`;

    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(wsUrl);
      this.connectionState = ConnectionState.CONNECTING;

      this.ws.onopen = () => {
        this.connectionState = ConnectionState.CONNECTED;
        console.log('WebSocket connected');
        resolve();
      };

      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data) as WebSocketMessage;
        this.handleMessage(message);
      };

      this.ws.onclose = () => {
        this.connectionState = ConnectionState.DISCONNECTED;
        console.log('WebSocket disconnected');
      };

      this.ws.onerror = (error) => {
        this.connectionState = ConnectionState.ERROR;
        reject(error);
      };
    });
  }

  // 发送消息
  sendMessage<T>(message: WebSocketMessage<T>): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.connectionState !== ConnectionState.CONNECTED) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      try {
        this.ws.send(JSON.stringify(message));
        resolve();
      } catch (error) {
        reject(error);
      }
    });
  }

  // 消息处理
  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type) || [];
    handlers.forEach(handler => handler(message));

    // 处理请求响应
    if (message.requestId) {
      const handler = this.requestHandlers.get(message.requestId);
      if (handler) {
        handler(message);
        this.requestHandlers.delete(message.requestId);
      }
    }
  }

  // 订阅消息类型
  on<T>(messageType: MessageType, handler: (message: WebSocketMessage<T>) => void): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }

  // 发送请求并等待响应
  async sendRequest<TRequest, TResponse>(
    message: WebSocketMessage<TRequest>
  ): Promise<WebSocketMessage<TResponse>> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.requestHandlers.delete(message.id);
        reject(new Error('Request timeout'));
      }, 30000);

      this.requestHandlers.set(message.id, (response: WebSocketMessage<TResponse>) => {
        clearTimeout(timeout);
        resolve(response);
      });

      this.sendMessage(message).catch(reject);
    });
  }
}
```

## 2. WebSocket连接

### 2.1 连接参数

```typescript
interface ConnectionParams {
  token: string;           // JWT认证令牌
  userId: string;          // 用户ID
  sessionId?: string;      // 会话ID（可选）
  clientType: 'web' | 'mobile' | 'desktop';
  clientVersion: string;   // 客户端版本
  locale?: string;         // 语言环境
  timezone?: string;       // 时区
}

// 连接示例
const params = new URLSearchParams({
  token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
  userId: 'user_123',
  clientType: 'web',
  clientVersion: '1.0.0',
  locale: 'zh-CN',
  timezone: 'Asia/Shanghai'
});

const wsUrl = `wss://api.luminaos.com/v1/ws?${params.toString()}`;
```

### 2.2 连接状态管理

```typescript
class ConnectionManager {
  private client: AgentWebSocketClient;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 2000;

  constructor() {
    this.client = new AgentWebSocketClient();
    this.setupReconnectLogic();
  }

  private setupReconnectLogic(): void {
    this.client.on(MessageType.DISCONNECT, () => {
      this.handleDisconnect();
    });
  }

  private async handleDisconnect(): Promise<void> {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      setTimeout(async () => {
        try {
          await this.client.connect(token, userId);
          this.reconnectAttempts = 0;
        } catch (error) {
          console.error('Reconnection failed:', error);
          await this.handleDisconnect();
        }
      }, this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1));
    }
  }

  // 心跳机制
  private startHeartbeat(): void {
    setInterval(() => {
      if (this.client.isConnected()) {
        this.client.sendMessage({
          id: uuidv4(),
          type: MessageType.HEARTBEAT,
          timestamp: Date.now(),
          payload: {},
          sessionId: this.sessionId,
          userId: this.userId
        });
      }
    }, 30000); // 30秒心跳
  }
}
```

## 3. 消息格式规范

### 3.1 基础消息结构

```typescript
// 发送消息的通用格式
function createMessage<T>(
  type: MessageType,
  payload: T,
  sessionId: string,
  userId: string,
  requestId?: string
): WebSocketMessage<T> {
  return {
    id: uuidv4(),
    type,
    timestamp: Date.now(),
    payload,
    sessionId,
    userId,
    requestId,
    metadata: {}
  };
}

// 使用示例
const chatMessage = createMessage(
  MessageType.CHAT_MESSAGE,
  {
    content: "Hello, AI assistant!",
    messageType: 'text' as const,
    conversationId: 'conv_123'
  },
  'session_456',
  'user_789'
);
```

### 3.2 消息验证

```typescript
function validateMessage(message: WebSocketMessage): boolean {
  // 检查必需字段
  if (!message.id || !message.type || !message.timestamp || !message.sessionId || !message.userId) {
    return false;
  }

  // 检查时间戳合理性
  const now = Date.now();
  if (message.timestamp > now + 5000 || message.timestamp < now - 300000) {
    return false;
  }

  // 检查消息ID格式
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(message.id)) {
    return false;
  }

  return true;
}
```

## 4. 聊天对话API

### 4.1 发送聊天消息

```typescript
class ChatManager {
  constructor(private client: AgentWebSocketClient) {}

  // 发送文本消息
  async sendTextMessage(
    content: string,
    conversationId: string,
    sessionId: string,
    userId: string
  ): Promise<void> {
    const message = createMessage(
      MessageType.CHAT_MESSAGE,
      {
        content,
        messageType: 'text' as const,
        conversationId
      } as ChatMessagePayload,
      sessionId,
      userId
    );

    await this.client.sendMessage(message);
  }

  // 发送带附件的消息
  async sendMessageWithAttachments(
    content: string,
    attachments: Attachment[],
    conversationId: string,
    sessionId: string,
    userId: string
  ): Promise<void> {
    const message = createMessage(
      MessageType.CHAT_MESSAGE,
      {
        content,
        messageType: 'text' as const,
        conversationId,
        attachments
      } as ChatMessagePayload,
      sessionId,
      userId
    );

    await this.client.sendMessage(message);
  }

  // 监听聊天响应
  onChatResponse(handler: (response: ChatResponsePayload) => void): void {
    this.client.on<ChatResponsePayload>(MessageType.CHAT_RESPONSE, (message) => {
      handler(message.payload);
    });
  }

  // 监听打字状态
  onTypingIndicator(handler: (isTyping: boolean, userId?: string) => void): void {
    this.client.on(MessageType.CHAT_TYPING, (message) => {
      const { isTyping, userId } = message.payload;
      handler(isTyping, userId);
    });
  }
}

// 使用示例
const chatManager = new ChatManager(client);

// 发送消息
await chatManager.sendTextMessage(
  "Can you help me analyze this document?",
  "conv_123",
  "session_456",
  "user_789"
);

// 监听响应
chatManager.onChatResponse((response) => {
  console.log('AI Response:', response.content);
  console.log('Confidence:', response.confidence);

  if (response.streaming && !response.isComplete) {
    // 处理流式响应
    updateMessageContent(response.messageId, response.content);
  } else {
    // 完整响应
    displayMessage(response);
  }
});
```

### 4.2 流式响应处理

```typescript
class StreamingMessageHandler {
  private partialMessages: Map<string, string> = new Map();

  handleStreamingResponse(response: ChatResponsePayload): void {
    const { messageId, content, isComplete } = response;

    if (response.streaming) {
      // 累积流式内容
      const existing = this.partialMessages.get(messageId) || '';
      const updated = existing + content;
      this.partialMessages.set(messageId, updated);

      // 更新UI显示
      this.updateMessageInUI(messageId, updated, !isComplete);

      if (isComplete) {
        // 流式传输完成
        this.partialMessages.delete(messageId);
        this.markMessageComplete(messageId);
      }
    } else {
      // 非流式完整响应
      this.displayCompleteMessage(response);
    }
  }

  private updateMessageInUI(messageId: string, content: string, isPartial: boolean): void {
    const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageElement) {
      const contentElement = messageElement.querySelector('.message-content');
      if (contentElement) {
        contentElement.textContent = content;

        // 添加打字效果
        if (isPartial) {
          contentElement.classList.add('typing');
        } else {
          contentElement.classList.remove('typing');
        }
      }
    }
  }
}
```

## 5. 工作流执行API

### 5.1 启动工作流

```typescript
class WorkflowManager {
  constructor(private client: AgentWebSocketClient) {}

  // 启动工作流
  async startWorkflow(
    workflowId: string,
    workflowName: string,
    input: Record<string, any>,
    sessionId: string,
    userId: string,
    config?: Record<string, any>
  ): Promise<string> {
    const message = createMessage(
      MessageType.WORKFLOW_START,
      {
        workflowId,
        workflowName,
        version: '1.0.0',
        input,
        config,
        priority: 'normal'
      } as WorkflowStartPayload,
      sessionId,
      userId
    );

    // 发送启动请求并等待响应
    const response = await this.client.sendRequest<WorkflowStartPayload, any>(message);

    if (response.type === MessageType.SUCCESS) {
      return response.payload.executionId;
    } else {
      throw new Error(response.payload.message || 'Failed to start workflow');
    }
  }

  // 监听工作流进度
  onWorkflowProgress(handler: (progress: WorkflowProgressPayload) => void): void {
    this.client.on<WorkflowProgressPayload>(MessageType.WORKFLOW_PROGRESS, (message) => {
      handler(message.payload);
    });
  }

  // 监听节点完成
  onNodeComplete(handler: (nodeResult: WorkflowNodeCompletePayload) => void): void {
    this.client.on<WorkflowNodeCompletePayload>(MessageType.WORKFLOW_NODE_COMPLETE, (message) => {
      handler(message.payload);
    });
  }

  // 监听工作流完成
  onWorkflowComplete(handler: (result: any) => void): void {
    this.client.on(MessageType.WORKFLOW_COMPLETE, (message) => {
      handler(message.payload);
    });
  }

  // 暂停工作流
  async pauseWorkflow(executionId: string, sessionId: string, userId: string): Promise<void> {
    const message = createMessage(
      MessageType.WORKFLOW_PAUSE,
      { executionId },
      sessionId,
      userId
    );

    await this.client.sendMessage(message);
  }

  // 恢复工作流
  async resumeWorkflow(executionId: string, sessionId: string, userId: string): Promise<void> {
    const message = createMessage(
      MessageType.WORKFLOW_RESUME,
      { executionId },
      sessionId,
      userId
    );

    await this.client.sendMessage(message);
  }

  // 取消工作流
  async cancelWorkflow(executionId: string, sessionId: string, userId: string): Promise<void> {
    const message = createMessage(
      MessageType.WORKFLOW_CANCEL,
      { executionId },
      sessionId,
      userId
    );

    await this.client.sendMessage(message);
  }
}

// 使用示例
const workflowManager = new WorkflowManager(client);

// 启动文档分析工作流
const executionId = await workflowManager.startWorkflow(
  'document-analysis-v1',
  'Document Analysis',
  {
    document_url: 'https://example.com/document.pdf',
    analysis_type: 'summary',
    language: 'zh-CN'
  },
  'session_456',
  'user_789'
);

// 监听进度更新
workflowManager.onWorkflowProgress((progress) => {
  console.log(`Workflow ${progress.workflowName}: ${progress.progress}%`);
  console.log(`Current node: ${progress.currentNodeName}`);

  // 更新进度条
  updateProgressBar(progress.progress);

  // 显示当前步骤
  showCurrentStep(progress.currentNodeName);

  // 显示预估时间
  if (progress.estimatedTimeRemaining) {
    showEstimatedTime(progress.estimatedTimeRemaining);
  }
});

// 监听节点完成
workflowManager.onNodeComplete((nodeResult) => {
  console.log(`Node ${nodeResult.nodeName} completed:`, nodeResult.output);

  if (nodeResult.status === 'success') {
    markNodeAsCompleted(nodeResult.nodeId);
  } else {
    markNodeAsFailed(nodeResult.nodeId, nodeResult.error);
  }
});
```

### 5.2 工作流状态追踪

```typescript
class WorkflowTracker {
  private activeExecutions: Map<string, WorkflowExecutionState> = new Map();

  constructor(private workflowManager: WorkflowManager) {
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    this.workflowManager.onWorkflowProgress((progress) => {
      this.updateExecutionState(progress.executionId, {
        status: progress.status,
        progress: progress.progress,
        currentNode: progress.currentNode
      });
    });

    this.workflowManager.onNodeComplete((nodeResult) => {
      this.updateNodeStatus(nodeResult.executionId, nodeResult.nodeId, {
        status: nodeResult.status,
        executionTime: nodeResult.executionTime,
        output: nodeResult.output,
        error: nodeResult.error
      });
    });
  }

  private updateExecutionState(executionId: string, updates: Partial<WorkflowExecutionState>): void {
    const current = this.activeExecutions.get(executionId);
    if (current) {
      this.activeExecutions.set(executionId, { ...current, ...updates });
      this.notifyStateChange(executionId);
    }
  }

  private updateNodeStatus(
    executionId: string,
    nodeId: string,
    updates: Partial<NodeExecutionStatus>
  ): void {
    const execution = this.activeExecutions.get(executionId);
    if (execution) {
      execution.nodeStatuses[nodeId] = {
        ...execution.nodeStatuses[nodeId],
        ...updates
      };
      this.notifyStateChange(executionId);
    }
  }

  private notifyStateChange(executionId: string): void {
    const state = this.activeExecutions.get(executionId);
    if (state) {
      // 触发状态变更事件
      document.dispatchEvent(new CustomEvent('workflowStateChanged', {
        detail: { executionId, state }
      }));
    }
  }

  // 获取执行状态
  getExecutionState(executionId: string): WorkflowExecutionState | undefined {
    return this.activeExecutions.get(executionId);
  }

  // 获取所有活跃执行
  getActiveExecutions(): WorkflowExecutionState[] {
    return Array.from(this.activeExecutions.values());
  }
}
```

## 6. 智能体调用API

### 6.1 直接调用智能体

```typescript
class AgentManager {
  constructor(private client: AgentWebSocketClient) {}

  // 执行智能体
  async executeAgent(
    agentId: string,
    input: string,
    context: Record<string, any>,
    conversationId: string,
    sessionId: string,
    userId: string,
    config?: {
      streaming?: boolean;
      timeout?: number;
      enableCache?: boolean;
    }
  ): Promise<string> {
    const message = createMessage(
      MessageType.AGENT_EXECUTE,
      {
        agentId,
        agentName: '', // 可以从配置中获取
        input: {
          content: input,
          context,
          variables: {},
          conversationId,
          metadata: {}
        },
        config: {
          streaming: config?.streaming ?? false,
          timeout: config?.timeout ?? 30000,
          retryCount: 3,
          enableCache: config?.enableCache ?? true,
          cacheTtl: 300
        }
      } as AgentExecutePayload,
      sessionId,
      userId
    );

    const response = await this.client.sendRequest<AgentExecutePayload, any>(message);

    if (response.type === MessageType.SUCCESS) {
      return response.payload.executionId;
    } else {
      throw new Error(response.payload.message || 'Failed to execute agent');
    }
  }

  // 监听智能体响应
  onAgentResponse(handler: (response: AgentResponsePayload) => void): void {
    this.client.on<AgentResponsePayload>(MessageType.AGENT_RESPONSE, (message) => {
      handler(message.payload);
    });
  }

  // 监听智能体思考过程
  onAgentThinking(handler: (thinking: AgentThinkingPayload) => void): void {
    this.client.on<AgentThinkingPayload>(MessageType.AGENT_THINKING, (message) => {
      handler(message.payload);
    });
  }

  // 监听工具调用
  onToolCall(handler: (toolCall: any) => void): void {
    this.client.on(MessageType.AGENT_TOOL_CALL, (message) => {
      handler(message.payload);
    });
  }
}

// 使用示例
const agentManager = new AgentManager(client);

// 执行代码审查智能体
const executionId = await agentManager.executeAgent(
  'code-review-agent',
  'Please review this JavaScript code for security vulnerabilities',
  {
    code: 'const userInput = req.body.input; eval(userInput);',
    language: 'javascript',
    checkTypes: ['security', 'performance', 'maintainability']
  },
  'conv_456',
  'session_789',
  'user_123',
  {
    streaming: true,
    timeout: 60000,
    enableCache: true
  }
);

// 监听智能体思考过程
agentManager.onAgentThinking((thinking) => {
  console.log(`Agent ${thinking.agentName} is ${thinking.status}`);
  if (thinking.thought) {
    console.log('Thought:', thinking.thought);
  }

  // 更新UI显示思考状态
  showThinkingStatus(thinking.agentId, thinking.status, thinking.thought);
});

// 监听最终响应
agentManager.onAgentResponse((response) => {
  console.log('Agent execution completed:', response.success);
  console.log('Response:', response.output.content);
  console.log('Confidence:', response.output.confidenceScore);
  console.log('Execution time:', response.output.executionTime);

  if (response.success) {
    displayAgentResult(response.output);
  } else {
    showError(response.error || 'Agent execution failed');
  }
});
```

## 7. 决策点交互API

### 7.1 处理决策请求

```typescript
class DecisionManager {
  private pendingDecisions: Map<string, DecisionRequestPayload> = new Map();
  private decisionTimeouts: Map<string, number> = new Map();

  constructor(private client: AgentWebSocketClient) {
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    this.client.on<DecisionRequestPayload>(MessageType.DECISION_REQUEST, (message) => {
      this.handleDecisionRequest(message.payload);
    });

    this.client.on<UserInputRequestPayload>(MessageType.USER_INPUT_REQUEST, (message) => {
      this.handleUserInputRequest(message.payload);
    });
  }

  // 处理决策请求
  private handleDecisionRequest(decision: DecisionRequestPayload): void {
    this.pendingDecisions.set(decision.decisionId, decision);

    // 设置超时
    if (decision.timeout) {
      const timeoutId = window.setTimeout(() => {
        this.handleDecisionTimeout(decision.decisionId);
      }, decision.timeout);
      this.decisionTimeouts.set(decision.decisionId, timeoutId);
    }

    // 显示决策UI
    this.showDecisionDialog(decision);
  }

  // 显示决策对话框
  private showDecisionDialog(decision: DecisionRequestPayload): void {
    // 创建决策对话框
    const dialog = document.createElement('div');
    dialog.className = 'decision-dialog';
    dialog.innerHTML = `
      <div class="decision-content">
        <h3>${decision.question}</h3>
        ${decision.description ? `<p>${decision.description}</p>` : ''}
        <div class="decision-options">
          ${decision.options.map(option => `
            <button
              class="decision-option"
              data-option-id="${option.id}"
              data-decision-id="${decision.decisionId}"
            >
              <strong>${option.label}</strong>
              ${option.description ? `<br><small>${option.description}</small>` : ''}
            </button>
          `).join('')}
        </div>
        ${decision.allowCustomInput ? `
          <div class="custom-input">
            <textarea placeholder="或者输入自定义选择..." data-decision-id="${decision.decisionId}"></textarea>
            <button class="submit-custom" data-decision-id="${decision.decisionId}">提交</button>
          </div>
        ` : ''}
      </div>
    `;

    // 添加事件监听
    dialog.querySelectorAll('.decision-option').forEach(button => {
      button.addEventListener('click', (e) => {
        const optionId = (e.target as HTMLElement).dataset.optionId!;
        const decisionId = (e.target as HTMLElement).dataset.decisionId!;
        this.submitDecision(decisionId, optionId);
      });
    });

    if (decision.allowCustomInput) {
      const submitButton = dialog.querySelector('.submit-custom') as HTMLButtonElement;
      submitButton.addEventListener('click', (e) => {
        const decisionId = (e.target as HTMLElement).dataset.decisionId!;
        const textarea = dialog.querySelector('textarea') as HTMLTextAreaElement;
        this.submitDecision(decisionId, undefined, textarea.value);
      });
    }

    document.body.appendChild(dialog);
  }

  // 提交决策
  async submitDecision(
    decisionId: string,
    selectedOption?: string,
    customInput?: any
  ): Promise<void> {
    const decision = this.pendingDecisions.get(decisionId);
    if (!decision) return;

    // 清除超时
    const timeoutId = this.decisionTimeouts.get(decisionId);
    if (timeoutId) {
      clearTimeout(timeoutId);
      this.decisionTimeouts.delete(decisionId);
    }

    // 发送决策响应
    const message = createMessage(
      MessageType.DECISION_RESPONSE,
      {
        decisionId,
        selectedOption,
        customInput,
        timestamp: Date.now()
      } as DecisionResponsePayload,
      'session_id', // 从决策请求中获取
      'user_id'
    );

    await this.client.sendMessage(message);

    // 清理
    this.pendingDecisions.delete(decisionId);
    this.hideDecisionDialog(decisionId);
  }

  // 处理决策超时
  private handleDecisionTimeout(decisionId: string): void {
    const decision = this.pendingDecisions.get(decisionId);
    if (decision && decision.defaultOption) {
      this.submitDecision(decisionId, decision.defaultOption);
    }
  }

  // 隐藏决策对话框
  private hideDecisionDialog(decisionId: string): void {
    const dialog = document.querySelector(`[data-decision-id="${decisionId}"]`)?.closest('.decision-dialog');
    if (dialog) {
      dialog.remove();
    }
  }
}
```

### 7.2 用户输入处理

```typescript
class UserInputManager {
  constructor(private client: AgentWebSocketClient) {}

  // 处理用户输入请求
  private handleUserInputRequest(inputRequest: UserInputRequestPayload): void {
    this.showInputDialog(inputRequest);
  }

  // 显示输入对话框
  private showInputDialog(inputRequest: UserInputRequestPayload): void {
    const dialog = document.createElement('div');
    dialog.className = 'user-input-dialog';

    let inputElement = '';
    switch (inputRequest.inputType) {
      case 'text':
        inputElement = `<input type="text" id="user-input" placeholder="${inputRequest.placeholder || ''}" value="${inputRequest.defaultValue || ''}">`;
        break;
      case 'number':
        inputElement = `<input type="number" id="user-input" placeholder="${inputRequest.placeholder || ''}" value="${inputRequest.defaultValue || ''}">`;
        break;
      case 'date':
        inputElement = `<input type="date" id="user-input" value="${inputRequest.defaultValue || ''}">`;
        break;
      case 'select':
        const options = inputRequest.validation?.options || [];
        inputElement = `
          <select id="user-input">
            ${options.map(option => `<option value="${option}">${option}</option>`).join('')}
          </select>
        `;
        break;
      case 'file':
        inputElement = `<input type="file" id="user-input" multiple>`;
        break;
      default:
        inputElement = `<textarea id="user-input" placeholder="${inputRequest.placeholder || ''}">${inputRequest.defaultValue || ''}</textarea>`;
    }

    dialog.innerHTML = `
      <div class="input-content">
        <h3>${inputRequest.prompt}</h3>
        <div class="input-field">
          ${inputElement}
        </div>
        <div class="input-actions">
          <button id="submit-input">确认</button>
          <button id="cancel-input">取消</button>
        </div>
        <div id="validation-error" class="error-message" style="display: none;"></div>
      </div>
    `;

    // 添加事件监听
    const submitButton = dialog.querySelector('#submit-input') as HTMLButtonElement;
    const cancelButton = dialog.querySelector('#cancel-input') as HTMLButtonElement;
    const inputField = dialog.querySelector('#user-input') as HTMLInputElement;

    submitButton.addEventListener('click', () => {
      const value = this.getInputValue(inputField, inputRequest.inputType);
      const validation = this.validateInput(value, inputRequest.validation);

      if (validation.isValid) {
        this.submitUserInput(inputRequest.requestId, value);
        dialog.remove();
      } else {
        this.showValidationError(dialog, validation.error);
      }
    });

    cancelButton.addEventListener('click', () => {
      dialog.remove();
    });

    document.body.appendChild(dialog);
  }

  // 获取输入值
  private getInputValue(inputElement: HTMLInputElement, inputType: string): any {
    switch (inputType) {
      case 'number':
        return parseFloat(inputElement.value);
      case 'file':
        return Array.from((inputElement as HTMLInputElement).files || []);
      case 'multi-select':
        return Array.from((inputElement as HTMLSelectElement).selectedOptions).map(opt => opt.value);
      default:
        return inputElement.value;
    }
  }

  // 验证输入
  private validateInput(value: any, validation?: any): { isValid: boolean; error?: string } {
    if (!validation) return { isValid: true };

    if (validation.required && (!value || value === '')) {
      return { isValid: false, error: '此字段为必填项' };
    }

    if (typeof value === 'string') {
      if (validation.minLength && value.length < validation.minLength) {
        return { isValid: false, error: `最少需要 ${validation.minLength} 个字符` };
      }
      if (validation.maxLength && value.length > validation.maxLength) {
        return { isValid: false, error: `最多允许 ${validation.maxLength} 个字符` };
      }
      if (validation.pattern && !new RegExp(validation.pattern).test(value)) {
        return { isValid: false, error: '输入格式不正确' };
      }
    }

    return { isValid: true };
  }

  // 提交用户输入
  async submitUserInput(requestId: string, value: any): Promise<void> {
    const message = createMessage(
      MessageType.USER_INPUT_RESPONSE,
      {
        requestId,
        value,
        timestamp: Date.now(),
        isValid: true
      } as UserInputResponsePayload,
      'session_id',
      'user_id'
    );

    await this.client.sendMessage(message);
  }

  // 显示验证错误
  private showValidationError(dialog: HTMLElement, error?: string): void {
    const errorElement = dialog.querySelector('#validation-error') as HTMLElement;
    if (errorElement && error) {
      errorElement.textContent = error;
      errorElement.style.display = 'block';
    }
  }
}
```

## 8. 状态同步API

### 8.1 状态同步管理

```typescript
class StateManager {
  private localState: Map<string, any> = new Map();
  private stateVersions: Map<string, number> = new Map();
  private syncQueue: Array<{ stateId: string, data: any }> = [];
  private syncInProgress: boolean = false;

  constructor(private client: AgentWebSocketClient) {
    this.setupEventListeners();
    this.startPeriodicSync();
  }

  private setupEventListeners(): void {
    this.client.on<StateSyncPayload>(MessageType.STATE_SYNC, (message) => {
      this.handleRemoteStateSync(message.payload);
    });

    this.client.on<ContextUpdatePayload>(MessageType.CONTEXT_UPDATE, (message) => {
      this.handleContextUpdate(message.payload);
    });
  }

  // 设置本地状态
  setState(stateId: string, data: any, immediate: boolean = false): void {
    this.localState.set(stateId, data);
    const version = (this.stateVersions.get(stateId) || 0) + 1;
    this.stateVersions.set(stateId, version);

    if (immediate) {
      this.syncState(stateId);
    } else {
      this.queueStateSync(stateId, data);
    }
  }

  // 获取本地状态
  getState(stateId: string): any {
    return this.localState.get(stateId);
  }

  // 队列同步
  private queueStateSync(stateId: string, data: any): void {
    // 移除已存在的同一状态
    this.syncQueue = this.syncQueue.filter(item => item.stateId !== stateId);
    this.syncQueue.push({ stateId, data });
  }

  // 立即同步状态
  async syncState(stateId: string): Promise<void> {
    const data = this.localState.get(stateId);
    const version = this.stateVersions.get(stateId) || 0;

    if (!data) return;

    const message = createMessage(
      MessageType.STATE_SYNC,
      {
        stateType: 'conversation',
        stateId,
        state: data,
        version,
        timestamp: Date.now(),
        partial: false
      } as StateSyncPayload,
      'session_id',
      'user_id'
    );

    await this.client.sendMessage(message);
  }

  // 处理远程状态同步
  private handleRemoteStateSync(sync: StateSyncPayload): void {
    const localVersion = this.stateVersions.get(sync.stateId) || 0;

    if (sync.version > localVersion) {
      // 远程版本更新，更新本地状态
      if (sync.partial) {
        // 部分更新
        const currentState = this.localState.get(sync.stateId) || {};
        const updatedState = { ...currentState, ...sync.state };
        this.localState.set(sync.stateId, updatedState);
      } else {
        // 完全替换
        this.localState.set(sync.stateId, sync.state);
      }

      this.stateVersions.set(sync.stateId, sync.version);

      // 触发状态变更事件
      this.notifyStateChange(sync.stateId, sync.state);
    } else if (sync.version < localVersion) {
      // 本地版本更新，向远程推送
      this.syncState(sync.stateId);
    }
    // 版本相同，无需处理
  }

  // 处理上下文更新
  private handleContextUpdate(update: ContextUpdatePayload): void {
    const currentData = this.localState.get(update.contextId) || {};

    switch (update.operation) {
      case 'set':
        this.localState.set(update.contextId, update.updates);
        break;
      case 'update':
      case 'merge':
        this.localState.set(update.contextId, { ...currentData, ...update.updates });
        break;
      case 'delete':
        Object.keys(update.updates).forEach(key => {
          delete currentData[key];
        });
        this.localState.set(update.contextId, currentData);
        break;
    }

    this.notifyStateChange(update.contextId, this.localState.get(update.contextId));
  }

  // 定期同步
  private startPeriodicSync(): void {
    setInterval(() => {
      this.processSyncQueue();
    }, 5000); // 每5秒同步一次队列
  }

  // 处理同步队列
  private async processSyncQueue(): Promise<void> {
    if (this.syncInProgress || this.syncQueue.length === 0) return;

    this.syncInProgress = true;

    try {
      const batch = this.syncQueue.splice(0, 10); // 每次最多同步10个状态

      for (const item of batch) {
        await this.syncState(item.stateId);
      }
    } catch (error) {
      console.error('Sync queue processing failed:', error);
    } finally {
      this.syncInProgress = false;
    }
  }

  // 通知状态变更
  private notifyStateChange(stateId: string, data: any): void {
    document.dispatchEvent(new CustomEvent('stateChanged', {
      detail: { stateId, data }
    }));
  }
}
```

## 9. 错误处理

### 9.1 错误处理策略

```typescript
class ErrorHandler {
  private errorStrategies: Map<ErrorCode, ErrorHandlingStrategy> = new Map();
  private errorQueue: ErrorPayload[] = [];

  constructor() {
    this.setupDefaultStrategies();
  }

  private setupDefaultStrategies(): void {
    // 连接错误 - 自动重试
    this.errorStrategies.set(ErrorCode.CONNECTION_FAILED, {
      retryAttempts: 5,
      retryDelay: 2000,
      exponentialBackoff: true,
      showUserNotification: false,
      logToConsole: true,
      reportToAnalytics: true
    });

    // 认证错误 - 不重试，显示登录
    this.errorStrategies.set(ErrorCode.AUTHENTICATION_FAILED, {
      retryAttempts: 0,
      retryDelay: 0,
      exponentialBackoff: false,
      showUserNotification: true,
      logToConsole: true,
      reportToAnalytics: true
    });

    // 限流错误 - 延迟重试
    this.errorStrategies.set(ErrorCode.RATE_LIMIT_EXCEEDED, {
      retryAttempts: 3,
      retryDelay: 5000,
      exponentialBackoff: true,
      showUserNotification: true,
      logToConsole: true,
      reportToAnalytics: false
    });

    // 智能体错误 - 有限重试
    this.errorStrategies.set(ErrorCode.AGENT_EXECUTION_FAILED, {
      retryAttempts: 2,
      retryDelay: 1000,
      exponentialBackoff: false,
      showUserNotification: true,
      logToConsole: true,
      reportToAnalytics: true
    });
  }

  // 处理错误
  async handleError(error: ErrorPayload, originalRequest?: WebSocketMessage): Promise<boolean> {
    const strategy = this.errorStrategies.get(error.code as ErrorCode);

    if (!strategy) {
      // 未知错误，使用默认策略
      this.handleUnknownError(error);
      return false;
    }

    // 记录错误
    if (strategy.logToConsole) {
      console.error('WebSocket Error:', error);
    }

    // 报告错误
    if (strategy.reportToAnalytics) {
      this.reportError(error);
    }

    // 显示用户通知
    if (strategy.showUserNotification) {
      this.showErrorNotification(error);
    }

    // 尝试重试
    if (error.retryable && strategy.retryAttempts > 0 && originalRequest) {
      return this.attemptRetry(error, originalRequest, strategy);
    }

    return false;
  }

  // 尝试重试
  private async attemptRetry(
    error: ErrorPayload,
    originalRequest: WebSocketMessage,
    strategy: ErrorHandlingStrategy
  ): Promise<boolean> {
    let attempts = 0;

    while (attempts < strategy.retryAttempts) {
      attempts++;

      const delay = strategy.exponentialBackoff
        ? strategy.retryDelay * Math.pow(2, attempts - 1)
        : strategy.retryDelay;

      // 等待重试延迟
      await new Promise(resolve => setTimeout(resolve, delay));

      try {
        // 重新发送原始请求
        await this.resendRequest(originalRequest);

        console.log(`Request retry ${attempts} succeeded`);
        return true;
      } catch (retryError) {
        console.log(`Request retry ${attempts} failed:`, retryError);

        if (attempts >= strategy.retryAttempts) {
          this.showFinalErrorNotification(error, attempts);
        }
      }
    }

    return false;
  }

  // 重发请求
  private async resendRequest(request: WebSocketMessage): Promise<void> {
    // 更新时间戳和ID
    request.id = uuidv4();
    request.timestamp = Date.now();

    // 这里需要访问WebSocket客户端实例
    // 实际实现中应该从依赖注入或事件系统获取
    throw new Error('WebSocket client not available for retry');
  }

  // 显示错误通知
  private showErrorNotification(error: ErrorPayload): void {
    const notification = {
      type: 'error' as const,
      title: this.getErrorTitle(error.code),
      message: error.message,
      timeout: 5000,
      actions: this.getErrorActions(error)
    };

    this.displayNotification(notification);
  }

  // 获取错误标题
  private getErrorTitle(code: string): string {
    const titles: Record<string, string> = {
      [ErrorCode.CONNECTION_FAILED]: '连接失败',
      [ErrorCode.AUTHENTICATION_FAILED]: '认证失败',
      [ErrorCode.RATE_LIMIT_EXCEEDED]: '请求过于频繁',
      [ErrorCode.AGENT_EXECUTION_FAILED]: '智能体执行失败',
      [ErrorCode.WORKFLOW_EXECUTION_FAILED]: '工作流执行失败'
    };

    return titles[code] || '未知错误';
  }

  // 获取错误操作
  private getErrorActions(error: ErrorPayload): Array<{ label: string; action: () => void }> {
    switch (error.code) {
      case ErrorCode.AUTHENTICATION_FAILED:
        return [{
          label: '重新登录',
          action: () => this.redirectToLogin()
        }];

      case ErrorCode.RATE_LIMIT_EXCEEDED:
        return [{
          label: '稍后重试',
          action: () => this.scheduleRetry(error)
        }];

      default:
        return [];
    }
  }

  // 处理未知错误
  private handleUnknownError(error: ErrorPayload): void {
    console.error('Unknown error:', error);

    this.showErrorNotification({
      ...error,
      message: '发生了未知错误，请联系技术支持'
    });

    this.reportError(error);
  }

  // 显示最终错误通知
  private showFinalErrorNotification(error: ErrorPayload, attempts: number): void {
    this.showErrorNotification({
      ...error,
      message: `操作失败，已重试 ${attempts} 次。请检查网络连接或联系技术支持。`
    });
  }

  // 报告错误到分析系统
  private reportError(error: ErrorPayload): void {
    // 实现错误报告逻辑
    const errorReport = {
      code: error.code,
      message: error.message,
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      userId: 'current_user_id', // 从当前状态获取
      sessionId: 'current_session_id'
    };

    // 发送到分析服务
    console.log('Error reported:', errorReport);
  }

  // 显示通知（需要与通知系统集成）
  private displayNotification(notification: any): void {
    // 实现通知显示逻辑
    console.log('Notification:', notification);
  }

  // 重定向到登录页
  private redirectToLogin(): void {
    window.location.href = '/login';
  }

  // 安排重试
  private scheduleRetry(error: ErrorPayload): void {
    if (error.retryAfter) {
      setTimeout(() => {
        // 实现重试逻辑
        console.log('Retrying after delay...');
      }, error.retryAfter);
    }
  }
}
```

## 10. 实际示例

### 10.1 完整聊天应用示例

```typescript
// 完整的聊天应用示例
class ChatApplication {
  private client: AgentWebSocketClient;
  private chatManager: ChatManager;
  private stateManager: StateManager;
  private errorHandler: ErrorHandler;

  constructor() {
    this.client = new AgentWebSocketClient();
    this.chatManager = new ChatManager(this.client);
    this.stateManager = new StateManager(this.client);
    this.errorHandler = new ErrorHandler();

    this.setupApplication();
  }

  private async setupApplication(): Promise<void> {
    try {
      // 连接到服务器
      await this.client.connect('user_token', 'user_123');

      // 设置事件监听
      this.setupEventListeners();

      // 初始化UI
      this.initializeUI();

      console.log('Chat application initialized successfully');
    } catch (error) {
      console.error('Failed to initialize chat application:', error);
      this.errorHandler.handleError({
        code: ErrorCode.CONNECTION_FAILED,
        message: '无法连接到服务器',
        details: { error },
        retryable: true
      });
    }
  }

  private setupEventListeners(): void {
    // 监听聊天响应
    this.chatManager.onChatResponse((response) => {
      this.handleChatResponse(response);
    });

    // 监听打字状态
    this.chatManager.onTypingIndicator((isTyping, userId) => {
      this.updateTypingIndicator(isTyping, userId);
    });

    // 监听状态变更
    document.addEventListener('stateChanged', (event: CustomEvent) => {
      this.handleStateChange(event.detail.stateId, event.detail.data);
    });

    // 监听错误
    this.client.on(MessageType.ERROR, (message) => {
      this.errorHandler.handleError(message.payload);
    });
  }

  private initializeUI(): void {
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) return;

    chatContainer.innerHTML = `
      <div class="chat-header">
        <h2>AI 助手</h2>
        <div class="connection-status" id="connection-status">已连接</div>
      </div>
      <div class="chat-messages" id="chat-messages"></div>
      <div class="typing-indicator" id="typing-indicator" style="display: none;">
        AI 正在输入...
      </div>
      <div class="chat-input">
        <div class="input-container">
          <textarea
            id="message-input"
            placeholder="输入消息..."
            rows="3"
          ></textarea>
          <button id="send-button">发送</button>
          <input type="file" id="file-input" multiple style="display: none;">
          <button id="attach-button">📎</button>
        </div>
      </div>
    `;

    this.setupInputHandlers();
  }

  private setupInputHandlers(): void {
    const messageInput = document.getElementById('message-input') as HTMLTextAreaElement;
    const sendButton = document.getElementById('send-button') as HTMLButtonElement;
    const attachButton = document.getElementById('attach-button') as HTMLButtonElement;
    const fileInput = document.getElementById('file-input') as HTMLInputElement;

    sendButton.addEventListener('click', () => {
      this.sendMessage();
    });

    messageInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    attachButton.addEventListener('click', () => {
      fileInput.click();
    });

    fileInput.addEventListener('change', () => {
      this.handleFileAttachment();
    });
  }

  private async sendMessage(): Promise<void> {
    const messageInput = document.getElementById('message-input') as HTMLTextAreaElement;
    const content = messageInput.value.trim();

    if (!content) return;

    try {
      // 显示用户消息
      this.displayMessage({
        id: uuidv4(),
        type: 'text',
        content,
        sender: '用户',
        senderId: 'user_123',
        timestamp: Date.now(),
        status: 'sending'
      });

      // 清空输入框
      messageInput.value = '';

      // 发送到AI
      await this.chatManager.sendTextMessage(
        content,
        'default_conversation',
        'session_456',
        'user_123'
      );

      // 更新消息状态
      this.updateMessageStatus('sending', 'sent');

    } catch (error) {
      console.error('Failed to send message:', error);
      this.updateMessageStatus('sending', 'failed');

      this.errorHandler.handleError({
        code: ErrorCode.MESSAGE_TOO_LARGE,
        message: '消息发送失败',
        details: { error },
        retryable: true
      });
    }
  }

  private handleChatResponse(response: ChatResponsePayload): void {
    if (response.streaming && !response.isComplete) {
      // 处理流式响应
      this.updateStreamingMessage(response.messageId, response.content);
    } else {
      // 处理完整响应
      this.displayMessage({
        id: response.messageId,
        type: 'text',
        content: response.content,
        sender: response.agentName || 'AI 助手',
        senderId: response.agentId || 'ai',
        timestamp: Date.now(),
        status: 'delivered',
        metadata: {
          toolCalls: response.toolCalls,
          citations: response.citations,
          confidence: response.confidence
        }
      });

      // 显示推理步骤（如果有）
      if (response.reasoning && response.reasoning.length > 0) {
        this.displayReasoningSteps(response.reasoning);
      }

      // 显示知识库引用（如果有）
      if (response.citations && response.citations.length > 0) {
        this.displayCitations(response.citations);
      }
    }
  }

  private displayMessage(message: Message): void {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;

    const messageElement = document.createElement('div');
    messageElement.className = `message ${message.senderId === 'user_123' ? 'user-message' : 'ai-message'}`;
    messageElement.setAttribute('data-message-id', message.id);

    messageElement.innerHTML = `
      <div class="message-header">
        <span class="sender">${message.sender}</span>
        <span class="timestamp">${new Date(message.timestamp).toLocaleTimeString()}</span>
        <span class="status ${message.status}">${this.getStatusText(message.status)}</span>
      </div>
      <div class="message-content">${this.formatMessageContent(message.content)}</div>
      ${message.metadata?.citations ? this.renderCitations(message.metadata.citations) : ''}
    `;

    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  private updateStreamingMessage(messageId: string, content: string): void {
    let messageElement = document.querySelector(`[data-message-id="${messageId}"]`);

    if (!messageElement) {
      // 创建新消息元素
      this.displayMessage({
        id: messageId,
        type: 'text',
        content: '',
        sender: 'AI 助手',
        senderId: 'ai',
        timestamp: Date.now(),
        status: 'delivered'
      });
      messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
    }

    const contentElement = messageElement?.querySelector('.message-content');
    if (contentElement) {
      contentElement.innerHTML = this.formatMessageContent(content);
      contentElement.classList.add('streaming');
    }
  }

  private formatMessageContent(content: string): string {
    // 支持 Markdown 格式
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }

  private renderCitations(citations: KnowledgeCitation[]): string {
    if (!citations || citations.length === 0) return '';

    return `
      <div class="citations">
        <h4>参考文档</h4>
        <ul>
          ${citations.map(citation => `
            <li>
              <a href="#" data-document-id="${citation.documentId}">
                ${citation.documentName}
              </a>
              <span class="score">${Math.round(citation.score * 100)}%</span>
            </li>
          `).join('')}
        </ul>
      </div>
    `;
  }

  private displayReasoningSteps(reasoning: string[]): void {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;

    const reasoningElement = document.createElement('div');
    reasoningElement.className = 'reasoning-steps';
    reasoningElement.innerHTML = `
      <h4>推理过程</h4>
      <ol>
        ${reasoning.map(step => `<li>${step}</li>`).join('')}
      </ol>
    `;

    messagesContainer.appendChild(reasoningElement);
  }

  private updateTypingIndicator(isTyping: boolean, userId?: string): void {
    const indicator = document.getElementById('typing-indicator');
    if (!indicator) return;

    if (isTyping && userId !== 'user_123') {
      indicator.style.display = 'block';
    } else {
      indicator.style.display = 'none';
    }
  }

  private updateMessageStatus(currentStatus: string, newStatus: string): void {
    const messages = document.querySelectorAll(`.message .status.${currentStatus}`);
    messages.forEach(statusElement => {
      statusElement.className = `status ${newStatus}`;
      statusElement.textContent = this.getStatusText(newStatus);
    });
  }

  private getStatusText(status: string): string {
    const statusTexts: Record<string, string> = {
      sending: '发送中',
      sent: '已发送',
      delivered: '已送达',
      failed: '发送失败'
    };

    return statusTexts[status] || status;
  }

  private handleFileAttachment(): void {
    const fileInput = document.getElementById('file-input') as HTMLInputElement;
    const files = fileInput.files;

    if (!files || files.length === 0) return;

    const attachments: Attachment[] = Array.from(files).map(file => ({
      id: uuidv4(),
      type: file.type.startsWith('image/') ? 'image' : 'file',
      name: file.name,
      size: file.size,
      url: URL.createObjectURL(file)
    }));

    // 这里应该上传文件并获取实际URL
    // 为演示目的，直接显示本地URL
    this.displayAttachmentMessage(attachments);
  }

  private displayAttachmentMessage(attachments: Attachment[]): void {
    const content = `发送了 ${attachments.length} 个文件：${attachments.map(a => a.name).join(', ')}`;

    this.displayMessage({
      id: uuidv4(),
      type: 'text',
      content,
      sender: '用户',
      senderId: 'user_123',
      timestamp: Date.now(),
      status: 'sent'
    });
  }

  private handleStateChange(stateId: string, data: any): void {
    console.log('State changed:', stateId, data);

    // 根据状态变更更新UI
    if (stateId === 'conversation_state') {
      this.updateConversationUI(data);
    }
  }

  private updateConversationUI(conversationData: any): void {
    // 实现对话状态UI更新逻辑
    console.log('Updating conversation UI:', conversationData);
  }
}

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
  const app = new ChatApplication();
});
```

## 11. 最佳实践

### 11.1 性能优化

```typescript
// 消息批处理
class MessageBatcher {
  private batchQueue: WebSocketMessage[] = [];
  private batchTimer: number | null = null;
  private readonly batchSize = 10;
  private readonly batchInterval = 100; // 100ms

  constructor(private client: AgentWebSocketClient) {}

  // 添加消息到批次
  addToBatch(message: WebSocketMessage): void {
    this.batchQueue.push(message);

    if (this.batchQueue.length >= this.batchSize) {
      this.flushBatch();
    } else if (this.batchTimer === null) {
      this.batchTimer = window.setTimeout(() => {
        this.flushBatch();
      }, this.batchInterval);
    }
  }

  // 发送批次
  private async flushBatch(): Promise<void> {
    if (this.batchQueue.length === 0) return;

    const batch = this.batchQueue.splice(0);
    if (this.batchTimer !== null) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    try {
      for (const message of batch) {
        await this.client.sendMessage(message);
      }
    } catch (error) {
      console.error('Batch send failed:', error);
      // 重新排队失败的消息
      this.batchQueue.unshift(...batch);
    }
  }
}

// 内存管理
class MemoryManager {
  private readonly maxMessages = 1000;
  private readonly maxAttachments = 100;

  // 清理旧消息
  cleanupOldMessages(): void {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;

    const messages = messagesContainer.querySelectorAll('.message');
    if (messages.length > this.maxMessages) {
      const toRemove = messages.length - this.maxMessages;
      for (let i = 0; i < toRemove; i++) {
        messages[i].remove();
      }
    }
  }

  // 清理旧附件
  cleanupOldAttachments(): void {
    const attachments = document.querySelectorAll('[data-attachment-url]');
    if (attachments.length > this.maxAttachments) {
      const toRemove = attachments.length - this.maxAttachments;
      for (let i = 0; i < toRemove; i++) {
        const url = attachments[i].getAttribute('data-attachment-url');
        if (url) {
          URL.revokeObjectURL(url);
        }
        attachments[i].remove();
      }
    }
  }
}
```

### 11.2 安全考虑

```typescript
// 输入验证和清理
class InputSanitizer {
  // HTML 清理
  sanitizeHTML(input: string): string {
    const div = document.createElement('div');
    div.textContent = input;
    return div.innerHTML;
  }

  // 文件类型验证
  validateFileType(file: File, allowedTypes: string[]): boolean {
    return allowedTypes.some(type => {
      if (type.endsWith('/*')) {
        return file.type.startsWith(type.slice(0, -1));
      }
      return file.type === type;
    });
  }

  // 文件大小验证
  validateFileSize(file: File, maxSizeBytes: number): boolean {
    return file.size <= maxSizeBytes;
  }

  // 消息长度验证
  validateMessageLength(message: string, maxLength: number): boolean {
    return message.length <= maxLength;
  }

  // URL 验证
  validateURL(url: string): boolean {
    try {
      const urlObj = new URL(url);
      return ['http:', 'https:'].includes(urlObj.protocol);
    } catch {
      return false;
    }
  }
}

// 速率限制
class RateLimiter {
  private requestCounts: Map<string, number[]> = new Map();
  private readonly windowSize = 60000; // 1分钟
  private readonly maxRequests = 60; // 每分钟最多60个请求

  // 检查是否允许请求
  isAllowed(userId: string): boolean {
    const now = Date.now();
    const userRequests = this.requestCounts.get(userId) || [];

    // 清理过期的请求记录
    const validRequests = userRequests.filter(timestamp =>
      now - timestamp < this.windowSize
    );

    if (validRequests.length >= this.maxRequests) {
      return false;
    }

    // 记录当前请求
    validRequests.push(now);
    this.requestCounts.set(userId, validRequests);

    return true;
  }

  // 获取剩余请求数
  getRemainingRequests(userId: string): number {
    const userRequests = this.requestCounts.get(userId) || [];
    const now = Date.now();
    const validRequests = userRequests.filter(timestamp =>
      now - timestamp < this.windowSize
    );

    return Math.max(0, this.maxRequests - validRequests.length);
  }
}
```

### 11.3 测试示例

```typescript
// 单元测试示例
describe('AgentWebSocketClient', () => {
  let client: AgentWebSocketClient;
  let mockWebSocket: any;

  beforeEach(() => {
    mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn()
    };

    // Mock WebSocket constructor
    (global as any).WebSocket = jest.fn(() => mockWebSocket);

    client = new AgentWebSocketClient();
  });

  test('should send message successfully', async () => {
    const message = createMessage(
      MessageType.CHAT_MESSAGE,
      { content: 'test', messageType: 'text', conversationId: 'conv_1' },
      'session_1',
      'user_1'
    );

    await client.sendMessage(message);

    expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify(message));
  });

  test('should handle connection errors', async () => {
    const errorHandler = jest.fn();
    client.on(MessageType.ERROR, errorHandler);

    // Simulate connection error
    mockWebSocket.onerror({ error: 'Connection failed' });

    expect(errorHandler).toHaveBeenCalled();
  });
});

// 集成测试示例
describe('ChatManager Integration', () => {
  test('should handle complete chat flow', async () => {
    const client = new AgentWebSocketClient();
    const chatManager = new ChatManager(client);

    // Mock server responses
    const responseHandler = jest.fn();
    chatManager.onChatResponse(responseHandler);

    // Send message
    await chatManager.sendTextMessage(
      'Hello AI',
      'conv_1',
      'session_1',
      'user_1'
    );

    // Simulate server response
    const response: ChatResponsePayload = {
      content: 'Hello! How can I help you?',
      messageId: 'msg_1',
      conversationId: 'conv_1',
      streaming: false,
      isComplete: true
    };

    // Trigger response handler
    client.handleMessage(createMessage(MessageType.CHAT_RESPONSE, response, 'session_1', 'user_1'));

    expect(responseHandler).toHaveBeenCalledWith(response);
  });
});
```

这份API文档为前端开发团队提供了完整的智能体交互协议使用指南，包含了所有必要的类型定义、使用示例和最佳实践。开发团队可以基于这个文档快速构建功能完整的智能体对话和工作流应用。