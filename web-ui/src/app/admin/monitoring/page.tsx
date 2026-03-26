'use client';

import { useEffect, useState } from 'react';
import { MonitoringOverview, getAllServicesMonitoring } from '@/lib/api/monitoring';
import { ServiceStatus } from '@/components/ServiceStatus';
import Link from 'next/link';

const MONITORING_URLS = {
  mcpGateway: '/api/mcp/monitoring',
  workflowEngine: '/api/v1/monitoring',
  authService: '/api/auth-monitoring',
};

export default function MonitoringPage() {
  const [overview, setOverview] = useState<MonitoringOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = async () => {
    try {
      setLoading(true);
      const data = await getAllServicesMonitoring();
      setOverview(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setOverview(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
    const interval = setInterval(fetchOverview, 5000);
    return () => clearInterval(interval);
  }, []);

  const getOverallStatusColor = (status: string) => {
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

  if (loading && !overview) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            <div className="h-64 bg-gray-200 rounded"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* 页面标题和导航 */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900">系统监控</h1>
          <div className="flex gap-2">
            <Link
              href="/admin/monitoring/services"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              服务详情
            </Link>
            <Link
              href="/admin/monitoring/logs"
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              日志查看
            </Link>
            <button
              onClick={fetchOverview}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              刷新
            </button>
          </div>
        </div>

        {/* 整体状态卡片 */}
        {overview && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-2">系统状态总览</h2>
                <div className="flex items-center gap-4">
                  <div>
                    <span className="text-sm text-gray-500">整体状态:</span>
                    <span
                      className={`ml-2 px-3 py-1 rounded-full text-sm font-medium border ${getOverallStatusColor(
                        overview.overall_status
                      )}`}
                    >
                      {overview.overall_status.toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">总告警数:</span>
                    <span className="ml-2 text-lg font-semibold">{overview.total_alerts}</span>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">严重告警:</span>
                    <span className="ml-2 text-lg font-semibold text-red-600">
                      {overview.critical_alerts}
                    </span>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">服务数量:</span>
                    <span className="ml-2 text-lg font-semibold">{overview.services.length}</span>
                  </div>
                </div>
              </div>
              <div className="text-sm text-gray-500">
                最后更新: {new Date(overview.timestamp).toLocaleString()}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-red-500 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* 服务状态卡片 */}
      <div className="space-y-6">
        {overview?.services.map((service) => (
          <ServiceStatus
            key={service.service_name}
            serviceName={service.service_name}
            monitoringUrl={
              service.service_name === 'mcp-gateway'
                ? MONITORING_URLS.mcpGateway
                : service.service_name === 'workflow-engine'
                  ? MONITORING_URLS.workflowEngine
                  : MONITORING_URLS.authService
            }
            refreshInterval={5000}
          />
        ))}
      </div>
    </div>
  );
}
