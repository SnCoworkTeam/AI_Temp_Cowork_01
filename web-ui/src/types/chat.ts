/**
 * 聊天相关类型定义
 */
export type MessageType = 'text' | 'system' | 'workflow' | 'tool' | 'error';

export type MessageStatus = 'sending' | 'sent' | 'failed' | 'delivered';

export interface Message {
  id: string;
  type: MessageType;
  content: string;
  sender: string;
  senderId: string;
  timestamp: number;
  status: MessageStatus;
  metadata?: {
    workflowId?: string;
    workflowName?: string;
    toolName?: string;
    executionId?: string;
    progress?: number;
    error?: string;
    executing?: boolean;
    execution?: any; // 工作流执行结果
    // 动态工作流相关
    workflowMessageId?: string;
    workflowType?: 'dynamic' | 'static';
    workflowChunks?: any[]; // 工作流chunks
    // 知识库相关
    knowledgeCitations?: Array<{
      chunk_id: string;
      document_id: string;
      document_name: string;
      content: string;
      score: number;
    }>;
    sourceDocuments?: string[]; // 文档ID列表
  };
}

export interface ChatSession {
  id: string;
  title: string;
  lastMessage?: string;
  lastMessageTime?: number;
  unreadCount: number;
  createdAt: number;
}

export interface WorkflowExecutionStatus {
  executionId: string;
  workflowId: string;
  workflowName: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  currentNode?: string;
  nodeResults?: Record<string, any>;
  error?: string;
  startTime: number;
  endTime?: number;
}

export interface ToolExecutionStatus {
  toolName: string;
  executionId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
  startTime: number;
  endTime?: number;
}
