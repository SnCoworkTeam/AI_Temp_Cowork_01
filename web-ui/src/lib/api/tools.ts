/**
 * MCP工具API客户端
 */
import { mcpGatewayClient } from './client';

export interface Tool {
  name: string;
  description: string;
  parameters?: Record<string, any>;
}

export interface ToolExecutionRequest {
  tool_name: string;
  parameters: Record<string, any>;
}

export interface ToolExecutionResponse {
  success: boolean;
  result: any;
  tool_name: string;
  error?: string;
}

export async function getTools(): Promise<Tool[]> {
  // 如果通过API Gateway访问，路径是 /tools（API Gateway会转发到 /api/tools）
  // 如果直接访问MCP Gateway，路径是 /api/tools
  const baseUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
  const endpoint = baseUrl ? '/tools' : '/api/tools';
  const res = await mcpGatewayClient.get<any>(endpoint);
  if (Array.isArray(res)) return res as Tool[];
  if (res?.tools && Array.isArray(res.tools)) return res.tools as Tool[];
  return [];
}

export async function getToolInfo(toolName: string): Promise<Tool> {
  const baseUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
  const endpoint = baseUrl ? `/tools/${toolName}` : `/api/tools/${toolName}`;
  return mcpGatewayClient.get<Tool>(endpoint);
}

export async function executeTool(
  toolName: string,
  parameters: Record<string, any>
): Promise<ToolExecutionResponse> {
  const baseUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
  const endpoint = baseUrl ? '/tools/execute' : '/api/tools/execute';
  return mcpGatewayClient.post<ToolExecutionResponse>(endpoint, {
    tool_name: toolName,
    parameters,
  });
}
