/**
 * 监控API客户端
 */
import { mcpGatewayClient, apiGatewayClient } from './client';

export interface ServiceHealth {
  service_name: string;
  status: 'healthy' | 'unhealthy' | 'degraded' | 'down' | 'unknown';
  version: string;
  uptime: number;
  last_check: string;
  checks: Record<string, any>;
}

export interface APIStatistics {
  endpoint: string;
  method: string;
  total_requests: number;
  success_count: number;
  error_count: number;
  avg_response_time: number;
  min_response_time: number;
  max_response_time: number;
  p95_response_time: number;
  p99_response_time: number;
}

export interface SystemResourceUsage {
  cpu_percent: number;
  memory_used: number;
  memory_total: number;
  memory_percent: number;
  disk_used: number;
  disk_total: number;
  disk_percent: number;
  network_bytes_sent: number;
  network_bytes_recv: number;
}

export interface Alert {
  id: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  service: string;
  created_at: string;
  resolved_at?: string;
  resolved: boolean;
  metadata: Record<string, any>;
}

export interface Metric {
  name: string;
  metric_type: string;
  description: string;
  unit?: string;
  points: Array<{
    timestamp: string;
    value: number;
    labels: Record<string, string>;
  }>;
}

export interface ServiceMonitoringData {
  service_name: string;
  health: ServiceHealth;
  api_statistics: APIStatistics[];
  metrics: Metric[];
  resource_usage?: SystemResourceUsage;
  alerts: Alert[];
  last_updated: string;
}

export interface MonitoringOverview {
  services: ServiceMonitoringData[];
  total_alerts: number;
  critical_alerts: number;
  system_resource?: SystemResourceUsage;
  overall_status: string;
  timestamp: string;
}

export interface WorkflowExecutionStats {
  workflow_id?: string;
  workflow_name?: string;
  total_executions: number;
  success_count: number;
  failed_count: number;
  running_count: number;
  avg_execution_time: number;
  total_execution_time: number;
}

export interface UserActivityStats {
  user_id?: string;
  username?: string;
  active_sessions: number;
  total_requests: number;
  last_activity?: string;
  login_count: number;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  service: string;
  logger: string;
  message: string;
  context: Record<string, any>;
  traceback?: string;
}

export interface LogQueryParams {
  service?: string;
  level?: string;
  start_time?: string;
  end_time?: string;
  keyword?: string;
  limit?: number;
  offset?: number;
}

export interface LogQueryResponse {
  success: boolean;
  logs: LogEntry[];
  total: number;
  limit: number;
  offset: number;
  timestamp: string;
}

/**
 * 获取MCP Gateway监控数据
 */
export async function getMCPGatewayMonitoring(): Promise<ServiceMonitoringData> {
  try {
    return await mcpGatewayClient.get<ServiceMonitoringData>('/monitoring');
  } catch (error: any) {
    if (error?.statusCode === 404) {
      return mcpGatewayClient.get<ServiceMonitoringData>('/api/monitoring');
    }
    throw error;
  }
}

/**
 * 获取Workflow Engine监控数据
 */
export async function getWorkflowEngineMonitoring(): Promise<ServiceMonitoringData> {
  // 监控API在 /api/v1/monitoring，通过 API Gateway 访问
  return apiGatewayClient.get<ServiceMonitoringData>('/api/v1/monitoring');
}

/**
 * 获取Auth Service监控数据
 */
export async function getAuthServiceMonitoring(): Promise<ServiceMonitoringData> {
  const response = await fetch('/api/auth-monitoring');
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
}

/**
 * 获取所有服务监控数据
 */
export async function getAllServicesMonitoring(): Promise<MonitoringOverview> {
  const [mcpGateway, workflowEngine, authService] = await Promise.allSettled([
    getMCPGatewayMonitoring(),
    getWorkflowEngineMonitoring(),
    getAuthServiceMonitoring(),
  ]);

  const services: ServiceMonitoringData[] = [];

  if (mcpGateway.status === 'fulfilled') {
    services.push(mcpGateway.value);
  }
  if (workflowEngine.status === 'fulfilled') {
    services.push(workflowEngine.value);
  }
  if (authService.status === 'fulfilled') {
    services.push(authService.value);
  }

  const total_alerts = services.reduce((sum, s) => sum + s.alerts.length, 0);
  const critical_alerts = services.reduce(
    (sum, s) => sum + s.alerts.filter((a) => a.level === 'critical' || a.level === 'error').length,
    0
  );

  // 计算整体状态
  let overall_status = 'healthy';
  if (services.some((s) => s.health.status === 'down')) {
    overall_status = 'down';
  } else if (services.some((s) => s.health.status === 'unhealthy')) {
    overall_status = 'unhealthy';
  } else if (services.some((s) => s.health.status === 'degraded')) {
    overall_status = 'degraded';
  }

  return {
    services,
    total_alerts,
    critical_alerts,
    system_resource: services[0]?.resource_usage,
    overall_status,
    timestamp: new Date().toISOString(),
  };
}

/**
 * 获取工作流执行统计
 */
export async function getWorkflowExecutionStats(): Promise<{
  workflow_execution_stats: WorkflowExecutionStats[];
  timestamp: string;
}> {
  // 监控API在 /api/v1/monitoring，不在 /api/workflows 下
  // 所以需要直接通过 API Gateway 访问
  const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://127.0.0.1:8080';
  try {
    const response = await fetch(`${API_GATEWAY_URL}/api/v1/monitoring/workflow-stats`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        // 柔性降级：如果接口不存在或返回404，则返回空数据，避免前端报错
        return { workflow_execution_stats: [], timestamp: new Date().toISOString() };
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  } catch (e: any) {
    // 柔性降级：如果接口不存在或返回404，则返回空数据，避免前端报错
    if (e?.statusCode === 404 || e?.status === 404 || e?.message?.includes('404')) {
      return { workflow_execution_stats: [], timestamp: new Date().toISOString() };
    }
    throw e;
  }
}

/**
 * 获取用户活跃度统计
 */
export async function getUserActivityStats(): Promise<{
  user_activity_stats: UserActivityStats[];
  timestamp: string;
}> {
  try {
    const response = await fetch('/api/auth-monitoring/user-activity');
    if (!response.ok) {
      if (response.status === 404) {
        return { user_activity_stats: [], timestamp: new Date().toISOString() };
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  } catch (e: any) {
    if (e?.statusCode === 404 || e?.status === 404 || e?.message?.includes('404')) {
      return { user_activity_stats: [], timestamp: new Date().toISOString() };
    }
    throw e;
  }
}

/**
 * 查询日志
 */
export async function queryLogs(params: LogQueryParams): Promise<LogQueryResponse> {
  const queryString = new URLSearchParams();
  if (params.service) queryString.append('service', params.service);
  if (params.level) queryString.append('level', params.level);
  if (params.start_time) queryString.append('start_time', params.start_time);
  if (params.end_time) queryString.append('end_time', params.end_time);
  if (params.keyword) queryString.append('keyword', params.keyword);
  if (params.limit) queryString.append('limit', params.limit.toString());
  if (params.offset) queryString.append('offset', params.offset.toString());

  // 这里应该有一个统一的日志查询端点，暂时返回空结果
  // 实际实现需要后端提供统一的日志查询API
  return {
    success: true,
    logs: [],
    total: 0,
    limit: params.limit || 100,
    offset: params.offset || 0,
    timestamp: new Date().toISOString(),
  };
}
