/**
 * 交互协议类型定义
 */

export enum InteractionType {
  EXECUTION_START = 'execution_start',
  EXECUTION_PROGRESS = 'execution_progress',
  EXECUTION_STEP = 'execution_step',
  EXECUTION_PAUSED = 'execution_paused',
  EXECUTION_RESUMED = 'execution_resumed',
  EXECUTION_CANCELLED = 'execution_cancelled',
  EXECUTION_COMPLETED = 'execution_completed',
  EXECUTION_ERROR = 'execution_error',
  USER_INTERACTION_REQUIRED = 'user_interaction_required',
  CONFIRMATION_REQUIRED = 'confirmation_required',
}

export enum ExecutionStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  ERROR = 'error',
  WAITING_FOR_INPUT = 'waiting_for_input',
}

export interface InteractiveMessage {
  type: InteractionType;
  execution_id: string;
  session_id: string;
  timestamp: string;
  data: Record<string, any>;
  actions?: string[];
  progress?: number;
  metadata?: Record<string, any>;
}

export interface UserAction {
  action: string;
  execution_id: string;
  session_id: string;
  parameters?: Record<string, any>;
  timestamp: string;
}

export interface ExecutionState {
  execution_id: string;
  session_id: string;
  status: ExecutionStatus;
  current_step: number;
  total_steps: number;
  progress: number;
  user_input?: string;
  context?: Record<string, any>;
  paused: boolean;
  cancelled: boolean;
  waiting_for_input?: string;
  created_at: string;
  updated_at: string;
}
