'use client';

import { useEffect, useState } from 'react';
import { ServiceMonitoringData, ServiceHealth } from '@/lib/api/monitoring';

interface ServiceStatusProps {
  serviceName: string;
  monitoringUrl: string;
  refreshInterval?: number;
}

export function ServiceStatus({
  serviceName,
  monitoringUrl,
  refreshInterval = 5000,
}: ServiceStatusProps) {
  const [monitoringData, setMonitoringData] = useState<ServiceMonitoringData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMonitoringData = async () => {
    try {
      setLoading(true);
      const response = await fetch(monitoringUrl);
      if (!response.ok) {
        throw new Error(`Failed to fetch monitoring data: ${response.statusText}`);
      }
      const data = await response.json();
      setMonitoringData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setMonitoringData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitoringData();
    const interval = setInterval(fetchMonitoringData, refreshInterval);
    return () => clearInterval(interval);
  }, [monitoringUrl, refreshInterval]);

  if (loading && !monitoringData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!monitoringData) {
    return null;
  }

  const { health, api_statistics, resource_usage, alerts } = monitoringData;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 border-green-500';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 border-yellow-500';
      case 'unhealthy':
      case 'down':
        return 'bg-red-100 text-red-800 border-red-500';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-500';
    }
  };

  const getAlertLevelColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-500';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-500';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-500';
      case 'info':
        return 'bg-blue-100 text-blue-800 border-blue-500';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-500';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* 服务状态 */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{serviceName}</h3>
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(
              health.status
            )}`}
          >
            {health.status.toUpperCase()}
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">版本</p>
            <p className="text-lg font-semibold">{health.version}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">运行时间</p>
            <p className="text-lg font-semibold">{Math.floor(health.uptime / 3600)}h</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">最后检查</p>
            <p className="text-sm font-semibold">
              {new Date(health.last_check).toLocaleTimeString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">API端点</p>
            <p className="text-lg font-semibold">{api_statistics.length}</p>
          </div>
        </div>
      </div>

      {/* 资源使用情况 */}
      {resource_usage && (
        <div className="mb-6">
          <h4 className="text-md font-semibold text-gray-900 mb-3">资源使用情况</h4>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>CPU</span>
                <span>{resource_usage.cpu_percent.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    resource_usage.cpu_percent > 80
                      ? 'bg-red-500'
                      : resource_usage.cpu_percent > 60
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                  }`}
                  style={{ width: `${resource_usage.cpu_percent}%` }}
                ></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>内存</span>
                <span>{resource_usage.memory_percent.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    resource_usage.memory_percent > 80
                      ? 'bg-red-500'
                      : resource_usage.memory_percent > 60
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                  }`}
                  style={{ width: `${resource_usage.memory_percent}%` }}
                ></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>磁盘</span>
                <span>{resource_usage.disk_percent.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    resource_usage.disk_percent > 80
                      ? 'bg-red-500'
                      : resource_usage.disk_percent > 60
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                  }`}
                  style={{ width: `${resource_usage.disk_percent}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* API统计 */}
      {api_statistics.length > 0 && (
        <div className="mb-6">
          <h4 className="text-md font-semibold text-gray-900 mb-3">API统计</h4>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    端点
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    请求数
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    成功率
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    平均响应时间
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {api_statistics.slice(0, 5).map((stat, idx) => (
                  <tr key={idx}>
                    <td className="px-4 py-2 text-sm text-gray-900">
                      {stat.method} {stat.endpoint}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-900">{stat.total_requests}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">
                      {stat.total_requests > 0
                        ? ((stat.success_count / stat.total_requests) * 100).toFixed(1)
                        : 0}
                      %
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-900">
                      {stat.avg_response_time.toFixed(2)}ms
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 告警 */}
      {alerts.length > 0 && (
        <div>
          <h4 className="text-md font-semibold text-gray-900 mb-3">告警</h4>
          <div className="space-y-2">
            {alerts.slice(0, 5).map((alert) => (
              <div
                key={alert.id}
                className={`p-3 rounded-lg border-l-4 ${getAlertLevelColor(alert.level)}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-sm">{alert.title}</p>
                    <p className="text-sm mt-1">{alert.message}</p>
                  </div>
                  <span className="text-xs text-gray-500">
                    {new Date(alert.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
