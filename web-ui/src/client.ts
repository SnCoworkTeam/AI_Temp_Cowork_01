/**
 * API客户端基础配置
 */

// 优先使用 API Gateway，如果没有则使用直接地址
const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL

const API_BASE_URLS = {
  // API Gateway 基础URL（如果配置了）
  apiGateway: API_GATEWAY_URL || 'http://127.0.0.1:8080',
  // MCP Gateway - 优先使用 API Gateway 的 /api/mcp 路由，否则使用直接地址
  mcpGateway: API_GATEWAY_URL 
    ? `${API_GATEWAY_URL}/api/mcp`
    : (process.env.NEXT_PUBLIC_MCP_GATEWAY_URL || 'http://127.0.0.1:8001'),
  // 如果配置了 API Gateway，workflowEngine 使用 API Gateway；否则使用直接地址
  // API Gateway 路由是 /api/workflows/{path}，workflow-engine 的路由是 /api/v1/...
  // 所以通过 API Gateway 访问时，baseUrl 应该是 /api/workflows，然后在调用时加上 /v1/...
  workflowEngine: API_GATEWAY_URL 
    ? `${API_GATEWAY_URL}/api/workflows`
    : (process.env.NEXT_PUBLIC_WORKFLOW_ENGINE_URL || 'http://127.0.0.1:8002'),
  // 如果配置了 API Gateway，authService 使用 API Gateway；否则使用直接地址
  authService: API_GATEWAY_URL 
    ? `${API_GATEWAY_URL}/api`
    : (process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://127.0.0.1:8003'),
  // 如果配置了 API Gateway，knowledgeBase 使用 API Gateway；否则使用直接地址
  knowledgeBase: API_GATEWAY_URL 
    ? `${API_GATEWAY_URL}/api/knowledge`
    : (process.env.NEXT_PUBLIC_KNOWLEDGE_BASE_URL || 'http://127.0.0.1:8004'),
  // DAG Orchestrator - 优先使用 API Gateway，否则使用直接地址
  dagOrchestrator: API_GATEWAY_URL
    ? `${API_GATEWAY_URL}/api/dag`
    : (process.env.NEXT_PUBLIC_DAG_ORCHESTRATOR_URL || 'http://127.0.0.1:8009/api/v1'),
}

export interface ApiError {
  message: string
  details?: string
  statusCode: number
}

export class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    // 获取访问令牌（如果存在）
    // 优先从 localStorage 获取，然后从 cookie 获取
    let accessToken: string | null = null
    if (typeof window !== 'undefined') {
      // 从 localStorage 获取（主要方式）
      accessToken = localStorage.getItem('access_token')
      
      // 如果 localStorage 没有，尝试从 cookie 获取
      if (!accessToken) {
        const cookieToken = document.cookie
          .split('; ')
          .find(row => row.startsWith('access_token='))
          ?.split('=')[1]
        if (cookieToken) {
          accessToken = cookieToken
        }
      }
    }
    
    const defaultHeaders: HeadersInit = {
      'Content-Type': 'application/json',
    }
    
    // 如果有访问令牌，添加到请求头
    if (accessToken) {
      defaultHeaders['Authorization'] = `Bearer ${accessToken}`
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    })

    if (!response.ok) {
      const error: ApiError = {
        message: `HTTP error! status: ${response.status}`,
        statusCode: response.status,
      }

      try {
        const errorData = await response.json()
        error.message = errorData.detail || errorData.message || error.message
        error.details = errorData.details || errorData.detail || errorData
      } catch {
        // 如果响应不是JSON，使用默认错误消息
      }

      // 对于404错误，不抛出异常，而是返回一个特殊的错误对象
      // 调用方可以检查 statusCode === 404 来决定是否静默处理
      if (response.status === 404) {
        // 标记为404错误，但不打印到控制台
        error.message = 'Resource not found'
      }

      throw error
    }

    return response.json()
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

// 导出预配置的API客户端
export const apiGatewayClient = new ApiClient(API_BASE_URLS.apiGateway)
export const mcpGatewayClient = new ApiClient(API_BASE_URLS.mcpGateway)
export const workflowEngineClient = new ApiClient(API_BASE_URLS.workflowEngine)
export const authServiceClient = new ApiClient(API_BASE_URLS.authService)
export const knowledgeBaseClient = new ApiClient(API_BASE_URLS.knowledgeBase)
export const dagOrchestratorClient = new ApiClient(API_BASE_URLS.dagOrchestrator)

