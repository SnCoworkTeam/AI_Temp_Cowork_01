/**
 * 工作流API客户端
 */
import { workflowEngineClient } from './client';

export interface Workflow {
  name: string;
  description: string;
  version: string;
}

export interface WorkflowExecutionRequest {
  workflow_name: string;
  input_data: Record<string, any>;
  context?: Record<string, any>;
}

export interface WorkflowExecutionResponse {
  success: boolean;
  execution_id?: string;
  result: any;
  workflow_name: string;
  error?: string;
}

// 注意：如果使用 API Gateway，workflowEngineClient 的 baseUrl 已经是 /api/workflows
// workflow-engine 的实际路径是 /v1/...，所以通过 API Gateway 时需要加上 /v1 前缀
const getWorkflowPath = (path: string) => {
  const baseUrl = (workflowEngineClient as any).baseUrl || '';

  // 调试：记录路径构建过程
  if (process.env.NODE_ENV === 'development') {
    console.log('[workflow.ts] getWorkflowPath:', { baseUrl, inputPath: path });
  }

  // 清理输入路径，移除可能的前缀
  // 保留路径开头的 /，但移除 /api/v1/workflows, /api/workflows, /v1/workflows, /workflows 等前缀
  let cleanPath = path
    .replace(/^\/api\/v1\/workflows\//, '/') // 保留后面的路径，只移除前缀
    .replace(/^\/api\/v1\/workflows$/, '') // 完全匹配时返回空
    .replace(/^\/api\/v1\/workflows/, '') // 其他情况移除前缀
    .replace(/^\/api\/workflows\//, '/') // 保留后面的路径，只移除前缀
    .replace(/^\/api\/workflows$/, '') // 完全匹配时返回空
    .replace(/^\/api\/workflows/, '') // 其他情况移除前缀
    .replace(/^\/v1\/workflows\//, '/') // 保留后面的路径，只移除前缀
    .replace(/^\/v1\/workflows$/, '') // 完全匹配时返回空
    .replace(/^\/v1\/workflows/, '') // 其他情况移除前缀
    .replace(/^\/workflows\//, '/') // 保留后面的路径，只移除前缀
    .replace(/^\/workflows$/, '') // 完全匹配时返回空
    .replace(/^\/workflows/, ''); // 其他情况移除前缀

  // 确保路径以 / 开头（如果cleanPath不为空且不是空字符串）
  if (cleanPath && cleanPath !== '' && !cleanPath.startsWith('/')) {
    cleanPath = '/' + cleanPath;
  }

  // 如果 baseUrl 包含 /api/workflows（通过 API Gateway）
  // API Gateway 会将 /api/workflows/{path} 转发到 workflow-engine 的 /api/v1/workflows/{path}
  if (baseUrl.includes('/api/workflows')) {
    // 通过 API Gateway 访问
    // baseUrl 是 /api/workflows
    // API Gateway 会将 /api/workflows/{path} 转发到 workflow-engine 的 /api/v1/workflows/{path}
    // 所以这里直接返回 cleanPath（不包含 /workflows 前缀）
    // 例如：cleanPath = '/abc123' -> 最终URL = /api/workflows/abc123 -> 转发到 /api/v1/workflows/abc123

    if (!cleanPath || cleanPath === '' || cleanPath === '/') {
      // 列表请求，返回空字符串，API Gateway 会转发到 /api/v1/workflows
      const finalPath = '';
      if (process.env.NODE_ENV === 'development') {
        console.log(
          '[workflow.ts] Final path (API Gateway, list):',
          finalPath,
          '-> /api/v1/workflows'
        );
      }
      return finalPath;
    }

    // 单个工作流ID或其他路径
    // 直接返回 cleanPath，API Gateway 会将其转发到 /api/v1/workflows{cleanPath}
    // 例如：cleanPath = '/abc123' -> 最终URL = /api/workflows/abc123 -> 转发到 /api/v1/workflows/abc123
    const finalPath = cleanPath;
    if (process.env.NODE_ENV === 'development') {
      console.log(
        '[workflow.ts] Final path (API Gateway):',
        finalPath,
        '-> /api/v1/workflows' + finalPath
      );
    }
    return finalPath;
  }

  // 直接访问 workflow-engine 时，workflow-engine 的路由是 /api/v1/workflows
  // 所以需要添加 /api/v1/workflows 前缀
  const finalPath = `/api/v1/workflows${cleanPath || ''}`;
  if (process.env.NODE_ENV === 'development') {
    console.log('[workflow.ts] Final path (direct access):', finalPath);
  }
  return finalPath;
};

export async function getWorkflows(): Promise<Workflow[]> {
  return workflowEngineClient.get<Workflow[]>(getWorkflowPath('/workflows'));
}

export async function getWorkflowInfo(workflowName: string): Promise<Workflow> {
  return workflowEngineClient.get<Workflow>(getWorkflowPath(`/workflows/${workflowName}`));
}

export async function executeWorkflow(
  workflowName: string,
  inputData: Record<string, any>,
  context?: Record<string, any>
): Promise<WorkflowExecutionResponse> {
  return workflowEngineClient.post<WorkflowExecutionResponse>(
    getWorkflowPath('/workflows/execute'),
    {
      workflow_name: workflowName,
      input_data: inputData,
      context,
    }
  );
}

export async function getExecutionStatus(executionId: string): Promise<Record<string, any>> {
  return workflowEngineClient.get<Record<string, any>>(
    getWorkflowPath(`/workflows/executions/${executionId}`)
  );
}

export async function saveWorkflow(
  workflowConfig: Record<string, any>,
  overwrite: boolean = false
): Promise<{ workflow_id: string; workflow_name: string; message: string }> {
  try {
    const path = getWorkflowPath('/workflows');
    console.log(
      '[workflow.ts] saveWorkflow - calling path:',
      path,
      'baseUrl:',
      (workflowEngineClient as any).baseUrl
    );

    return await workflowEngineClient.post<{
      workflow_id: string;
      workflow_name: string;
      message: string;
    }>(path, {
      workflow: workflowConfig,
      overwrite,
    });
  } catch (error: any) {
    // 检查是否是404错误（端点可能不存在）
    const is404 =
      error?.statusCode === 404 ||
      error?.status === 404 ||
      error?.response?.status === 404 ||
      error?.response?.statusCode === 404 ||
      (error?.message &&
        (error.message.includes('404') ||
          error.message.includes('Not Found') ||
          error.message.includes('not found')));

    if (is404) {
      // 404错误：端点不存在，返回友好的错误信息
      const friendlyError: any = new Error('工作流保存功能暂未实现（API端点不存在）');
      friendlyError.statusCode = 404;
      friendlyError.details = '工作流引擎的保存接口尚未实现，请联系管理员';
      throw friendlyError;
    }

    // 如果工作流已存在且未设置 overwrite，自动使用 overwrite=true 重试
    if (
      !overwrite &&
      error?.statusCode === 400 &&
      (error?.message?.includes('already exists') ||
        error?.details?.includes('already exists') ||
        error?.message?.includes('Use overwrite=True'))
    ) {
      console.log('[workflow.ts] Workflow already exists, retrying with overwrite=true');
      return await workflowEngineClient.post<{
        workflow_id: string;
        workflow_name: string;
        message: string;
      }>(getWorkflowPath('/workflows'), {
        workflow: workflowConfig,
        overwrite: true,
      });
    }
    throw error;
  }
}

export async function getWorkflow(workflowId: string): Promise<Record<string, any>> {
  // 直接使用工作流ID，getWorkflowPath 会处理路径转换
  // API Gateway 会将 /api/workflows/{id} 转发到 /api/v1/workflows/{id}
  return workflowEngineClient.get<Record<string, any>>(getWorkflowPath(`/${workflowId}`));
}

export interface WorkflowListItem {
  workflow_id: string;
  name: string;
  description?: string;
  status?: string;
  version?: string;
  created_at?: string;
  updated_at?: string;
}

export async function listWorkflows(): Promise<{ workflows: WorkflowListItem[] }> {
  try {
    // 使用正确的路径：/workflows（getWorkflowPath 会自动添加 /v1 前缀）
    const path = getWorkflowPath('/workflows');
    const response = await workflowEngineClient.get<{ workflows: WorkflowListItem[] }>(path);
    return response;
  } catch (error: any) {
    // 404 错误时，静默处理，不显示错误日志
    // 检查是否是404错误（可能是 statusCode 或 status）
    const is404 =
      error?.statusCode === 404 ||
      error?.status === 404 ||
      error?.response?.status === 404 ||
      error?.response?.statusCode === 404 ||
      (error?.message &&
        (error.message.includes('404') ||
          error.message.includes('Not Found') ||
          error.message.includes('not found'))) ||
      (error?.toString && error.toString().includes('404'));

    // 404错误完全静默处理，不输出任何日志
    if (!is404) {
      console.error('[workflow.ts] Failed to list workflows:', error);
    }
    // 如果失败，返回空列表而不是抛出错误
    return { workflows: [] };
  }
}

export async function executeWorkflowById(
  workflowId: string,
  inputData: Record<string, any>,
  context?: Record<string, any>
): Promise<WorkflowExecutionResponse> {
  const path = getWorkflowPath(`/api/v1/workflows/${workflowId}/execute`);
  return workflowEngineClient.post<WorkflowExecutionResponse>(path, {
    input_data: inputData,
    context,
  });
}
