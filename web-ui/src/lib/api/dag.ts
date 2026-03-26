/**
 * DAG Orchestrator API客户端
 */
import { apiGatewayClient, dagOrchestratorClient } from './client';

export interface DAGExecutionRequest {
  user_input: string;
  context?: Record<string, any>;
  priority?: string;
  callback_url?: string;
  user_id?: string;
}

export interface DAGExecutionResult {
  execution_id: string;
  dag_id?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  results: Record<string, any>;
  final_output?: string;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  execution_time?: number;
}

export interface DAGPlan {
  dag_id: string;
  task_nodes: Record<
    string,
    {
      node_id: string;
      name: string;
      description: string;
      task_type: string;
      target_service: string;
      action: string;
      parameters: Record<string, any>;
      dependencies: string[];
    }
  >;
  entry_nodes: string[];
  exit_nodes: string[];
  metadata: Record<string, any>;
}

/**
 * 执行复杂任务（通过DAG编排）
 */
export async function executeDAGTask(request: DAGExecutionRequest): Promise<DAGExecutionResult> {
  const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL;

  // 如果配置了 API Gateway，使用 API Gateway；否则直接访问 DAG Orchestrator
  if (API_GATEWAY_URL) {
    // 通过 API Gateway: /api/dag/tasks/execute -> dag-orchestrator:8009/api/v1/tasks/execute
    return apiGatewayClient.post<DAGExecutionResult>('/api/dag/tasks/execute', request);
  } else {
    // 直接访问 DAG Orchestrator: /api/v1/tasks/execute
    return dagOrchestratorClient.post<DAGExecutionResult>('/tasks/execute', request);
  }
}

/**
 * 仅分解任务（不执行）
 */
export async function decomposeTask(
  userInput: string,
  context?: Record<string, any>
): Promise<DAGPlan> {
  const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL;

  if (API_GATEWAY_URL) {
    return apiGatewayClient.post<DAGPlan>('/api/dag/tasks/decompose', {
      user_input: userInput,
      context: context || {},
    });
  } else {
    return dagOrchestratorClient.post<DAGPlan>('/tasks/decompose', {
      user_input: userInput,
      context: context || {},
    });
  }
}

/**
 * 获取执行状态
 */
export async function getDAGExecutionStatus(executionId: string): Promise<DAGExecutionResult> {
  const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL;

  if (API_GATEWAY_URL) {
    return apiGatewayClient.get<DAGExecutionResult>(`/api/dag/executions/${executionId}`);
  } else {
    return dagOrchestratorClient.get<DAGExecutionResult>(`/executions/${executionId}`);
  }
}
