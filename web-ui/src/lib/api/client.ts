/**
 * API客户端基础配置
 */
import { getAccessToken, refreshAccessToken } from '../auth';

// 优先使用 API Gateway，如果没有则使用直接地址
const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL;

const isBrowser = typeof window !== 'undefined';
const isLoopbackUrl = (url: string) => /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?/i.test(url);
const safeGetHost = (url: string) => {
  try {
    return new URL(url).host;
  } catch {
    return '';
  }
};
const isLocalBrowser = () =>
  isBrowser && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
const shouldUseGatewayProxy = () => {
  if (!isBrowser) return false;
  if (isLocalBrowser()) return false;

  const gatewayIsLoopback = !API_GATEWAY_URL || isLoopbackUrl(API_GATEWAY_URL);
  if (gatewayIsLoopback) return true;

  const originHost = window.location.host;
  const gatewayHost = safeGetHost(API_GATEWAY_URL || '');
  if (gatewayHost && gatewayHost !== originHost) return true;

  return false;
};

const useGatewayProxy = shouldUseGatewayProxy();
const apiGatewayBase = useGatewayProxy ? '' : API_GATEWAY_URL || 'http://127.0.0.1:8080';

const API_BASE_URLS = {
  // API Gateway 基础URL（如果配置了）
  apiGateway: apiGatewayBase,
  // MCP Gateway - 优先使用 API Gateway 的 /api/mcp 路由，否则使用直接地址
  mcpGateway: useGatewayProxy
    ? '/api/mcp'
    : API_GATEWAY_URL
      ? `${API_GATEWAY_URL}/api/mcp`
      : process.env.NEXT_PUBLIC_MCP_GATEWAY_URL || 'http://127.0.0.1:8001',
  // 如果配置了 API Gateway，workflowEngine 使用 API Gateway；否则使用直接地址
  // API Gateway 路由是 /api/workflows/{path}，workflow-engine 的路由是 /api/v1/...
  // 所以通过 API Gateway 访问时，baseUrl 应该是 /api/workflows，然后在调用时加上 /v1/...
  workflowEngine: useGatewayProxy
    ? '/api/workflows'
    : API_GATEWAY_URL
      ? `${API_GATEWAY_URL}/api/workflows`
      : process.env.NEXT_PUBLIC_WORKFLOW_ENGINE_URL || 'http://127.0.0.1:8002',
  // 如果配置了 API Gateway，authService 使用 API Gateway；否则使用直接地址
  authService: useGatewayProxy
    ? '/api'
    : API_GATEWAY_URL
      ? `${API_GATEWAY_URL}/api`
      : process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://127.0.0.1:8003',
  // 如果配置了 API Gateway，knowledgeBase 使用 API Gateway；否则使用直接地址
  knowledgeBase: useGatewayProxy
    ? '/api/knowledge'
    : API_GATEWAY_URL
      ? `${API_GATEWAY_URL}/api/knowledge`
      : process.env.NEXT_PUBLIC_KNOWLEDGE_BASE_URL || 'http://127.0.0.1:8004',
  // DAG Orchestrator - 优先使用 API Gateway，否则使用直接地址
  dagOrchestrator: useGatewayProxy
    ? '/api/dag'
    : API_GATEWAY_URL
      ? `${API_GATEWAY_URL}/api/dag`
      : process.env.NEXT_PUBLIC_DAG_ORCHESTRATOR_URL || 'http://127.0.0.1:8009/api/v1',
};

export interface ApiError {
  message: string;
  details?: string;
  statusCode: number;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async request<T>(endpoint: string, options: RequestInit = {}, retryOn401: boolean = true): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    // 获取访问令牌（如果存在）
    let accessToken = getAccessToken();

    const hasContentTypeHeader = (headers?: HeadersInit) => {
      if (!headers) return false;
      if (headers instanceof Headers) return headers.has('Content-Type');
      if (Array.isArray(headers)) {
        return headers.some(([key]) => key.toLowerCase() === 'content-type');
      }
      return Object.keys(headers).some((key) => key.toLowerCase() === 'content-type');
    };

    const isFormData =
      typeof FormData !== 'undefined' && options.body instanceof FormData;
    const isBlob = typeof Blob !== 'undefined' && options.body instanceof Blob;
    const isArrayBuffer = options.body instanceof ArrayBuffer;
    const isUrlEncoded =
      typeof URLSearchParams !== 'undefined' && options.body instanceof URLSearchParams;

    const defaultHeaders: HeadersInit = {};
    if (
      !hasContentTypeHeader(options.headers) &&
      !isFormData &&
      !isBlob &&
      !isArrayBuffer &&
      !isUrlEncoded
    ) {
      defaultHeaders['Content-Type'] = 'application/json';
    }

    // 如果有访问令牌，添加到请求头
    if (accessToken) {
      defaultHeaders['Authorization'] = `Bearer ${accessToken}`;
    }

    let response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });

    // 处理 401 错误：尝试刷新 token 并重试
    if (response.status === 401 && retryOn401) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        // 使用新 token 重试请求
        const retryHeaders: HeadersInit = {
          ...defaultHeaders,
          'Authorization': `Bearer ${newToken}`,
          ...options.headers,
        };
        response = await fetch(url, {
          ...options,
          headers: retryHeaders,
        });
      } else {
        // Token 刷新失败，重定向到登录页
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        throw new Error('Authentication failed. Please login again.');
      }
    }

    // 处理 429 错误：请求过于频繁
    if (response.status === 429) {
      const retryAfter = response.headers.get('Retry-After');
      const delay = retryAfter ? parseInt(retryAfter) * 1000 : 2000; // 默认延迟2秒
      console.warn(`Rate limited. Retrying after ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
      // 重试一次
      response = await fetch(url, {
        ...options,
        headers: {
          ...defaultHeaders,
          ...options.headers,
        },
      });
    }

    if (!response.ok) {
      const error: ApiError = {
        message: `HTTP error! status: ${response.status}`,
        statusCode: response.status,
      };

      try {
        const errorData = await response.json();
        error.message = errorData.detail || errorData.message || error.message;
        error.details = errorData.details || errorData.detail || errorData;
      } catch {
        // 如果响应不是JSON，使用默认错误消息
      }

      // 对于404错误，不抛出异常，而是返回一个特殊的错误对象
      // 调用方可以检查 statusCode === 404 来决定是否静默处理
      if (response.status === 404) {
        // 标记为404错误，但不打印到控制台
        error.message = 'Resource not found';
      }

      throw error;
    }

    // 204 No Content 或无响应体时直接返回 undefined，避免解析 JSON 报错
    if (response.status === 204) {
      return undefined as T;
    }

    const contentLength = response.headers.get('Content-Length');
    if (contentLength === '0' || contentLength === null) {
      // 某些服务可能不返回 Content-Length，但实际没有 body，这里尝试安全处理
      try {
        const text = await response.text();
        if (!text) {
          return undefined as T;
        }
        return JSON.parse(text) as T;
      } catch {
        return undefined as T;
      }
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data !== undefined ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

// 导出预配置的API客户端
export const apiGatewayClient = new ApiClient(API_BASE_URLS.apiGateway);
export const mcpGatewayClient = new ApiClient(API_BASE_URLS.mcpGateway);
export const workflowEngineClient = new ApiClient(API_BASE_URLS.workflowEngine);
export const authServiceClient = new ApiClient(API_BASE_URLS.authService);
export const knowledgeBaseClient = new ApiClient(API_BASE_URLS.knowledgeBase);
export const dagOrchestratorClient = new ApiClient(API_BASE_URLS.dagOrchestrator);
