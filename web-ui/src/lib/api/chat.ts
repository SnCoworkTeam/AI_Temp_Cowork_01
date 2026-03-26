/**
 * 智能聊天API客户端
 * 使用智能路由端点，自动识别意图并路由到合适的服务
 */

import { ApiClient } from './client';

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://127.0.0.1:8080';

const chatClient = new ApiClient(API_GATEWAY_URL);

export interface IntelligentChatRequest {
  message: string;
  conversation_history?: Array<{ role: string; content: string }>;
  user_context?: Record<string, any>;
  stream?: boolean;
}

export interface IntelligentChatResponse {
  success: boolean;
  output?: string;
  intent_analysis?: {
    task_type: string;
    confidence: number;
    reasoning: string;
  };
  strategy?: string;
  error?: string;
  execution_id?: string;
}

/**
 * 智能聊天 - 自动路由到合适的服务
 */
export async function intelligentChat(
  request: IntelligentChatRequest
): Promise<IntelligentChatResponse> {
  try {
    const response = await chatClient.request<IntelligentChatResponse>('/api/chat/intelligent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    return response;
  } catch (error: any) {
    console.error('Intelligent chat failed:', error);
    throw error;
  }
}

/**
 * 直接使用agent-service的智能对话端点
 */
export async function agentChat(request: IntelligentChatRequest): Promise<IntelligentChatResponse> {
  try {
    // 直接调用agent-service的智能对话端点
    const agentServiceUrl = process.env.NEXT_PUBLIC_AGENT_SERVICE_URL || 'http://127.0.0.1:8010';
    const agentClient = new ApiClient(agentServiceUrl);

    const response = await agentClient.request<IntelligentChatResponse>('/api/v1/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    return response;
  } catch (error: any) {
    console.error('Agent chat failed:', error);
    throw error;
  }
}
