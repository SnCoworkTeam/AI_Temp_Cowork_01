/**
 * 工作流API客户端
 */
import { workflowEngineClient } from './client'

export interface Workflow {
  name: string
  description: string
  version: string
}

export interface WorkflowExecutionRequest {
  workflow_name: string
  input_data: Record<string, any>
  context?: Record<string, any>
}

export interface WorkflowExecutionResponse {
  success: boolean
  execution_id?: string
  result: any
  workflow_name: string
  error?: string
}

// 注意：如果使用 API Gateway，workflowEngineClient 的 baseUrl 已经是 /api/workflows
// workflow-engine 的实际路径是 /v1/...，所以通过 API Gateway 时需要加上 /v1 前缀
const getWorkflowPath = (path: string) => {
  const baseUrl = (workflowEngineClient as any).baseUrl || ''
  // 如果 baseUrl 包含 /api/workflows（通过 API Gateway），需要添加 /v1 前缀
  if (baseUrl.includes('/api/workflows') && !baseUrl.includes('/api/workflows/v1')) {
    // 移除路径中的 /api/v1 或 /api，然后添加 /v1
    let cleanPath = path.replace(/^\/api\/v1/, '').replace(/^\/api/, '')
    // 如果 cleanPath 已经以 /v1 开头，直接返回
    if (cleanPath.startsWith('/v1')) {
      return cleanPath
    }
    // 否则添加 /v1 前缀
    return `/v1${cleanPath}`
  }
  // 直接访问 workflow-engine 时，保持原路径
  return path
}

export async function getWorkflows(): Promise<Workflow[]> {
  return workflowEngineClient.get<Workflow[]>(getWorkflowPath('/workflows'))
}

export async function getWorkflowInfo(workflowName: string): Promise<Workflow> {
  return workflowEngineClient.get<Workflow>(getWorkflowPath(`/workflows/${workflowName}`))
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
  )
}

export async function getExecutionStatus(
  executionId: string
): Promise<Record<string, any>> {
  return workflowEngineClient.get<Record<string, any>>(
    getWorkflowPath(`/workflows/executions/${executionId}`)
  )
}

export async function saveWorkflow(
  workflowConfig: Record<string, any>,
  overwrite: boolean = false
): Promise<{ workflow_id: string; workflow_name: string; message: string }> {
  try {
    return await workflowEngineClient.post<{ workflow_id: string; workflow_name: string; message: string }>(
      getWorkflowPath('/workflows'),
      {
        workflow: workflowConfig,
        overwrite
      }
    )
  } catch (error: any) {
    // 如果工作流已存在且未设置 overwrite，自动使用 overwrite=true 重试
    if (
      !overwrite &&
      error?.statusCode === 400 &&
      (error?.message?.includes('already exists') || 
       error?.details?.includes('already exists') ||
       error?.message?.includes('Use overwrite=True'))
    ) {
      console.log('Workflow already exists, retrying with overwrite=true')
      return await workflowEngineClient.post<{ workflow_id: string; workflow_name: string; message: string }>(
        getWorkflowPath('/workflows'),
        {
          workflow: workflowConfig,
          overwrite: true
        }
      )
    }
    throw error
  }
}

export async function getWorkflow(
  workflowId: string
): Promise<Record<string, any>> {
  return workflowEngineClient.get<Record<string, any>>(
    getWorkflowPath(`/workflows/${workflowId}`)
  )
}

export interface WorkflowListItem {
  workflow_id: string
  name: string
  description?: string
  status?: string
  version?: string
  created_at?: string
  updated_at?: string
}

export async function listWorkflows(): Promise<{ workflows: WorkflowListItem[] }> {
  try {
    // 使用正确的路径：/workflows（getWorkflowPath 会自动添加 /v1 前缀）
    const path = getWorkflowPath('/workflows')
    const response = await workflowEngineClient.get<{ workflows: WorkflowListItem[] }>(path)
    return response
  } catch (error) {
    // 404 错误时，静默处理，不显示错误日志
    if ((error as any)?.statusCode !== 404) {
      console.error('Failed to list workflows:', error)
    }
    // 如果失败，返回空列表而不是抛出错误
    return { workflows: [] }
  }
}

export async function executeWorkflowById(
  workflowId: string,
  inputData: Record<string, any>,
  context?: Record<string, any>
): Promise<WorkflowExecutionResponse> {
  const path = getWorkflowPath(`/api/v1/workflows/${workflowId}/execute`)
  return workflowEngineClient.post<WorkflowExecutionResponse>(
    path,
    {
      input_data: inputData,
      context,
    }
  )
}

